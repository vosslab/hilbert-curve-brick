# Plan: Rainbow color along the Hilbert curve

## Context

The generator visits voxels in curve order through `int_to_hilbert(index, 3)`
(`hilbert_curve_brick/curve.py`), then `build_hilbert_volume`
(`hilbert_curve_brick/volume.py:19`) writes a flat `1.0` at every occupied
voxel, which drops the order. The same float array also carries the grid (`0.5`)
and the LDraw threshold (`>= 0.5`), mixing three meanings.

The user wants the curve colored like a rainbow in 16 equal steps along its
length (blue at the curve start through red at the curve end, matching the
reference image), for both the PNG slices (the primary target) and the LDraw
model (a secondary target that keeps working).

This problem is integer-based. The `float32` volume is historical: it traces to
the user's old MRC export system and feeds `leginon.imagefile.arrayToPng`, whose
heritage is EM-microscopy grayscale images (MRC float data, normalized to
0-255). The `0.0 / 0.5 / 1.0` values are grayscale
display values stored in the data array, not a continuous quantity. The model
data here are all discrete: empty vs occupied, grid state, integer curve index,
integer band number, and `uint8` RGB. This plan treats the float values as
legacy display encoding and rebuilds the model as integers, converting to
grayscale or RGB only at the slice-writing step.

Locked decisions:

- Color is opt-in through a CLI flag; the default stays mono (black and white).
- Color uses 16 discrete bands (hard edges).
- The 16 band colors live as human-editable RGB hex in a YAML file that ships
  with jet-like defaults for the user to tune later.
- The model becomes a single integer volume: `0` empty, `index + 1` (curve
  step) at occupied and connector voxels. A connector voxel takes the earlier
  curve point's index, so it colors with the segment that enters it.
- The grid becomes a render-time overlay (a separate mask), kept out of the
  model volume.
- Mono output stays visually equivalent (same black / gray / white result),
  rendered from the integer volume; exact byte matching is not a goal.
- The LDraw brick merger keeps its current greedy behavior; each merged brick
  colors by its anchor-cell band. A brick that spans two bands shows the anchor
  band (a minor seam the user accepts).
- One shared YAML hex palette drives both PNG (RGB) and LDraw (direct color
  `0x2RRGGBB`); the smoke check reads the generated `.ldr` lines to confirm the
  color codes.

## Objectives

- Replace the float occupancy volume with one integer model volume and move
  grayscale and RGB encoding to the slice-writing step.
- Render PNG slices (primary) with the curve in 16 discrete rainbow bands by
  curve position, on a white background with a gray grid, in color mode.
- Render the LDraw model (secondary) with each brick colored by its
  curve-position band, while keeping mono LDraw output working.
- Load the 16 band colors from one human-editable YAML hex file that both
  outputs share, shipping jet-like defaults.
- Keep mono PNG and LDraw output visually equivalent to today.

## Design philosophy

Model the data as integers and convert to display values only when writing a
slice, because the problem is categorical (empty, grid, occupied) plus an
integer curve index, and the existing `float32` array conflates model data with
grayscale display encoding. This follows "fix the design, not the symptom": the
rejected alternative bolts a second color array onto the float volume, which is
smaller today but deepens the historical float design and keeps the `0.5` grid
sentinel entangled with the LDraw threshold. Mono stays visually equivalent
rather than byte-identical, because chasing exact bytes would force the new
integer render path to reproduce the old normalize-and-invert math for no user
benefit.

## Scope

- Add `hilbert_curve_brick/color.py`: load and validate the YAML hex palette,
  map a curve index to a 16-band color (RGB tuple and LDraw direct-color code).
- Add `hilbert_curve_brick/rainbow_palette.yaml` with 16 editable hex entries
  and jet-like defaults, packaged so an installed copy loads it.
- Rework `volume.py` to a single integer model volume (`build_curve_volume`), a
  grid mask builder, and a display step (`slice_to_grayscale`, `slice_to_rgb`)
  used by `write_slices`.
