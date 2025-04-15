# remove_dummy_relations

## 概要

このスクリプトは、tier4のVector Map Builderから指定された `.osm` ファイルから以下の条件に該当するLaneを左右のLineStringを保持しながら削除します：

- `subtype`が`dummy`
- `OptionalTags`の'key'が`dummy``

削除された `Lane` の ID は`relation` の IDとしてターミナルに出力され、変更後の `.osm` ファイルは入力ファイルと同じディレクトリに出力されます。

## 概要のスクリプトのフローチャートに基づく説明

このスクリプトはxmlファイルを読み込み以下のどちらかの要素をもつ`<relation>` 要素を削除します：

- `<tag k="subtype" v="dummy"/>`
- `<tag k="dummy" v="任意の値"/>`

削除された `relation` の ID はターミナルに出力され、変更後の `.osm` ファイルは入力ファイルと同じディレクトリに出力されます。

## 想定する利用シーン

Vector Map Builder上で`Lane`を削除した場合、その`Lane`以外に関連付けられていない`LineString`は削除されます。

ここで車道の`Lane`の外側に一定間隔でroad_borderを配置する場合`Change Lanelet Width`の機能を利用するのが便利ですが`LineString`を残して`Lane`を削除する方法が存在しません。

また本来なら`road_shoulder`あるいは`pedestrian_lane`が設定されるべきであるのだが4月15日時点では`road_shoulder`の取り扱いに不具合が報告されています。

そのため無関係な`dummy`を設定して問題の回避を試みますがファイルの肥大化を起こすので当スクリプトで削減します。

## 特徴

- 削除対象の `relation id` を標準出力に表示
- 削除対象が存在しない場合はファイルを出力せずに通知
- 出力ファイル名が既に存在する場合、自動でシリアルナンバーを付与

---

## 使用方法

```bash
python remove_dummy_relations.py path/to/input_file.osm
```

### 引数

- `input_file.osm`：処理対象の`OSM`ファイル

---

## 出力ファイル

- 入力ファイル名の末尾に `_DE` を付加した名前になります
  - 例：`map.osm` → `map_DE.osm`
- 同名のファイルが存在する場合は、シリアル番号を付加
  - 例：`map_DE_1.osm`, `map_DE_2.osm` ...
- 出力ファイルは入力ファイルと**同じディレクトリ**に保存されます。

---

## 実行結果の例

```bash
$ python remove_dummy_relations.py sample.osm
削除: relation id=123456
削除: relation id=789012
出力ファイル: sample_DE.osm
```

削除対象が存在しない場合：

```bash
$ python remove_dummy_relations.py sample.osm
削除対象の relation は存在しません。
```
