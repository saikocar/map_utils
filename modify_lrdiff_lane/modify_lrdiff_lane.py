import xml.etree.ElementTree as ET
import sys
import os
import math
from collections import defaultdict

class OSMManager:
    def __init__(self, tree: ET.ElementTree):
        self.tree = tree
        self.root = tree.getroot()

        # 最大ID管理
        self.max_node_id = 0
        self.max_way_id = 0
        self.max_rel_id = 0

        # 要素辞書（ID:str -> XML要素）
        self.nodes = {}
        self.ways = {}
        self.relations = {}

        # ノード情報辞書（id:str -> dict(x,y,zなど)）
        self.node_data = {}

        # 追加物管理（IDセット）
        self.modified_ways = set()
        self.modified_relations = set()
        self.added_nodes = set()

        self._init_from_tree()

    def _init_from_tree(self):
        # ノードを読み込み最大ID更新
        for node in self.root.findall("node"):
            nid = node.get("id")
            self.nodes[nid] = node
            self.max_node_id = max(self.max_node_id, int(nid))
            self.node_data[nid] = self.extract_node_data(node)

        # ウェイを読み込み最大ID更新
        for way in self.root.findall("way"):
            wid = way.get("id")
            self.ways[wid] = way
            self.max_way_id = max(self.max_way_id, int(wid))

        # リレーションを読み込み最大ID更新
        for rel in self.root.findall("relation"):
            rid = rel.get("id")
            self.relations[rid] = rel
            self.max_rel_id = max(self.max_rel_id, int(rid))

    def extract_node_data(self, node_elem):
        """
        ノード要素から local_x, local_y, ele を抽出して (x, y, z) にマッピング。
        必須タグが存在しない場合は例外を発生させる。
        """
        x = y = z = None
        for tag in node_elem.findall("tag"):
            k = tag.get("k")
            v = tag.get("v")
            if k == "local_x":
                x = float(v)
            elif k == "local_y":
                y = float(v)
            elif k == "ele":
                z = float(v)

        missing = []
        if x is None:
            missing.append("local_x")
        if y is None:
            missing.append("local_y")
        if z is None:
            missing.append("ele")

        if missing:
            raise ValueError(f"Node ID {node_elem.get('id')} is missing required tags: {', '.join(missing)}")

        return {"x": x, "y": y, "z": z}

    def get_new_node_id(self):
        self.max_node_id += 1
        return str(self.max_node_id)

    def get_new_way_id(self):
        self.max_way_id += 1
        return str(self.max_way_id)

    def get_new_relation_id(self):
        self.max_rel_id += 1
        return str(self.max_rel_id)

    # --- ノード操作 ---
    def add_node(self, node_info):
        """
        新ノードを追加し、XMLツリー・辞書を同期。
        node_info: {'x': float, 'y': float, 'z': float}
        lat/lon は空文字とし、local_x, local_y, ele をタグに記録。
        """
        new_id = self.get_new_node_id()
        node_elem = ET.Element("node", id=str(new_id), lat="", lon="")  # 必須属性のみ指定

        ET.SubElement(node_elem, "tag", k="local_x", v=str(node_info["x"]))
        ET.SubElement(node_elem, "tag", k="local_y", v=str(node_info["y"]))
        ET.SubElement(node_elem, "tag", k="ele", v=str(node_info.get("z", 0)))

        self.root.append(node_elem)
        self.nodes[new_id] = node_elem
        self.node_data[new_id] = node_info
        self.added_nodes.add(new_id)
        return new_id

    def update_node(self, node_id, node_info):
        """
        ノード情報を更新（local_x, local_y, ele）
        """
        if node_id not in self.nodes:
            return False
        node_elem = self.nodes[node_id]
        node_elem.set("lat", "")
        node_elem.set("lon", "")

        # local_x, local_y, ele のタグを更新
        def set_or_create_tag(k, v):
            for tag in node_elem.findall("tag"):
                if tag.get("k") == k:
                    tag.set("v", str(v))
                    return
            ET.SubElement(node_elem, "tag", k=k, v=str(v))

        set_or_create_tag("local_x", node_info["x"])
        set_or_create_tag("local_y", node_info["y"])
        set_or_create_tag("ele", node_info.get("z", 0))

        self.node_data[node_id] = node_info
        return True


    # --- ウェイ操作 ---
    def get_way_nodes(self, way_id):
        """
        指定ウェイのノードIDリストを取得
        """
        way_elem = self.ways.get(way_id)
        if way_elem is None:
            return None
        return [nd.get("ref") for nd in way_elem.findall("nd")]

    def set_way_nodes(self, way_id, node_refs):
        """
        ウェイのノード参照リストを更新しXMLも同期
        """
        way_elem = self.ways.get(way_id)
        if way_elem is None:
            return False
        # 既存ndを削除
        for nd in list(way_elem.findall("nd")):
            way_elem.remove(nd)
        # 新規ndを追加
        for ref in node_refs:
            ET.SubElement(way_elem, "nd", ref=ref)
        return True

    def insert_node_to_way(self, way_id, after_node_id, new_node_id):
        """
        指定ノードの直後に新ノードを挿入
        """
        nodes = self.get_way_nodes(way_id)
        if nodes is None:
            return False
        try:
            idx = nodes.index(after_node_id)
        except ValueError:
            return False
        nodes.insert(idx + 1, new_node_id)
        return self.set_way_nodes(way_id, nodes)

    # --- リレーション操作 ---
    def get_relation_members(self, rel_id):
        """
        指定リレーションのmember要素のリストを取得
        """
        rel_elem = self.relations.get(rel_id)
        if rel_elem is None:
            return None
        return list(rel_elem.findall("member"))

    def add_relation_member(self, rel_id, member_type, ref, role):
        """
        リレーションにメンバーを追加
        """
        rel_elem = self.relations.get(rel_id)
        if rel_elem is None:
            return False
        ET.SubElement(rel_elem, "member", type=member_type, ref=ref, role=role)
        return True

    # 必要に応じて他メソッドも追加してください

