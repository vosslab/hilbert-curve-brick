#!/usr/bin/env python3
"""
Command-line parsing helpers.
"""

# Standard Library
import argparse


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
	output_group.add_argument(
		'--write-pngs', dest='write_pngs', action='store_true',
		help='Write PNG slices.'
	)
	output_group.add_argument(
		'--no-pngs', dest='write_pngs', action='store_false',
		help='Disable PNG output.'
	)
	output_group.set_defaults(write_pngs=True)

	ldr_group = parser.add_argument_group("ldraw options")
	ldr_group.add_argument(
		'-l', '--ldr-output', dest='ldr_output', type=str, default='',
		help='Write LDraw output to this file.'
	)
	ldr_group.add_argument(
		'--ldr-color', dest='ldr_color', type=int, default=15,
		help='LDraw color index (default 15).'
	)
	ldr_group.add_argument(
		'--ldr-threshold', dest='ldr_threshold', type=float, default=0.5,
		help='Threshold for voxel occupancy.'
	)
	ldr_group.add_argument(
		'--ldr-scale', dest='ldr_scale', type=int, default=None,
		help='Override scale for LDraw output.'
	)
	ldr_group.add_argument(
		'--ldr-scale-y', dest='ldr_scale_y', type=int, default=None,
		help='Override Y scale for LDraw output.'
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
def validate_args(args: argparse.Namespace) -> None:
	"""
	Validate parsed arguments.

	Args:
		args: Parsed arguments.
	"""
	if not is_power_of_two(args.dimension):
		raise ValueError("dimension must be a power of two")
	if args.dimension < 1:
		raise ValueError("dimension must be at least 1")
	if args.target_size < 1:
		raise ValueError("target-size must be at least 1")
	if args.scale_y < 1:
		raise ValueError("scale-y must be at least 1")
	if args.ldr_scale is not None and args.ldr_scale < 1:
		raise ValueError("ldr-scale must be at least 1")
	if args.ldr_scale_y is not None and args.ldr_scale_y < 1:
		raise ValueError("ldr-scale-y must be at least 1")
