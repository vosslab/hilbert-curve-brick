# Code architecture

This document describes how the `hilbert-curve-brick` generator is organized and
how data flows from command-line arguments to PNG slices and an optional LDraw
brick model. It targets contributors who need a map of the modules before making
changes.

## Overview

- A 3D Hilbert curve is built in a voxel grid, scaled up by integer block
  replication, then exported as PNG slices and an optional LDraw `.ldr` file.
- The entry point is [hilbert-curve-brick.py](../hilbert-curve-brick.py); all
  reusable logic lives in the [hilbert_curve_brick/](../hilbert_curve_brick)
  package.
- PNG writing is always on. LDraw export runs only when `--ldr-output` is set.

## Major components

- [hilbert-curve-brick.py](../hilbert-curve-brick.py): thin entry point. Parses
  and validates args, builds the base volume, scales it, writes PNG slices, and
  optionally writes LDraw bricks.
- [hilbert_curve_brick/cli.py](../hilbert_curve_brick/cli.py): argparse setup and
  validation. Holds six user-facing options (`--dimension`, `--target-size`,
  `--output-dir`, `--ldr-output`, grid toggle, color toggle) plus fixed run
  constants (`SCALE_Y`, `AXIS`, `SLICE_START`, `SLICE_END`, `PREFIX`,
  `LDR_COLOR`). The `N_BANDS` constant lives in
  [hilbert_curve_brick/color.py](../hilbert_curve_brick/color.py).
- [hilbert_curve_brick/curve.py](../hilbert_curve_brick/curve.py): pure Hilbert
  math. Maps a linear index to n-dimensional coordinates via Gray-code traversal,
  with inverse and legacy-named wrappers.
- [hilbert_curve_brick/volume.py](../hilbert_curve_brick/volume.py): volume
  generation and PNG output. Builds the curve into a 3D array, computes the
  power-of-two scale, block-replicates with `scipy.ndimage.zoom`, slices along
  an axis, applies a render-time grid mask when enabled, and writes PNGs.
- [hilbert_curve_brick/color.py](../hilbert_curve_brick/color.py): palette loading
  and color mapping. Reads `rainbow_palette.yaml` (16 hex entries), maps a
  0-based curve index to a discrete band, and converts `(r, g, b)` to LDraw
  direct-color strings (`0x2RRGGBB`).
- [hilbert_curve_brick/ldraw.py](../hilbert_curve_brick/ldraw.py): LDraw export.
  Greedily tiles occupied voxels (`volume > 0`) with 2x2x3 vertical bricks then
  2x6, 2x4, and 2x2 layer bricks, and formats LDraw lines. In color mode each
  brick carries a direct-color code derived from its anchor cell's curve band.
- [leginon/imagefile.py](../leginon/imagefile.py): minimal PNG writer used by
  `volume.write_slices` to normalize an array and save it with Pillow.

## Data flow

1. `cli.parse_args` and `cli.validate_args` read and check options; `--dimension`
   must be a power of two.
2. `volume.build_curve_volume(dimension)` returns an integer (`int32`) volume:
   `0` for empty, `index + 1` at occupied and connector voxels, so the curve
   order is preserved for band coloring.
3. `volume.compute_scale` derives a power-of-two scale from `--target-size`;
   `volume.scale_volume` block-replicates the base volume (Y uses `SCALE_Y`).
   Integer labels are preserved exactly by `order=0` nearest-neighbor zoom.
4. When the grid is enabled, `volume.grid_params(scale)` returns `(step, offset)`
   and `volume.build_grid_mask(shape, step, offset)` builds a separate boolean
   mask; the model volume is never mutated.
5. In color mode the entrypoint calls `color.load_palette()` (reads the packaged
   YAML) to get 16 `(r, g, b)` tuples and passes `total = dimension**3` so
   `write_slices` can map each voxel label to a color band.
6. `volume.write_slices` iterates slices along `AXIS`, converts each label slice
   to grayscale (mono) or RGB (color) via `slice_to_grayscale` /
   `slice_to_rgb`, and writes PNGs through `leginon.imagefile.arrayToPng`.
7. If `--ldr-output` is set, `ldraw.volume_to_bricks(volume)` converts the
   scaled volume to brick placements using `volume > 0` occupancy, then
   `ldraw.write_ldraw` writes the `.ldr` file. In color mode each brick is
   colored with `0x2RRGGBB` direct-color codes; in mono mode a single LDraw
   color index is used.

## Testing and verification

- Fast tests live in [tests/](../tests) and run with `pytest tests/`.
- [tests/test_grid_alignment.py](../tests/test_grid_alignment.py) checks grid
  lines never cut squares and each square maps to one cell.
- [tests/test_cli_validation.py](../tests/test_cli_validation.py) checks the
  power-of-two validation.
- [tests/smoke_test.sh](../tests/smoke_test.sh) runs the generator end to end.

## Extension points

- New CLI options: add to `parse_args` in
  [hilbert_curve_brick/cli.py](../hilbert_curve_brick/cli.py); promote a constant
  to a flag only when users change it between runs.
- New brick shapes: add a part dict and placement rule in
  [hilbert_curve_brick/ldraw.py](../hilbert_curve_brick/ldraw.py).
- Alternate output formats: add a writer module and call it from
  [hilbert-curve-brick.py](../hilbert-curve-brick.py).

## Known gaps

- Confirm whether the `int_to_Hilbert` / `Hilbert_to_int` legacy wrappers in
  [hilbert_curve_brick/curve.py](../hilbert_curve_brick/curve.py) still have
  external callers, or can be removed.
