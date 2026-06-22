"""
Command-line parsing helpers.
"""

# Standard Library
import argparse


# Fixed run settings. These were once CLI flags, but they rarely change between
# runs, so they live here as named constants instead. The values match the
# previous argparse defaults so behavior is unchanged. Edit a value here to
# retune it for every run.
SCALE_Y = 1            # Y-axis scale factor (1 keeps Y unscaled).
AXIS = 'y'             # Axis sliced when writing PNG files.
INVERT = True          # Invert slices so the background is white.
NORMALIZE = True       # Normalize slice values before saving.
SLICE_START = 1        # First slice index to save (skips the border slice).
SLICE_END = -1         # Last slice index, exclusive; -1 means through the end.
PREFIX = 'hilbert'     # Output filename prefix (joined with the dimension).
LDR_COLOR = 15         # LDraw color index for emitted bricks.
LDR_THRESHOLD = 0.5    # Voxel occupancy threshold for LDraw bricks.


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

	# Dimension: cells per axis. Must be a power of two for a clean curve.
	parser.add_argument(
		'-d', '--dimension', dest='dimension', type=int, default=8,
		help='Hilbert dimension per axis (must be a power of two: 2, 4, 8, 16, ...).'
	)
	# Target size: drives the power-of-two scale that fills roughly this many pixels.
	parser.add_argument(
		'-s', '--target-size', dest='target_size', type=int, default=800,
		help='Target max image size used to compute the scale.'
	)
	# Output directory: where the PNG slices are written.
	parser.add_argument(
		'-o', '--output-dir', dest='output_dir', type=str, default='output',
		help='Directory for PNG slices.'
	)
	# LDraw output: optional path; when empty, no LDraw file is written.
	parser.add_argument(
		'-l', '--ldr-output', dest='ldr_output', type=str, default='',
		help='Write an LDraw (.ldr) brick file to this path.'
	)
	# Grid toggle: one concept, two flags. The grid frames each Hilbert cell.
	parser.add_argument(
		'-g', '--add-grid', dest='add_grid', action='store_true',
		help='Overlay grid planes (default).'
	)
	parser.add_argument(
		'-G', '--no-grid', dest='add_grid', action='store_false',
		help='Do not overlay grid planes.'
	)
	parser.set_defaults(add_grid=True)

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
	# Reject zero and negatives; powers of two are positive.
	if value <= 0:
		return False
	# A power of two has a single set bit, so value & (value - 1) clears it to 0.
	is_power = (value & (value - 1)) == 0
	return is_power


#============================================
def validate_args(args: argparse.Namespace) -> None:
	"""
	Validate parsed arguments.

	Args:
		args: Parsed arguments.
	"""
	# Dimension must be a power of two so the Hilbert curve fills the cube cleanly.
	if not is_power_of_two(args.dimension):
		raise ValueError(f"dimension must be a power of two, got {args.dimension}")
	# Target size must be positive to compute a usable scale.
	if args.target_size < 1:
		raise ValueError(f"target-size must be at least 1, got {args.target_size}")
