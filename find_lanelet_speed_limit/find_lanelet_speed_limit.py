import xml.etree.ElementTree as ET
import argparse

def extract_speed_limit_relations(osm_path, lower=10, upper=10):
    tree = ET.parse(osm_path)
    root = tree.getroot()

    result_ids = []

    for relation in root.findall('relation'):
        tags = {tag.attrib['k']: tag.attrib['v'] for tag in relation.findall('tag')}

        # type=lanelet, subtype=road, and no turn_direction tag
        if (
            tags.get("type") == "lanelet" and
            tags.get("subtype") == "road" and
            "turn_direction" not in tags
        ):
            speed_limit = tags.get("speed_limit")
            if speed_limit is not None:
                try:
                    speed = float(speed_limit)
                    if lower <= speed <= upper:
                        relation_id = relation.attrib.get('id')
                        if relation_id:
                            result_ids.append(relation_id)
                except ValueError:
                    continue  # skip if speed_limit is not a valid float

    return result_ids

def main():
    parser = argparse.ArgumentParser(description='Extract lanelet road relations within a speed limit range, excluding those with turn_direction.')
    parser.add_argument('osm_file', help='Path to the OSM file')
    parser.add_argument('--lower', type=float, default=10, help='Lower bound of speed_limit (inclusive)')
    parser.add_argument('--upper', type=float, default=10, help='Upper bound of speed_limit (inclusive)')
    args = parser.parse_args()

    matching_ids = extract_speed_limit_relations(args.osm_file, args.lower, args.upper)
    for rid in matching_ids:
        print(rid)

if __name__ == "__main__":
    main()
