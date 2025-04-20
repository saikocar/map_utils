import xml.etree.ElementTree as ET
import sys

def extract_tags(osm_file):
    # OSMファイルの解析
    tree = ET.parse(osm_file)
    root = tree.getroot()
    
    keys = set()  # keyのリスト
    values = set()  # valueのリスト
    
    # node, way, relationを対象にタグのkey, valueを抽出
    for elem in root:
        if elem.tag == 'node' or elem.tag == 'way' or elem.tag == 'relation':
            for tag in elem.findall('tag'):
                key = tag.get('k')
                value = tag.get('v')
                
                keys.add(key)  # keyは必ず追加
                
                # 数値データを除外したvalueを追加
                if not is_numeric(value):
                    values.add(value)  # 数値でなければvalueを追加
    
    # 結果を表示
    print("Keys:")
    for key in keys:
        print(f"  {key}")
    
    print("\nValues:")
    for value in values:
        print(f"  {value}")

def is_numeric(value):
    """数値データかどうかを判定する"""
    try:
        float(value)  # 数値に変換できるか試す
        return True
    except ValueError:
        return False

# コマンドライン引数でファイル名を受け取る
if len(sys.argv) != 2:
    print("Usage: python script.py <osm_file>")
    sys.exit(1)

osm_file = sys.argv[1]  # 引数で渡されたOSMファイルのパス
extract_tags(osm_file)
