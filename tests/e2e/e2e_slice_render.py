"""
E2E tests for PNG slice rendering: write_slices creates files on disk.
These tests write real PNG files to disk and verify they exist.
Run directly: source source_me.sh && python3 tests/e2e/e2e_slice_render.py
Exits 0 on success, non-zero on failure.
"""

# Standard Library
import os
import subprocess
import sys
import tempfile

# Add the repo root to sys.path so local modules resolve when running directly.
_repo_root = subprocess.check_output(
	['git', 'rev-parse', '--show-toplevel'], text=True
).strip()
if _repo_root not in sys.path:
	sys.path.insert(0, _repo_root)

# PIP3 modules
import numpy

# local repo modules
import hilbert_curve_brick.color
import hilbert_curve_brick.volume


#============================================
def test_write_slices_mono_writes_pngs(tmp_dir: str) -> None:
	"""
	write_slices in mono mode creates one PNG file per slice.
	"""
	vol = numpy.zeros((3, 3, 3), dtype=numpy.int32)
	vol[1, 1, 1] = 1
	out_dir = os.path.join(tmp_dir, "mono_slices")
	hilbert_curve_brick.volume.write_slices(
		vol, 'z', out_dir, 'slice', 0, 3,
		color=False
	)
	png_files = [f for f in os.listdir(out_dir) if f.endswith('.png')]
	assert len(png_files) == 3, (
		f"expected 3 PNG files in mono mode, got {len(png_files)}"
	)
	print("PASS: test_write_slices_mono_writes_pngs")


#============================================
def test_write_slices_color_writes_pngs(tmp_dir: str) -> None:
	"""
	write_slices in color mode creates one PNG file per slice.
	"""
	palette = hilbert_curve_brick.color.load_palette()
	vol = numpy.zeros((3, 3, 3), dtype=numpy.int32)
	vol[1, 1, 1] = 1
	out_dir = os.path.join(tmp_dir, "color_slices")
	hilbert_curve_brick.volume.write_slices(
		vol, 'z', out_dir, 'slice', 0, 3,
		color=True, grid_mask=None, palette=palette, total=27
	)
	png_files = [f for f in os.listdir(out_dir) if f.endswith('.png')]
	assert len(png_files) == 3, (
		f"expected 3 PNG files in color mode, got {len(png_files)}"
	)
	print("PASS: test_write_slices_color_writes_pngs")


#============================================
def main() -> None:
	"""Run all E2E slice render tests and exit 0 on success."""
	tmp_dir = tempfile.mkdtemp(prefix="e2e_slice_render_")
	try:
		test_write_slices_mono_writes_pngs(tmp_dir)
		test_write_slices_color_writes_pngs(tmp_dir)
	except AssertionError as e:
		print(f"FAIL: {e}", file=sys.stderr)
		raise SystemExit(1)
	print("All e2e_slice_render tests passed.")


if __name__ == '__main__':
	main()