- Rework `ldraw.py` to read occupancy and band from the integer volume.
- Add the `-c/--color` and `-C/--mono` CLI toggle and wire the color path in the
  entrypoint.
- Update tests affected by the integer model and add new tests.

## Non-goals

- Limit this round to 16 discrete bands (smooth gradients stay out).
- Keep `N_BANDS = 16` and the YAML path as fixed constants (a band-count flag,
  palette-path flag, and colormap-selection flag stay out).
- Keep the greedy LDraw merger as-is; band-boundary-aware merging stays out.
- Pursue byte-identical mono output (visually equivalent is the bar).

## Current state summary

- `build_hilbert_volume(dimension)` returns a float32 volume with `1.0` at curve
  and connector voxels (`volume.py:19-42`).
- `scale_volume(volume, scale, scale_y)` uses
  `scipy.ndimage.zoom(order=0, grid_mode=True)` block replication, which
  preserves integer labels exactly (`volume.py:67-85`).
- `apply_grid_overlay` writes `0.5` planes into the volume (`volume.py:89-114`).
- `write_slices` inverts, then writes grayscale PNGs through
  `leginon.imagefile.arrayToPng` with normalize (`volume.py:150-181`).
- `leginon.imagefile._array_to_image` builds a grayscale image from `(h, w)` and
  an RGB image from `(h, w, 3)` uint8 (`leginon/imagefile.py:51-60`), so both
  display paths reuse the existing writer with `normalize=False`.
- `ldraw.volume_to_bricks(volume, threshold)` thresholds at `>= 0.5`;
  `write_ldraw` applies one `color` to every brick (`ldraw.py:45-128`);
  `_make_brick` builds the placement dict (`ldraw.py:238-282`).
- CLI constants live in `hilbert_curve_brick/cli.py` (`LDR_COLOR = 15`,
  `LDR_THRESHOLD = 0.5`, `INVERT`, `NORMALIZE`, ...); the repo argparse style
  pairs on/off flags with `set_defaults` (`docs/PYTHON_STYLE.md` argparse rule).
- `pyyaml` is a declared dependency; `importlib.resources` is stdlib.
- Existing tests `tests/test_grid_alignment.py` and `tests/test_cli_validation.py`
  encode current volume and grid behavior and update with the integer model.

## Architecture boundaries and ownership

### Mapping (milestones / workstreams -> components / patches)

| Milestone / Workstream | Component | Expected patches |
| --- | --- | --- |
| M1 / WS-A palette | `hilbert_curve_brick/color.py`, `hilbert_curve_brick/rainbow_palette.yaml`, packaging include | 1 |
| M1 / WS-B integer model | `hilbert_curve_brick/volume.py` (model: build, grid mask, scale) | 1 |
| M1 / WS-E0 CLI flag | `hilbert_curve_brick/cli.py` | 1 |
| M2 / WS-C PNG render (primary) | `hilbert_curve_brick/volume.py` (display: slices + write) | 1 |
| M2 / WS-D LDraw color (secondary) | `hilbert_curve_brick/ldraw.py` | 1 |
| M3 / WS-E1 wiring + docs | `hilbert-curve-brick.py`, docs | 1 |
| each wave | `docs/CHANGELOG.md` (maintainer, post-wave) | 1 per wave |

Durable component terms: `color` module, `volume` module (model layer and
display layer), `ldraw` module, `cli` module, entrypoint script.

### Code layering

Organize the code around four clear layers so model logic and rendering stay
separate:

- Integer model construction (`volume.py`, model section): `build_curve_volume`,
  `build_grid_mask`, `grid_params`, `scale_volume`, `compute_scale`. No display
  values here.
- Render-time grid and display conversion (`volume.py`, rendering section):
  `iter_slices`, `slice_to_grayscale`, `slice_to_rgb`, `write_slices`. Display
  values (grayscale, RGB) are produced here, never stored in the model.
- Palette and color mapping (`color.py`): YAML load, `index_to_band`,
  `rgb_to_ldraw_direct`.
