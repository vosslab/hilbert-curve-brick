"""
Volume generation and PNG helpers.
"""

# Standard Library
import math
import os

# PIP3 modules
import numpy
import scipy.ndimage

# local repo modules
import hilbert_curve_brick.color
import hilbert_curve_brick.curve
import leginon.imagefile


#============================================
# MODEL LAYER
# Functions below build and manipulate the integer model volume.
# The model stores integer labels only:
#   0         -- empty voxel
#   index + 1 -- occupied voxel at curve step `index`
# Connector voxels (midpoints between two adjacent curve points) inherit
# the earlier curve point's label: a connector between step k and k+1
# stores k + 1 (the earlier point's label).
# No display values (grayscale, RGB) are stored here; those are produced
# at render time in the RENDERING LAYER below.
#============================================


#============================================
def build_curve_volume(dimension: int) -> numpy.ndarray:
	"""
	Build a 3D integer volume containing the Hilbert path.

	Occupied voxels store index + 1 where index is the curve step (0-based).
	Connector voxels between step k-1 and step k store k (the earlier step's
	label, which is (k-1)+1 = k), so the occupied path is non-decreasing and
	strict increase holds across actual curve points.

	Args:
		dimension: Hilbert dimension per axis.

	Returns:
		numpy.ndarray: int32 3D volume with 0 empty and index+1 at occupied voxels.
	"""
	# Allocate a cubic volume with a 1-voxel border.
	max_dim = dimension * 2 + 1
	volume = numpy.zeros((max_dim, max_dim, max_dim), dtype=numpy.int32)
	last_coord = None
	for index in range(dimension ** 3):
		# Use even coordinates to leave room for connector voxels between steps.
		coord = 2 * numpy.array(hilbert_curve_brick.curve.int_to_hilbert(index, 3), dtype=int)
		# Label is index + 1 so 0 stays unambiguously empty.
		label = index + 1
		volume[coord[0] + 1, coord[1] + 1, coord[2] + 1] = label
		if last_coord is not None:
			# Fill the midpoint between steps to keep the curve connected.
			# The connector between step index-1 and step index inherits the
			# EARLIER point's label: (index-1) + 1 = index.
			mid = (coord + last_coord) // 2
			volume[mid[0] + 1, mid[1] + 1, mid[2] + 1] = index
		last_coord = coord
	return volume


#============================================
def grid_params(scale: int) -> tuple[int, int]:
	"""
	Return (step, offset) grid parameters for the given render scale.

	The box pitch (distance between box centers after scaling) is scale*2 pixels.
	Setting the first grid line at scale//2 places each line halfway between
	neighboring box centers, so every black square lands centered in its cell.

	Args:
		scale: Block-replication scale factor (power of two).

	Returns:
		tuple: (step, offset) where step = scale*2 and offset = scale//2.
	"""
	step = scale * 2
	offset = scale // 2
	return step, offset


#============================================
def build_grid_mask(shape: tuple, step: int, offset: int) -> numpy.ndarray:
	"""
	Build a boolean mask marking grid planes on axis 0 and axis 2.

	Grid lines are placed at positions offset + k * step along each axis.
	Axis 0 (x) and axis 2 (z) receive grid planes (matching the old
	apply_grid_overlay which wrote volume[line,:,:] and volume[:,:,line]).
	The mask is kept separate from the model volume so the grid is a
	render-time overlay and never contaminates model labels.

	Args:
		shape: Shape tuple (size0, size1, size2) of the target volume.
		step: Pixel distance between grid lines.
		offset: Pixel position of the first grid line.

	Returns:
		numpy.ndarray: bool array of the same shape; True where a grid line falls.
	"""
	mask = numpy.zeros(shape, dtype=bool)
	# Axis 0 (x) grid planes: walk from the first gap center to the axis-0 edge.
	line = offset
	while line < shape[0]:
		mask[line, :, :] = True
		line += step
	# Axis 2 (z) grid planes: walk independently to the axis-2 edge.
	line = offset
	while line < shape[2]:
		mask[:, :, line] = True
		line += step
	return mask


#============================================
def compute_scale(dimension: int, target_size: int) -> int:
	"""
	Compute a power-of-two scale for the requested target size.

	Args:
		dimension: Hilbert dimension per axis.
		target_size: Desired maximum size.

	Returns:
		int: Power-of-two scale factor.
	"""
	# Match the target size with a power-of-two scale.
	raw_scale = target_size / float((dimension * 2) + 2)
	scale_factor = int(math.floor(math.log(raw_scale, 2)))
	if scale_factor < 0:
		scale_factor = 0
	scale = 2 ** scale_factor
	return scale


