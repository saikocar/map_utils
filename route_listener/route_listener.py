import sys
import os
import re
import xml.etree.ElementTree as ET

import rclpy
from rclpy.node import Node

import math

from autoware_planning_msgs.msg import LaneletRoute
from rviz_2d_overlay_msgs.msg import OverlayText

class LaneDataManager:
    def __init__(self):
        self.lane_ids = []
        self.lane_lengths = []

    def clear(self):
        """lane_idsとlane_lengthsを初期化（空にする）"""
        self.lane_ids.clear()
        self.lane_lengths.clear()

    def add(self, lane_id, lane_length):
        """新しいlane_idとその長さを追加"""
        self.lane_ids.append(lane_id)
        self.lane_lengths.append(lane_length)

    def __str__(self):
        """状態を簡易表示用に文字列化"""
        return f"LaneDataManager({len(self.lane_ids)} lanes)"

    def summary(self):
        """格納されているlane_idとその長さを一覧表示"""
        for i, (lid, llen) in enumerate(zip(self.lane_ids, self.lane_lengths)):
            print(f"[{i}] ID: {lid}, Length: {llen:.2f} m")

class ActionDataManager:
    def __init__(self):
        self.action_ids = []
        self.actions = []

    def clear(self):
        """action_idsとactionsを初期化（空にする）"""
        self.action_ids.clear()
        self.actions.clear()

    def add(self, action_id, action):
        """新しいaction_idとその内容を追加"""
        self.action_ids.append(action_id)
        self.actions.append(action)

    def __str__(self):
        """状態を簡易表示用に文字列化"""
        return f"ActionDataManager({len(self.action_ids)} actions)"

    def summary(self):
        """格納されているaction_idと内容を一覧表示"""
        for i, (aid, act) in enumerate(zip(self.action_ids, self.actions)):
            print(f"[{i}] ID: {aid}, Action: {act}")

