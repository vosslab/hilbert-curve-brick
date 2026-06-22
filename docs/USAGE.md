# Usage

Run [hilbert-curve-brick.py](../hilbert-curve-brick.py) to generate PNG slices of
a 3D Hilbert curve sized for LEGO-compatible brick builds, and optionally an
LDraw `.ldr` brick model.

## Quick start

- Generate slices for an 8x8x8 curve into `output/`:
  ```bash
  python3 hilbert-curve-brick.py -d 8 -o output
  ```
- Generate slices in 16-band rainbow color:
  ```bash
  python3 hilbert-curve-brick.py -d 8 -c -o output
  ```
- Also write an LDraw model:
  ```bash
  python3 hilbert-curve-brick.py -d 8 -o output -l output/hilbert.ldr
  ```
- LDraw model with rainbow color bricks:
  ```bash
  python3 hilbert-curve-brick.py -d 8 -c -o output -l output/hilbert.ldr
  ```

## CLI

The CLI lives in [hilbert_curve_brick/cli.py](../hilbert_curve_brick/cli.py) and
exposes six option concepts:

| Flag | Description |
| --- | --- |
| `-d`, `--dimension` | Cells per axis; must be a power of two (default 8). |
| `-s`, `--target-size` | Target max image size used to compute the scale (default 800). |
| `-o`, `--output-dir` | Directory for PNG slices (default `output`). |
| `-l`, `--ldr-output` | Path for an LDraw `.ldr` file; empty means no LDraw output. |
| `-g`, `--add-grid` / `-G`, `--no-grid` | Overlay or omit the cell grid (default on). |
| `-c`, `--color` / `-C`, `--mono` | Render in 16-band rainbow color or mono (default mono). |

In color mode the curve is divided into 16 equal bands from start (band 0) to end
(band 15). Band colors are loaded from
[hilbert_curve_brick/rainbow_palette.yaml](../hilbert_curve_brick/rainbow_palette.yaml)
and can be edited there to change the palette. Both PNG slices and LDraw bricks
use the same palette.

Fixed run settings (axis, slice range, prefix, LDraw color) are constants in
[hilbert_curve_brick/cli.py](../hilbert_curve_brick/cli.py); edit them there to
retune every run.

## Examples

- Larger curve without the grid overlay:
  ```bash
  python3 hilbert-curve-brick.py -d 16 -G -o output
  ```
- Smaller images by lowering the target size:
  ```bash
  python3 hilbert-curve-brick.py -d 4 -s 400 -o output
  ```
- Color output with LDraw:
  ```bash
  python3 hilbert-curve-brick.py -d 8 -c -o output -l output/hilbert8.ldr
  ```

## Inputs and outputs

- Inputs: command-line options only; no input files are read.
- Outputs: PNG slices named like `hilbert8-001.png` in the output directory,
  sliced along the y axis, and an optional LDraw `.ldr` brick model.

## Known gaps

- [ ] No `--dry-run` flag exists; add one if a preview mode is wanted.
