#!/usr/bin/env python3
"""
Generate 3D Hilbert curve outputs for LEGO-compatible brick builds.
"""

# local repo modules
import hilbert_curve_brick.cli
import hilbert_curve_brick.color
import hilbert_curve_brick.ldraw
import hilbert_curve_brick.volume


#============================================
def main() -> None:
	"""
	Script entry point.
	"""
	args = hilbert_curve_brick.cli.parse_args()
	hilbert_curve_brick.cli.validate_args(args)

	# Build the curve in a base voxel grid, then enlarge it with integer block
	# scaling. SCALE_Y stays separate so the Y axis can keep its own factor.
	base_volume = hilbert_curve_brick.volume.build_curve_volume(args.dimension)
	scale = hilbert_curve_brick.volume.compute_scale(args.dimension, args.target_size)
	scaled_volume = hilbert_curve_brick.volume.scale_volume(
		base_volume, scale, hilbert_curve_brick.cli.SCALE_Y)

	# Build the grid mask separately from the model volume when enabled.
	# The grid is a render-time overlay; it never mutates the integer volume.
	grid_mask = None
	if args.add_grid:
		# Box voxels sit two base units apart, so after block scaling the pitch
		# between box centers is scale*2 pixels (the grid step). Offsetting the
		# first line by half a box (scale // 2) puts every line halfway between
		# neighboring box centers, so each black square ends up centered in its
		# grid cell.
		step, offset = hilbert_curve_brick.volume.grid_params(scale)
		grid_mask = hilbert_curve_brick.volume.build_grid_mask(scaled_volume.shape, step, offset)

	# Load the palette and total for color mode; both are required by write_slices
	# and write_ldraw when color=True.
	palette = None
	total = None
	if args.color:
		palette = hilbert_curve_brick.color.load_palette()
		total = args.dimension ** 3

	# PNG slices are always written. Pass grid_mask and color routing to write_slices.
	hilbert_curve_brick.volume.write_slices(
		scaled_volume,
		hilbert_curve_brick.cli.AXIS,
		args.output_dir,
		f"{hilbert_curve_brick.cli.PREFIX}{args.dimension}",
		hilbert_curve_brick.cli.SLICE_START,
		hilbert_curve_brick.cli.SLICE_END,
		args.color,
		grid_mask=grid_mask,
		palette=palette,
		total=total,
	)

	# LDraw output is optional and reuses the unscaled base volume, scaled with
	# the same factors so the brick model matches the PNG geometry.
	if args.ldr_output:
		ldr_volume = hilbert_curve_brick.volume.scale_volume(
			base_volume, scale, hilbert_curve_brick.cli.SCALE_Y)
		bricks = hilbert_curve_brick.ldraw.volume_to_bricks(ldr_volume)
		title = f"{hilbert_curve_brick.cli.PREFIX}{args.dimension}"
		if args.color:
			# In color mode pass palette and total so each brick gets a direct-color code.
			ldr_total = args.dimension ** 3
			hilbert_curve_brick.ldraw.write_ldraw(
				bricks, args.ldr_output, hilbert_curve_brick.cli.LDR_COLOR, title,
				palette=palette, total=ldr_total)
		else:
			# Mono mode: single integer color for all bricks.
			hilbert_curve_brick.ldraw.write_ldraw(
				bricks, args.ldr_output, hilbert_curve_brick.cli.LDR_COLOR, title)


#============================================
if __name__ == '__main__':
	main()
