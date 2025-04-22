# check_kvtypo

このスクリプトはlanelet2（.osm）ファイルから `node`、`way`、`relation` に含まれるすべてのタグの `key` と **非数値の** `value` を抽出して表示します。

## 特徴

- 数値の value は自動的に除外されます（例: `"ele": "10.5"` は value として無視）。
- `key` は常に表示対象になります。
- `key` や `value` の除外リストファイルを指定可能です。

## 使用方法

### 基本的な使い方

```bash
python3 check_kvtypo.py your_file.osm
```

### 除外リストを指定する場合

```bash
python3 check_kvtypo.py your_file.osm --exk exclude_keys.list --exv exclude_values.list
```

- `--exk`：除外する key のリストファイル（省略可能）
- `--exv`：除外する value のリストファイル（省略可能）

## 除外リストファイルの形式

### exclude_keys.list

```
local_x
local_y
ele
```

### exclude_values.list

```
crosswalk
crosswalk_polygon
```

各行に1つずつ key や value を記述します。空行は無視されます。

## 出力例

```
Keys:
  area
  arrow

Values:
  begin
  crosswalk
```

## 動作環境

- Python 3.6 以降
- 標準ライブラリのみを使用（追加のパッケージ不要）
