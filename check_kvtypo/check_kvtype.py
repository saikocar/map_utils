import xml.etree.ElementTree as ET
import argparse

def load_exclusion_list(filepath):
    """除外リストファイルを読み込んでセットとして返す"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return set(line.strip() for line in f if line.strip())
    except FileNotFoundError:
        print(f"Warning: Exclusion file '{filepath}' not found. Ignoring.")
        return set()

def is_numeric(value):
    """数値データかどうかを判定する"""
    try:
        float(value)
        return True
    except ValueError:
        return False

def extract_tags(osm_file, exclude_keys, exclude_values):
    tree = ET.parse(osm_file)
    root = tree.getroot()
    
    keys = set()
    values = set()
    
    for elem in root:
        if elem.tag in {'node', 'way', 'relation'}:
            for tag in elem.findall('tag'):
                key = tag.get('k')
                value = tag.get('v')

                if key and key not in exclude_keys:
                    keys.add(key)
                if value and not is_numeric(value) and value not in exclude_values:
                    values.add(value)
    
    print("Keys:")
    for key in sorted(keys):
        print(f"  {key}")
    
    print("\nValues:")
    for value in sorted(values):
        print(f"  {value}")

def main():
    parser = argparse.ArgumentParser(description="Extract tag keys and non-numeric values from an OSM file.")
    parser.add_argument("osm_file", help="Path to the OSM file")
    parser.add_argument("--exk", help="Path to exclude_keys.list", default=None)
    parser.add_argument("--exv", help="Path to exclude_values.list", default=None)

    args = parser.parse_args()

    exclude_keys = load_exclusion_list(args.exk) if args.exk else set()
    exclude_values = load_exclusion_list(args.exv) if args.exv else set()

    extract_tags(args.osm_file, exclude_keys, exclude_values)

if __name__ == "__main__":
    main()
