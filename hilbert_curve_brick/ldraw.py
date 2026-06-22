"""
LDraw export helpers.
"""

# Standard Library
import os

# PIP3 modules
import numpy

# local repo modules
import hilbert_curve_brick.color


CELL_LDU = 40
BRICK_HEIGHT_LDU = 24

ROT_IDENTITY = (1, 0, 0, 0, 1, 0, 0, 0, 1)
ROT_Y_90 = (0, 0, 1, 0, 1, 0, -1, 0, 0)

PART_2X2 = {
	"id": "3003.dat",
	"size_x": 1,
	"size_z": 1,
	"height": 1,
}
PART_2X4 = {
	"id": "3001.dat",
	"size_x": 2,
	"size_z": 1,
	"height": 1,
}
PART_2X6 = {
	"id": "2456.dat",
	"size_x": 3,
	"size_z": 1,
	"height": 1,
}
PART_2X2X3 = {
	"id": "30145.dat",
	"size_x": 1,
	"size_z": 1,
	"height": 3,
}


#============================================
def volume_to_bricks(volume: numpy.ndarray) -> list:
	"""
	Convert an integer volume into LDraw brick placements.

	Occupancy is read as ``volume > 0``.  Each brick records the integer
	label of its anchor cell (the cell that starts the brick in the
	greedy sweep).  The label equals ``curve_index + 1``, so
	``label - 1`` gives the 0-based curve index for band mapping.

	Args:
		volume: Integer model volume (0 empty, index+1 at occupied voxels).

	Returns:
		list: Brick placement dictionaries, each containing 'label'.
	"""
	# Occupancy is any non-zero label in the integer volume.
	occupied = volume > 0
	covered = numpy.zeros(occupied.shape, dtype=numpy.bool_)
	bricks = []

	x_size, y_size, z_size = occupied.shape

	# Place 2x2x3 bricks on vertical runs first.
	for y_index in range(0, y_size - 2):
		for z_index in range(z_size):
			for x_index in range(x_size):
				if not occupied[x_index, y_index, z_index]:
					continue
				if covered[x_index, y_index, z_index]:
					continue
				if covered[x_index, y_index + 1, z_index]:
					continue
				if covered[x_index, y_index + 2, z_index]:
					continue
				if not occupied[x_index, y_index + 1, z_index]:
					continue
				if not occupied[x_index, y_index + 2, z_index]:
					continue
				# Anchor label: the integer label at this brick's starting cell.
				anchor_label = int(volume[x_index, y_index, z_index])
				brick = _make_brick(
					PART_2X2X3,
					x_index,
					y_index,
					z_index,
					rot=ROT_IDENTITY,
					anchor_label=anchor_label,
				)
				bricks.append(brick)
				covered[x_index, y_index, z_index] = True
				covered[x_index, y_index + 1, z_index] = True
				covered[x_index, y_index + 2, z_index] = True

	# Tile remaining cells with 2x6, 2x4, and 2x2 bricks.
	for y_index in range(y_size):
		layer_occ = occupied[:, y_index, :]
		layer_covered = covered[:, y_index, :]
		layer_vol = volume[:, y_index, :]
		layer_bricks = _tile_layer(layer_occ, layer_covered, layer_vol, y_index)
		bricks.extend(layer_bricks)

	return bricks


