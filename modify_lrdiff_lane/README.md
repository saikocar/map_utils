# modify lrdiff lane

このスクリプトは、Autowareのlanelet2（.osm）ファイル中のlaneletにおいて、左右のLineStringのPointの数が一致しない場合に、少ない方のLineStringにPointを補完することで左右で1対1の対応関係を作り、整合性のあるデータへと修正します。

## 主な機能

- lanelet内のPoint数が少ない側のLineStringに対して多い側の点の情報を利用して点を補完
- 変更されたLineStringやLane、追加されたPointの追跡管理

## 使用方法

1. 対象の `.osm` ファイルに対して以下のコマンドを実行します：

   ```bash
   python modify_lrdiff_lane.py input.osm
   ```
   
   処理結果は `input_modify.osm` として保存されます。

2. 出力された `input_modify.osm` をVector Map Builderにインポートし、再エクスポートしてください。

   - 当スクリプトは `lat`・`lon` 情報を空にして出力するため、正しい緯度経度情報を補完するには Vector Map Builder 上で再計算する必要があります。
   - エクスポートされたファイルには `lat`・`lon` が正しく付与されており、通常の地図ツールや自動運転システムで利用可能になります。

## ノード補完アルゴリズム概要

- 各 `fewer_nodes` 側のノードに対し、`more_nodes` 側のノードから最短距離のものを対応付け。
- 対応付けできなかった `more_nodes` 側のノードに対して、補間処理を行い、`fewer_nodes` に新しいノードを追加。
- 追加されるノードは、線分上での最近傍点として計算される。

## データ構造と制約

- `local_x`, `local_y`, `ele` タグが各ノードに必要です。これらが欠如しているとエラーが発生します。
- `lat`, `lon` は空とし、管理上は `local_x`, `local_y` により平面座標を使用します。
- lanelet2の仕様に準拠しており、OpenStreetMapの仕様とは異なります。

## エラー処理

- 入力ノードに `local_x`, `local_y`, `ele` タグが存在しない場合、例外が発生します。
- ノードの挿入に失敗した場合には、エラーメッセージが表示されます。
