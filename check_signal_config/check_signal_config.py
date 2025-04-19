import xml.etree.ElementTree as ET
import sys

def find_unused_and_missing_traffic_light_relations(osm_file_path):
    tree = ET.parse(osm_file_path)
    root = tree.getroot()

    # step 1: traffic_light の regulatory_element relation の ID を収集
    traffic_light_ids = set()
    for rel in root.findall("relation"):
        tags = {tag.attrib['k']: tag.attrib['v'] for tag in rel.findall('tag')}
        if tags.get("type") == "regulatory_element" and tags.get("subtype") == "traffic_light":
            traffic_light_ids.add(rel.attrib["id"])

    # step 2: 他の relation に含まれる cp.signal_id を収集
    referenced_signal_ids = set()
    for rel in root.findall("relation"):
        for tag in rel.findall("tag"):
            if tag.attrib.get("k") == "cp.signal_id":
                referenced_signal_ids.add(tag.attrib.get("v"))

    # step 3: traffic_light_ids に含まれない cp.signal_id を検出
    invalid_signal_ids = sorted(
        [sid for sid in referenced_signal_ids if sid not in traffic_light_ids],
        key=lambda x: int(x)
    )

    # step 4: 未使用の traffic_light relation ID を検出
    unused_ids = sorted(
        [rid for rid in traffic_light_ids if rid not in referenced_signal_ids],
        key=lambda x: int(x)
    )

    # 出力：未使用 ID
    if unused_ids:
        print("Unused traffic light relation IDs:")
        for uid in unused_ids:
            print(uid)
    else:
        print("すべてのtraffic_light relationはcp.signal_idとして参照されています。")

    print()

    # 出力：cp.signal_idにあるが traffic_light relation がない ID
    if invalid_signal_ids:
        print("cp.signal_idに指定されているが、対応するtraffic_light relationが存在しないID:")
        for sid in invalid_signal_ids:
            print(sid)
    else:
        print("cp.signal_idに存在しないtraffic_light relationの参照はありません。")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python check_unused_traffic_lights.py <path_to_osm_file>")
        sys.exit(1)

    osm_file_path = sys.argv[1]
    find_unused_and_missing_traffic_light_relations(osm_file_path)
