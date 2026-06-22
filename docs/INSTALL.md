# Install

This repo is a command-line tool run from source. "Installed" means the
dependencies are present and [hilbert-curve-brick.py](../hilbert-curve-brick.py)
runs from the repo root.

## Requirements

- Python 3.12 (the pinned interpreter for this repo's tooling).
- Python packages from [pip_requirements.txt](../pip_requirements.txt): `numpy`,
  `pillow`, `pyflakes`, `scipy`.
- Homebrew `python@3.12` on macOS, per the [Brewfile](../Brewfile).

## Install steps

- Obtain the source (clone the repo).
- Install runtime dependencies: `pip3 install -r pip_requirements.txt`.
- Install developer dependencies for tests:
  `pip3 install -r pip_requirements-dev.txt`.
- On macOS, install the pinned interpreter with `brew bundle`.

## Verify install

- Run the help output to confirm the CLI loads:
  `python3 hilbert-curve-brick.py --help`.

## Known gaps

- [ ] Confirm supported platforms beyond macOS (Linux, Windows).
- [ ] Confirm whether a virtual environment is the expected workflow.
