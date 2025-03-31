import xml.etree.ElementTree as ET
import numpy as np
import os
import argparse


# Function to generate unique output filename
def generate_output_filename(input_file, suffix="plant", extension=".pcd"):
    """
    Generate output filename based on the input file, adding a suffix and ensuring uniqueness.
    :param input_file: Input XML/OSM file name
    :param suffix: Suffix to be added to the filename (default: 'plant')
    :param extension: File extension to be added (default: '.pcd')
    :return: Unique output filename with appropriate suffix and extension
    """
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    output_file = f"{base_name}_{suffix}{extension}"

    # Check if the file already exists
    counter = 1
    while os.path.exists(output_file):
        output_file = f"{base_name}_{suffix}({counter}){extension}"
        counter += 1

    return output_file


# Function to calculate the plane normal vector from 4 points
def calculate_plane_normal(points):
    """
    Calculate the normal vector of the best-fit plane given 4 points.
    :param points: List of 4 points, each in the form (x, y, z).
    :return: Normal vector of the plane (a, b, -1), normalized.
    """
    if len(points) != 4:
        raise ValueError("Exactly 4 points are required to calculate the plane normal.")
    
    # Extract x, y, and z coordinates
    x_coords, y_coords, z_coords = zip(*points)

    # Construct matrix P and vector Z
    P = np.array([
        [x_coords[0], y_coords[0], 1],
        [x_coords[1], y_coords[1], 1],
        [x_coords[2], y_coords[2], 1],
        [x_coords[3], y_coords[3], 1]
    ])

    Z = np.array(z_coords).reshape(4, 1)

    # Solve for plane parameters (a, b, c)
    P_T = P.T
    try:
        plane_params = np.linalg.inv(P_T @ P) @ P_T @ Z
    except np.linalg.LinAlgError:
        raise ValueError("Matrix is singular or nearly singular. Cannot compute the plane.")

    # Extract a, b, and c
    a, b, c = plane_params.flatten()

    # Normal vector is [a, b, -1]
    normal_vector = np.array([a, b, -1])

    # Normalize the normal vector
    normal_vector /= np.linalg.norm(normal_vector)

    return normal_vector


# Function to fill the lane area between the given points (left and right)
def fill_lane_area(left_point1, left_point2, right_point1, right_point2, step, height=None):
    if step <= 0:
        raise ValueError("Step must be a positive value.")
    
    # Calculate the distance between two points
    def calculate_distance(p1, p2):
        return np.linalg.norm(np.array(p2) - np.array(p1))

    # Function to calculate the number of points between two points
    def calculate_num_points(p1, p2, step):
        distance = calculate_distance(p1, p2)
        return int(np.ceil(distance / step))

    # Determine the longer and shorter line
    left_distance = calculate_distance(left_point1, left_point2)
    right_distance = calculate_distance(right_point1, right_point2)

    # Determine which line is longer (left or right)
    if left_distance >= right_distance:
        # Use left as long line
        long_line_points = [left_point1, left_point2]
        short_line_points = [right_point1, right_point2]
    else:
        # Use right as long line
        long_line_points = [right_point1, right_point2]
        short_line_points = [left_point1, left_point2]

    # Calculate number of points for the long line
    num_points_long = calculate_num_points(long_line_points[0], long_line_points[1], step)

    # Generate points for the long line (based on the number of points)
    long_line_points_generated = []
    for i in range(num_points_long + 1):
        point = tuple(np.array(long_line_points[0]) + i * (np.array(long_line_points[1]) - np.array(long_line_points[0])) / num_points_long)
        long_line_points_generated.append(point)

    # Generate points for the short line to match the number of points in the long line
    short_line_points_generated = []
    for i in range(num_points_long + 1):
        point = tuple(np.array(short_line_points[0]) + i * (np.array(short_line_points[1]) - np.array(short_line_points[0])) / num_points_long)
        short_line_points_generated.append(point)

    # Generate filled points along the connecting lines
    filled_points = []
    for p1, p2 in zip(long_line_points_generated, short_line_points_generated):
        filled_points.extend(generate_line_points(p1, p2, step))

    # Add all boundary points explicitly to ensure boundary coverage
    filled_points.extend(long_line_points_generated)
    filled_points.extend(short_line_points_generated)

    # Get the plane normal for the 4 points
    plane_normal = calculate_plane_normal([left_point1, left_point2, right_point1, right_point2])

    # Fill points along the normal direction up to height
    if height is not None and height > 0:
        filled_points_with_height = []
        for point in filled_points:
            # 修正：法線方向の符号を反転して z が増大する方向に合わせる
            direction = np.sign(plane_normal[2])  # z 成分の符号
            normal_adjusted = direction * plane_normal

            # Place points along the corrected normal direction with step intervals
            num_height_steps = int(np.ceil(height / step))
            for j in range(num_height_steps + 1):
                offset = j * step
                new_point = np.array(point) + offset * normal_adjusted
                # Ensure the final height point is always added
                if offset >= height:
                    new_point = np.array(point) + height * normal_adjusted
                filled_points_with_height.append(tuple(new_point) + (1.0,))  # Add intensity=1.0
        return filled_points_with_height

    # Add intensity for ground points
    return [point + (1.0,) for point in filled_points]


