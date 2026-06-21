#!/usr/bin/env python3
"""
Generate 3D Hilbert curve outputs for LEGO-compatible brick builds.
"""

# Standard Library

# local repo modules
import hilbert_curve_brick as hcb


#============================================
def main() -> None:
	"""
	Script entry point.
	"""
	args = hcb.cli.parse_args()
	hcb.cli.validate_args(args)

	base_volume = hcb.volume.build_hilbert_volume(args.dimension)
	scale = hcb.volume.compute_scale(args.dimension, args.target_size)
	scaled_volume = hcb.volume.scale_volume(base_volume, scale, args.scale_y)

	if args.write_pngs:
		png_volume = scaled_volume
		if args.add_grid:
			# Copy to avoid mutating the scaled volume used elsewhere.
			png_volume = hcb.volume.apply_grid_overlay(png_volume.copy(), (scale * 2) + 4)
		hcb.volume.write_slices(
			png_volume,
			args.axis,
			args.output_dir,
			f"{args.prefix}{args.dimension}",
			args.invert,
			args.normalize,
			args.slice_start,
			args.slice_end
		)

	if args.ldr_output:
		ldr_scale = args.ldr_scale if args.ldr_scale is not None else scale
		ldr_scale_y = args.ldr_scale_y if args.ldr_scale_y is not None else args.scale_y
		ldr_volume = hcb.volume.scale_volume(base_volume, ldr_scale, ldr_scale_y)
		bricks = hcb.ldraw.volume_to_bricks(ldr_volume, args.ldr_threshold)
		title = f"{args.prefix}{args.dimension}"
		hcb.ldraw.write_ldraw(bricks, args.ldr_output, args.ldr_color, title)


#============================================
if __name__ == '__main__':
	main()
