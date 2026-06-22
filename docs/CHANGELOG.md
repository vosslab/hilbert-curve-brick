# Changelog

## 2026-06-21

### Behavior or Interface Changes
- Trim the CLI to five option concepts (`--dimension`, `--target-size`, `--output-dir`, `--ldr-output`, grid toggle). Move `scale-y`, `axis`, `invert`, `normalize`, `slice-start`, `slice-end`, `prefix`, and the LDraw color/threshold/scale flags to named constants in `hilbert_curve_brick/cli.py` preserving prior defaults. Remove `write-pngs`/`no-pngs`; PNG slices are now always written.
- State the power-of-two requirement in `--dimension` help and name the offending value in the validation error.

### Fixes and Maintenance
- Fix the grid so it works as a placement guide. Use grid_mode block replication in `scale_volume` so each base voxel maps to exactly `scale` pixels, set the grid step to `scale * 2`, and offset the first line by `scale // 2`. Each black square now sits centered in one grid cell with empty cells clearly empty, at every power-of-two dimension. Previously the grid drifted onto the squares past the image midpoint.
- Empty `hilbert_curve_brick/__init__.py` and import submodules directly in the entrypoint, replacing the lazy `__getattr__` loader.
- Annotate `pytest_addoption` and `ascii_fix_enabled` fixture parameters in `tests/conftest.py`.

### Removals and Deprecations
- Remove unused vendored `leginon/mrc.py` (imported nowhere; depended on absent `pyami.*` modules).

### Developer Tests and Notes
- Add `tests/test_grid_alignment.py` (grid lines never cut squares, each square maps to one cell, consistent spacing via exact block replication) and `tests/test_cli_validation.py` (power-of-two validation).

## 2025-12-23
- Add `hilbert-curve-brick.py` Python 3 generator with CLI and comments.
- Trim `leginon/imagefile.py` to a minimal PNG writer and add package init.
- Add `numpy`, `pillow`, `pyflakes`, and `scipy` to `pip_requirements.txt`.
- Expand `README.md` with usage and output details.
- Add `tests/run_pyflakes.sh` and `tests/smoke_test.sh`.
- Update legacy scripts to Python 3 print syntax for pyflakes.
- Split helpers into `hilbert_curve_brick/` modules and add LDraw output support.
- Import `hilbert_curve_brick` as `hcb` in the entrypoint.
- Exclude `legacy/` from pyflakes and lazy-load package submodules.
