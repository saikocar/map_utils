import xml.etree.ElementTree as ET
import sys

def parse_osm(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    
    ways = {}
    for way in root.findall("way"):
        way_id = way.get("id")
        node_refs = [nd.get("ref") for nd in way.findall("nd")]
        ways[way_id] = node_refs
    
    found_difference = False
    for relation in root.findall("relation"):
        members = {m.get("role"): m.get("ref") for m in relation.findall("member") if m.get("role") in ["left", "right"]}
        
        if "left" in members and "right" in members:
            left_way_id = members["left"]
            right_way_id = members["right"]
            
            left_nodes = ways.get(left_way_id, [])
            right_nodes = ways.get(right_way_id, [])
            
            if len(left_nodes) != len(right_nodes):
                print(f"Relation ID: {relation.get('id')}, Left nodes: {len(left_nodes)}, Right nodes: {len(right_nodes)}")
                found_difference = True
    
    if not found_difference:
        print("No relations found with differing left and right node counts.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <osm_file>")
        sys.exit(1)
    
    osm_file = sys.argv[1]
    parse_osm(osm_file)

