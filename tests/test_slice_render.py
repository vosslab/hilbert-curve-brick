"""
Tests for the PNG rendering layer: slice_to_grayscale, slice_to_rgb, and
write_slices error paths.

Display values (grayscale and RGB uint8) are produced by the rendering
layer; the integer model stores only 0 (empty) and index+1 (occupied).

Tests that write real PNG files to disk live in
tests/e2e/e2e_slice_render.py and are run directly, not via pytest.
"""

# Standard Library
import os

# PIP3 modules
import numpy
import pytest

# local repo modules
import hilbert_curve_brick.color
import hilbert_curve_brick.volume


#============================================
def make_label_slice() -> tuple[numpy.ndarray, numpy.ndarray]:
	"""
	Build a minimal 3x3 label slice with one empty, one occupied, and a grid.

	Returns:
		tuple: (label_slice, grid_slice) both shape (3, 3).
	"""
	# label_slice: 0 = empty, >0 = occupied
	label = numpy.zeros((3, 3), dtype=numpy.int32)
	# Place one occupied voxel with label 1 at (0, 0).
	label[0, 0] = 1
	# Grid line along the last row.
	grid = numpy.zeros((3, 3), dtype=bool)
	grid[2, :] = True
	return label, grid


#============================================
def test_slice_to_grayscale_empty_is_white() -> None:
	"""
	Empty voxels (label == 0) map to 255 (white) in grayscale output.
	"""
	label, grid = make_label_slice()
	result = hilbert_curve_brick.volume.slice_to_grayscale(label, grid)
	# (1, 1) is empty and not on a grid plane.
	assert result[1, 1] == 255


#============================================
def test_slice_to_grayscale_occupied_is_black() -> None:
	"""
	Occupied voxels (label > 0) map to 0 (black) in grayscale output.
	"""
	label, grid = make_label_slice()
	result = hilbert_curve_brick.volume.slice_to_grayscale(label, grid)
	# (0, 0) has label 1 (occupied).
	assert result[0, 0] == 0


#============================================
def test_slice_to_grayscale_grid_is_gray() -> None:
	"""
	Grid pixels map to 128 (gray) in grayscale output, drawn over all cells.
	"""
	label, grid = make_label_slice()
	result = hilbert_curve_brick.volume.slice_to_grayscale(label, grid)
	# Row 2 is the grid row; all pixels there should be gray.
	assert numpy.all(result[2, :] == 128)


#============================================
def test_slice_to_grayscale_shape_and_dtype() -> None:
	"""
	slice_to_grayscale returns a (h, w) uint8 array.
	"""
	label, grid = make_label_slice()
	result = hilbert_curve_brick.volume.slice_to_grayscale(label, grid)
	assert result.shape == (3, 3)
	assert result.dtype == numpy.uint8


#============================================
def test_slice_to_grayscale_no_grid() -> None:
	"""
	Passing grid_slice=None leaves no gray pixels when no grid is present.
	"""
	label = numpy.zeros((3, 3), dtype=numpy.int32)
	result = hilbert_curve_brick.volume.slice_to_grayscale(label, None)
	# All empty, no grid: entire slice should be white.
	assert numpy.all(result == 255)


#============================================
def test_slice_to_rgb_empty_is_white() -> None:
	"""
	Empty voxels map to (255, 255, 255) white in RGB output.
	"""
	palette = hilbert_curve_brick.color.load_palette()
	label, grid = make_label_slice()
	result = hilbert_curve_brick.volume.slice_to_rgb(label, grid, total=64, palette=palette, n_bands=16)
	# (1, 1) is empty; should be white.
	assert tuple(result[1, 1]) == (255, 255, 255)


