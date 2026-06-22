# File structure

This document maps the repository layout so contributors can find code, tests,
docs, and generated output quickly.

## Top-level layout

```text
hilbert-curve-brick/
+- hilbert-curve-brick.py   entry point: build volume, write PNGs and LDraw
+- hilbert_curve_brick/     core package (CLI, curve math, volume, LDraw)
+- leginon/                 minimal PNG writer helper
+- legacy/                  old standalone scripts, kept for reference
+- devel/                   maintenance scripts (version bump, changelog tools)
+- tests/                   pytest suite, lint checks, smoke test
+- docs/                    documentation and style guides
+- output/                  generated PNG slices (git ignored)
+- README.md                project overview and quick start
+- AGENTS.md                agent instructions (pointers into docs/)
+- pip_requirements.txt     runtime dependencies
+- pip_requirements-dev.txt developer dependencies
+- Brewfile                 Homebrew dependencies
+- source_me.sh             shell bootstrap for running Python
+- REPO_TYPE                repo type marker (python)
+- VERSION                  version string, synced with releases
`- LICENSE                  license text
```

## Key subtrees

- [hilbert_curve_brick/](../hilbert_curve_brick): the importable package.
  - [cli.py](../hilbert_curve_brick/cli.py): argparse and validation, run constants.
  - [curve.py](../hilbert_curve_brick/curve.py): Hilbert index/coordinate math.
  - [volume.py](../hilbert_curve_brick/volume.py): volume build, scale, grid, PNG slices.
  - [ldraw.py](../hilbert_curve_brick/ldraw.py): LDraw brick tiling and output.
- [tests/](../tests): fast pytest modules (`test_*.py`), repo-wide lint checks,
  shared [file_utils.py](../tests/file_utils.py), and
  [smoke_test.sh](../tests/smoke_test.sh).
- [devel/](../devel): changelog rotation/query/commit tools, version bump, and
  [DEVEL_README.md](../devel/DEVEL_README.md).
- [legacy/](../legacy): older `hilbert.py` and `lego_hilbert.py` scripts,
  excluded from lint and not part of the package.

## Generated artifacts

- `output/`: PNG slices and any `.ldr` files; git ignored.
- `__pycache__/` and `.pytest_cache/`: bytecode and pytest caches; not committed.
- `.DS_Store`: macOS metadata; git ignored.

## Documentation map

- [docs/](.): all reference docs and style guides.
  - [CODE_ARCHITECTURE.md](CODE_ARCHITECTURE.md): module map and data flow.
  - [CHANGELOG.md](CHANGELOG.md): dated record of changes.
  - Style guides: [PYTHON_STYLE.md](PYTHON_STYLE.md),
    [REPO_STYLE.md](REPO_STYLE.md), [MARKDOWN_STYLE.md](MARKDOWN_STYLE.md),
    [PYTEST_STYLE.md](PYTEST_STYLE.md), [E2E_TESTS.md](E2E_TESTS.md).
- Root docs: [README.md](../README.md), [AGENTS.md](../AGENTS.md),
  [LICENSE](../LICENSE).

## Where to add new work

- Core logic: add a module under [hilbert_curve_brick/](../hilbert_curve_brick).
- Tests: add `test_*.py` under [tests/](../tests); slow end-to-end checks go in
  `tests/e2e/`.
- Docs: add SCREAMING_SNAKE_CASE `.md` files under [docs/](.).
- Maintenance scripts: add to [devel/](../devel).
