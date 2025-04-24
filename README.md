# map_utils
このリポジトリは地図データを処理・操作及びエラーチェックを行うユーティリティツール群を提供します。

また地図データはOpenStreetMapのosmファイルと拡張子は同じですがtier4のVector Map Builder（VMB）を利用して編集していることが前提となります。

VMBで作成したosmファイルはAutoware向けの独自の仕様となっていることに注意してください。

スクリプトの詳細は各ディレクトリの個別のREADMEを参照してください。

## check_crosswalk_regulatory
crosswalkにregulatoryが関連付けられたままのものを表示するスクリプトです。

このスクリプトはgenerate_crosswalk_regulatoryの事後処理用です。

## check_kvtypo
VMBのミスタイプを探索するスクリプトです。

## check_signal_config
cp.signal_idの未完了・不正な入力を探索するスクリプトです。

## find_collinear_nodes
レーンの形状に寄与しない直線上の点を削除するスクリプトです。

## find_lanelet_speed_limit
指定の速度の範囲内のレーンを探索するスクリプトです。

## generate_crosswalk_regulatory
crosswalkに関してregulatoryが未設定ならそのcrosswalkにregulatoryを作成するスクリプトです。

## make_crosswalk_polygon
crosswalkのpointに連動するcrosswalk_polygonを生成するスクリプトです。

## osm_relation_checker
左右のLineStringのPointの数が異なるLaneのidを表示するスクリプトです。

## plant_area_maker
指定した範囲に指定の間隔で点群を充填するスクリプトです。

## remove_dummy_relations
ダミーのレーンを削除するスクリプトです。


## 問題報告
問題を報告したい場合は、[Issues](https://github.com/saikocar/map_utils/issues) にて報告してください。
