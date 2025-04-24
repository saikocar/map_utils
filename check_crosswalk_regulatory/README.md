# find_crosswalk_with_regulatory.py

このスクリプトは、OpenStreetMap (OSM) ファイル内の `<tag k="type" v="lanelet"/>` および `<tag k="subtype" v="crosswalk"/>` を持つ `relation` について、
その中に `<member type="relation" role="regulatory_element" ref="XXXX"/>` を含むものの ID を抽出・表示するツールです。

## 使用方法

```bash
python find_crosswalk_with_regulatory.py your_map.osm
```

- `your_map.osm` は対象の OSM ファイルパスです。

## 出力

- `lanelet` タイプで `subtype=crosswalk` を持ち、かつ `regulatory_element` を参照する `relation` の ID を標準出力に表示します。

### 出力例

```
1200456
1200789
...
```

## 利用シーン

- OSM データ構造の整合性検証
