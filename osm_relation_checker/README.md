
# osm relation checker

## 概要

osmファイルのレーンの左右の線の頂点の数が異なる場合、自動運転ソフトウェアである`Autoware`の`drivable area expantion`の挙動が不正確なことになる可能性が指摘されています。`osm_relation_checker` スクリプトは、地理的環境における車線を表すosmファイルのレーンの左右の線の頂点の数を確認し、不整合があれば警告的なメッセージをターミナル上に出力します。警告的なメッセージにはレーンのIDが含まれており、Tier IV社の`Vector Map Builder`を用いた修正作業に役立てることが出来ます。`osm_relation_checker`スクリプトがosmファイルを変更することはありません。

> **Note:** TIER IVが提供する地図作成ツールであるVector Map Builderで編集されたlanelet2ファイルが入力されることを想定しています。Open Street Mapで利用されるosm形式とは拡張子は同じですがlenelet2は拡張された仕様であることに留意してください。

## 必要条件

- Python 3.x(動作確認済み:`3.10.12`)
- 要求されるPythonライブラリ:
  - `xml.etree.ElementTree`

## 使用方法

スクリプトを実行するには、次のコマンドを使用します:

```bash
python3 osm_relation_checker.py <osm_file>
```

### 引数

- `<osm_file>`: osmファイルのパス。

## 出力

Lane(osmのrelaton)の左右のLineStringのPoint(osmのnode)の数が異なるものが見つかった場合、
```
Relation ID: XXXX, Left nodes: YYYY, Right nodes: ZZZZ
Relation ID: ......
```
という形式で出力されます。不整合が見つからなかった場合は
```
No relations found with differing left and right node counts.
```
と出力されます。

## Vector Map Builderでの活用

1.`Vector Map Builder`でosmファイルをインポートし、`ObjectSearch`に不整合として出力されたrelationのIDを入力して該当のLaneletにジャンプします。

2.Laneletの`Left Bound`または`Right Bound`を選び、Pointを必要なだけinsertあるいはdeleteすることで数を合わせる。

> **Note:** (おそらくですが)点は左右対称的に配置されることが望ましい。

## アルゴリズム
lenelet2ファイルはosmファイルの拡張であり
- lanelet -> relation
- LineString -> way
- Point -> node
と読み替える必要がある。

あとで書く
