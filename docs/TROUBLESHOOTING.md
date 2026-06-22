# Troubleshooting

Common failures when running [hilbert-curve-brick.py](../hilbert-curve-brick.py)
and how to resolve them. Each item below is tied to repo behavior.

## Dimension must be a power of two

- Symptom: `ValueError: dimension must be a power of two, got <n>`.
- Cause: `--dimension` was not a power of two.
- Fix: pass 2, 4, 8, 16, and so on.

## Target size must be at least 1

- Symptom: `ValueError: target-size must be at least 1, got <n>`.
- Cause: `--target-size` was zero or negative.
- Fix: pass a positive integer (default is 800).

## Missing dependencies

- Symptom: `ModuleNotFoundError` for `numpy`, `scipy`, or `PIL`.
- Cause: runtime dependencies are not installed.
- Fix: `pip3 install -r pip_requirements.txt`. See
  [docs/INSTALL.md](INSTALL.md).

## No LDraw file written

- Symptom: only PNG slices appear, no `.ldr` file.
- Cause: `--ldr-output` defaults to empty, so LDraw export is skipped.
- Fix: pass a path, for example `--ldr-output output/hilbert.ldr`.

## Known gaps

- [ ] Document behavior for very large dimensions (memory and runtime limits).
