import xml.etree.ElementTree as ET
import sys

def find_unreferenced_crosswalk_lanelets(osm_file):
    tree = ET.parse(osm_file)
    root = tree.getroot()

    # crosswalk lanelet relation の ID を収集
    lanelet_crosswalk_ids = set()
    for relation in root.findall("relation"):
        tags = {tag.get("k"): tag.get("v") for tag in relation.findall("tag")}
        if tags.get("type") == "lanelet" and tags.get("subtype") == "crosswalk":
            lanelet_crosswalk_ids.add(relation.get("id"))

    # regulatory_element crosswalk が参照している relation の ID を収集
    referenced_ids = set()
    for relation in root.findall("relation"):
        tags = {tag.get("k"): tag.get("v") for tag in relation.findall("tag")}
        if tags.get("type") == "regulatory_element" and tags.get("subtype") == "crosswalk":
            for member in relation.findall("member"):
                if member.get("type") == "relation" and member.get("role") == "refers":
                    referenced_ids.add(member.get("ref"))

    # 一度も参照されていない lanelet crosswalk を抽出
    unreferenced_ids = lanelet_crosswalk_ids - referenced_ids

    # 結果表示
    if unreferenced_ids:
        print("一度も参照されていない crosswalk lanelet relation の ID:")
        for rid in sorted(unreferenced_ids, key=int):
            print(rid)
    else:
        print("すべての crosswalk lanelet は regulatory_element から参照されています。")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("使用方法: python script_name.py input.osm")
        sys.exit(1)

    osm_file = sys.argv[1]
    find_unreferenced_crosswalk_lanelets(osm_file)
