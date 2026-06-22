# hilbert_curve_brick

Generate 3D Hilbert curve PNG slices and optional LDraw brick models for LEGO-compatible builds. Pick any power-of-two dimension, scale to a target image size, and overlay a placement grid that centers each curve cell for hands-on brick assembly.

## Documentation

- [docs/INSTALL.md](docs/INSTALL.md): requirements and setup steps.
- [docs/USAGE.md](docs/USAGE.md): CLI flags and example commands.
- [docs/CODE_ARCHITECTURE.md](docs/CODE_ARCHITECTURE.md): module map and data flow.
- [docs/FILE_STRUCTURE.md](docs/FILE_STRUCTURE.md): repository layout.
- [docs/CHANGELOG.md](docs/CHANGELOG.md): dated record of changes.

## Quick start

- Install dependencies: `pip3 install -r pip_requirements.txt`
- Run: `python3 hilbert-curve-brick.py -d 8 -o output`

## Output

- PNG slices saved to the output directory, for example `hilbert8-001.png`.
- Slices are taken along the y axis.
- Grid overlays are enabled by default; disable them with `--no-grid`.
- Mono output (default) renders the curve black on a white background.
- Color output (`--color`) renders the curve in 16 rainbow bands from curve start
  to end; band colors are editable in
  [hilbert_curve_brick/rainbow_palette.yaml](hilbert_curve_brick/rainbow_palette.yaml).
- LDraw output is optional: `--ldr-output output/hilbert.ldr`.
- LDraw uses 2x2, 2x4, 2x6, and 2x2x3 bricks (parts 3003, 3001, 2456, 30145).
- In color mode LDraw bricks use direct-color codes (`0x2RRGGBB`) matching the
  PNG palette.

## Testing

- Run the test suite: `pytest tests/`
- Run the smoke test: `tests/smoke_test.sh`

## Notes

- Use power-of-two dimensions (2, 4, 8, 16) for a clean Hilbert path.
