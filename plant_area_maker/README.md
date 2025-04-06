
# Plant Area Maker

## 概要

`plant_area_maker` スクリプトは、地理的環境における車線を表すosmファイルから点群を生成します。このスクリプトは指定のタグを持つlaneから情報を取得し、提供されているジオメトリに基づいて領域を点で埋めて3D点群を作成します。生成された点群はpcdファイルとして保存され、その後のアプリケーションやシミュレーション（自動運転車の開発や地理情報システム（GIS）など）で使用できます。またこのスクリプトは点の生成におけるステップサイズのカスタマイズが可能です。

> **Note:** TIER IVが提供する地図作成ツールであるVector Map Builderで編集されたlanelet2ファイルが入力されることを想定しています。Open Street Mapで利用されるosm形式とは拡張子は同じですがlenelet2は拡張された仕様であることに留意してください。

## 特徴

- **点群生成**: 3D点群（PCD形式）を生成します。これにはX、Y、Z座標および強度（intensity）値が含まれます。ただし**intensityは1で固定**です
- **柔軟なステップサイズ**: 車線境界に沿った点の生成のためのステップサイズをカスタマイズ可能です。
- **高さのサポート**: 高さ情報を使用してZ方向に領域を埋めることができます。

## 必要条件

- Python 3.x(動作確認済み:`3.10.12`)
- 要求されるPythonライブラリ:
  - `numpy`(動作確認済み:`1.26.4`)
  - `xml.etree.ElementTree`

## 使用方法

スクリプトを実行するには、次のコマンドを使用します:

```bash
python plant_area_maker.py <osm_file> --step <step_size> --intensity <intensity_param>
```
または
```bash
python plant_area_maker.py <osm_file> --step <step_size> --rgb <r> <g> <b>
```

### 引数

- `<osm_file>`: osmファイルのパス。
- `--step <step_size>`: （オプション）車線境界に沿って点を生成するためのステップサイズ。指定しない場合、デフォルト値は `0.1` です。
- `--intensity <intensity_param>`: （オプション）intensityのパラメータを指定します。デフォルト値は`1`です。
- `--rgb <r> <g> <b>`: （オプション）rgbのパラメータを指定します。このオプションを利用しない場合pcdファイルは`x y z intensity`で保存します。

### 例

```bash
python plant_area_maker.py map.osm --step 0.05
```

これにより、`map.osm` ファイルが処理され、ステップサイズ `0.05` 、intensity`1`で点が生成されます。

```bash
python plant_area_maker.py map.osm --step 0.02 --rgb 255 255 255
```

こちらの場合は、`map.osm` ファイルが処理され、ステップサイズ `0.02` 、`R=255,G=255,B=255`で点が生成されます。


## 出力

スクリプトはPCDファイルを生成します。これは標準的な点群フォーマットです。出力ファイルは、入力osmファイルと同じ名前で、末尾に `_plant` を追加したものになります。ファイルが既に存在する場合、スクリプトは上書きしないようにサフィックスを追加します。

例えば、入力osmファイルが`map.osm`の場合、出力ファイルは`map_plant.pcd`となります。同名のファイルが存在した場合は`map_plant(1).pcd`となり、`map_plant(2).pcd`、`map_plant(3).pcd`と続きます。

## Vector Map Builderでの領域の指定方法

1.指定したい領域の底面にlaneを作成します。

2.laneの属性のeditでsubtypeに`plant`、optional tagsでkeyに`height`、valueに高さの数値を入力します。
> **Note:** laneの左右のlinestringが持つpointは同数である必要があります。

## アルゴリズム
plant_area_makerスクリプトは2本の直線で挟まれた領域を指定の間隔(`step`)で指定の高さ(`height`)まで充填することを繰り返すものである。

以下は2本の直線（4つの頂点）をlaneの情報から抽出した後の処理内容である。

1.2本のlineの長さを比較して長い方を指定のstep幅で分割する。短い方は長い方と同じ分割数となるように等間隔で分割する。

2.分割された点を左右で対応付けて結んだ直線上に指定のstep幅で点を配置する。

3.それぞれの点からlineのoptional tagsで指定したheightまで指定のstep幅で点を配置する。heightがstepの整数倍でない場合でもheightの位置には点は配置される。
  > **Note:** heightの方向はlaneで指定された4つの頂点を基に計算された平面の法線方向である。数学的に説明するとheightの方向は底面の4頂点を最小二乗的に近似する平面の法線方向でxyz空間のzが増加する方向としている。
