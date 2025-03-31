# map_utils
このリポジトリは地図データを処理・操作及びエラーチェックを行うユーティリティツール群を提供します。
詳細は各ディレクトリの個別のREADMEを参照してください。

## plant_area_maker
.osmファイルで指定した範囲に指定の間隔で点群を充填するスクリプトが`plant_area_maker`ディレクトリ内にあります。
複数のpcdファイルを同時に読むこむ運用を想定しており、.pcdファイルに破壊的な変更は行わない設計になっています。
### quickmanual
`python3 plant_area_maker.py input.osm --step 0.1`
- `input.osm`:入力するosmファイルのパス
- `--step`:点群を充填する間隔を指定するパラメータ。指定しない場合はデフォルトで0.1が使用される。
- 出力されるファイル名は入力された.osmファイルの名前に_plantが付与されたものになります。例えばhogepiyo.osmを入力したならhogepiyo_plant.pcdとなります。また同名のファイルが存在した場合はシリアル番号が付与されます。
osmファイルは充填したい範囲の情報が含まれている必要があります。範囲の指定方法についてはplant_area_makerの[README.md](https://github.com/minamidani/map_utils/blob/main/plant_area_maker/README.md)に説明があります。

## ライセンス
現在、ライセンスの選定を行っています。決定次第、こちらに記載します。（記載日：2025年3月31日、4月4日を目安に）

## 問題報告
問題を報告したい場合は、[Issues](https://github.com/midamidani/map_utils/issues) にて報告してください。
