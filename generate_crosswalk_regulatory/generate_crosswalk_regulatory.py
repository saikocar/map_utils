import xml.etree.ElementTree as ET
import sys
import copy
from collections import defaultdict
from xml.dom import minidom

def parse_osm(osm_path):
    tree = ET.parse(osm_path)
    root = tree.getroot()
    return tree, root

def get_max_id(root):
    max_id = 0
    for elem in root:
        if "id" in elem.attrib:
            try:
                max_id = max(max_id, int(elem.attrib["id"]))
            except ValueError:
                continue
    return max_id

def build_node_map(root):
    node_map = defaultdict(set)
    for way in root.findall("way"):
        way_id = way.get("id")
        for nd in way.findall("nd"):
            node_map[way_id].add(nd.get("ref"))
    return node_map

def get_way_tags(way):
    return {tag.get("k"): tag.get("v") for tag in way.findall("tag")}

def find_polygon_candidate(root, left_id, right_id, node_map):
    left_nodes = node_map.get(left_id, set())
    right_nodes = node_map.get(right_id, set())
    combined_nodes = left_nodes.union(right_nodes)

    for way in root.findall("way"):
        tags = get_way_tags(way)
        if tags.get("type") != "crosswalk_polygon" or tags.get("area") != "yes":
            continue
        way_id = way.get("id")
        way_nodes = node_map.get(way_id, set())
        if combined_nodes == way_nodes:
            return way_id
    return None

def find_unreferenced_crosswalk_lanelets(root):
    lanelet_ids = set()
    id_to_elem = {}
    for relation in root.findall("relation"):
        tags = {t.get("k"): t.get("v") for t in relation.findall("tag")}
        if tags.get("type") == "lanelet" and tags.get("subtype") == "crosswalk":
            rid = relation.get("id")
            lanelet_ids.add(rid)
            id_to_elem[rid] = relation

    referenced_ids = set()
    for relation in root.findall("relation"):
        tags = {t.get("k"): t.get("v") for t in relation.findall("tag")}
        if tags.get("type") == "regulatory_element" and tags.get("subtype") == "crosswalk":
            for member in relation.findall("member"):
                if member.get("type") == "relation" and member.get("role") == "refers":
                    referenced_ids.add(member.get("ref"))

    return lanelet_ids - referenced_ids, id_to_elem

def create_regulatory_relation(new_id, refers_id, polygon_way_id=None):
    relation = ET.Element("relation", id=str(new_id))

    if polygon_way_id:
        ET.SubElement(relation, "member", {
            "type": "way",
            "role": "crosswalk_polygon",
            "ref": polygon_way_id
        })

    ET.SubElement(relation, "member", {
        "type": "relation",
        "role": "refers",
        "ref": refers_id
    })

    ET.SubElement(relation, "tag", {"k": "type", "v": "regulatory_element"})
    ET.SubElement(relation, "tag", {"k": "subtype", "v": "crosswalk"})

    return relation

def get_member_way_ids(relation, role):
    return [m.get("ref") for m in relation.findall("member") if m.get("type") == "way" and m.get("role") == role]

def write_pretty_xml(root, output_path):
    rough_string = ET.tostring(root, encoding="utf-8")
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ")
    with open(output_path, "w", encoding="utf-8") as f:
        for line in pretty_xml.splitlines():
            if line.strip():  # 空行を除去
                f.write(line + "\n")

def main():
    if len(sys.argv) != 2:
        print("Usage: python generate_crosswalk_regulatory.py input.osm")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = input_path.replace(".osm", "_crosswalk.osm")

    tree, root = parse_osm(input_path)
    original = copy.deepcopy(root)

    node_map = build_node_map(root)
    unreferenced_ids, id_to_elem = find_unreferenced_crosswalk_lanelets(root)
    max_id = get_max_id(root)
    new_id = max_id + 1
    created_ids = []

    for rel_id in unreferenced_ids:
        rel = id_to_elem[rel_id]
        left_ids = get_member_way_ids(rel, "left")
        right_ids = get_member_way_ids(rel, "right")
        if len(left_ids) != 1 or len(right_ids) != 1:
            continue

        polygon_id = find_polygon_candidate(root, left_ids[0], right_ids[0], node_map)
        regulatory_relation = create_regulatory_relation(new_id, rel_id, polygon_id)
        root.append(regulatory_relation)

        # 元の crosswalk relation に <member role="regulatory_element" ...> を追加
        ET.SubElement(rel, "member", {
            "type": "relation",
            "role": "regulatory_element",
            "ref": str(new_id)
        })

        created_ids.append(new_id)
        new_id += 1

    # 差分検出と出力
    new_data = ET.tostring(root, encoding="unicode")
    old_data = ET.tostring(original, encoding="unicode")
    if new_data != old_data:
        write_pretty_xml(root, output_path)
        print(f"[更新されたファイル] {output_path}")
        print("=== 作成された relation ID ===")
        for i in created_ids:
            print(i)
    else:
        print("変更はありませんでした。")

if __name__ == "__main__":
    main()
