import xml.etree.ElementTree as ET
import numpy as np
import os
import argparse
import struct

# Function to generate unique output filename
def generate_output_filename(input_file, suffix="plant", extension=".pcd"):
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    output_file = f"{base_name}_{suffix}{extension}"

    counter = 1
    while os.path.exists(output_file):
        output_file = f"{base_name}_{suffix}({counter}){extension}"
        counter += 1

    return output_file

# Function to calculate the plane normal vector from 4 points
def calculate_plane_normal(points):
    if len(points) != 4:
        raise ValueError("Exactly 4 points are required to calculate the plane normal.")

    x_coords, y_coords, z_coords = zip(*points)

    P = np.array([
        [x_coords[0], y_coords[0], 1],
        [x_coords[1], y_coords[1], 1],
        [x_coords[2], y_coords[2], 1],
        [x_coords[3], y_coords[3], 1]
    ])

    Z = np.array(z_coords).reshape(4, 1)

    P_T = P.T
    try:
        plane_params = np.linalg.inv(P_T @ P) @ P_T @ Z
    except np.linalg.LinAlgError:
        raise ValueError("Matrix is singular or nearly singular. Cannot compute the plane.")

    a, b, c = plane_params.flatten()
    normal_vector = np.array([a, b, -1])
    normal_vector /= np.linalg.norm(normal_vector)

    return normal_vector

# Function to encode RGB to packed float
def rgb_to_float(r, g, b):
    rgb_int = (r << 16) | (g << 8) | b
    return struct.unpack('f', struct.pack('I', rgb_int))[0]

# Function to fill the lane area
def fill_lane_area(left_point1, left_point2, right_point1, right_point2, step, height=None, value=1.0):
    if step <= 0:
        raise ValueError("Step must be a positive value.")

    def calculate_distance(p1, p2):
        return np.linalg.norm(np.array(p2) - np.array(p1))

    def calculate_num_points(p1, p2, step):
        distance = calculate_distance(p1, p2)
        return int(np.ceil(distance / step))

    left_distance = calculate_distance(left_point1, left_point2)
    right_distance = calculate_distance(right_point1, right_point2)

    if left_distance >= right_distance:
        long_line_points = [left_point1, left_point2]
        short_line_points = [right_point1, right_point2]
    else:
        long_line_points = [right_point1, right_point2]
        short_line_points = [left_point1, left_point2]

    num_points_long = calculate_num_points(long_line_points[0], long_line_points[1], step)

    long_line_points_generated = [tuple(np.array(long_line_points[0]) + i * (np.array(long_line_points[1]) - np.array(long_line_points[0])) / num_points_long) for i in range(num_points_long + 1)]
    short_line_points_generated = [tuple(np.array(short_line_points[0]) + i * (np.array(short_line_points[1]) - np.array(short_line_points[0])) / num_points_long) for i in range(num_points_long + 1)]

    filled_points = []
    for p1, p2 in zip(long_line_points_generated, short_line_points_generated):
        filled_points.extend(generate_line_points(p1, p2, step))

    filled_points.extend(long_line_points_generated)
    filled_points.extend(short_line_points_generated)

    plane_normal = calculate_plane_normal([left_point1, left_point2, right_point1, right_point2])

    if height is not None and height > 0:
        filled_points_with_height = []
        for point in filled_points:
            direction = np.sign(plane_normal[2])
            normal_adjusted = direction * plane_normal
            num_height_steps = int(np.ceil(height / step))
            for j in range(num_height_steps + 1):
                offset = j * step
                new_point = np.array(point) + offset * normal_adjusted
                if offset >= height:
                    new_point = np.array(point) + height * normal_adjusted
                filled_points_with_height.append(tuple(new_point) + (value,))
        return filled_points_with_height

    return [point + (value,) for point in filled_points]

# Generate points along line
def generate_line_points(point1, point2, step):
    distance = np.linalg.norm(np.array(point2) - np.array(point1))
    num_points = int(np.ceil(distance / step))
    return [tuple(np.array(point1) + i * (np.array(point2) - np.array(point1)) / num_points) for i in range(num_points + 1)]