#============================================
def test_slice_to_rgb_grid_is_gray() -> None:
	"""
	Grid pixels map to (128, 128, 128) gray in RGB output.
	"""
	palette = hilbert_curve_brick.color.load_palette()
	label, grid = make_label_slice()
	result = hilbert_curve_brick.volume.slice_to_rgb(label, grid, total=64, palette=palette, n_bands=16)
	# Row 2 is the grid row.
	assert numpy.all(result[2, :, 0] == 128)
	assert numpy.all(result[2, :, 1] == 128)
	assert numpy.all(result[2, :, 2] == 128)


#============================================
def test_slice_to_rgb_occupied_uses_palette() -> None:
	"""
	Occupied voxels take the palette color for their curve band.
	"""
	palette = hilbert_curve_brick.color.load_palette()
	label, grid = make_label_slice()
	# label[0,0] = 1 -> curve index 0 -> band 0 (pure blue).
	result = hilbert_curve_brick.volume.slice_to_rgb(label, grid, total=64, palette=palette, n_bands=16)
	expected_band = hilbert_curve_brick.color.index_to_band(0, 64, 16)
	expected_rgb = palette[expected_band]
	assert tuple(result[0, 0]) == tuple(expected_rgb)


#============================================
def test_slice_to_rgb_shape_and_dtype() -> None:
	"""
	slice_to_rgb returns a (h, w, 3) uint8 array.
	"""
	palette = hilbert_curve_brick.color.load_palette()
	label, _ = make_label_slice()
	result = hilbert_curve_brick.volume.slice_to_rgb(label, None, total=64, palette=palette, n_bands=16)
	assert result.shape == (3, 3, 3)
	assert result.dtype == numpy.uint8


#============================================
def test_write_slices_color_missing_palette_raises(tmp_path: "os.PathLike[str]") -> None:
	"""
	write_slices raises ValueError when color=True and palette is not provided.
	"""
	volume = numpy.zeros((3, 3, 3), dtype=numpy.int32)
	with pytest.raises(ValueError, match="palette"):
		hilbert_curve_brick.volume.write_slices(
			volume, 'z', str(tmp_path), 'test', 0, 3,
			color=True, grid_mask=None, palette=None, total=27
		)


#============================================
def test_write_slices_color_missing_total_raises(tmp_path: "os.PathLike[str]") -> None:
	"""
	write_slices raises ValueError when color=True and total is not provided.
	"""
	palette = hilbert_curve_brick.color.load_palette()
	volume = numpy.zeros((3, 3, 3), dtype=numpy.int32)
	with pytest.raises(ValueError, match="total"):
		hilbert_curve_brick.volume.write_slices(
			volume, 'z', str(tmp_path), 'test', 0, 3,
			color=True, grid_mask=None, palette=palette, total=None
		)


#============================================
def test_color_index0_cell_is_bluer_than_red() -> None:
	"""
	The first curve index maps to band 0 which is bluer than red (b > r).

	This tests that the palette ordering (blue start, red end) is respected
	in the RGB rendering path.
	"""
	palette = hilbert_curve_brick.color.load_palette()
	# Build a 2x2x2 volume: dimension=2, total = 2**3 = 8.
	dimension = 2
	total = dimension ** 3
	volume = hilbert_curve_brick.volume.build_curve_volume(dimension)
	# Flatten all slices along z and find a slice containing curve label 1 (index 0).
	found_blue = False
	found_red = False
	last_label = total
	for _idx, label_slice in hilbert_curve_brick.volume.iter_slices(volume, 'z', 0, volume.shape[2]):
		if numpy.any(label_slice == 1):
			# Curve index 0: band 0 should be bluer than red (b > r).
			band = hilbert_curve_brick.color.index_to_band(0, total, 16)
			r, g, b = palette[band]
			assert b > r
			found_blue = True
		if numpy.any(label_slice == last_label):
			# Curve last index: band 15 should be redder than blue (r > b).
			band = hilbert_curve_brick.color.index_to_band(total - 1, total, 16)
			r, g, b = palette[band]
			assert r > b
			found_red = True
	assert found_blue
	assert found_red