def distance(a, b):
    return math.sqrt(
        (float(a["x"]) - float(b["x"])) ** 2 +
        (float(a["y"]) - float(b["y"])) ** 2 +
        (float(a["z"]) - float(b["z"])) ** 2
    )

def project_onto_segment(p, a, b):
    px, py, pz = float(p["x"]), float(p["y"]), float(p["z"])
    ax, ay, az = float(a["x"]), float(a["y"]), float(a["z"])
    bx, by, bz = float(b["x"]), float(b["y"]), float(b["z"])

    ab = [bx - ax, by - ay, bz - az]
    ap = [px - ax, py - ay, pz - az]
    ab_len_sq = sum(v ** 2 for v in ab)
    if ab_len_sq == 0:
        return a, 0

    t = sum(ap[i] * ab[i] for i in range(3)) / ab_len_sq
    #一致されると管理上面倒なのでわずかにずらす
    epsilon = 1e-10
    t_clamped = max(epsilon, min(1.0 - epsilon, t))

    proj = {
        "x": ax + ab[0] * t_clamped,
        "y": ay + ab[1] * t_clamped,
        "z": az + ab[2] * t_clamped,
    }
    return proj, t_clamped

def extract_node_data(node):
    tags = {tag.get("k"): tag.get("v") for tag in node.findall("tag")}
    return {
        "x": tags.get("local_x", "0"),
        "y": tags.get("local_y", "0"),
        "z": tags.get("ele", "0")
    }

