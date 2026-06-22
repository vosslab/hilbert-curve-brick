"""
Palette loading and color-mapping helpers for Hilbert curve rainbow display.
"""

# Standard Library
import importlib.resources
import string

# PIP3 modules
import yaml


# Number of discrete color bands used for the rainbow display.
N_BANDS = 16


#============================================
def load_palette() -> list[tuple[int, int, int]]:
	"""
	Load the 16-band rainbow palette from the packaged YAML file.

	Reads ``hilbert_curve_brick/rainbow_palette.yaml`` through
	``importlib.resources`` so the file resolves from an installed package.

	Returns:
		list[tuple]: 16 (r, g, b) int triples, values in 0-255, band 0 first.

	Raises:
		ValueError: When the YAML has fewer than 16 entries, a non-hex string,
			or a channel value outside 0-255, with the offending entry named.
	"""
	# Locate the YAML as a package resource so installed copies resolve cleanly.
	resource_path = importlib.resources.files('hilbert_curve_brick').joinpath('rainbow_palette.yaml')
	with importlib.resources.as_file(resource_path) as yaml_path:
		with open(yaml_path, 'r') as fh:
			data = yaml.safe_load(fh)

	raw_entries = data['bands']

	# Validate entry count before parsing individual values.
	if len(raw_entries) < N_BANDS:
		raise ValueError(
			f"palette must have at least {N_BANDS} entries, found {len(raw_entries)}"
		)

	palette = []
	for i, entry in enumerate(raw_entries[:N_BANDS]):
		rgb = _parse_hex_entry(entry, i)
		palette.append(rgb)
	return palette


#============================================
def _parse_hex_entry(entry: str, index: int) -> tuple[int, int, int]:
	"""
	Parse a single #RRGGBB hex string into an (r, g, b) int triple.

	Args:
		entry: Hex color string, expected as '#RRGGBB'.
		index: Band index, used in error messages.

	Returns:
		tuple: (r, g, b) int triple, each value in 0-255.

	Raises:
		ValueError: When the string is not a valid 7-character hex entry or any
			channel is outside 0-255, naming the offending entry and index.
	"""
	# Require '#' prefix, total length 7, and all 6 remaining chars as hex digits.
	if not isinstance(entry, str) or len(entry) != 7 or entry[0] != '#':
		raise ValueError(
			f"palette entry {index} is not a valid #RRGGBB hex string: {entry!r}"
		)
	if not all(c in string.hexdigits for c in entry[1:7]):
		raise ValueError(
			f"palette entry {index} is not a valid #RRGGBB hex string: {entry!r}"
		)
	# All six chars are valid hex digits; parse without try/except.
	r = int(entry[1:3], 16)
	g = int(entry[3:5], 16)
	b = int(entry[5:7], 16)

	# Each channel must fit in 0-255; two hex digits can produce at most 0xFF=255.
	for channel_name, channel_val in (('r', r), ('g', g), ('b', b)):
		if not (0 <= channel_val <= 255):
			raise ValueError(
				f"palette entry {index} channel {channel_name}={channel_val} is outside 0-255: {entry!r}"
			)

	rgb = (r, g, b)
	return rgb


#============================================
def index_to_band(index: int, total: int, n_bands: int) -> int:
	"""
	Map a curve index to a discrete color band.

	Band formula: ``band = min(n_bands - 1, index * n_bands // total)``

	The ``min`` clamp ensures the final boundary (``index == total - 1``) always
	maps to the last band (``n_bands - 1``) rather than overflowing to a
	hypothetical ``n_bands`` th slot due to integer rounding at the edge.

	Args:
		index: Curve index (0-based, from 0 to total-1 inclusive).
		total: Total number of curve steps.
		n_bands: Number of discrete bands.

	Returns:
		int: Band number in [0, n_bands - 1].

	Raises:
		ValueError: When total is <= 0, to avoid division by zero.
	"""
	if total <= 0:
		raise ValueError(f"total must be a positive integer, got {total}")
	# Apply the clamped linear band formula.
	band = min(n_bands - 1, index * n_bands // total)
	return band


#============================================
def rgb_to_ldraw_direct(rgb: tuple[int, int, int]) -> str:
	"""
	Convert an (r, g, b) int triple to an LDraw direct color string.

	LDraw direct color format: ``0x2`` followed by 6 uppercase hex digits in
	RRGGBB order, with each channel zero-padded to two digits.

	Args:
		rgb: (r, g, b) int triple, values in 0-255.

	Returns:
		str: LDraw direct color string, e.g. ``"0x2FF0000"`` for (255, 0, 0).
	"""
	r, g, b = rgb
	# Format each channel as exactly two uppercase hex digits.
	ldraw_color = f"0x2{r:02X}{g:02X}{b:02X}"
	return ldraw_color
