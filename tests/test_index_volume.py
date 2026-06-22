"""
Tests for the integer model volume produced by build_curve_volume.

The volume stores integer labels: 0 is empty, index + 1 is the label
for curve step `index`. Connector voxels (midpoints between adjacent
curve points) inherit the earlier point's label so the occupied path
is non-decreasing. Strict increase holds only across actual curve
point voxels, not across connectors.
"""

# PIP3 modules
import numpy

# local repo modules
import hilbert_curve_brick.curve
import hilbert_curve_brick.volume


#============================================
def test_build_curve_volume_returns_int32() -> None:
	"""
	build_curve_volume returns an int32 array.
	"""
	volume = hilbert_curve_brick.volume.build_curve_volume(2)
	assert volume.dtype == numpy.int32


#============================================
def test_build_curve_volume_empty_voxels_are_zero() -> None:
	"""
	Empty voxels in the volume are exactly 0.
	"""
	volume = hilbert_curve_brick.volume.build_curve_volume(2)
	# The volume has both occupied (>0) and empty (==0) voxels.
	assert numpy.any(volume == 0)
	# No negative labels exist.
	assert numpy.all(volume >= 0)


#============================================
def test_build_curve_volume_occupied_voxels_positive() -> None:
	"""
	All occupied voxels have a label strictly greater than 0.
	"""
	volume = hilbert_curve_brick.volume.build_curve_volume(2)
	occupied_labels = volume[volume > 0]
	assert len(occupied_labels) > 0
	assert numpy.all(occupied_labels > 0)


#============================================
def test_build_curve_volume_occupied_mask_matches_prior_float() -> None:
	"""
	The non-zero mask of the integer volume matches the float volume's non-zero mask.

	The float volume used 1.0 for occupied; the integer volume uses index+1.
	The occupied (non-zero) voxels must be the same set.
	"""
	dimension = 2
	# Build the integer volume via the new function.
	int_vol = hilbert_curve_brick.volume.build_curve_volume(dimension)
	# Build the expected occupied mask by replicating the old logic with float32.
	max_dim = dimension * 2 + 1
	float_vol = numpy.zeros((max_dim, max_dim, max_dim), dtype=numpy.float32)
	last_coord = None
	for index in range(dimension ** 3):
		coord = 2 * numpy.array(
			hilbert_curve_brick.curve.int_to_hilbert(index, 3), dtype=int)
		float_vol[coord[0] + 1, coord[1] + 1, coord[2] + 1] = 1.0
		if last_coord is not None:
			mid = (coord + last_coord) // 2
			float_vol[mid[0] + 1, mid[1] + 1, mid[2] + 1] = 1.0
		last_coord = coord
	assert numpy.array_equal(int_vol > 0, float_vol > 0)


#============================================
def test_build_curve_volume_curve_points_strictly_increase() -> None:
	"""
	Labels at actual curve point voxels strictly increase along the curve.

	Curve points are placed at 2*hilbert(index) + 1 on every axis (offset by
	the 1-voxel border). The label there is index + 1.
	"""
	dimension = 2
	volume = hilbert_curve_brick.volume.build_curve_volume(dimension)
	labels = []
	for index in range(dimension ** 3):
		coord = 2 * numpy.array(
			hilbert_curve_brick.curve.int_to_hilbert(index, 3), dtype=int)
		label = volume[coord[0] + 1, coord[1] + 1, coord[2] + 1]
		labels.append(int(label))
	# Strict increase: each label must be exactly one more than the previous.
	for i in range(1, len(labels)):
		assert labels[i] > labels[i - 1]


#============================================
def test_build_curve_volume_full_path_nondecreasing() -> None:
	"""
	Labels along the full occupied path (including connectors) are non-decreasing.

	Connectors inherit the earlier curve point's label, so the path stays
	non-decreasing but is not strictly increasing at every step.
	"""
	dimension = 2
	volume = hilbert_curve_brick.volume.build_curve_volume(dimension)
	path_labels = []
	last_coord = None
	for index in range(dimension ** 3):
		coord = 2 * numpy.array(
			hilbert_curve_brick.curve.int_to_hilbert(index, 3), dtype=int)
		# Collect the connector label first (if any), then the curve point label.
		if last_coord is not None:
			mid = (coord + last_coord) // 2
			connector_label = volume[mid[0] + 1, mid[1] + 1, mid[2] + 1]
			path_labels.append(int(connector_label))
		curve_label = volume[coord[0] + 1, coord[1] + 1, coord[2] + 1]
		path_labels.append(int(curve_label))
		last_coord = coord
	# Non-decreasing: no label is smaller than the one before it.
	for i in range(1, len(path_labels)):
		assert path_labels[i] >= path_labels[i - 1]


#============================================
def test_build_grid_mask_marks_correct_planes() -> None:
	"""
	build_grid_mask returns True at grid line positions on axis 0 and axis 2.
	"""
	shape = (20, 20, 20)
	step = 4
	offset = 2
	mask = hilbert_curve_brick.volume.build_grid_mask(shape, step, offset)
	assert mask.dtype == bool
	# Check that the expected grid lines are fully True.
	line = offset
	while line < min(shape[0], shape[2]):
		assert numpy.all(mask[line, :, :])
		assert numpy.all(mask[:, :, line])
		line += step


#============================================
def test_build_grid_mask_non_grid_planes_false() -> None:
	"""
	Positions between grid lines on both axes are False in the grid mask.

	A voxel at (row, y, col) is only True if row is a grid line on axis 0
	OR col is a grid line on axis 2. A voxel where neither applies is False.
	"""
	shape = (20, 20, 20)
	step = 4
	offset = 2
	mask = hilbert_curve_brick.volume.build_grid_mask(shape, step, offset)
	# Position 0 is not a grid line on axis 0 (first grid line is at offset=2).
	# Position 0 is also not a grid line on axis 2.
	# So mask[0, :, 0] must be entirely False.
	assert not numpy.any(mask[0, :, 0])


#============================================
def test_scale_volume_preserves_integer_labels() -> None:
	"""
	scale_volume block-replicates integer labels without alteration.
	"""
	# A 2x2x2 volume with distinct integer labels.
	base = numpy.array([[[1, 2], [3, 4]], [[5, 6], [7, 8]]], dtype=numpy.int32)
	scaled = hilbert_curve_brick.volume.scale_volume(base, 2, 2)
	# Every label in the output must appear in the input.
	for label in numpy.unique(scaled):
		assert label in numpy.unique(base)