- Output writing: `leginon.imagefile.arrayToPng` (PNG) and `ldraw.write_ldraw`
  (LDraw).

`volume.py` carries an equal-sign banner comment marking where the model layer
ends and the rendering layer begins, so a future maintainer sees the boundary.
The entrypoint stays orchestration only: it computes the scale, builds and
scales the model, asks the model layer for grid parameters, then calls the
rendering and output layers. Grid `step`/`offset` math moves out of the
entrypoint into the model layer's `grid_params`.

### Parallel dispatch and concurrency

Each work package edits a distinct file within a wave, so concurrent doers avoid
collisions. The waves shorten wall time:

- Wave 1 (3 doers in parallel): WP-A1 (`color.py` + YAML), WP-B1 (`volume.py`
  model layer), WP-E0 (`cli.py` flag). No dependencies among them.
- Wave 2 (2 doers in parallel): WP-C1 (`volume.py` display layer, primary PNG)
  and WP-D1 (`ldraw.py`, secondary). Both consume the Wave 1 contracts and edit
  different files. WP-C1 edits `volume.py` after WP-B1 merges, so the two
  `volume.py` packages stay sequential.
- Wave 3 (1 doer): WP-E1 entrypoint wiring + docs, after WP-C1 and WP-D1.

The agreed function signatures in each workstream's `Provides` let Wave 2 build
against the Wave 1 contracts without re-reading prose. A maintainer appends the
`docs/CHANGELOG.md` entries once per wave (not per parallel patch) so the shared
changelog avoids concurrent writes.

## Milestone plan

| M | Title | Summary | Goal |
| --- | --- | --- | --- |
| M1 | Foundations | Palette + packaged YAML, integer model volume, CLI flag | Provide the color source, the integer position source, and the opt-in flag |
| M2 | Rendering | PNG display layer (primary) and LDraw color (secondary) | Convert the integer volume to grayscale or 16-band RGB, and to colored bricks |
| M3 | Integration | Entrypoint wiring + docs | The user opts into color end to end while mono stays the default |

### Milestone: M1 Foundations

- Depends on: none
- Workstreams: WS-A (palette), WS-B (integer model), WS-E0 (CLI flag)
- Entry criteria: current tests pass.
- Exit criteria: `color.load_palette()` returns 16 RGB tuples through a
  package-resource lookup; `color.index_to_band` follows
  `band = min(n_bands - 1, index * n_bands // total)` so index 0 maps to band 0
  and `total - 1` maps to band 15; malformed-palette inputs raise a clear error;
  `build_curve_volume` returns an int volume (`0` empty, `index + 1` at curve
  and connector voxels); `-c/--color` and `-C/--mono` set `args.color` with a
  mono default; new and updated unit tests pass; `pytest tests/` and the
  pyflakes gate pass; the maintainer records the wave in `docs/CHANGELOG.md`.
- Parallel-plan ready: yes (WS-A, WS-B, WS-E0 edit different files; up to 3
  doers).

### Milestone: M2 Rendering

- Depends on: M1 (WS-C and WS-D consume the `color` API and the integer volume)
- Workstreams: WS-C (PNG display, primary), WS-D (LDraw color, secondary)
- Entry criteria: M1 exit criteria met.
- Exit criteria: `slice_to_grayscale` returns `(h, w)` uint8 (white background,
  gray grid, black curve) visually equivalent to today; `slice_to_rgb` returns
  `(h, w, 3)` uint8 (white background, gray grid, banded curve); color-mode
  `write_slices` requires palette and total, raising a clear error when either
  is missing, and calls `arrayToPng(..., normalize=False)`; `volume_to_bricks`
  reads occupancy and band from the integer volume and `write_ldraw` emits
  direct colors in color mode; the curve-start cell is blue and the curve-end
  cell is red in both outputs; new tests pass; gates pass; the maintainer
  records the wave in `docs/CHANGELOG.md`.
- Parallel-plan ready: yes (WS-C edits the `volume.py` display layer, WS-D edits
  `ldraw.py`; the files stay disjoint).