#============================================
def scale_volume(volume: numpy.ndarray, scale: int, scale_y: int) -> numpy.ndarray:
	"""
	Scale the volume with nearest-neighbor interpolation.

	Uses grid_mode block replication so each base voxel maps to exactly
	`scale` output pixels. Integer labels are preserved exactly because
	order=0 nearest-neighbor never interpolates between labels.

	Args:
		volume: Input volume (integer labels or float).
		scale: Scale factor for X and Z.
		scale_y: Scale factor for Y.

	Returns:
		numpy.ndarray: Scaled volume with the same dtype as input.
	"""
	scales = (scale, scale_y, scale)
	# Use grid_mode block replication so each base voxel maps to exactly
	# `scale` output pixels. The default (grid_mode=False) maps by
	# (n_out-1)/(n_in-1), which stretches the pitch slightly and makes the
	# fixed-step grid overlay drift onto boxes across the image.
	scaled = scipy.ndimage.zoom(volume, scales, order=0, grid_mode=True, mode='grid-constant')
	return scaled


#============================================
def iter_slices(volume: numpy.ndarray, axis: str, start: int, end: int) -> tuple:
	"""
	Iterate slices along a specific axis.

	Args:
		volume: Input volume.
		axis: Axis label ('x', 'y', 'z').
		start: First slice index.
		end: End slice index (exclusive).

	Returns:
		tuple: (slice_index, slice_array).
	"""
	axis_map = {'x': 0, 'y': 1, 'z': 2}
	axis_index = axis_map[axis]
	max_slices = volume.shape[axis_index]
	start_index = max(0, start)
	end_index = end
	if end_index < 0:
		end_index = max_slices + end_index + 1
	end_index = min(end_index, max_slices)
	for slice_index in range(start_index, end_index):
		if axis_index == 0:
			slice_array = volume[slice_index, :, :]
		elif axis_index == 1:
			slice_array = volume[:, slice_index, :]
		else:
			slice_array = volume[:, :, slice_index]
		yield slice_index, slice_array


#============================================
# RENDERING LAYER
# Functions below convert integer model slices to display values.
# Display values (grayscale uint8 and RGB uint8) are produced here, never
# stored in the model. The integer volume carries only 0 (empty) and index+1
# (occupied); all color encoding happens at slice-write time.
#============================================

# Gray value for grid overlay pixels (matches the visual equivalence rule:
# classify by nearest of white/gray/black; 128 is unambiguously mid-gray).
_GRID_GRAY = 128


#============================================
def slice_to_grayscale(
		label_slice: numpy.ndarray,
		grid_slice: numpy.ndarray | None
	) -> numpy.ndarray:
	"""
	Convert one integer label slice to a grayscale uint8 display array.

	Display values are produced here; the model stores only integer labels.
	Category encoding:
	  - empty voxels (label == 0)  -> 255 (white)
	  - occupied voxels (label > 0) -> 0 (black)
	  - grid pixels (grid_slice True) -> 128 (gray), drawn last so grid shows
	    over both empty and occupied cells, matching the old apply_grid_overlay
	    behavior which set 0.5 unconditionally on every grid plane pixel.

	Args:
		label_slice: 2D int32 array from the integer volume (0 empty, >0 occupied).
		grid_slice: 2D bool array of the same shape, or None for no grid overlay.

	Returns:
		numpy.ndarray: (h, w) uint8 display array.
	"""
	# Start with white background (empty = 255).
	display = numpy.full(label_slice.shape, 255, dtype=numpy.uint8)
	# Set occupied voxels to black.
	display[label_slice > 0] = 0
	# Draw grid over everything (matches old unconditional grid plane write).
	if grid_slice is not None:
		display[grid_slice] = _GRID_GRAY
	return display


