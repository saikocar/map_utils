
# OSM Colinear Node Cleanup Tool

This script processes an OSM (OpenStreetMap) file and removes nodes from `way` elements that are determined to be colinear, i.e., they lie approximately on a straight line between two other nodes. This helps reduce redundancy in map data while preserving geometric accuracy.

## Features

- Detects and removes colinear nodes using 3D coordinates (`local_x`, `local_y`, `ele`).
- Only removes nodes that:
  - Appear to lie on a straight line within a tolerance (`eps`).
  - Are not referenced by any other way.
- Ensures that the first and last nodes of each way are preserved.
- Only modifies `way` elements with specific `type` tags: `line_thin`, `virtual`, `road_border`, `stop_line`, `fence`, `guard_rail`.
- Preserves all `node`, `relation`, and untouched `way` data.
- Does not produce an output file if no changes are made.

## Requirements

- Python 3.x

## Usage

```bash
python script.py input.osm [--eps EPSILON] [--m | --cm | --mm]
```

- `--eps`: Error tolerance for determining colinearity (in meters). Default is `1e-15`.
- `--m`, `--cm`, `--mm`: Unit multipliers to apply to `--eps`.
  - Use only one of these options at a time.
  - For example, `--cm` sets the effective epsilon to `eps * 0.01`.

### Example

```bash
python script.py map.osm --eps 1e-4 --cm
```

## Output

If changes are detected, a new file named `<original>_colinear.osm` will be created in the same directory.

## Notes

- Only nodes with valid `local_x`, `local_y`, and `ele` tags will be considered.
- If a node is shared across multiple ways, it will not be removed even if it's colinear.
- The script will notify you of any removed nodes and the associated geometric deviation.
