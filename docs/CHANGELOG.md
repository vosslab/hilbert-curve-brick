# Changelog

## 2026-06-22

### Additions and New Features
- Add opt-in 16-band rainbow color along the Hilbert curve for PNG slices (primary) and the LDraw model (secondary) via `-c`/`--color` (default mono, `-C`/`--mono`).
- Add `hilbert_curve_brick/color.py` with `load_palette` (via `importlib.resources`), `index_to_band`, `rgb_to_ldraw_direct`, and `N_BANDS=16`.
- Add `hilbert_curve_brick/rainbow_palette.yaml` with 16 human-editable jet-like hex entries (blue to red).
- Add `pyproject.toml` with package-data include so the YAML ships with an installed package; add `pyyaml` to `pip_requirements.txt`.
- Add render-layer helpers `slice_to_grayscale` and `slice_to_rgb` in `volume.py`.

### Behavior or Interface Changes
- Redesign the model volume from a float32 occupancy array (legacy MRC/grayscale display encoding) to a single int32 model volume: 0 for empty, index+1 at occupied and connector voxels; connectors inherit the earlier curve point's label.
- Move the grid from a 0.5 sentinel baked into the volume to a render-time boolean overlay mask (`build_grid_mask`); add `grid_params(scale)` returning (step, offset); the entrypoint is now orchestration only.
- Rewrite `write_slices` to take the integer volume, optional grid mask, and color settings; display values (grayscale or RGB uint8) are produced only at render time, dropping the legacy invert/normalize float path.
- `ldraw.volume_to_bricks(volume)` now reads occupancy as `volume > 0` (threshold argument removed); `write_ldraw` emits per-brick LDraw direct color `0x2RRGGBB` in color mode (merged bricks color by anchor-cell band) and the single integer color in mono mode.

### Fixes and Maintenance
- Audit cleanup: remove dead `cli.py` constants (`INVERT`, `NORMALIZE`, and the duplicate `N_BANDS`; `color.N_BANDS` is the single source of truth); derive the LDraw `total` from `dimension ** 3` like the PNG path and drop the entrypoint `numpy` import; fix optional-parameter annotations in `ldraw.write_ldraw` and parameterize `tuple` hints in `color.py`; scrub a planning-reference comment in `ldraw.py`; prune three fragile tests (a duplicate palette-resolution test, a self-testing validation test, and a `grid_params` formula-mirror test) and a redundant assertion; refresh `docs/OUTPUT_FORMATS.md`, `docs/FILE_STRUCTURE.md`, `docs/INSTALL.md`, `docs/TROUBLESHOOTING.md`, and `docs/CODE_ARCHITECTURE.md`.
- Consolidate `leginon/imagefile.py` PNG writer: rename the real function `arrayToPng` to `array_to_png` (snake_case) and delete the dead wrapper that called it; update the live call site in `hilbert_curve_brick/volume.py` (function call + 5 comment mentions) and the legacy call site in `legacy/lego_hilbert.py`.
- Fix `build_grid_mask` non-cubic defect in `hilbert_curve_brick/volume.py`: the single loop capped both axes at `min(shape[0], shape[2])`, truncating grid lines on the longer axis; replaced with two independent loops so axis-0 and axis-2 each walk to their own edge.
- Remove duplicate `pyflakes` entry from `pip_requirements.txt`; `pyflakes` is a dev/lint tool and is already declared in `pip_requirements-dev.txt`.

### Removals and Deprecations
- Remove the `LDR_THRESHOLD` CLI constant and the float 0.5 grid sentinel / `apply_grid_overlay` volume write.
- Rename `build_hilbert_volume` to `build_curve_volume` across all call sites; no compatibility wrapper retained.

### Decisions and Failures
- Mono output is held visually equivalent (white/gray/black category masks), not byte-identical; a one-time migration check confirmed 15/16 slices identical and corrected one legacy bug where empty-border-slice grid lines rendered black instead of gray.
- Connector voxels take the earlier curve point's index; band mapping is `min(n_bands-1, index * n_bands // total)`.

### Developer Tests and Notes
- Add `tests/test_color.py`, `tests/test_index_volume.py`, `tests/test_cli_color_flag.py`, `tests/test_ldraw_color.py`, `tests/test_slice_render.py`; update `tests/test_grid_alignment.py` for the integer model.
- Full test suite: 621 passing.
- Restore `test_load_palette_has_16_bands` in `tests/test_color.py`: asserts `len(palette) == 16` (16 is a locked design constant, not a tunable; 609 passed after cleanup batch).

## 2026-06-21

### Additions and New Features
- Add `docs/CODE_ARCHITECTURE.md` (module map and data flow) and `docs/FILE_STRUCTURE.md` (repository layout).
- Add `docs/INSTALL.md` (requirements, setup, verify step) and `docs/USAGE.md` (CLI flags and examples).
- Add `docs/TROUBLESHOOTING.md` (validation errors, missing deps, LDraw output) and `docs/OUTPUT_FORMATS.md` (PNG slice naming and LDraw line format).

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
- Rewrite `README.md`: longer About paragraph (246 chars, near the 250 limit), a Documentation section linking the new `docs/` set, and a corrected Testing section (`pytest tests/` and `tests/smoke_test.sh`, replacing the stale `tests/run_pyflakes.sh` reference).
- Correct `AGENTS.md` to reference `tests/smoke_test.sh` and the pytest lint gates instead of nonexistent pyflakes/mypy runner scripts.
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
