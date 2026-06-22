"""
E2E tests for LDraw color support: per-brick direct color, mono fallback.
These tests write real .ldr files to disk and read them back.
Run directly: source source_me.sh && python3 tests/e2e/e2e_ldraw_color.py
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
import hilbert_curve_brick.color as color
import hilbert_curve_brick.ldraw as ldraw
import hilbert_curve_brick.volume as volume


#============================================
def _small_int_volume() -> numpy.ndarray:
	"""
	Build a minimal integer volume: dimension=2 Hilbert curve.

	Returns an int32 volume with labels at curve voxels so tests do not
	depend on the full curve generator startup cost.
	"""
	return volume.build_curve_volume(2)


#============================================
def _find_brick_at_label(bricks: list, target_label: int) -> dict:
	"""Return the first brick whose anchor label equals target_label, or None."""
	for brick in bricks:
		if brick["label"] == target_label:
			return brick
	return None


#============================================
def test_rainbow_mode_first_cell_is_blue_band(tmp_dir: str) -> None:
	"""
	With a palette, the brick anchored at the first curve cell (label=1)
	must carry a blue-band direct color (band 0 is blue in the jet palette).
	"""
	int_vol = _small_int_volume()
	bricks = ldraw.volume_to_bricks(int_vol)
	palette = color.load_palette()
	# Use dimension**3 for total, not numpy.max, to match the curve definition.
	dimension = 2
	total = dimension ** 3

	# Write the LDraw file.
	out_path = os.path.join(tmp_dir, "test.ldr")
	ldraw.write_ldraw(bricks, out_path, color=15, title="test", palette=palette, total=total)

	# Band for label=1 (index=0) must be band 0 (blue).
	first_brick = _find_brick_at_label(bricks, 1)
	assert first_brick is not None, "no brick anchored at label 1 (first curve cell)"
	band = color.index_to_band(first_brick["label"] - 1, total, 16)
	# Band 0 corresponds to palette[0] which is blue-dominant.
	r0, g0, b0 = palette[0]
	assert b0 > r0, "palette band 0 should be blue-dominant"
	expected_color = color.rgb_to_ldraw_direct(palette[band])
	# Confirm the .ldr file contains that color for a line starting with "1 ".
	with open(out_path, "r", encoding="ascii") as fh:
		ldr_text = fh.read()
	assert expected_color in ldr_text, (
		f"expected direct color {expected_color} not found in .ldr output"
	)
	print("PASS: test_rainbow_mode_first_cell_is_blue_band")


#============================================
def test_rainbow_mode_last_cell_is_red_band(tmp_dir: str) -> None:
	"""
	With a palette, the brick anchored at the last curve cell (label=max)
	must carry a red-band direct color (band 15 is red in the jet palette).
	"""
	int_vol = _small_int_volume()
	bricks = ldraw.volume_to_bricks(int_vol)
	palette = color.load_palette()
	dimension = 2
	total = dimension ** 3

	out_path = os.path.join(tmp_dir, "test_last.ldr")
	ldraw.write_ldraw(bricks, out_path, color=15, title="test", palette=palette, total=total)

	# Find the brick with the highest label (last curve cell).
	last_label = max(b["label"] for b in bricks)
	last_brick = _find_brick_at_label(bricks, last_label)
	assert last_brick is not None, "no brick anchored at last curve cell label"

	band = color.index_to_band(last_brick["label"] - 1, total, 16)
	# Band 15 corresponds to palette[15] which is red-dominant.
	r15, g15, b15 = palette[15]
	assert r15 > b15, "palette band 15 should be red-dominant"
	expected_color = color.rgb_to_ldraw_direct(palette[band])
	with open(out_path, "r", encoding="ascii") as fh:
		ldr_text = fh.read()
	assert expected_color in ldr_text, (
		f"expected direct color {expected_color} not found in .ldr output"
	)
	print("PASS: test_rainbow_mode_last_cell_is_red_band")


#============================================
def test_rainbow_first_and_last_colors_differ(tmp_dir: str) -> None:
	"""
	The direct color at the first curve cell must differ from the last.

	This confirms blue-to-red sweep rather than a flat color.
	"""
	int_vol = _small_int_volume()
	bricks = ldraw.volume_to_bricks(int_vol)
	palette = color.load_palette()
	dimension = 2
	total = dimension ** 3

	first_brick = _find_brick_at_label(bricks, 1)
	last_label = max(b["label"] for b in bricks)
	last_brick = _find_brick_at_label(bricks, last_label)

	first_band = color.index_to_band(first_brick["label"] - 1, total, 16)
	last_band = color.index_to_band(last_brick["label"] - 1, total, 16)
	first_color = color.rgb_to_ldraw_direct(palette[first_band])
	last_color = color.rgb_to_ldraw_direct(palette[last_band])
	assert first_color != last_color, (
		"first and last curve cells must map to different direct colors"
	)
	print("PASS: test_rainbow_first_and_last_colors_differ")


#============================================
def test_mono_mode_uses_integer_color(tmp_dir: str) -> None:
	"""
	Without a palette, write_ldraw must apply the single integer color to
	every brick line.
	"""
	int_vol = _small_int_volume()
	bricks = ldraw.volume_to_bricks(int_vol)

	out_path = os.path.join(tmp_dir, "mono.ldr")
	ldraw.write_ldraw(bricks, out_path, color=15, title="mono_test")

	with open(out_path, "r", encoding="ascii") as fh:
		ldr_text = fh.read()

	# Every type-1 line must start with "1 15 " (the integer color).
	brick_lines = [ln for ln in ldr_text.splitlines() if ln.startswith("1 ")]
	assert len(brick_lines) > 0, "no brick lines written"
	for ln in brick_lines:
		assert ln.startswith("1 15 "), (
			f"expected mono color 15 but found: {ln}"
		)
	print("PASS: test_mono_mode_uses_integer_color")


#============================================
def test_mono_mode_no_direct_color_codes(tmp_dir: str) -> None:
	"""
	Without a palette, no direct-color codes (starting with 0x2) should appear.
	"""
	int_vol = _small_int_volume()
	bricks = ldraw.volume_to_bricks(int_vol)

	out_path = os.path.join(tmp_dir, "mono_nodirect.ldr")
	ldraw.write_ldraw(bricks, out_path, color=15, title="mono_nodirect")

	with open(out_path, "r", encoding="ascii") as fh:
		ldr_text = fh.read()

	assert "0x2" not in ldr_text, "direct-color codes must not appear in mono mode"
	print("PASS: test_mono_mode_no_direct_color_codes")


#============================================
def test_rainbow_mode_direct_color_format(tmp_dir: str) -> None:
	"""
	In rainbow mode every brick line must have a color token starting with
	'0x2' followed by exactly 6 uppercase hex digits.
	"""
	int_vol = _small_int_volume()
	bricks = ldraw.volume_to_bricks(int_vol)
	palette = color.load_palette()
	dimension = 2
	total = dimension ** 3

	out_path = os.path.join(tmp_dir, "rainbow.ldr")
	ldraw.write_ldraw(bricks, out_path, color=15, title="rainbow_fmt", palette=palette, total=total)

	with open(out_path, "r", encoding="ascii") as fh:
		ldr_text = fh.read()

	brick_lines = [ln for ln in ldr_text.splitlines() if ln.startswith("1 ")]
	assert len(brick_lines) > 0
	for ln in brick_lines:
		# LDraw type-1 line: "1 <color> <x> <y> <z> <rot...> <part>"
		tokens = ln.split()
		brick_color_token = tokens[1]
		assert brick_color_token.startswith("0x2"), (
			f"expected direct-color token starting with '0x2', got: {brick_color_token!r}"
		)
		# After '0x2' there must be exactly 6 hex digits.
		hex_digits = brick_color_token[3:]
		assert len(hex_digits) == 6, (
			f"direct-color token must have 6 hex digits after '0x2', got: {brick_color_token!r}"
		)
		assert all(c in "0123456789ABCDEFabcdef" for c in hex_digits), (
			f"non-hex character in direct-color token: {brick_color_token!r}"
		)
	print("PASS: test_rainbow_mode_direct_color_format")


#============================================
def main() -> None:
	"""Run all E2E LDraw color tests and exit 0 on success."""
	tmp_dir = tempfile.mkdtemp(prefix="e2e_ldraw_color_")
	try:
		test_rainbow_mode_first_cell_is_blue_band(tmp_dir)
		test_rainbow_mode_last_cell_is_red_band(tmp_dir)
		test_rainbow_first_and_last_colors_differ(tmp_dir)
		test_mono_mode_uses_integer_color(tmp_dir)
		test_mono_mode_no_direct_color_codes(tmp_dir)
		test_rainbow_mode_direct_color_format(tmp_dir)
	except AssertionError as e:
		print(f"FAIL: {e}", file=sys.stderr)
		raise SystemExit(1)
	print("All e2e_ldraw_color tests passed.")


if __name__ == '__main__':
	main()
