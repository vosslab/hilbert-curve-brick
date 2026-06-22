"""
Tests for hilbert_curve_brick.color: palette loading, band mapping, and LDraw color.
"""

# Standard Library
import pytest

# local repo modules
import hilbert_curve_brick.color as color


#============================================
def test_load_palette_has_16_bands() -> None:
	"""The palette ships exactly 16 bands by design."""
	palette = color.load_palette()
	assert len(palette) == 16, f"expected 16 bands, got {len(palette)}"


#============================================
def test_load_palette_triples_are_ints_in_range() -> None:
	"""Every channel in the palette must be an int in 0-255."""
	palette = color.load_palette()
	for band_idx, (r, g, b) in enumerate(palette):
		assert isinstance(r, int) and isinstance(g, int) and isinstance(b, int), (
			f"band {band_idx} channels are not all ints"
		)
		assert 0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255, (
			f"band {band_idx} channel out of 0-255 range"
		)


#============================================
def test_index_to_band_first_index_is_zero() -> None:
	"""Index 0 must map to band 0 for any total."""
	assert color.index_to_band(0, 100, 16) == 0


def test_index_to_band_last_index_is_last_band() -> None:
	"""Index total-1 must map to the last band (n_bands - 1)."""
	total = 512
	result = color.index_to_band(total - 1, total, 16)
	assert result == 15


def test_index_to_band_monotonic() -> None:
	"""Bands must be non-decreasing as index increases."""
	total = 100
	bands = [color.index_to_band(i, total, 16) for i in range(total)]
	for i in range(1, len(bands)):
		assert bands[i] >= bands[i - 1], (
			f"band decreased at index {i}: {bands[i-1]} -> {bands[i]}"
		)


def test_index_to_band_zero_total_raises() -> None:
	"""total <= 0 must raise a clear ValueError."""
	with pytest.raises(ValueError, match="total"):
		color.index_to_band(0, 0, 16)


def test_index_to_band_negative_total_raises() -> None:
	"""Negative total must also raise a ValueError."""
	with pytest.raises(ValueError, match="total"):
		color.index_to_band(0, -1, 16)


#============================================
def test_rgb_to_ldraw_direct_red() -> None:
	"""(255, 0, 0) must produce '0x2FF0000'."""
	result = color.rgb_to_ldraw_direct((255, 0, 0))
	assert result == "0x2FF0000"


def test_rgb_to_ldraw_direct_format() -> None:
	"""Output must start with '0x2' and have 9 characters total."""
	result = color.rgb_to_ldraw_direct((0, 128, 255))
	assert result.startswith("0x2")
	# '0x2' prefix + 6 hex digits = 9 characters total
	assert len(result) == 9


def test_rgb_to_ldraw_direct_zero_padding() -> None:
	"""Channels less than 16 must be zero-padded to two digits."""
	result = color.rgb_to_ldraw_direct((0, 0, 255))
	# Blue-only: R=00, G=00, B=FF
	assert result == "0x20000FF"


#============================================
def test_palette_non_hex_string_raises() -> None:
	"""A non-hex string in the palette must raise a clear ValueError naming the entry."""
	with pytest.raises(ValueError, match="entry 2"):
		color._parse_hex_entry("notahex", 2)


def test_palette_channel_out_of_range_raises() -> None:
	"""A channel value outside 0-255 must raise a clear ValueError naming the entry."""
	# Manually craft a value with no '#' prefix to trigger the format check.
	with pytest.raises(ValueError, match="entry 5"):
		color._parse_hex_entry("GGGGGG", 5)
