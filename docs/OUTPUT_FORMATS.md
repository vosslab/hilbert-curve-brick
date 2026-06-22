# Output formats

This tool produces two outputs: PNG slice images (always) and an optional LDraw
brick model. Both are written by [hilbert_curve_brick/](../hilbert_curve_brick).

## PNG slices

- Written by `write_slices` in
  [hilbert_curve_brick/volume.py](../hilbert_curve_brick/volume.py) through
  `leginon.imagefile.arrayToPng`.
- One grayscale PNG per slice along the y axis.
- Filenames follow `<prefix><dimension>-<index>.png`, for example
  `hilbert8-001.png` (`prefix` is `hilbert`, index is zero-padded to 3 digits).
- Slices are inverted (white background) and normalized to 0-255 by default,
  controlled by the `INVERT` and `NORMALIZE` constants in
  [hilbert_curve_brick/cli.py](../hilbert_curve_brick/cli.py).
- The first border slice is skipped (`SLICE_START = 1`).

## LDraw model

- Written by `write_ldraw` in
  [hilbert_curve_brick/ldraw.py](../hilbert_curve_brick/ldraw.py) when
  `--ldr-output` is set.
- A plain-text `.ldr` file beginning with `0 FILE`, name, author, and license
  meta lines.
- Each brick is a type-1 line: `1 <color> <x> <y> <z> <3x3 rotation matrix> <part>`.
- Parts used: 3003 (2x2), 3001 (2x4), 2456 (2x6), and 30145 (2x2x3).
- Coordinates use LDraw units: 40 LDU per cell, 24 LDU per brick height.
- Color index comes from the `LDR_COLOR` constant (default 15).

## Known gaps

- [ ] Document how to import the `.ldr` file into LDraw viewers or LeoCAD.
