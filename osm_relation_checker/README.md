
# osm relation checker

## 概要

.osmファイルのレーンの左右の線の頂点の数が異なる場合、自動運転ソフトウェアである`Autoware`の`drivable area expansion`の挙動が不正確になる可能性が指摘されています。`osm_relation_checker` スクリプトは、地理的環境における車線を表すosmファイルのレーンの左右の線の頂点の数を確認し、不整合があれば警告メッセージをターミナル上に出力します。この警告メッセージにはレーンのIDが含まれており、Tier IVの`Vector Map Builder`を用いた修正作業に活用出来ます。このスクリプトは.osmファイルを変更しません。

> **Note:** TIER IVが提供する地図作成ツールであるVector Map Builderで編集されたlanelet2ファイルが入力されることを想定しています。
> `lanelet2` は `OSM` の拡張仕様であり、`.osm` という拡張子は同じですが、標準の `OpenStreetMap` 形式とは異なります。

## 必要条件

- Python 3.x(動作確認済み:`3.10.12`)

## 使用方法

スクリプトを実行するには、次のコマンドを使用します:

```bash
python3 osm_relation_checker.py <osm_file>
```

### 引数

- `<osm_file>`: osmファイルのパス。

## 出力

Lane(OSMのRelaton)の左右のLineStringのPoint(OSMのNode)の数が異なるものが見つかった場合、
```
Relation ID: XXXX, Left nodes: YYYY, Right nodes: ZZZZ
Relation ID: ......
```
という形式で出力されます。不整合が見つからなかった場合は以下のメッセージが出力されます。
```
No relations found with differing left and right node counts.
```

## Vector Map Builderでの活用

1.`Vector Map Builder`でosmファイルをインポートし、`ObjectSearch`に出力されたRelationのIDを入力して該当のLaneletにジャンプする。

2.Laneletの`Left Bound`または`Right Bound`を選び、Pointを必要なだけ挿入(insertPointToLineString)あるいは削除(delete)することで数を合わせる。

> **Note:** (おそらく)点は左右対称的に配置されることが望ましい。

## アルゴリズム
lanelet2ファイルは`OSM`ファイルの拡張であり以下のように読み替える。
- `Lanelet` -> `Relation`
- `LineString` -> `Way`
- `Point` -> `Node`

.osm拡張子は.xmlを地図データとして利用していることを示すものであり、XMLのパース方法は通常のものと同一である。

osm_relation_checkerは以下のような仕組みとなっている。
1. `xml.etree.ElementTree`ライブラリを利用してosmファイルをインポート
2. `left` および `right` の `member` を持つ `Relation` 要素を抽出する。
3. `left` の `id` を持つ `Way` が参照する `Node` の数と、`right` の `id` を持つ `Way` が参照する `Node` の数を比較し、異なれば警告を出力する。 