### Milestone: M3 Integration

- Depends on: M2 (the entrypoint wires the rendering APIs)
- Workstreams: WS-E1 (wiring + docs)
- Entry criteria: M2 exit criteria met.
- Exit criteria: the entrypoint builds and scales the integer volume, builds the
  grid mask for the PNG path, and routes palette plus volume into the primary
  PNG path and the secondary LDraw path in color mode; a mono run reads visually
  equivalent to the pre-change output (compared category masks, not bytes); the
  end-to-end color smoke run produces colored PNGs and a colored `.ldr`; gates
  pass; the patch updates `docs/USAGE.md` and `README.md`; the maintainer
  records the wave in `docs/CHANGELOG.md`.
- Parallel-plan ready: no (one integration lane depending on all prior
  workstreams).

## Workstream breakdown

### Workstream: WS-A palette

- Owner: coder
- Needs: `pyyaml` (declared), `importlib.resources` (stdlib).
- Provides: `color.load_palette() -> list[tuple]` (16 RGB int triples loaded as
  a package resource), `color.index_to_band(index: int, total: int, n_bands:
  int) -> int`, `color.rgb_to_ldraw_direct(rgb: tuple) -> str` (returns
  `0x2RRGGBB`), `color.N_BANDS`, and the packaged `rainbow_palette.yaml`.

### Workstream: WS-B integer model

- Owner: coder
- Needs: `curve.int_to_hilbert`.
- Provides: `volume.build_curve_volume(dimension: int) -> numpy.ndarray` (int32:
  `0` empty, `index + 1` at curve voxels, the earlier point's `index + 1` at
  connector voxels); `volume.build_grid_mask(shape: tuple, step: int, offset:
  int) -> numpy.ndarray` (bool); `volume.grid_params(scale: int) -> tuple`
  returning `(step, offset)` (moved out of the entrypoint); `scale_volume`
  confirmed to preserve integer labels. These live under a `MODEL LAYER` banner
  comment in `volume.py`.

### Workstream: WS-C PNG render (primary)

- Owner: coder
- Needs: WS-A palette API, WS-B integer volume and grid mask.
- Provides: `volume.slice_to_grayscale(label_slice, grid_slice) ->
  numpy.ndarray`, `volume.slice_to_rgb(label_slice, grid_slice, total, palette,
  n_bands) -> numpy.ndarray`, and a rewritten `write_slices` that takes the
  integer volume, optional grid mask, and color settings. These live under a
  `RENDERING LAYER` banner comment in `volume.py`, below the model section.

### Workstream: WS-D LDraw color (secondary)

- Owner: coder
- Needs: WS-A palette API, WS-B integer volume.
- Provides: `volume_to_bricks(volume)` reading occupancy as `volume > 0` and
  recording each brick's anchor label (the integer volume already carries the
  curve index, so no separate index array is passed); `write_ldraw(bricks,
  output_path, color, title, palette=None, total=None, n_bands=16)` emitting
  per-brick direct colors from the anchor label when `palette` is given, and the
  single `color` otherwise.

### Workstream: WS-E0 CLI flag

- Owner: coder
- Needs: nothing (independent of rendering).
- Provides: `-c/--color` and `-C/--mono` toggle, `N_BANDS` constant in
  `cli.py`; removes the now-unused `LDR_THRESHOLD` constant.

### Workstream: WS-E1 wiring + docs

- Owner: coder
- Needs: WS-C and WS-D rendering APIs, WS-E0 flag.
- Provides: entrypoint color path, mono visual-equivalence check, `docs/USAGE.md`
  and `README.md` color-flag notes.

## Work packages

### Work package: WP-A1 palette module and packaged YAML

- Owner: coder
- Touch points: create `hilbert_curve_brick/color.py`,
  `hilbert_curve_brick/rainbow_palette.yaml`; add the YAML to packaging includes
  (`pyproject.toml` package-data and `MANIFEST.in` if present); create
  `tests/test_color.py`.
