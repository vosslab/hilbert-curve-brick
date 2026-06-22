"""
Grid alignment tests.

scale_volume uses grid_mode block replication, so each base voxel maps to
exactly `scale` output pixels and a scaled column c comes from base index
c // scale. Box voxels (Hilbert curve points) sit on odd base indices; even
base indices are gaps. grid_params returns (step, offset) where step = scale*2
(the box pitch) and offset = scale//2, placing each grid line halfway between
neighboring box centers so every box sits centered in its cell. Centering only
holds when the zoom replicates exactly.
"""

# PIP3 modules
import numpy
import pytest

# local repo modules
import hilbert_curve_brick.volume

# Occupied voxels in the integer model are label > 0.
BOX_LABEL = 1

# A small scale keeps the test cheap; the centering property holds for any
# scale because scale_volume replicates each base voxel by exactly `scale`.
TEST_SCALE = 4


#============================================
def build_scaled(dimension: int) -> tuple[numpy.ndarray, int]:
	"""
	Build a base cube with boxes on odd indices and scale it.

	The real curve places box voxels on odd base indices (axis 0 here mirrors
	that). Centering depends only on the base axis size (2*dim+1) and the
	block-replication factor, not on the Hilbert content or production scale,
	so a small scale exercises the geometry cheaply.

	Args:
		dimension: Hilbert dimension per axis.

	Returns:
		tuple: (scaled_volume, scale) for the requested dimension.
	"""
	base_size = dimension * 2 + 1
	# Use integer dtype matching the new model.
	base = numpy.zeros((base_size, base_size, base_size), dtype=numpy.int32)
	# Boxes occupy odd base indices along axis 0, gaps are even (matches the curve).
	base[1::2, :, :] = BOX_LABEL
	scaled = hilbert_curve_brick.volume.scale_volume(base, TEST_SCALE, TEST_SCALE)
	return scaled, TEST_SCALE


#============================================
def box_runs(scaled: numpy.ndarray) -> list[tuple[int, int]]:
	"""
	Return (start, end_exclusive) pixel spans of box columns along axis 0.

	Args:
		scaled: Scaled volume with boxes on some axis-0 columns.

	Returns:
		list: Contiguous box-column spans.
	"""
	box_cols = numpy.where(numpy.any(scaled > 0, axis=(1, 2)))[0]
	runs = []
	start = None
	prev = None
	for column in box_cols:
		if start is None:
			start = column
		elif column != prev + 1:
			# A gap in the column indices means the current run has ended.
			runs.append((int(start), int(prev) + 1))
			start = column
		prev = column
	if start is not None:
		runs.append((int(start), int(prev) + 1))
	return runs


#============================================
def grid_columns(scaled_size: int, step: int, offset: int) -> list[int]:
	"""
	Compute the grid plane indices the mask would mark.

	Args:
		scaled_size: Size of the scaled axis.
		step: Grid step in scaled pixels.
		offset: Pixel position of the first grid line.

	Returns:
		list: Grid plane indices.
	"""
	columns = []
	line = offset
	while line < scaled_size:
		columns.append(line)
		line += step
	return columns


#============================================
def test_scale_volume_replicates_each_base_voxel_exactly() -> None:
	"""
	scale_volume maps base voxel (z, y, x) to a solid scale-sized block.
	"""
	# Distinct integer values so any drift in the mapping shows up immediately.
	base = numpy.arange(2 * 2 * 2, dtype=numpy.int32).reshape((2, 2, 2))
	scale = 3
	scale_y = 2
	scaled = hilbert_curve_brick.volume.scale_volume(base, scale, scale_y)
	# Exact block replication equals the Kronecker product with a ones block.
	expected = numpy.kron(base, numpy.ones((scale, scale_y, scale), dtype=base.dtype))
	assert numpy.array_equal(scaled, expected)


#============================================
@pytest.mark.parametrize("dimension", [2, 4, 8])
def test_grid_lines_do_not_cut_boxes(dimension: int) -> None:
	"""
	No grid line passes through an occupied box column.
	"""
	scaled, scale = build_scaled(dimension)
	step, offset = hilbert_curve_brick.volume.grid_params(scale)
	columns = grid_columns(scaled.shape[0], step, offset)
	# A grid line column must carry no box pixel, so squares stay readable.
	for column in columns:
		assert not numpy.any(scaled[column, :, :] > 0)


#============================================
@pytest.mark.parametrize("dimension", [2, 4, 8])
def test_each_box_sits_in_one_cell(dimension: int) -> None:
	"""
	Every box run falls between two adjacent grid lines (one cell).
	"""
	scaled, scale = build_scaled(dimension)
	step, offset = hilbert_curve_brick.volume.grid_params(scale)
	columns = grid_columns(scaled.shape[0], step, offset)
	for start, end in box_runs(scaled):
		# The lines immediately bounding the box define its single cell. Default
		# to the image edges so a box at the border does not raise on an empty
		# candidate list.
		left = max((line for line in columns if line <= start), default=0)
		right = min((line for line in columns if line >= end), default=scaled.shape[0])
		# A box owns one cell when no other grid line sits inside that cell.
		inside = [line for line in columns if left < line < right]
		assert not inside


#============================================
@pytest.mark.parametrize("dimension", [2, 4, 8])
def test_grid_mask_marks_grid_columns(dimension: int) -> None:
	"""
	build_grid_mask marks True on each grid plane along axis 0 and axis 2.
	"""
	scaled, scale = build_scaled(dimension)
	step, offset = hilbert_curve_brick.volume.grid_params(scale)
	columns = grid_columns(scaled.shape[0], step, offset)
	mask = hilbert_curve_brick.volume.build_grid_mask(scaled.shape, step, offset)
	for column in columns:
		# Every voxel on a grid plane along axis 0 must be True in the mask.
		assert numpy.all(mask[column, :, :])


#============================================
@pytest.mark.parametrize("dimension", [2, 4, 8])
def test_grid_mask_marks_axis2_columns(dimension: int) -> None:
	"""
	build_grid_mask marks True on grid planes along axis 2 as well.
	"""
	scaled, scale = build_scaled(dimension)
	step, offset = hilbert_curve_brick.volume.grid_params(scale)
	columns = grid_columns(scaled.shape[2], step, offset)
	mask = hilbert_curve_brick.volume.build_grid_mask(scaled.shape, step, offset)
	for column in columns:
		# Every voxel on a grid plane along axis 2 must be True in the mask.
		assert numpy.all(mask[:, :, column])
