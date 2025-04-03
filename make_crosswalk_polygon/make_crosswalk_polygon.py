import xml.etree.ElementTree as ET
import argparse
import os
from collections import defaultdict

def normalize_polygon(nodes):
    """
    ノードIDのリストをソートし、循環的な等価性を考慮して比較可能な形にする。
    """
    if not nodes:
        return tuple()
    min_index = min(range(len(nodes)), key=lambda i: nodes[i])
    return tuple(nodes[min_index:] + nodes[:min_index])

def find_referenced_nodes(osm_file):
    tree = ET.parse(osm_file)
    root = tree.getroot()
    
    ways_dict = {}
    max_way_id = -1
    existing_polygons = set()
    
    for way in root.findall('way'):
        way_id = int(way.get('id'))
        nodes = [nd.get('ref') for nd in way.findall('nd')]
        ways_dict[way_id] = nodes
        max_way_id = max(max_way_id, way_id)
        
        for tag in way.findall('tag'):
            if tag.get('k') == 'type' and tag.get('v') == 'crosswalk_polygon':
                existing_polygons.add(normalize_polygon(nodes))
    
    relations_dict = defaultdict(lambda: {'left': [], 'right': []})
    
    for relation in root.findall('relation'):
        has_type_lanelet = False
        has_subtype_crosswalk = False
        
        for tag in relation.findall('tag'):
            if tag.get('k') == 'type' and tag.get('v') == 'lanelet':
                has_type_lanelet = True
            if tag.get('k') == 'subtype' and tag.get('v') == 'crosswalk':
                has_subtype_crosswalk = True
        
        if has_type_lanelet and has_subtype_crosswalk:
            relation_id = relation.get('id')
            for member in relation.findall('member'):
                if member.get('type') == 'way':
                    if member.get('role') == 'left':
                        relations_dict[relation_id]['left'].append(member.get('ref'))
                    elif member.get('role') == 'right':
                        relations_dict[relation_id]['right'].append(member.get('ref'))
    
    return relations_dict, ways_dict, max_way_id, existing_polygons

def create_crosswalk_polygon(osm_file, relations_dict, ways_dict, start_id, existing_polygons):
    base_name, _ = os.path.splitext(osm_file)
    output_file = os.path.abspath(f"{base_name}_append.osm")
    added_count = 0
    
    new_content = []
    for relation_id, refs in relations_dict.items():
        left_node_ids = []
        right_node_ids = []
        
        for way_ref in refs['left']:
            way_ref_id = int(way_ref)
            if way_ref_id in ways_dict:
                left_node_ids.extend(ways_dict[way_ref_id])
        
        for way_ref in refs['right']:
            way_ref_id = int(way_ref)
            if way_ref_id in ways_dict:
                right_node_ids.extend(ways_dict[way_ref_id])
        
        left_sorted = sorted(left_node_ids, key=int)
        right_sorted = sorted(right_node_ids, key=int, reverse=True)
        new_polygon = normalize_polygon(left_sorted + right_sorted)
        
        if new_polygon in existing_polygons:
            print(f"Skipping existing crosswalk_polygon for relation {relation_id}")
            continue
        
        new_way_id = start_id + 1
        new_content.append(f'<way id="{new_way_id}">\n')
        for node_id in left_sorted + right_sorted:
            new_content.append(f'    <nd ref="{node_id}"/>\n')
        new_content.append('    <tag k="type" v="crosswalk_polygon"/>\n')
        new_content.append('    <tag k="area" v="yes"/>\n')
        new_content.append('</way>\n')
        
        existing_polygons.add(new_polygon)
        added_count += 1
        start_id += 1
    
    if added_count > 0:
        with open(output_file, 'w') as f:
            f.writelines(new_content)
        print(f"Added {added_count} new crosswalk_polygon(s). Output file: {output_file}")
    else:
        print("No new crosswalk_polygon added. Output file was not created.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create crosswalk_polygon from OSM relations with type 'lanelet' and subtype 'crosswalk'.")
    parser.add_argument("osm_file", help="Path to the OSM file")
    args = parser.parse_args()

    relations_dict, ways_dict, max_way_id, existing_polygons = find_referenced_nodes(args.osm_file)
    create_crosswalk_polygon(args.osm_file, relations_dict, ways_dict, max_way_id, existing_polygons)