- Depends on: none
- Acceptance criteria: the YAML ships 16 explicit hex entries (jet-like, ordered
  blue to red) as literal values; runtime code reads those literals.
  `load_palette()` reads the file through `importlib.resources` so an installed
  copy resolves, returning 16 `(r, g, b)` int triples in 0-255.
  `index_to_band` implements `band = min(n_bands - 1, index * n_bands //
  total)`; `index_to_band(0, total, 16) == 0`; `index_to_band(total - 1, total,
  16) == 15`; band stays monotonic non-decreasing; `total <= 0` raises a clear
  `ValueError` rather than dividing by zero. `rgb_to_ldraw_direct((255,
  0, 0)) == "0x2FF0000"`. Band 0 reads bluer than band 15 and band 15 redder
  than band 0 (behavioral). Malformed palettes raise a clear `ValueError`:
  fewer than 16 entries, a non-hex string, and a channel outside 0-255 each
  raise with a message naming the offending entry. A comment states the band
  formula and why `min` clamps the final boundary.
- Verification commands: `source source_me.sh && pytest tests/test_color.py`;
  `source source_me.sh && pytest tests/test_pyflakes_code_lint.py`.
- Obvious follow-ons: confirm the installed-package resource test passes; hand
  the changelog bullet to the maintainer for the Wave 1 entry.

### Work package: WP-B1 integer model volume

- Owner: coder
- Touch points: capture the mono baseline first (run the current entrypoint
  into the scratch directory `/tmp/hcb_baseline/` before editing; this is
  throwaway scratch, never committed); modify
  `hilbert_curve_brick/volume.py` (replace `build_hilbert_volume` with
  `build_curve_volume` returning the integer model, add `build_grid_mask` and
  `grid_params`, retire `apply_grid_overlay`'s `0.5` write, add the `MODEL LAYER`
  banner comment); rename all `build_hilbert_volume`
  call sites to `build_curve_volume` in the same patch (full rename, no
  compatibility wrapper); update `tests/test_grid_alignment.py` to assert grid
  placement through the grid mask; create `tests/test_index_volume.py`.
- Depends on: none
- Acceptance criteria: the mono baseline is captured before the refactor so
  WP-E1 can compare against it. `build_curve_volume(d)` returns int32 with `0`
  empty and `index + 1` at occupied and connector voxels; the occupied mask
  matches the prior float volume's non-zero mask for a small `d`. Curve-point
  indices strictly increase along the curve; the full occupied path including
  connectors stays non-decreasing (connectors inherit the earlier point's
  index, so the test asserts strict increase only across actual curve points).
  `build_grid_mask` marks lines at `offset + k * step` on the two in-plane axes.
  `scale_volume` returns the same integer labels block-replicated. Comments
  explain the integer label meaning (`0` empty, `index + 1` occupied), the
  connector inheritance rule, and the grid mask offset/step.
- Verification commands: `source source_me.sh && pytest
  tests/test_index_volume.py tests/test_grid_alignment.py`; `source
  source_me.sh && pytest tests/`.
- Obvious follow-ons: hand the changelog bullet to the maintainer for the
  Wave 1 entry.

### Work package: WP-E0 CLI flag

- Owner: coder
- Touch points: modify `hilbert_curve_brick/cli.py` (`-c/--color` with
  `action='store_true'`, `-C/--mono` with `action='store_false'`,
  `set_defaults(color=False)`, `N_BANDS`; remove `LDR_THRESHOLD`); create
  `tests/test_cli_color_flag.py`.
- Depends on: none
- Acceptance criteria: `parse_args(['-d', '8', '-c'])` yields `args.color is
  True`; `parse_args(['-d', '8', '-C'])` yields `args.color is False`; the
  default yields `False`. The paired flags follow the repo argparse on/off
  convention.
- Verification commands: `source source_me.sh && pytest
  tests/test_cli_color_flag.py`; `source source_me.sh && pytest
  tests/test_pyflakes_code_lint.py`.
- Obvious follow-ons: hand the changelog bullet to the maintainer for the
  Wave 1 entry.