#============================================
def write_ldraw(
		bricks: list,
		output_path: str,
		color: int,
		title: str,
		palette: list | None = None,
		total: int | None = None,
		n_bands: int = 16,
	) -> None:
	"""
	Write LDraw bricks to a file.

	When ``palette`` and ``total`` are given, each brick is colored by the
	direct-color code ``0x2RRGGBB`` for the band of its anchor cell.  The
	band is determined by ``color.index_to_band(label - 1, total, n_bands)``
	where ``label`` is the anchor cell's integer label (``index + 1``).
	When ``palette`` is None, the single integer ``color`` applies to every
	brick (mono mode).

	Args:
		bricks: Brick placement dictionaries (each must contain 'label').
		output_path: Output path.
		color: LDraw color index used in mono mode.
		title: Model title.
		palette: Optional list of 16 (r, g, b) triples for rainbow mode.
		total: Total number of curve steps (required when palette is given).
		n_bands: Number of color bands (default 16).
	"""
	# Guard: palette requires total to compute per-brick band indices.
	if palette is not None and total is None:
		raise ValueError("write_ldraw: total is required when palette is given")

	lines = []
	lines.append(f"0 FILE {os.path.basename(output_path)}")
	lines.append(f"0 Name: {title}")
	lines.append("0 Author: hilbert-curve-brick")
	lines.append("0 !LDRAW_ORG Unofficial_Model")
	lines.append("0 !LICENSE Redistributable under CC BY-SA 4.0")

	for brick in bricks:
		if palette is not None:
			# Rainbow mode: map this brick's anchor label to a band, then look up
			# the direct color.  label is index+1, so label-1 is the 0-based index.
			# Merged bricks spanning multiple bands color by their anchor cell's band;
			# anchor-cell coloring is intentional for merged bricks.
			band = hilbert_curve_brick.color.index_to_band(brick["label"] - 1, total, n_bands)
			rgb = palette[band]
			brick_color = hilbert_curve_brick.color.rgb_to_ldraw_direct(rgb)
		else:
			# Mono mode: apply the single integer color to every brick.
			brick_color = color
		line = _format_brick_line(brick, brick_color)
		lines.append(line)

	output_dir = os.path.dirname(output_path)
	if output_dir:
		os.makedirs(output_dir, exist_ok=True)

	with open(output_path, "w", encoding="ascii") as handle:
		handle.write("\n".join(lines))
		handle.write("\n")


#============================================
def _tile_layer(
		layer_occ: numpy.ndarray,
		layer_covered: numpy.ndarray,
		layer_vol: numpy.ndarray,
		y_index: int,
	) -> list:
	"""
	Greedily tile a layer with 2x6, 2x4, and 2x2 bricks.

	Args:
		layer_occ: Occupancy for this layer.
		layer_covered: Coverage mask for this layer.
		layer_vol: Integer volume slice for this layer (for anchor labels).
		y_index: Layer index.

	Returns:
		list: Brick placement dictionaries.
	"""
	x_size, z_size = layer_occ.shape
	bricks = []
	for z_index in range(z_size):
		for x_index in range(x_size):
			if not layer_occ[x_index, z_index]:
				continue
			if layer_covered[x_index, z_index]:
				continue

			# Anchor label from the integer volume at this cell.
			anchor_label = int(layer_vol[x_index, z_index])

			if _can_place(layer_occ, layer_covered, x_index, z_index, 3, 1):
				brick = _make_brick(
					PART_2X6, x_index, y_index, z_index, ROT_IDENTITY,
					anchor_label=anchor_label,
				)
				bricks.append(brick)
				_mark(layer_covered, x_index, z_index, 3, 1)
				continue
			if _can_place(layer_occ, layer_covered, x_index, z_index, 1, 3):
				brick = _make_brick(
					PART_2X6, x_index, y_index, z_index, ROT_Y_90, 1, 3,
					anchor_label=anchor_label,
				)
				bricks.append(brick)
				_mark(layer_covered, x_index, z_index, 1, 3)
				continue
			if _can_place(layer_occ, layer_covered, x_index, z_index, 2, 1):
				bricks.append(_make_brick(PART_2X4, x_index, y_index, z_index, ROT_IDENTITY, anchor_label=anchor_label))
				_mark(layer_covered, x_index, z_index, 2, 1)
				continue
			if _can_place(layer_occ, layer_covered, x_index, z_index, 1, 2):
				bricks.append(_make_brick(PART_2X4, x_index, y_index, z_index, ROT_Y_90, 1, 2, anchor_label=anchor_label))
				_mark(layer_covered, x_index, z_index, 1, 2)
				continue
			bricks.append(_make_brick(PART_2X2, x_index, y_index, z_index, ROT_IDENTITY, anchor_label=anchor_label))
			layer_covered[x_index, z_index] = True

	return bricks


