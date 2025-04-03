# Crosswalk Polygon Maker

## 概要

本スクリプトは、Vector Map Builderで作成されたOSMファイル内の lanelet タイプの relation で subtype が crosswalk のものを解析し、新たな crosswalk_polygon を生成するものです。 既に同じノード構成の crosswalk_polygon が存在する場合、新しいポリゴンは追加されません。

rvizはcrosswalkにpolygonが関連付けられていない場合に表示上の警告メッセージを発するのでその対策になります。

## 特徴

本スクリプトは既存のosmファイルに破壊的な変更を加えません。この動作は安全ですがスクリプトの実行のみで編集作業は完了しないことを意味します。

## 必要環境

Python 3.x

## 使い方

python crosswalk_polygon_maker.py input.osm

- input.osm : OSM ファイルのパス

## 出力

- input_append.osm (crosswalk_polygonの追加がある場合のみ)

入力ファイルと同一階層に入力ファイル名に`_append`を付与したファイルが出力されます。

またスクリプト実行後、以下のメッセージが表示されます：

crosswalk_polygonが追加された場合： Added X new crosswalk_polygon(s). Output file: /full/path/to/input_append.osm

crisswalk_polygonの追加がなかった場合： No new crosswalk_polygon added. Output file was not created.

## 出力されたファイルの扱い方

1. input.osmとinput_append.osmをテキストエディタで開き`</osm>`の上部にinput_append.osmの内容をコピーアンドペーストします。
2. Vector Map Builderでinput_append.osmの内容が加えられたinput.osmをインポートしRegulatoryElementsを適切に関連付ける。
