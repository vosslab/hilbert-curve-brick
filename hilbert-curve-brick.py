#!/usr/bin/env python3
"""
Generate 3D Hilbert curve slices for LEGO-compatible brick builds.
"""

# Standard Library
import argparse
import math
import os

# PIP3 modules
import numpy
import scipy.ndimage

# local repo modules
import leginon.imagefile


#============================================
def parse_args() -> argparse.Namespace:
	"""
	Parse command-line arguments.

	Returns:
		argparse.Namespace: Parsed arguments.
	"""
	parser = argparse.ArgumentParser(
		description="Generate 3D Hilbert curve PNG slices for brick layouts."
	)

	curve_group = parser.add_argument_group("curve options")
	curve_group.add_argument(
		'-d', '--dimension', dest='dimension', type=int, default=8,
		help='Hilbert dimension per axis (power of two).'
	)
	curve_group.add_argument(
		'-s', '--target-size', dest='target_size', type=int, default=800,
		help='Target max size used to compute scale.'
	)
	curve_group.add_argument(
		'-y', '--scale-y', dest='scale_y', type=int, default=1,
		help='Scale factor for Y axis (default keeps Y unscaled).'
	)

	output_group = parser.add_argument_group("output options")
	output_group.add_argument(
		'-o', '--output-dir', dest='output_dir', type=str, default='output',
		help='Directory for PNG slices.'
	)
	output_group.add_argument(
		'-p', '--prefix', dest='prefix', type=str, default='hilbert',
		help='Output filename prefix.'
	)
	output_group.add_argument(
		'-a', '--axis', dest='axis', type=str, default='y',
		choices=('x', 'y', 'z'),
		help='Axis to slice when saving PNG files.'
	)
	output_group.add_argument(
		'-g', '--add-grid', dest='add_grid', action='store_true',
		help='Overlay grid planes.'
	)
	output_group.add_argument(
		'-G', '--no-grid', dest='add_grid', action='store_false',
		help='Do not overlay grid planes.'
	)
	output_group.set_defaults(add_grid=True)
	output_group.add_argument(
		'-i', '--invert', dest='invert', action='store_true',
		help='Invert output slices (white background).'
	)
	output_group.add_argument(
		'-I', '--no-invert', dest='invert', action='store_false',
		help='Do not invert output slices.'
	)
	output_group.set_defaults(invert=True)
	output_group.add_argument(
		'-n', '--normalize', dest='normalize', action='store_true',
		help='Normalize slices before saving.'
	)
	output_group.add_argument(
		'-N', '--no-normalize', dest='normalize', action='store_false',
		help='Save slices without normalization.'
	)
	output_group.set_defaults(normalize=True)
	output_group.add_argument(
		'-b', '--slice-start', dest='slice_start', type=int, default=1,
		help='First slice index to save.'
	)
	output_group.add_argument(
		'-e', '--slice-end', dest='slice_end', type=int, default=-1,
		help='Last slice index (exclusive). Use -1 for the last slice.'
	)

	args = parser.parse_args()
	return args


#============================================
def is_power_of_two(value: int) -> bool:
	"""
	Check if a value is a power of two.

	Args:
		value: Value to check.

	Returns:
		bool: True when value is a power of two.
	"""
	if value <= 0:
		return False
	is_power = (value & (value - 1)) == 0
	return is_power


#============================================
def int_to_hilbert(index: int, n_dimensions: int = 2) -> tuple:
	"""
	Convert a Hilbert index to coordinates.

	Args:
		index: Hilbert index.
		n_dimensions: Number of dimensions.

	Returns:
		tuple: Coordinate tuple in n_dimensions space.
	"""
	index_chunks = unpack_index(index, n_dimensions)
	chunk_count = len(index_chunks)
	mask = 2 ** n_dimensions - 1
	start, end = initial_start_end(chunk_count, n_dimensions)
	coord_chunks = [0] * chunk_count
	for chunk_index in range(chunk_count):
		chunk_value = index_chunks[chunk_index]
		coord_chunks[chunk_index] = gray_encode_travel(start, end, mask, chunk_value)
		start, end = child_start_end(start, end, mask, chunk_value)
	coords = pack_coords(coord_chunks, n_dimensions)
	return coords


