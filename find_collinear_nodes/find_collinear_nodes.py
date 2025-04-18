import os
import math
import argparse
import xml.etree.ElementTree as ET

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('input_file', help='Input OSM file')
    parser.add_argument('--eps', type=float, default=1e-15, help='Tolerance (in meters)')
    parser.add_argument('--m', action='store_true')
    parser.add_argument('--cm', action='store_true')
    parser.add_argument('--mm', action='store_true')
    return parser.parse_args()

def apply_unit_conversion(args):
    units = [args.m, args.cm, args.mm]
    if sum(units) > 1:
        print("Error: Specify only one of --m, --cm, or --mm.")
        exit(1)
    original_eps = args.eps
    if args.cm:
        args.eps *= 0.01
    elif args.mm:
        args.eps *= 0.001
    if args.eps != original_eps:
        print(f"eps overwritten to {args.eps} based on unit conversion.")
    return args

def load_osm_data(input_file):
    tree = ET.parse(input_file)
    root = tree.getroot()

    nodes = {}
    ways = []
    unmodified_ways = []
    relations = []
    meta = []

    valid_types = {"line_thin", "virtual", "road_border", "stop_line", "fence", "guard_rail"}

    for child in root:
        if child.tag == 'node':
            node_id = child.get('id')
            try:
                local_x = float(child.find("./tag[@k='local_x']").get('v'))
                local_y = float(child.find("./tag[@k='local_y']").get('v'))
                ele = float(child.find("./tag[@k='ele']").get('v'))
                nodes[node_id] = (local_x, local_y, ele, child)
            except:
                continue
        elif child.tag == 'way':
            way_id = child.get('id')
            nds = [nd.get('ref') for nd in child.findall('nd')]
            tag = child.find("./tag[@k='type']")
            type_value = tag.get('v') if tag is not None else ""
            if type_value in valid_types:
                ways.append((way_id, nds, type_value, child))
            else:
                unmodified_ways.append(child)
        elif child.tag == 'relation':
            relations.append(child)
        else:
            meta.append(child)

    return nodes, ways, unmodified_ways, relations, meta

def build_ref_count(ways):
    ref_count = {}
    for _, nds, _, _ in ways:
        for nd in nds:
            ref_count[nd] = ref_count.get(nd, 0) + 1
    return ref_count

def distance_from_line(p1, p2, p3):
    v1 = [p2[i] - p1[i] for i in range(3)]
    v2 = [p3[i] - p1[i] for i in range(3)]
    cross = [
        v1[1]*v2[2] - v1[2]*v2[1],
        v1[2]*v2[0] - v1[0]*v2[2],
        v1[0]*v2[1] - v1[1]*v2[0]
    ]
    cross_norm = math.sqrt(sum(c**2 for c in cross))
    v1_norm = math.sqrt(sum(c**2 for c in v1))
    return cross_norm / v1_norm if v1_norm != 0 else 0

def find_removable_nodes(nodes, ways, ref_count, eps):
    removable_nodes = set()
    for _, nds, _, _ in ways:
        if len(nds) < 3:
            continue
        for i in range(1, len(nds) - 1):
            n1, n2, n3 = nds[i-1], nds[i], nds[i+1]
            if all(n in nodes for n in (n1, n2, n3)) and ref_count.get(n2, 0) == 1:
                p1 = nodes[n1][:3]
                p2 = nodes[n2][:3]
                p3 = nodes[n3][:3]
                error = distance_from_line(p1, p2, p3)
                if error < eps:
                    removable_nodes.add(n2)
                    print(f"id:{n2}:error={error:.5e}")
    return removable_nodes

def update_ways(ways, removable_nodes):
    updated_ways = []
    modified = False
    for way_id, nds, type_value, elem in ways:
        new_nds = [nds[0]] if nds else []
        for i in range(1, len(nds) - 1):
            if nds[i] not in removable_nodes:
                new_nds.append(nds[i])
        if len(nds) >= 2:
            new_nds.append(nds[-1])
        if new_nds != nds:
            modified = True
            for nd in list(elem.findall('nd')):
                elem.remove(nd)
            for ref in new_nds:
                ET.SubElement(elem, 'nd', ref=ref)
        updated_ways.append(elem)
    return updated_ways, modified

def save_osm(input_file, nodes, updated_ways, unmodified_ways, relations, meta):
    new_root = ET.Element("osm", generator="VMB")
    for m in meta:
        new_root.append(m)
    for node_id, (_, _, _, node_elem) in nodes.items():
        new_root.append(node_elem)
    for way_elem in updated_ways + unmodified_ways:
        new_root.append(way_elem)
    for rel in relations:
        new_root.append(rel)

    out_file = os.path.splitext(input_file)[0] + "_colinear.osm"
    ET.ElementTree(new_root).write(out_file, encoding="UTF-8", xml_declaration=True)
    print(f"Updated OSM saved to: {out_file}")

def main():
    args = apply_unit_conversion(parse_args())
    nodes, ways, unmodified_ways, relations, meta = load_osm_data(args.input_file)
    ref_count = build_ref_count(ways)
    removable_nodes = find_removable_nodes(nodes, ways, ref_count, args.eps)
    updated_ways, modified = update_ways(ways, removable_nodes)
    if modified:
        save_osm(args.input_file, nodes, updated_ways, unmodified_ways, relations, meta)
    else:
        print("No changes detected. Output file not written.")

if __name__ == "__main__":
    main()