# Function to generate points along a line between two points
def generate_line_points(point1, point2, step):
    """
    Generate points between point1 and point2 with a given step size.
    """
    distance = np.linalg.norm(np.array(point2) - np.array(point1))
    num_points = int(np.ceil(distance / step))
    line_points = []
    
    for i in range(num_points + 1):
        point = tuple(np.array(point1) + i * (np.array(point2) - np.array(point1)) / num_points)
        line_points.append(point)
    
    return line_points


# Function to parse XML file and process lanes
def process_xml(xml_file, step):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    all_filled_points = []
    excluded_relations = []
    
    for relation in root.findall("relation"):
        subtype = relation.find("tag[@k='subtype']")
        height_tag = relation.find("tag[@k='height']")
        
        if subtype is None or height_tag is None:
            continue
        
        # Process only relations with subtype "plant"
        if subtype.attrib["v"] == "plant" and height_tag.attrib["v"].isdigit():
            
            height = float(height_tag.attrib["v"])
            
            # Get left and right ways
            left_way_ref = relation.find("member[@role='left']").attrib["ref"]
            right_way_ref = relation.find("member[@role='right']").attrib["ref"]
            
            left_way = get_way_by_ref(root, left_way_ref)
            right_way = get_way_by_ref(root, right_way_ref)
            
            # Check if valid ways are found
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

            # Process each pair of nodes
            for i in range(len(left_nodes) - 1):
                left_point1 = left_nodes[i]
                left_point2 = left_nodes[i + 1]
                right_point1 = right_nodes[i]
                right_point2 = right_nodes[i + 1]
                
                # Fill the lane area for this segment with the updated algorithm
                filled_points = fill_lane_area(left_point1, left_point2, right_point1, right_point2, step, height)
                all_filled_points.extend(filled_points)
    
    return all_filled_points, excluded_relations


# Function to get way from XML by reference
def get_way_by_ref(root, ref):
    for way in root.findall("way"):
        if way.attrib["id"] == ref:
            return way
    return None


# Function to get nodes for a given way
def get_nodes_for_way(root, way):
    nodes = []
    for nd in way.findall("nd"):
        node_ref = nd.attrib["ref"]
        node = get_node_by_ref(root, node_ref)
        if node is not None:
            x = float(node.find("tag[@k='local_x']").attrib["v"])
            y = float(node.find("tag[@k='local_y']").attrib["v"])
            z = float(node.find("tag[@k='ele']").attrib["v"])
            nodes.append((x, y, z))
    return nodes


# Function to get node from XML by reference
def get_node_by_ref(root, ref):
    for node in root.findall("node"):
        if node.attrib["id"] == ref:
            return node
    return None


# Function to write points to PCD file
def write_pcd_file(points, output_file):
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


# Main function to parse arguments and run the script
def main():
    parser = argparse.ArgumentParser(description="Process OSM XML and generate PCD point cloud.")
    parser.add_argument("input_file", help="Input OSM XML file")
    parser.add_argument("--step", type=float, default=0.1, help="Step size for filling points (default: 0.1)")
    
    args = parser.parse_args()

    # Generate unique output filename
    output_file = generate_output_filename(args.input_file)

    # Process XML and generate points
    filled_points, excluded_relations = process_xml(args.input_file, args.step)
    
    # Write PCD file
    write_pcd_file(filled_points, output_file)
    
    print(f"PCD file '{output_file}' generated successfully with {len(filled_points)} points.")
    
    if excluded_relations:
        print("Excluded relations:")
        for message in excluded_relations:
            print(f"  - {message}")


if __name__ == "__main__":
    main()

