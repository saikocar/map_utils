import sys
import os
import xml.etree.ElementTree as ET

def should_delete_relation(relation):
    for tag in relation.findall('tag'):
        k = tag.attrib.get('k')
        v = tag.attrib.get('v')
        if (k == 'subtype' and v == 'dummy') or (k == 'dummy'):
            return True
    return False

def generate_output_filename(input_file):
    base, ext = os.path.splitext(input_file)
    output_file = base + "_DE" + ext
    counter = 1
    while os.path.exists(output_file):
        output_file = f"{base}_DE_{counter}{ext}"
        counter += 1
    return output_file

def main():
    if len(sys.argv) != 2:
        print("Usage: python remove_dummy_relations.py <input_file.osm>")
        sys.exit(1)

    input_file = sys.argv[1]

    if not os.path.exists(input_file):
        print(f"File not found: {input_file}")
        sys.exit(1)

    tree = ET.parse(input_file)
    root = tree.getroot()

    relations = root.findall('relation')
    to_delete = []

    for relation in relations:
        if should_delete_relation(relation):
            to_delete.append(relation)

    if not to_delete:
        print("削除対象の relation は存在しません。")
        return

    for rel in to_delete:
        print(f"削除: relation id={rel.attrib.get('id')}")
        root.remove(rel)

    output_file = generate_output_filename(input_file)
    tree.write(output_file, encoding="utf-8", xml_declaration=True)
    print(f"出力ファイル: {output_file}")

if __name__ == "__main__":
    main()