# Parse XML file
def process_xml(xml_file, step, value):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    all_filled_points = []
    excluded_relations = []

    for relation in root.findall("relation"):
        subtype = relation.find("tag[@k='subtype']")
        height_tag = relation.find("tag[@k='height']")

        if subtype is None or height_tag is None:
            continue

        if subtype.attrib["v"] == "plant" and height_tag.attrib["v"].isdigit():
            height = float(height_tag.attrib["v"])

            left_way_ref = relation.find("member[@role='left']").attrib["ref"]
            right_way_ref = relation.find("member[@role='right']").attrib["ref"]

            left_way = get_way_by_ref(root, left_way_ref)
            right_way = get_way_by_ref(root, right_way_ref)

            if left_way is None or right_way is None:
                excluded_relations.append(f"Relation {relation.attrib['id']} excluded: Invalid way references.")
                continue

            left_nodes = get_nodes_for_way(root, left_way)
            right_nodes = get_nodes_for_way(root, right_way)

            if len(left_nodes) != len(right_nodes):
                excluded_relations.append(f"Relation {relation.attrib['id']} excluded: Left and right have different number of nodes.")
                continue

            if len(left_nodes) < 2 or len(right_nodes) < 2:
                excluded_relations.append(f"Relation {relation.attrib['id']} excluded: Insufficient nodes.")
                continue

            for i in range(len(left_nodes) - 1):
                left_point1 = left_nodes[i]
                left_point2 = left_nodes[i + 1]
                right_point1 = right_nodes[i]
                right_point2 = right_nodes[i + 1]

                filled_points = fill_lane_area(left_point1, left_point2, right_point1, right_point2, step, height, value)
                all_filled_points.extend(filled_points)

    return all_filled_points, excluded_relations

def get_way_by_ref(root, ref):
    return next((way for way in root.findall("way") if way.attrib["id"] == ref), None)

def get_nodes_for_way(root, way):
    nodes = []
    for nd in way.findall("nd"):
        node_ref = nd.attrib["ref"]
        node = get_node_by_ref(root, node_ref)
        if node is not None:
            x = float(node.find('tag[@k="local_x"]').attrib["v"])
            y = float(node.find('tag[@k="local_y"]').attrib["v"])
            z = float(node.find('tag[@k="ele"]').attrib["v"])
            nodes.append((x, y, z))
    return nodes

def get_node_by_ref(root, ref):
    return next((node for node in root.findall("node") if node.attrib["id"] == ref), None)

def write_pcd_file(points, output_file, use_rgb):
    if use_rgb:
        header = f"""# .PCD v0.7 - Point Cloud Data file format
VERSION 0.7
FIELDS x y z rgb
SIZE 4 4 4 4
TYPE F F F F
COUNT 1 1 1 1
WIDTH {len(points)}
HEIGHT 1
VIEWPOINT 0 0 0 1 0 0 0
POINTS {len(points)}
DATA ascii
"""
    else:
        header = f"""# .PCD v0.7 - Point Cloud Data file format
VERSION 0.7
FIELDS x y z intensity
SIZE 4 4 4 4
TYPE F F F F
COUNT 1 1 1 1
WIDTH {len(points)}
HEIGHT 1
VIEWPOINT 0 0 0 1 0 0 0
POINTS {len(points)}
DATA ascii
"""

    with open(output_file, "w") as f:
        f.write(header)
        for point in points:
            f.write(f"{point[0]} {point[1]} {point[2]} {point[3]}\n")

def main():
    parser = argparse.ArgumentParser(description="Process OSM XML and generate PCD point cloud.")
    parser.add_argument("input_file", help="Input OSM XML file")
    parser.add_argument("--step", type=float, default=0.1, help="Step size for filling points")
    parser.add_argument("--intensity", type=float, help="Intensity value for points")
    parser.add_argument("--rgb", type=int, nargs=3, metavar=('R', 'G', 'B'), help="RGB values (0-255) to encode into the point cloud")

    args = parser.parse_args()

    output_file = generate_output_filename(args.input_file)

    use_rgb = args.rgb is not None
    if use_rgb:
        r, g, b = args.rgb
        value = rgb_to_float(r, g, b)
    else:
        value = args.intensity if args.intensity is not None else 1.0

    filled_points, excluded_relations = process_xml(args.input_file, args.step, value)
    write_pcd_file(filled_points, output_file, use_rgb)

    print(f"PCD file '{output_file}' generated successfully with {len(filled_points)} points.")
    if excluded_relations:
        print("Excluded relations:")
        for msg in excluded_relations:
            print(f"  - {msg}")

if __name__ == "__main__":
    main()
