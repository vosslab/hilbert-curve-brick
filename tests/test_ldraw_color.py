"""
Tests for LDraw color support: geometry equivalence between integer volume
and float occupancy, and brick label properties.

Write-path tests (those that write .ldr files to disk) live in
tests/e2e/e2e_ldraw_color.py and are run directly, not via pytest.
"""

# PIP3 modules
import numpy

# local repo modules
import hilbert_curve_brick.ldraw as ldraw
import hilbert_curve_brick.volume as volume


#============================================
# Helpers

def _small_int_volume() -> numpy.ndarray:
	"""
	Build a minimal integer volume: dimension=2 Hilbert curve.

	Returns an int32 volume with labels at curve voxels so tests do not
	depend on the full curve generator startup cost.
	"""
	return volume.build_curve_volume(2)


def _small_float_volume(int_vol: numpy.ndarray) -> numpy.ndarray:
	"""
	Build a float occupancy matching the integer volume: 1.0 wherever int_vol > 0.

	This reproduces the old pre-integer-model pattern so the geometry-equivalence
	test can compare brick coordinate sets between the two representations.
	"""
	float_vol = numpy.where(int_vol > 0, 1.0, 0.0).astype(numpy.float32)
	return float_vol


def _brick_coord_set(bricks: list) -> set:
	"""Return the set of (x, y, z) LDU coordinates from a brick list."""
	return {(b["x"], b["y"], b["z"]) for b in bricks}


#============================================
# Geometry equivalence tests

def test_volume_to_bricks_no_threshold_arg() -> None:
	"""volume_to_bricks must accept a single volume argument (no threshold)."""
	int_vol = _small_int_volume()
	# This call would fail with TypeError if the old signature still requires threshold.
	bricks = ldraw.volume_to_bricks(int_vol)
	assert isinstance(bricks, list)


def test_geometry_equivalence_integer_vs_float() -> None:
	"""
	Geometry equivalence: integer volume with >0 must yield the same brick
	coordinate set as the old >=0.5 float occupancy over the same voxels.

	The old path: occupied = float_volume >= 0.5
	The new path: occupied = int_volume > 0
	Both cover identical voxel sets when float_volume is 1.0 exactly where
	int_volume is non-zero.
	"""
	int_vol = _small_int_volume()
	float_vol = _small_float_volume(int_vol)

	# New integer-volume path.
	int_bricks = ldraw.volume_to_bricks(int_vol)

	# Old float-occupancy path reproduced inline: build bricks from float_vol
	# using the >=0.5 rule directly without going through volume_to_bricks.
	# We replicate the greedy merger logic by building an equivalent int volume
	# where any voxel >= 0.5 gets label 1 and running volume_to_bricks on it.
	# This confirms ">0 on int" matches ">=0.5 on float(1.0)" for the same set.
	float_as_int = numpy.where(float_vol >= 0.5, 1, 0).astype(numpy.int32)
	float_bricks = ldraw.volume_to_bricks(float_as_int)

	assert _brick_coord_set(int_bricks) == _brick_coord_set(float_bricks), (
		"brick coordinate sets differ between integer (>0) and float (>=0.5) occupancy"
	)


def test_volume_to_bricks_returns_nonempty_for_occupied_volume() -> None:
	"""A volume with occupied voxels must produce at least one brick."""
	int_vol = _small_int_volume()
	bricks = ldraw.volume_to_bricks(int_vol)
	assert len(bricks) > 0


def test_bricks_carry_label() -> None:
	"""Every brick dict must include a 'label' key."""
	int_vol = _small_int_volume()
	bricks = ldraw.volume_to_bricks(int_vol)
	for brick in bricks:
		assert "label" in brick, f"brick missing 'label': {brick}"


def test_bricks_label_positive() -> None:
	"""Every brick label must be a positive integer (index+1 >= 1)."""
	int_vol = _small_int_volume()
	bricks = ldraw.volume_to_bricks(int_vol)
	for brick in bricks:
		assert isinstance(brick["label"], int) and brick["label"] >= 1, (
			f"unexpected label value: {brick['label']}"
		)