#============================================
def hilbert_to_int(coords: tuple) -> int:
	"""
	Convert Hilbert coordinates into a linear index.

	Args:
		coords: Coordinate tuple.

	Returns:
		int: Hilbert index.
	"""
	n_dimensions = len(coords)
	coord_chunks = unpack_coords(coords)
	chunk_count = len(coord_chunks)
	mask = 2 ** n_dimensions - 1
	start, end = initial_start_end(chunk_count, n_dimensions)
	index_chunks = [0] * chunk_count
	for chunk_index in range(chunk_count):
		chunk_value = gray_decode_travel(start, end, mask, coord_chunks[chunk_index])
		index_chunks[chunk_index] = chunk_value
		start, end = child_start_end(start, end, mask, chunk_value)
	index = pack_index(index_chunks, n_dimensions)
	return index


#============================================
def int_to_Hilbert(index: int, nD: int = 2) -> tuple:
	"""
	Compatibility wrapper for legacy naming.

	Args:
		index: Hilbert index.
		nD: Number of dimensions.

	Returns:
		tuple: Coordinate tuple.
	"""
	coords = int_to_hilbert(index, nD)
	return coords


#============================================
def Hilbert_to_int(coords: tuple) -> int:
	"""
	Compatibility wrapper for legacy naming.

	Args:
		coords: Coordinate tuple.

	Returns:
		int: Hilbert index.
	"""
	index = hilbert_to_int(coords)
	return index


#============================================
def initial_start_end(chunk_count: int, n_dimensions: int) -> tuple:
	"""
	Return start and end corners for the top-level cube.

	Args:
		chunk_count: Number of coordinate chunks.
		n_dimensions: Number of dimensions.

	Returns:
		tuple: (start, end) values.
	"""
	start = 0
	end = 2 ** ((-chunk_count - 1) % n_dimensions)
	return start, end


#============================================
def unpack_index(index: int, n_dimensions: int) -> list:
	"""
	Unpack a Hilbert index into base 2**n_dimensions chunks.

	Args:
		index: Hilbert index.
		n_dimensions: Number of dimensions.

	Returns:
		list: Index chunks.
	"""
	base = 2 ** n_dimensions
	chunk_count = max(1, int(math.ceil(math.log(index + 1, base))))
	chunks = [0] * chunk_count
	value = index
	for chunk_index in range(chunk_count - 1, -1, -1):
		chunks[chunk_index] = value % base
		value //= base
	return chunks


#============================================
def pack_index(chunks: list, n_dimensions: int) -> int:
	"""
	Pack index chunks into a single Hilbert index.

	Args:
		chunks: Index chunks.
		n_dimensions: Number of dimensions.

	Returns:
		int: Hilbert index.
	"""
	base = 2 ** n_dimensions
	index = 0
	for chunk in chunks:
		index = index * base + chunk
	return index


#============================================
def unpack_coords(coords: tuple) -> list:
	"""
	Unpack coordinates into bit-transposed chunks.

	Args:
		coords: Coordinate tuple.

	Returns:
		list: Coordinate chunks.
	"""
	biggest = max(coords)
	chunk_count = max(1, int(math.ceil(math.log(biggest + 1, 2))))
	chunks = transpose_bits(coords, chunk_count)
	return chunks


#============================================
def pack_coords(chunks: list, n_dimensions: int) -> tuple:
	"""
	Pack coordinate chunks into coordinate tuple.

	Args:
		chunks: Coordinate chunks.
		n_dimensions: Number of dimensions.

	Returns:
		tuple: Coordinate tuple.
	"""
	coords = transpose_bits(chunks, n_dimensions)
	coords_tuple = tuple(coords)
	return coords_tuple


#============================================
def transpose_bits(values: list, destination_bits: int) -> list:
	"""
	Transpose bits between integers.

	Args:
		values: Source integers.
		destination_bits: Output bit count.

	Returns:
		list: Transposed integers.
	"""
	srcs = list(values)
	src_count = len(srcs)
	dests = [0] * destination_bits
	for dest_index in range(destination_bits - 1, -1, -1):
		dest = 0
		for src_index in range(src_count):
			dest = dest * 2 + (srcs[src_index] % 2)
			srcs[src_index] //= 2
		dests[dest_index] = dest
	return dests


