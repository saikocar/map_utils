# check signal config

このスクリプトは、Vector Map Builderで作成したOSMファイル内の traffic light に関するRegulatoryElementsに関するタグを解析し、以下を検出します：

1. **`cp.signal_id`で一度も参照されないtraffic light**
2. **`cp.signal_id` に指定されているが、対応する traffic lightが存在しない ID**

---

## 要件

- Python 3.x
- 標準ライブラリのみ使用（外部依存なし）

---

## 使い方

```bash
python check_signal_cofig.py <path_to_osm_file>
```

---

## フローチャート

1. `<relation>` タグのうち、以下の2つのタグを持つIDを抽出：

    ```xml
    <tag k="type" v="regulatory_element"/>
    <tag k="subtype" v="traffic_light"/>
    ```

2. 他の `<relation>` の中にある以下の形式のタグを収集：

    ```xml
    <tag k="cp.signal_id" v="123456"/>
    ```

3. 以下の2種類のIDを出力：
    - `traffic_light` relationとして定義されているが、`cp.signal_id`として一度も参照されていないID
    - `cp.signal_id`に登場しているが、対応する`traffic_light` relationが存在しないID

---

## 出力例

```
Unused traffic light relation IDs:
12345678
12345679

cp.signal_idに指定されているが、対応するtraffic_light relationが存在しないID:
98765432
```

未使用が無い場合：
```
すべてのtraffic_light relationはcp.signal_idとして参照されています。

cp.signal_idに存在しないtraffic_light relationの参照はありません。
```

---