#============================================
def _can_place(
		layer_occ: numpy.ndarray,
		layer_covered: numpy.ndarray,
		start_x: int,
		start_z: int,
		size_x: int,
		size_z: int
	) -> bool:
	"""
	Check whether a brick fits on a layer.

	Args:
		layer_occ: Occupancy for this layer.
		layer_covered: Coverage mask for this layer.
		start_x: X cell index.
		start_z: Z cell index.
		size_x: Size in X cells.
		size_z: Size in Z cells.

	Returns:
		bool: True if the brick can be placed.
	"""
	x_size, z_size = layer_occ.shape
	if start_x + size_x > x_size:
		return False
	if start_z + size_z > z_size:
		return False
	for dz in range(size_z):
		for dx in range(size_x):
			x_index = start_x + dx
			z_index = start_z + dz
			if not layer_occ[x_index, z_index]:
				return False
			if layer_covered[x_index, z_index]:
				return False
	return True


#============================================
def _mark(
		layer_covered: numpy.ndarray,
		start_x: int,
		start_z: int,
		size_x: int,
		size_z: int
	) -> None:
	"""
	Mark a brick footprint as covered.

	Args:
		layer_covered: Coverage mask for this layer.
		start_x: X cell index.
		start_z: Z cell index.
		size_x: Size in X cells.
		size_z: Size in Z cells.
	"""
	for dz in range(size_z):
		for dx in range(size_x):
			layer_covered[start_x + dx, start_z + dz] = True


#============================================
def _make_brick(
		part: dict,
		x_index: int,
		y_index: int,
		z_index: int,
		rot: tuple,
		size_x: int | None = None,
		size_z: int | None = None,
		anchor_label: int = 0,
	) -> dict:
	"""
	Create a brick placement record.

	The ``anchor_label`` is the integer label from the model volume at the
	brick's starting cell.  It equals ``curve_index + 1``, so
	``anchor_label - 1`` gives the 0-based curve index used for band
	mapping.  When the greedy merger assembles a brick that spans multiple
	curve bands, the anchor-cell band is used (a minor seam the user
	accepts).

	Args:
		part: Part definition dictionary.
		x_index: X cell index.
		y_index: Y cell index.
		z_index: Z cell index.
		rot: Rotation matrix.
		size_x: Override size in X cells.
		size_z: Override size in Z cells.
		anchor_label: Integer label at the anchor cell (default 0 for empty).

	Returns:
		dict: Brick placement including 'label'.
	"""
	if size_x is None:
		size_x = part["size_x"]
	if size_z is None:
		size_z = part["size_z"]

	width_x = size_x * CELL_LDU
	width_z = size_z * CELL_LDU
	height = part["height"] * BRICK_HEIGHT_LDU

	x_ldu = x_index * CELL_LDU + (width_x // 2)
	y_ldu = y_index * BRICK_HEIGHT_LDU + (height // 2)
	z_ldu = z_index * CELL_LDU + (width_z // 2)

	brick = {
		"part": part["id"],
		"x": x_ldu,
		"y": y_ldu,
		"z": z_ldu,
		"rot": rot,
		"label": anchor_label,
	}
	return brick


#============================================
def _format_brick_line(brick: dict, color: object) -> str:
	"""
	Format a brick placement as an LDraw line.

	``color`` may be an integer (mono mode) or a direct-color string such as
	``"0x2RRGGBB"`` (rainbow mode).  Both are written verbatim into the
	LDraw type-1 line.

	Args:
		brick: Brick placement dictionary.
		color: LDraw color index (int) or direct-color string (str).

	Returns:
		str: LDraw line string.
	"""
	rot = brick["rot"]
	parts = [
		"1",
		str(color),
		str(brick["x"]),
		str(brick["y"]),
		str(brick["z"]),
		str(rot[0]),
		str(rot[1]),
		str(rot[2]),
		str(rot[3]),
		str(rot[4]),
		str(rot[5]),
		str(rot[6]),
		str(rot[7]),
		str(rot[8]),
		brick["part"],
	]
	line = " ".join(parts)
	return line