### Work package: WP-C1 PNG display layer (primary)

- Owner: coder
- Touch points: modify `hilbert_curve_brick/volume.py` (add the `RENDERING
  LAYER` banner comment, add `slice_to_grayscale` and `slice_to_rgb`, rewrite
  `write_slices` to take the integer volume, optional grid mask, and color
  settings, and call `arrayToPng(..., normalize=False)`); create
  `tests/test_slice_render.py`.
- Depends on: WP-A1, WP-B1
- Acceptance criteria: `slice_to_grayscale` returns `(h, w)` uint8 with empty ->
  255 (white), occupied -> 0 (black), grid -> the gray constant, visually
  equivalent to current mono. `slice_to_rgb` returns `(h, w, 3)` uint8 with
  empty -> white, grid -> gray, occupied -> `palette[index_to_band(label - 1,
  total, 16)]`. Color-mode `write_slices` requires palette and total and raises
  a clear `ValueError` when either is missing. The slice holding curve index 0
  shows a blue cell and the slice holding the last index shows a red cell
  (behavioral). A comment explains that display values are produced here, not
  stored in the model.
- Verification commands: `source source_me.sh && pytest
  tests/test_slice_render.py`; `source source_me.sh && pytest tests/`.
- Obvious follow-ons: hand the changelog bullet to the maintainer for the
  Wave 2 entry.

### Work package: WP-D1 LDraw color (secondary)

- Owner: coder
- Touch points: modify `hilbert_curve_brick/ldraw.py` (`volume_to_bricks` reads
  occupancy as `volume > 0` and records each brick's anchor label, `_make_brick`
  stores the anchor label, `write_ldraw` and `_format_brick_line` emit per-brick
  direct color when a palette is given); create `tests/test_ldraw_color.py`.
- Depends on: WP-A1, WP-B1
- Acceptance criteria: with a palette, a brick anchored at a known curve cell
  carries the direct color `0x2RRGGBB` for that cell's band (test builds a small
  volume and checks the brick anchored at the first curve cell is a blue-band
  code and the brick at the last curve cell is a red-band code, rather than
  relying on file order). With no palette, `write_ldraw` keeps applying the
  single `color`. Geometry equivalence: inside the WP-D1 test, build a small
  integer volume and a matching float occupancy (`1.0` at the same voxels),
  then assert `volume_to_bricks` on the integer volume yields the same brick
  coordinate set as the old `>= 0.5` occupancy path over that float volume. A
  comment explains the direct-color encoding and the anchor-band choice for
  merged bricks.
- Verification commands: `source source_me.sh && pytest
  tests/test_ldraw_color.py`; `source source_me.sh && pytest tests/`.
- Obvious follow-ons: note the merged-brick band-seam caveat for the maintainer
  changelog bullet (Wave 2 entry).

### Work package: WP-E1 entrypoint wiring and docs

- Owner: coder
- Touch points: modify `hilbert-curve-brick.py` to stay orchestration only
  (compute scale, build and scale the integer volume, ask `volume.grid_params`
  for `(step, offset)` and `build_grid_mask` for the PNG path, route palette plus
  volume into the primary PNG path and the secondary LDraw path in color mode);
  update `docs/USAGE.md` and `README.md`.
- Depends on: WP-C1, WP-D1, WP-E0
- Acceptance criteria: in color mode the entrypoint scales the integer volume
  with the same `scale`/`SCALE_Y` factors and routes it to both outputs. The
  mono visual-equivalence check compares the new mono PNGs against the
  `/tmp/hcb_baseline/` directory captured in WP-B1 (before the refactor) using a
  concrete helper: load each before/after PNG, classify every pixel into white,
  gray, or black by nearest of the three display values, and assert the white,
  gray, and black masks match per slice, plus equal image dimensions and slice
  count. The LDraw branch produces a valid `.ldr` in both mono and color mode.
- Verification commands: `source source_me.sh && python3
  hilbert-curve-brick.py -d 8 -c -o output_smoke -l output_smoke/hilbert8.ldr`;
  `source source_me.sh && python3 hilbert-curve-brick.py -d 8 -o output_smoke`;
  `source source_me.sh && pytest tests/`.