def parse_osm_and_correct(file_path):
    tree = ET.parse(file_path)
    osm = OSMManager(tree)  # OSMManagerクラスのインスタンス化

    changed = True
    new_relations = list(osm.relations.values())  # relation要素のリスト

    while changed:
        changed = False
        current_relations = new_relations
        new_relations = []
        total = len(current_relations)

        for idx, relation in enumerate(current_relations, start=1):
            rid = relation.get("id")
            #print(f"Processing relation {idx}/{total} (ID: {rid})")
            # left/right のmemberを取得
            members = {m.get("role"): m.get("ref") for m in relation.findall("member") if m.get("role") in ["left", "right"]}
            if "left" not in members or "right" not in members:
                continue

            left_id = members["left"]
            right_id = members["right"]
            left_nodes = osm.get_way_nodes(left_id) or []
            right_nodes = osm.get_way_nodes(right_id) or []

            if len(left_nodes) == len(right_nodes):
                print(f"Relation {rid} has equal node counts.")
                # その way が他の relation にも使われているかチェック
                used_elsewhere = False
                for other_rel in osm.relations.values():
                    if other_rel == relation:
                        continue
                    for mem in other_rel.findall("member"):
                        if mem.get("ref") in [left_id, right_id]:
                            used_elsewhere = True
                            print(f"Way {mem.get('ref')} is also used in relation {other_rel.get('id')}")
                            break
                    if used_elsewhere:
                        break
                if not used_elsewhere:
                    print(f"Relation {rid} is fully resolved and can be skipped in future.")
                    continue
                else:
                    new_relations.append(relation)
                    continue  # 将来的に再評価される可能性あり
            print(f"Processing relation {rid} with lengths: {len(left_nodes)} vs {len(right_nodes)}")

            if len(left_nodes) < len(right_nodes):
                fewer_nodes, more_nodes = left_nodes, right_nodes
                fewer_way = left_id
            else:
                fewer_nodes, more_nodes = right_nodes, left_nodes
                fewer_way = right_id

            relation_changed = False
            # fewer_nodes から closest more_nodes を探し、対応済みにする
            candidate_more_nodes = set(more_nodes[1:-1])
            matched_more_nodes = set()

            for fn_id in fewer_nodes[1:-1]:
                f_pos = osm.node_data[fn_id]

                min_dist = float("inf")
                closest_mn_id = None

                for mn_id in candidate_more_nodes - matched_more_nodes:
                    m_pos = osm.node_data[mn_id]
                    d = distance(f_pos, m_pos)
                    if d < min_dist:
                        min_dist = d
                        closest_mn_id = mn_id

                if closest_mn_id:
                    matched_more_nodes.add(closest_mn_id)

            # 未対応の more_node だけを補間対象とする
            unmatched_more_nodes = list(candidate_more_nodes - matched_more_nodes)
            print(f"Looping over {len(unmatched_more_nodes)} unmatched intermediate nodes")

            # ここから補間処理（新ノード挿入など）
            for mn_id in unmatched_more_nodes:
                m_pos = osm.node_data[mn_id]

                min_dist = float("inf")
                best_proj = None
                best_t = None
                insert_after = fewer_nodes[0]
                best_1 = None
                best_2 = None

                for i in range(len(fewer_nodes) - 1):
                    nid1 = fewer_nodes[i]
                    nid2 = fewer_nodes[i + 1]
                    proj, t = project_onto_segment(m_pos, osm.node_data[nid1], osm.node_data[nid2])
                    d = distance(proj, m_pos)
                    if d < min_dist:
                        min_dist = d
                        best_proj = proj
                        insert_after = nid1
                        best_t = t
                        best_1 = nid1
                        best_2 = nid2

                new_node_id = osm.add_node(best_proj)
                success = osm.insert_node_to_way(fewer_way, insert_after, new_node_id)

                if success:
                    # ↓ ここで fewer_nodes を最新の状態に更新する
                    fewer_nodes = osm.get_way_nodes(fewer_way)

                    osm.modified_ways.add(fewer_way)
                    osm.modified_relations.add(rid)
                    osm.added_nodes.add(new_node_id)
                    relation_changed = True
                    changed = True
                else:
                    print(f"Failed to insert node {new_node_id} after {insert_after} in way {fewer_way}")

            if relation_changed:
                new_relations.append(relation)
                # 変更があればウェイ要素のnd要素はosm.insert_node_to_wayで同期済みのため、改めて削除・追加は不要
                #break  # 1回のループで1relationまで処理し再検証へ

    if osm.modified_relations:
        print("Modified relation IDs:", ", ".join(sorted(osm.modified_relations,key=int)))
        print("Modified way IDs:", ", ".join(sorted(osm.modified_ways,key=int)))
        added = sorted(osm.added_nodes,key=int)
        if added:
            print(f"Added node IDs: {added[0]} ... {added[-1]}")
        else:
            print("Added node IDs: (none)")

        output_path = os.path.splitext(file_path)[0] + "_modify.osm"
        if os.path.exists(output_path):
            print("Output file already exists. Aborting.")
        else:
            osm.tree.write(output_path, encoding="utf-8", xml_declaration=True)
            print("Modified OSM file written to:", output_path)
    else:
        print("No relation modifications were necessary.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <osm_file>")
        sys.exit(1)
    parse_osm_and_correct(sys.argv[1])

