#!/usr/bin/env python3
"""
Hilbert curve encode/decode helpers.
"""

# Standard Library
import math


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
