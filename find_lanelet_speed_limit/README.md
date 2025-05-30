# find_lanelet_speed_limits

このスクリプトは、OpenStreetMap (OSM) 形式のXMLファイルから、以下の条件をすべて満たす `relation` を抽出し、その `id` を出力します。

VMBがthresholdで指定した速度の範囲外を警告で表示するのに対してこのスクリプトは速度の範囲内を表示します。

## 抽出対象の条件

- `<tag k="type" v="lanelet"/>` を持つ
- `<tag k="subtype" v="road"/>` を持つ
  - 車両が通るLaneを対象とします。退避レーンであるroad_shoulderは対象外です。
- `<tag k="turn_direction" v="..."/>` を **持たない**
- `<tag k="control" v="..."/>` を **持たない**
  - 交差点内は意図があって法定速度から逸脱させていることが明らかなので交差点内を対象外とします。controlタグは徐行エリア等を走行することを明示的にするためです。
- `<tag k="speed_limit" v="X"/>` の `X` が指定された数値範囲内である（デフォルトは 10〜10）

## 使用方法

```bash
python find_lanelet_speed_limits.py your_file.osm [--lower LOWER] [--upper UPPER]
```

- `your_file.osm`: 処理対象のOSMファイルのパス
- `--lower`: `speed_limit` の下限（デフォルト: 10）
- `--upper`: `speed_limit` の上限（デフォルト: 10）

### 例:

```bash
python find_lanelet_speed_limits.py map.osm --lower 5 --upper 15
```

この例では、`speed_limit` が5以上15以下の対象 `relation` を抽出し、`id` を出力します。

## 出力

抽出された各 `relation` のIDを、標準出力に一行ずつ表示します。

---

## 注意点

- `speed_limit` が数値でない場合は無視されます。
- `turn_direction` および `control` タグの有無はキーの存在だけで判断します（値にかかわらず除外されます）。
