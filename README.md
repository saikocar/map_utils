# map_utils
このリポジトリは地図データを処理・操作及びエラーチェックを行うユーティリティツール群を提供します。
詳細は各ディレクトリの個別のREADMEを参照してください。

## plant_area_maker
.osmファイルで指定した範囲に指定の間隔で点群を充填するスクリプトが`plant_area_maker`ディレクトリ内にあります。
複数のpcdファイルを同時に読むこむ運用を想定しており、pcdファイルに破壊的な変更は行わない設計になっています。
### Quick Manual
`python3 plant_area_maker.py input.osm --step 0.1`
- `input.osm`:入力するosmファイルのパス
- `--step`:点群を充填する間隔を指定するパラメータ。指定しない場合はデフォルトで0.1が使用される。
- 出力されるファイル名は入力された.osmファイルの名前に_plantが付与されたものになります。例えばhogepiyo.osmを入力したならhogepiyo_plant.pcdとなります。また同名のファイルが存在した場合はシリアル番号が付与されます。
osmファイルは充填したい範囲の情報が含まれている必要があります。範囲の指定方法については[plant_area_makerのREADME.md](https://github.com/minamidani/map_utils/blob/main/plant_area_maker/README.md)に説明があります。

## osm_relation_checker
.osmファイルで左右のLineStringのPoint(osmのnode)の数が異なるLane(osmのrelation)のidを表示するスクリプトが`osm_relation_checker`ディレクトリ内にあります。
### Quick Manual
`python3 osm_relation_checker.py input.osm`
- `input.osm`:入力するosmファイルのパス
- **出力** ： 左右の`LineString`に含まれる`Point`の数が異なる`Lane`を以下の形式で表示
```
Relation ID: XXXX, Left nodes: YYYY, Right nodes: ZZZZ
Relation ID: ......
```
（該当するものがない場合はNo relations found with differing left and right node counts.のメッセージが表示されます）

[osm_relation_checkerのREADME.md](https://github.com/minamidani/map_utils/blob/main/osm_relation_checker/README.md)に詳細な説明があります。

## make_crosswalk_polygon
crosswalkのpointに連動するcrosswalk_polygonを生成するスクリプトです。
osmファイルに対して破壊的な変更は行いませんが入力及び出力ファイルをテキストエディタで処理した後にVector Map Builderで適宜処理する必要があります。
### Quick Manual
`python3 make_crosswalk_maker.py input.osm`
- `input.osm`:入力するosmファイルのパス
- **出力** ： `input_append.osm`

[make_crosswalk_polygonのREADME.md](https://github.com/minamidani/map_utils/blob/main/make_crosswalk_polygon/README.md)に詳細な説明があります。

## remove_dummy_relations
ダミーのレーンを削除するスクリプトです。
### Quick Manual
`python3 remove_dummy_relations.py input.osm`
- `input.osm`:入力するosmファイルのパス
- **出力** ： `input_DE.osm`

[remove_dummy_relationsのREADME.md](https://github.com/minamidani/map_utils/blob/main/remove_dummy_relations/README.md)に詳細な説明があります。

## 問題報告
問題を報告したい場合は、[Issues](https://github.com/minamidani/map_utils/issues) にて報告してください。
