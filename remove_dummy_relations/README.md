# remove_dummy_relations

## 概要

このスクリプトは、指定された `.osm` ファイルから以下の条件に該当する `<relation>` 要素を削除します：

- `<tag k="subtype" v="dummy"/>`
- `<tag k="dummy" v="任意の値"/>`

削除された `relation` の ID はターミナルに出力され、変更後の `.osm` ファイルは入力ファイルと同じディレクトリに出力されます。

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

- `input_file.osm`：処理対象の OSM XML ファイル

---

## 出力ファイル

- 入力ファイル名の末尾に `_DE` を付加した名前になります
  - 例：`map.osm` → `map_DE.osm`
- 同名のファイルが存在する場合は、シリアル番号を付加
  - 例：`map_DE_1.osm`, `map_DE_2.osm` ...

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

---

## 注意点

- 入力ファイルは OSM XML 形式である必要があります。
- 出力ファイルは入力ファイルと**同じディレクトリ**に保存されます。

---

## ライセンス

このスクリプトは MIT ライセンスのもとで公開されています。