#============================================
def slice_to_rgb(
		label_slice: numpy.ndarray,
		grid_slice: numpy.ndarray | None,
		total: int,
		palette: list,
		n_bands: int
	) -> numpy.ndarray:
	"""
	Convert one integer label slice to an RGB uint8 display array.

	Display values are produced here; the model stores only integer labels.
	Category encoding:
	  - empty voxels  -> (255, 255, 255) white
	  - occupied voxels -> palette color for the voxel's curve band
	  - grid pixels    -> (128, 128, 128) gray, drawn last

	Args:
		label_slice: 2D int32 array (0 empty, >0 occupied with label = index+1).
		grid_slice: 2D bool array of the same shape, or None for no grid overlay.
		total: Total number of curve steps (dimension**3), passed by the caller.
		palette: List of 16 (r, g, b) int triples loaded from the YAML palette.
		n_bands: Number of discrete color bands (normally 16).

	Returns:
		numpy.ndarray: (h, w, 3) uint8 display array.
	"""
	height, width = label_slice.shape
	# Start with white background.
	display = numpy.full((height, width, 3), 255, dtype=numpy.uint8)
	# Color each occupied voxel by its curve band.
	# Build a per-pixel band lookup: label -> band index.
	occupied_mask = label_slice > 0
	occupied_labels = label_slice[occupied_mask]
	if occupied_labels.size > 0:
		# Map each occupied label to a band index (label - 1 = curve index).
		bands = numpy.array(
			[hilbert_curve_brick.color.index_to_band(int(lbl) - 1, total, n_bands) for lbl in occupied_labels],
			dtype=numpy.int32
		)
		# Build a color lookup table from the palette for vectorized assignment.
		palette_array = numpy.array(palette, dtype=numpy.uint8)
		# Assign RGB for each occupied pixel using the band table.
		display[occupied_mask] = palette_array[bands]
	# Draw grid over everything.
	if grid_slice is not None:
		display[grid_slice, 0] = _GRID_GRAY
		display[grid_slice, 1] = _GRID_GRAY
		display[grid_slice, 2] = _GRID_GRAY
	return display


#============================================
def write_slices(
		volume: numpy.ndarray,
		axis: str,
		output_dir: str,
		prefix: str,
		slice_start: int,
		slice_end: int,
		color: bool,
		grid_mask: numpy.ndarray | None = None,
		palette: list | None = None,
		total: int | None = None
	) -> None:
	"""
	Write PNG slices from the integer volume to disk.

	Iterates slices along the given axis, converts each to a grayscale or RGB
	uint8 display array, and writes it with array_to_png(normalize=False).
	Display values are produced here from the integer model; the model itself
	stores no display information.

	Args:
		volume: Integer model volume (0 empty, index+1 at occupied voxels).
		axis: Axis label ('x', 'y', 'z').
		output_dir: Directory for output PNG files.
		prefix: Filename prefix for each slice.
		slice_start: First slice index.
		slice_end: End slice index (exclusive).
		color: True for 16-band rainbow RGB output, False for grayscale mono.
		grid_mask: Optional bool volume matching the model volume shape.
		palette: 16-entry list of (r, g, b) tuples; required when color=True.
		total: Total curve steps (dimension**3); required when color=True.

	Raises:
		ValueError: When color=True and palette or total is not provided.
	"""
	if color and palette is None:
		raise ValueError("write_slices: palette is required for color=True")
	if color and total is None:
		raise ValueError("write_slices: total is required for color=True")

	os.makedirs(output_dir, exist_ok=True)

	# Slice the grid mask along the same axis as the volume when provided.
	grid_slices = iter_slices(grid_mask, axis, slice_start, slice_end) if grid_mask is not None else None

	for slice_index, label_slice in iter_slices(volume, axis, slice_start, slice_end):
		# Pull the matching grid slice if one is available.
		if grid_slices is not None:
			_, grid_slice = next(grid_slices)
		else:
			grid_slice = None

		if color:
			# Build RGB uint8 array then scale to 0-1 for array_to_png(normalize=False).
			uint8_array = slice_to_rgb(label_slice, grid_slice, total, palette, hilbert_curve_brick.color.N_BANDS)
			# leginon.imagefile.array_to_png with normalize=False expects values in [0,1],
			# so display uint8 (0/128/255) is divided by 255.0 to map into that range.
			output_array = uint8_array.astype(numpy.float32) / 255.0
		else:
			# Build grayscale uint8 array then scale to 0-1 for array_to_png(normalize=False).
			uint8_array = slice_to_grayscale(label_slice, grid_slice)
			# leginon.imagefile.array_to_png with normalize=False expects values in [0,1],
			# so display uint8 (0/128/255) is divided by 255.0 to map into that range.
			output_array = uint8_array.astype(numpy.float32) / 255.0

		filename = f"{prefix}-{slice_index:03d}.png"
		output_path = os.path.join(output_dir, filename)
		leginon.imagefile.array_to_png(output_array, output_path, normalize=False)
