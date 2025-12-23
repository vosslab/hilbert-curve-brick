# hilbert_curve_brick

Generate 3D Hilbert curve slices for LEGO-compatible brick builds.

## Quick start
- Install dependencies: `pip3 install -r pip_requirements.txt`
- Run: `python3 hilbert-curve-brick.py -d 8 -o output`

## Script
- `hilbert-curve-brick.py`: builds a 3D Hilbert curve volume and writes PNG slices.

## Output
- PNG slices saved to the output directory, for example `hilbert8-001.png`.
- Grid overlays are enabled by default; disable them with `--no-grid`.
- Change the slicing axis with `--axis x`, `--axis y`, or `--axis z`.

## Testing
- Run pyflakes: `tests/run_pyflakes.sh`
- Run smoke test: `tests/smoke_test.sh`

## Notes
- Use power-of-two dimensions (2, 4, 8, 16) for a clean Hilbert path.
