"""
CLI validation tests.

The dimension must be a power of two for the Hilbert curve to fill the cube.
These tests cover the user-facing behavior: validate_args rejects a non
power-of-two dimension and accepts a valid one, and is_power_of_two reports the
expected truth for representative inputs.
"""

# Standard Library
import argparse

# PIP3 modules
import pytest

# local repo modules
import hilbert_curve_brick.cli


#============================================
def make_args(dimension: int) -> argparse.Namespace:
	"""
	Build a minimal args namespace for validate_args.

	Args:
		dimension: Dimension value to validate.

	Returns:
		argparse.Namespace: Namespace with a valid target size.
	"""
	return argparse.Namespace(dimension=dimension, target_size=800)


#============================================
def test_validate_args_rejects_non_power_of_two() -> None:
	"""
	A dimension of 7 is not a power of two and must raise.
	"""
	with pytest.raises(ValueError):
		hilbert_curve_brick.cli.validate_args(make_args(7))


#============================================
def test_validate_args_accepts_power_of_two() -> None:
	"""
	A power-of-two dimension passes validation without raising.
	"""
	# No exception means the value is accepted.
	hilbert_curve_brick.cli.validate_args(make_args(8))


#============================================
def test_is_power_of_two_accepts_powers() -> None:
	"""
	is_power_of_two accepts representative single-bit values.
	"""
	assert all(hilbert_curve_brick.cli.is_power_of_two(value) for value in (1, 2, 16))


#============================================
def test_is_power_of_two_rejects_non_powers_and_non_positive() -> None:
	"""
	is_power_of_two rejects multi-bit values, zero, and negatives.
	"""
	assert not any(hilbert_curve_brick.cli.is_power_of_two(value) for value in (6, 0, -4))
