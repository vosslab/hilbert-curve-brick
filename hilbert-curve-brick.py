#!/usr/bin/env python3
"""
Generate 3D Hilbert curve outputs for LEGO-compatible brick builds.
"""

# Standard Library

# local repo modules
import hilbert_curve_brick.cli
import hilbert_curve_brick.volume
import hilbert_curve_brick.ldraw


#============================================
def main() -> None:
	"""
	Script entry point.
	"""
	args = hilbert_curve_brick.cli.parse_args()
	hilbert_curve_brick.cli.validate_args(args)

	# Build the curve in a base voxel grid, then enlarge it with integer block
	# scaling. SCALE_Y stays separate so the Y axis can keep its own factor.
	base_volume = hilbert_curve_brick.volume.build_hilbert_volume(args.dimension)
	scale = hilbert_curve_brick.volume.compute_scale(args.dimension, args.target_size)
	scaled_volume = hilbert_curve_brick.volume.scale_volume(
		base_volume, scale, hilbert_curve_brick.cli.SCALE_Y)

	# PNG slices are always written. Optionally overlay the cell grid first.
	png_volume = scaled_volume
	if args.add_grid:
		# Box voxels sit two base units apart, so after block scaling the pitch
		# between box centers is scale*2 pixels (the grid step). Offsetting the
		# first line by half a box (scale // 2) puts every line halfway between
		# neighboring box centers, so each black square ends up centered in its
		# grid cell. Copy first so the grid does not mutate the LDraw volume.
		grid_step = scale * 2
		grid_offset = scale // 2
		png_volume = hilbert_curve_brick.volume.apply_grid_overlay(
			png_volume.copy(), grid_step, grid_offset)
	hilbert_curve_brick.volume.write_slices(
		png_volume,
		hilbert_curve_brick.cli.AXIS,
		args.output_dir,
		f"{hilbert_curve_brick.cli.PREFIX}{args.dimension}",
		hilbert_curve_brick.cli.INVERT,
		hilbert_curve_brick.cli.NORMALIZE,
		hilbert_curve_brick.cli.SLICE_START,
		hilbert_curve_brick.cli.SLICE_END
	)

	# LDraw output is optional and reuses the unscaled base volume, scaled with
	# the same factors so the brick model matches the PNG geometry.
	if args.ldr_output:
		ldr_volume = hilbert_curve_brick.volume.scale_volume(
			base_volume, scale, hilbert_curve_brick.cli.SCALE_Y)
		bricks = hilbert_curve_brick.ldraw.volume_to_bricks(
			ldr_volume, hilbert_curve_brick.cli.LDR_THRESHOLD)
		title = f"{hilbert_curve_brick.cli.PREFIX}{args.dimension}"
		hilbert_curve_brick.ldraw.write_ldraw(
			bricks, args.ldr_output, hilbert_curve_brick.cli.LDR_COLOR, title)


#============================================
if __name__ == '__main__':
	main()
