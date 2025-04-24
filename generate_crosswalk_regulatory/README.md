# generate_crosswalk_regulatory.py

このスクリプトは、OpenStreetMap (OSM) 形式のファイル内で、`<tag k="type" v="lanelet"/>` および `<tag k="subtype" v="crosswalk"/>` を持つ `relation` が、
一度も `<relation type="regulatory_element" subtype="crosswalk">` から `refers` で参照されていない場合に対し、対応する `regulatory_element` を自動生成するツールです。

## 特徴

- 参照されていない `crosswalk lanelet` を抽出
- 条件に合う `crosswalk_polygon` を探し、regulatory_element を自動生成
- 元の lanelet relation に `regulatory_element` への参照を追加
- 差分がある場合、ファイル名に `_crosswalk.osm` を付けて保存

## 使用方法

```bash
python generate_crosswalk_regulatory.py your_map.osm
```

`your_map.osm` は処理対象の OSM ファイルです。

## 出力

- `your_map_crosswalk.osm`（変更があった場合）
- 生成された regulatory_element の ID を標準出力に表示

## 注意事項

- `<member role="crosswalk_polygon">` に使用される `way` は `left` と `right` の両方の `way` と同じノード集合を持ち、
  `<tag k="type" v="crosswalk_polygon"/>` および `<tag k="area" v="yes"/>` を有する必要があります。
- 条件に合致する `crosswalk_polygon` が存在しない場合、生成される `relation` から `crosswalk_polygon` メンバは省略されます。
- crosswalkのlaneから参照するのではなく交差するlaneから参照するのが正しい地図の構成です。生成されたosmファイルをVector Map Builderで編集する必要があります。