class RouteListener(Node):
    def __init__(self, osm_tree):
        super().__init__('lanelet_route_listener')
        self.osm_tree = osm_tree  # ElementTree オブジェクトを保持
        self.nodes = {node.attrib['id']: node for node in osm_tree.findall('node')}
        self.ways = {way.attrib['id']: way for way in osm_tree.findall('way')}
        self.relations = osm_tree.findall('relation')
        self.last_lanelet_id = None  # 直近のCurrent ID保持用

        self.lane_data = LaneDataManager()
        self.action_data = ActionDataManager()
        self.signal_ahead = 100

        # LaneletRoute 購読
        self.route_sub = self.create_subscription(
            LaneletRoute,
            '/planning/mission_planning/route',
            self.route_callback,
            10
        )
        self.get_logger().info('Subscribed to /planning/mission_planning/route')

        # Current Lanelet ID 購読
        self.current_id_sub = self.create_subscription(
            OverlayText,
            '/map/lanelet_param/current_lanelet_info_text',
            self.current_id_callback,
            10
        )

        self.extra_info_publisher = self.create_publisher(
            OverlayText,
            '/lanelet_param/extra_info_text',
            1
        )
        self.get_logger().info('Subscribed to /map/lanelet_param/current_lanelet_info_text')

    def publish_extra_info(self, text: str):
        msg = OverlayText()
        msg.action = OverlayText.ADD
        msg.width = 600
        msg.height = 100

        # 背景・前景色
        msg.bg_color.r = 0.0
        msg.bg_color.g = 0.0
        msg.bg_color.b = 0.0
        msg.bg_color.a = 0.8
        msg.fg_color.r = 0.0
        msg.fg_color.g = 1.0
        msg.fg_color.b = 0.0
        msg.fg_color.a = 1.0

        msg.text_size = 18.0
        msg.text = text

        self.extra_info_publisher.publish(msg)

    def route_callback(self, msg: LaneletRoute):

        self.lane_data.clear()
        self.action_data.clear()
        preferred_ids = [segment.preferred_primitive.id for segment in msg.segments]
        self.get_logger().info(f'Preferred Primitive IDs: {preferred_ids}')

        # OSM XML の <relation> 要素を取得
        root = self.osm_tree.getroot()
        relations = root.findall('relation')

        all_ok = True  # フラグ：全てOKなら True のまま

        for pid in preferred_ids:
            # relation の id 属性が一致するものを探す
            match = next((rel for rel in relations if rel.attrib.get('id') == str(pid)), None)

            if match:
                # tag type=lanelet が含まれているか確認
                has_lanelet_tag = any(
                    tag.attrib.get('k') == 'type' and tag.attrib.get('v') == 'lanelet'
                    for tag in match.findall('tag')
                )
                if has_lanelet_tag:
                    status = "OK"
                else:
                    status = "NG (no type=lanelet)"
                    all_ok = False
            else:
                status = "NG (relation not found)"
                all_ok = False

            #self.get_logger().info(f'ID {pid}: relation type=lanelet check -> {status}')

        if not all_ok:
            self.get_logger().warn('Some preferred primitives are invalid: missing relation or missing type=lanelet tag.')
        else:
            # 全てOKならまとめて通知
            self.get_logger().info('All preferred primitives are valid lanelet relations.')
            # 長さ計算用: ノードの local_x, local_y, ele を取得する関数
            def get_node_xyz(node_elem):
                tags = {tag.attrib['k']: tag.attrib['v'] for tag in node_elem.findall('tag')}
                try:
                    x = float(tags.get('local_x', '0.0'))
                    y = float(tags.get('local_y', '0.0'))
                    z = float(tags.get('ele', '0.0'))
                    return x, y, z
                except ValueError:
                    return None  # 値が不正な場合

            # 距離計算関数
            def compute_way_length(way_elem):
                nd_refs = [nd.attrib['ref'] for nd in way_elem.findall('nd')]
                length = 0.0
                for i in range(len(nd_refs) - 1):
                    n1 = self.nodes.get(nd_refs[i])
                    n2 = self.nodes.get(nd_refs[i + 1])
                    if n1 is None or n2 is None:
                        continue
                    p1 = get_node_xyz(n1)
                    p2 = get_node_xyz(n2)
                    if p1 is None or p2 is None:
                        continue
                    dx = p2[0] - p1[0]
                    dy = p2[1] - p1[1]
                    dz = p2[2] - p1[2]
                    length += math.sqrt(dx ** 2 + dy ** 2 + dz ** 2)
                return length
            length_sum=0
            for rid in preferred_ids:
                relation = next(rel for rel in relations if rel.attrib.get('id') == str(rid))
                left_way = None
                right_way = None
                for member in relation.findall('member'):
                    if member.attrib.get('type') == 'way':
                        role = member.attrib.get('role')
                        ref = member.attrib.get('ref')
                        if role == 'left':
                            left_way = self.ways.get(ref)
                        elif role == 'right':
                            right_way = self.ways.get(ref)

                if left_way and right_way:
                    left_length = compute_way_length(left_way)
                    right_length = compute_way_length(right_way)
                    avg_length = (left_length + right_length) / 2
                    #self.get_logger().info(f'Relation ID {rid}: average lanelet length = {avg_length:.3f} m')
                    self.lane_data.add(rid,avg_length)
                    length_sum+=avg_length
                else:
                    self.get_logger().warn(f'Relation ID {rid}: missing left or right way for length calculation')
            self.get_logger().info(f'average lanelet length_sum = {length_sum:.3f} m')

            found_any_traffic_light = False  # 一つでも見つかれば True にする
            traffic_light_lane_relations = []
            for rid in preferred_ids:
                lanelet_rel = next((rel for rel in self.relations if rel.attrib.get('id') == str(rid)), None)
                if lanelet_rel is None:
                    continue

                reg_elements = [
                    m.attrib.get('ref') for m in lanelet_rel.findall('member')
                    if m.attrib.get('type') == 'relation' and m.attrib.get('role') == 'regulatory_element'
                ]

                traffic_light_ids = []
                for reg_id in reg_elements:
                    reg_rel = next((rel for rel in self.relations if rel.attrib.get('id') == str(reg_id)), None)
                    if reg_rel is None:
                        continue

                    for tag in reg_rel.findall('tag'):
                        if tag.attrib.get('k') == 'subtype' and tag.attrib.get('v') == 'traffic_light':
                            traffic_light_ids.append(reg_id)
                            traffic_light_lane_relations.append((rid, reg_id))

                count = len(traffic_light_ids)
                if count == 1:
                    self.get_logger().info(f'Preferred ID {rid} has one regulatory_element with subtype=traffic_light (ID: {traffic_light_ids[0]})')
                    found_any_traffic_light = True
                elif count > 1:
                    self.get_logger().warn(f'[WARN] Preferred ID {rid} has MULTIPLE ({count}) regulatory_elements with subtype=traffic_light: IDs {traffic_light_ids} – check OSM validity')
                    found_any_traffic_light = True

            if not found_any_traffic_light:
                self.get_logger().info('No preferred primitives reference regulatory_elements with subtype=traffic_light')
            else:
                for (pid, tlid) in traffic_light_lane_relations:
                    self.get_logger().info(f'Preferred ID {pid} is linked to traffic_light ID {tlid}')

            def assign_actions_before_traffic_light(lane_data, traffic_light_lane_relations, required_distance=50.0):
                """
                traffic_light を含む lane の手前にあるレーンにアクションを割り当てる。
                self.lane_data から距離を計算し、self.action_data に登録する。
                """
                lane_ids = lane_data.lane_ids
                lane_lengths = lane_data.lane_lengths

                for (traffic_lane_id, traffic_light_id) in traffic_light_lane_relations:
                    if traffic_lane_id not in lane_ids:
                        self.get_logger().warn(f'Lane ID {traffic_lane_id} not found in lane_data. Skipping.')
                        continue

                    idx = lane_ids.index(traffic_lane_id)
                    accumulated = 0.0
                    found = False

                    # 進行方向における手前（indexを逆にたどる）
                    for i in range(idx - 1, -1, -1):
                        accumulated += lane_lengths[i]
                        if accumulated >= required_distance:
                            target_id = lane_ids[i]
                            self.action_data.add(target_id, traffic_light_id)
                            self.get_logger().info(f'Assigned action at lane {target_id} for traffic_light {traffic_light_id} (distance: {accumulated:.1f} m)')
                            found = True
                            break

                    if not found:
                        # 十分な距離を取れなかった場合、直後の lane に fallback
                        if idx + 1 < len(lane_ids):
                            fallback_id = lane_ids[idx + 1]
                            self.get_logger().warn(f'Distance to traffic_light {traffic_light_id} too short. Using next lane {fallback_id} instead.')
                            self.action_data.add(fallback_id, traffic_light_id)
                        else:
                            self.get_logger().warn(f'No fallback lane available after traffic_light {traffic_light_id}. Action not assigned.')
            assign_actions_before_traffic_light(self.lane_data,traffic_light_lane_relations, self.signal_ahead)


    def current_id_callback(self, msg: OverlayText):
        text = msg.text.strip()
        match = re.search(r'Current ID\s*:\s*(\d+)', text)
        if match:
            lanelet_id = int(match.group(1))
            if lanelet_id != self.last_lanelet_id:
                self.get_logger().info(f'Current Lanelet ID changed: {lanelet_id}')
                self.last_lanelet_id = lanelet_id
                if lanelet_id in self.action_data.action_ids:
                    indices = [i for i, x in enumerate(self.action_data.action_ids) if x == lanelet_id]
                    if len(indices) > 1:
                        mes="起こすべきアクションが複数あるレーン(pending)" 
                    else:
                        mes="信号から"+str(self.signal_ahead)+"m手前:signal ID:"+str(self.action_data.actions[indices[0]])
                    self.publish_extra_info(mes)


        else:
            self.get_logger().debug(f"Could not parse Lanelet ID from text: {text}")



def load_osm_file(file_path):
    try:
        tree = ET.parse(file_path)
        print(f"[INFO] Successfully loaded OSM file into memory: {file_path}")
        return tree

    except ET.ParseError as e:
        print(f"[ERROR] Failed to parse OSM file: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"[ERROR] File not found: {file_path}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        sys.exit(1)


def main(args=None):
    rclpy.init(args=args)

    if len(sys.argv) < 2:
        print("[ERROR] Please provide the OSM file path as an argument.")
        sys.exit(1)

    osm_path = sys.argv[1]

    if not os.path.isfile(osm_path):
        print(f"[ERROR] The file does not exist: {osm_path}")
        sys.exit(1)

    # OSMファイルを読み込んでメモリに保持
    osm_tree = load_osm_file(osm_path)

    # ROS2ノード起動、osm_treeを渡す
    node = RouteListener(osm_tree)
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