- Obvious follow-ons: hand the changelog bullet to the maintainer for the
  Wave 3 entry.

## Acceptance criteria and gates

- Per-patch gate: `source source_me.sh && pytest tests/` passes; the pyflakes
  gate `pytest tests/test_pyflakes_code_lint.py` passes; the ASCII compliance
  and typing gates pass.
- Integration gate: the end-to-end color smoke run (`-d 8 -c` with `-l`) writes
  RGB PNGs and a `.ldr` whose brick color codes sweep blue to red along the
  curve.
- Manual review gate: open several colored PNG slices (white background, gray
  grid, mixed-color curve squares) and read the `.ldr` lines (color codes begin
  with `0x2`; the bricks at the known first and last curve cells differ blue to
  red). Confirm a mono run (`-d 8`) reads visually equivalent to the pre-change
  output via the category-mask comparison.
- Documentation gate: the maintainer records one `docs/CHANGELOG.md` entry per
  wave, gathering the doer-supplied bullets.

## Test and verification strategy

- Unit tests follow `docs/PYTEST_STYLE.md`: assert behavioral properties over
  exact tunable values. Examples: the band formula at boundaries (0 -> 0,
  `total - 1` -> 15), monotonic band, palette length 16, integer-volume occupied
  mask, the three display cell categories for grayscale and RGB, LDraw
  direct-color format, and hue ordering (band 0 bluer than band 15) so a later
  palette edit keeps the tests valid.
- Palette robustness tests cover the values the user will edit: fewer than 16
  entries, a non-hex string, and a channel outside 0-255 each raise a clear
  error.
- Package-resource test confirms `load_palette()` resolves the YAML through
  `importlib.resources`, so an installed copy loads the file.
- Connector test asserts strict increase across actual curve points and
  non-decreasing across the full occupied path including connectors.
- LDraw color test builds a small volume and checks the bricks anchored at the
  known first and last curve cells, avoiding reliance on file order.
- End-to-end color rendering, the blue-start/red-end color-order check, and the
  mono visual-equivalence comparison (category masks in `tmp_path/before` vs
  `tmp_path/after`) live as a manual smoke run per `docs/E2E_TESTS.md`.
- Fast lane: every new pytest finishes well under one second and writes only
  under `tmp_path` when it writes at all.

## Migration and compatibility policy

- Additive rollout for users: color stays opt-in; mono stays the default.
- Internal change: the model volume moves from float to integer and the grid
  becomes a render overlay. Mono output stays visually equivalent.
- Backward compatibility: mono PNG and single-color LDraw output stay the
  default; `LDR_COLOR` still applies in mono mode. The `LDR_THRESHOLD` constant
  is retired because occupancy is now `volume > 0`.
- Legacy deletion criteria: remove the `0.5` grid sentinel and the float
  occupancy once the integer model lands and tests pass.
- Rollback strategy: revert the patch set; the YAML file stays inert in mono
  mode, so a revert needs no data or format unwind.

## Risk register

| Risk | Impact | Trigger | Owner | Mitigation |
| --- | --- | --- | --- | --- |
| Integer refactor shifts mono rendering | Mono PNGs look different | Display path diverges from old categories | coder | Category-mask comparison (before vs after) in WP-E1; visually equivalent bar |
| Existing tests assume float `1.0` / grid `0.5` | Test failures | `build_hilbert_volume` and grid behavior change | coder | WP-B1 updates `tests/test_grid_alignment.py` to the integer model and grid mask |
| Packaged YAML missing from an installed copy | `load_palette()` fails after install | Run from an installed package | coder | Load through `importlib.resources`; add packaging include; package-resource test |
| `scale_volume` alters integer labels | Wrong color after scaling | Non-nearest interpolation | coder | Keep `order=0, grid_mode=True`; assert labels preserved |
| Merged brick spans two bands | Minor color seam | Greedy merger covers cells from different bands | coder | Accept and document; brick colors by anchor band |
| Direct color `0x2RRGGBB` renders oddly in a tool | LDraw colors look off | Open `.ldr` in a strict tool | coder | Confirm codes by reading the `.ldr` lines |

