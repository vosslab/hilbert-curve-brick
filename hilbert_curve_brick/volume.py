"""
Volume generation and PNG helpers.
"""

# Standard Library
import math
import os

# PIP3 modules
import numpy
import scipy.ndimage

# local repo modules
import hilbert_curve_brick.curve
import leginon.imagefile


#============================================
def build_hilbert_volume(dimension: int) -> numpy.ndarray:
	"""
	Build a 3D volume containing the Hilbert path.

	Args:
		dimension: Hilbert dimension per axis.

	Returns:
		numpy.ndarray: 3D volume with the curve.
	"""
	# Allocate a cubic volume with a 1-voxel border.
	max_dim = dimension * 2 + 1
	volume = numpy.zeros((max_dim, max_dim, max_dim), dtype=numpy.float32)
	last_coord = None
	for index in range(dimension ** 3):
		# Use even coordinates to leave room for connector voxels.
		coord = 2 * numpy.array(hilbert_curve_brick.curve.int_to_hilbert(index, 3), dtype=int)
		volume[coord[0] + 1, coord[1] + 1, coord[2] + 1] = 1.0
		if last_coord is not None:
			# Fill the midpoint between steps to keep the curve connected.
			mid = (coord + last_coord) // 2
			volume[mid[0] + 1, mid[1] + 1, mid[2] + 1] = 1.0
		last_coord = coord
	return volume


#============================================
def compute_scale(dimension: int, target_size: int) -> int:
	"""
	Compute a power-of-two scale for the requested target size.

	Args:
		dimension: Hilbert dimension per axis.
		target_size: Desired maximum size.

	Returns:
		int: Power-of-two scale factor.
	"""
	# Match the target size with a power-of-two scale.
	raw_scale = target_size / float((dimension * 2) + 2)
	scale_factor = int(math.floor(math.log(raw_scale, 2)))
	if scale_factor < 0:
		scale_factor = 0
	scale = 2 ** scale_factor
	return scale


#============================================
def scale_volume(volume: numpy.ndarray, scale: int, scale_y: int) -> numpy.ndarray:
	"""
	Scale the volume with nearest-neighbor interpolation.

	Args:
		volume: Input volume.
		scale: Scale factor for X and Z.
		scale_y: Scale factor for Y.

	Returns:
		numpy.ndarray: Scaled volume.
	"""
	scales = (scale, scale_y, scale)
	# Use grid_mode block replication so each base voxel maps to exactly
	# `scale` output pixels. The default (grid_mode=False) maps by
	# (n_out-1)/(n_in-1), which stretches the pitch slightly and makes the
	# fixed-step grid overlay drift onto boxes across the image.
	scaled = scipy.ndimage.zoom(volume, scales, order=0, grid_mode=True, mode='grid-constant')
	return scaled


#============================================
def apply_grid_overlay(volume: numpy.ndarray, step: int, offset: int) -> numpy.ndarray:
	"""
	Overlay grid planes on the volume so each box sits centered in a cell.

	Box voxels are `step` pixels apart (the box pitch). Placing a line every
	`step` pixels starting at `offset` puts each line halfway between two
	neighboring box centers, so the boxes land centered inside the cells. With
	offset = half a box width, the lines fall on the gap centers and never cut
	through a box.

	Args:
		volume: Input volume.
		step: Pixel distance between grid lines (the box pitch).
		offset: Pixel position of the first grid line (half a cell from a center).

	Returns:
		numpy.ndarray: Volume with grid overlays.
	"""
	max_index = min(volume.shape[0], volume.shape[2])
	# Walk grid lines from the first gap center to the far edge.
	line = offset
	while line < max_index:
		volume[line, :, :] = 0.5
		volume[:, :, line] = 0.5
		line += step
	return volume


#============================================
def iter_slices(volume: numpy.ndarray, axis: str, start: int, end: int) -> tuple:
	"""
	Iterate slices along a specific axis.

	Args:
		volume: Input volume.
		axis: Axis label ('x', 'y', 'z').
		start: First slice index.
		end: End slice index (exclusive).

	Returns:
		tuple: (slice_index, slice_array).
	"""
	axis_map = {'x': 0, 'y': 1, 'z': 2}
	axis_index = axis_map[axis]
	max_slices = volume.shape[axis_index]
	start_index = max(0, start)
	end_index = end
	if end_index < 0:
		end_index = max_slices + end_index + 1
	end_index = min(end_index, max_slices)
	for slice_index in range(start_index, end_index):
		if axis_index == 0:
			slice_array = volume[slice_index, :, :]
		elif axis_index == 1:
			slice_array = volume[:, slice_index, :]
		else:
			slice_array = volume[:, :, slice_index]
		yield slice_index, slice_array


#============================================
def write_slices(
		volume: numpy.ndarray,
		axis: str,
		output_dir: str,
		prefix: str,
		invert: bool,
		normalize: bool,
		slice_start: int,
		slice_end: int
	) -> None:
	"""
	Write PNG slices to disk.

	Args:
		volume: Input volume.
		axis: Axis label.
		output_dir: Directory for output.
		prefix: Filename prefix.
		invert: Whether to invert slices.
		normalize: Whether to normalize slices.
		slice_start: First slice index.
		slice_end: End slice index (exclusive).
	"""
	os.makedirs(output_dir, exist_ok=True)
	for slice_index, slice_array in iter_slices(volume, axis, slice_start, slice_end):
		output_array = slice_array
		if invert:
			output_array = 1.0 - output_array
		filename = f"{prefix}-{slice_index:03d}.png"
		output_path = os.path.join(output_dir, filename)
		leginon.imagefile.arrayToPng(output_array, output_path, normalize=normalize)