#============================================
def gray_encode(value: int) -> int:
	"""
	Encode an integer into Gray code.

	Args:
		value: Integer to encode.

	Returns:
		int: Gray-coded value.
	"""
	assert value >= 0
	assert isinstance(value, int)
	encoded = value ^ (value // 2)
	return encoded


#============================================
def gray_decode(value: int) -> int:
	"""
	Decode a Gray-coded integer.

	Args:
		value: Gray-coded integer.

	Returns:
		int: Decoded value.
	"""
	shift = 1
	decoded = value
	while True:
		div = decoded >> shift
		decoded ^= div
		if div <= 1:
			return decoded
		shift <<= 1


#============================================
def gray_encode_travel(start: int, end: int, mask: int, index: int) -> int:
	"""
	Gray encode with start/end orientation for Hilbert traversal.

	Args:
		start: Start corner.
		end: End corner.
		mask: Maximum index value for this dimension.
		index: Step index.

	Returns:
		int: Encoded coordinate chunk.
	"""
	travel_bit = start ^ end
	modulus = mask + 1
	encoded = gray_encode(index) * (travel_bit * 2)
	rotated = (encoded | (encoded // modulus)) & mask
	result = rotated ^ start
	return result


#============================================
def gray_decode_travel(start: int, end: int, mask: int, value: int) -> int:
	"""
	Decode a Gray-travel value into its Hilbert step.

	Args:
		start: Start corner.
		end: End corner.
		mask: Maximum index value for this dimension.
		value: Encoded coordinate chunk.

	Returns:
		int: Decoded step index.
	"""
	travel_bit = start ^ end
	modulus = mask + 1
	rotated = (value ^ start) * (modulus // (travel_bit * 2))
	decoded = gray_decode((rotated | (rotated // modulus)) & mask)
	return decoded


#============================================
def child_start_end(parent_start: int, parent_end: int, mask: int, index: int) -> tuple:
	"""
	Return child start/end corners for the next Hilbert cube.

	Args:
		parent_start: Parent cube start.
		parent_end: Parent cube end.
		mask: Maximum index value for this dimension.
		index: Parent index.

	Returns:
		tuple: (child_start, child_end).
	"""
	start_index = max(0, (index - 1) & ~1)
	end_index = min(mask, (index + 1) | 1)
	child_start = gray_encode_travel(parent_start, parent_end, mask, start_index)
	child_end = gray_encode_travel(parent_start, parent_end, mask, end_index)
	return child_start, child_end


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
		coord = 2 * numpy.array(int_to_hilbert(index, 3), dtype=int)
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
	scaled = scipy.ndimage.zoom(volume, scales, order=0)
	return scaled


#============================================
def apply_grid_overlay(volume: numpy.ndarray, step: int) -> numpy.ndarray:
	"""
	Overlay grid planes on the volume.

	Args:
		volume: Input volume.
		step: Step size for grid planes.

	Returns:
		numpy.ndarray: Volume with grid overlays.
	"""
	max_index = min(volume.shape[0], volume.shape[2])
	grid_count = max_index // step
	for grid_index in range(1, grid_count):
		volume[grid_index * step, :, :] = 0.5
		volume[:, :, grid_index * step] = 0.5
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


#============================================
def main() -> None:
	"""
	Script entry point.
	"""
	args = parse_args()

	# Validate inputs early to keep error messages clear.
	if not is_power_of_two(args.dimension):
		raise ValueError("dimension must be a power of two")
	if args.dimension < 1:
		raise ValueError("dimension must be at least 1")
	if args.target_size < 1:
		raise ValueError("target-size must be at least 1")
	if args.scale_y < 1:
		raise ValueError("scale-y must be at least 1")

	# Build base curve, then scale to the requested size.
	volume = build_hilbert_volume(args.dimension)
	scale = compute_scale(args.dimension, args.target_size)
	scaled_volume = scale_volume(volume, scale, args.scale_y)

	if args.add_grid:
		# Overlay grid planes to match brick spacing.
		step = (scale * 2) + 4
		scaled_volume = apply_grid_overlay(scaled_volume, step)

	# Write PNG slices to disk.
	write_slices(
		scaled_volume,
		args.axis,
		args.output_dir,
		f"{args.prefix}{args.dimension}",
		args.invert,
		args.normalize,
		args.slice_start,
		args.slice_end
	)


#============================================
if __name__ == '__main__':
	main()
