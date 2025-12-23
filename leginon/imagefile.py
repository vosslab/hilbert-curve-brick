#!/usr/bin/env python3
"""
Minimal image helpers for writing PNG slices.
"""

# Standard Library

# PIP3 modules
import numpy
import PIL.Image


#============================================
def _normalize_array(numer: numpy.ndarray, normalize: bool) -> numpy.ndarray:
	"""
	Normalize or scale an array to 0-255.

	Args:
		numer: Input array.
		normalize: Whether to normalize the data range.

	Returns:
		numpy.ndarray: uint8 array in 0-255 range.
	"""
	if normalize:
		min_value = float(numpy.min(numer))
		max_value = float(numpy.max(numer))
		if max_value == min_value:
			scaled = numpy.zeros(numer.shape, dtype=numpy.float32)
		else:
			scaled = (numer - min_value) / (max_value - min_value)
		scaled = scaled * 255.0
	else:
		scaled = numer * 255.0

	clipped = numpy.clip(scaled, 0, 255)
	result = clipped.astype(numpy.uint8)
	return result


#============================================
def _array_to_image(numer: numpy.ndarray) -> "PIL.Image.Image":
	"""
	Convert a numpy array to a PIL image.

	Args:
		numer: Input array.

	Returns:
		PIL.Image.Image: PIL image.
	"""
	shape_length = len(numer.shape)
	if shape_length == 2:
		height, width = numer.shape
		image = PIL.Image.frombytes("L", (width, height), numer.tobytes())
		return image
	if shape_length == 3 and numer.shape[2] == 3:
		height, width, _ = numer.shape
		image = PIL.Image.frombytes("RGB", (width, height), numer.tobytes())
		return image
	raise ValueError("Unsupported image array shape")


#============================================
def arrayToPng(
		numer: numpy.ndarray,
		filename: str,
		normalize: bool = True,
		msg: bool = True
	) -> None:
	"""
	Write a numpy array to a PNG file.

	Args:
		numer: Input array.
		filename: Output path.
		normalize: Normalize array before saving.
		msg: Print a status line.
	"""
	normalized = _normalize_array(numer, normalize)
	image = _array_to_image(normalized)
	if msg:
		print(f"writing PNG: {filename}")
	image.save(filename, "PNG")


#============================================
def array_to_png(
		numer: numpy.ndarray,
		filename: str,
		normalize: bool = True,
		msg: bool = True
	) -> None:
	"""
	Snake-case wrapper for arrayToPng.

	Args:
		numer: Input array.
		filename: Output path.
		normalize: Normalize array before saving.
		msg: Print a status line.
	"""
	arrayToPng(numer, filename, normalize=normalize, msg=msg)