## Rollout and release checklist

- [ ] M1 merged: palette + packaged YAML + integer model + CLI flag, tests pass.
- [ ] M2 merged: PNG display layer + LDraw color, color-order checks pass.
- [ ] M3 merged: entrypoint wiring + docs, mono visual-equivalence confirmed.
- [ ] End-to-end color smoke run reviewed (PNG slices and `.ldr` lines).
- [ ] `docs/CHANGELOG.md`, `docs/USAGE.md`, `README.md` updated.

## Documentation close-out requirements

- Active plan / progress tracker: this plan; mark each milestone done as merged.
- docs/CHANGELOG.md entry: one entry per wave, written by the maintainer from
  the doer-supplied bullets, covering the integer-model redesign, the opt-in
  flag, the packaged YAML palette location, the LDraw direct-color note, and the
  merged-brick band-seam caveat.
- Archive / closure notes: on completion, move this plan to `docs/archive/`
  using `git mv` per `docs/REPO_STYLE.md`.

## Patch plan and reporting format

Wave 1 (parallel): Patches 1, 2, 3. Wave 2 (parallel): Patches 4, 5. Wave 3:
Patch 6. The maintainer commits one changelog entry per wave after its patches
merge.

- Patch 1 (WP-A1): `color.py` + `rainbow_palette.yaml` + packaging include +
  `tests/test_color.py`.
- Patch 2 (WP-B1): integer model volume + grid mask + updated
  `tests/test_grid_alignment.py` + `tests/test_index_volume.py`.
- Patch 3 (WP-E0): `cli.py` flag + `tests/test_cli_color_flag.py`.
- Patch 4 (WP-C1, primary): PNG display layer + `tests/test_slice_render.py`.
- Patch 5 (WP-D1, secondary): LDraw color + `tests/test_ldraw_color.py`.
- Patch 6 (WP-E1): entrypoint wiring + `docs/USAGE.md` + `README.md`.
- Per wave: maintainer appends the `docs/CHANGELOG.md` entry.

## Resolved decisions

- The model becomes a single integer volume; floats were legacy grayscale
  display encoding from the old MRC export / leginon imagefile heritage, not
  model data.
- `build_hilbert_volume` is renamed to `build_curve_volume` with all call sites
  updated in the same patch (no compatibility wrapper).
- The mono baseline is captured in WP-B1 into `/tmp/hcb_baseline/` (scratch,
  never committed) before the refactor; WP-E1 compares against it with a
  white/gray/black category-mask helper.
- `index_to_band` raises a clear error on `total <= 0`.
- Mono output stays visually equivalent, not byte-identical.
- The grid becomes a render-time overlay (a mask), kept out of the model volume.
- Connector voxels take the earlier curve point's index; tests assert strict
  increase across curve points and non-decreasing across the full path.
- The band mapping is `band = min(n_bands - 1, index * n_bands // total)`.
- The LDraw merger keeps greedy behavior; bricks color by anchor-cell band.
- The palette ships at `hilbert_curve_brick/rainbow_palette.yaml`, loaded as a
  package resource, with the packaging include added in Patch 1; the YAML holds
  literal hex values that runtime code reads.
- The CLI uses paired `-c/--color` and `-C/--mono` flags per the repo argparse
  style, defaulting to mono; `LDR_THRESHOLD` is retired.
- The maintainer updates `docs/CHANGELOG.md` once per wave to avoid concurrent
  writes during parallel patches.
- The code organizes into four layers: integer model construction and
  render-time display conversion (two banner-commented sections in `volume.py`),
  palette/color mapping (`color.py`), and output writing (`leginon.imagefile`,
  `ldraw.write_ldraw`). The entrypoint stays orchestration only; grid
  `step`/`offset` math moves into `volume.grid_params`.
