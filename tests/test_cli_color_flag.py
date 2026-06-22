"""
CLI color flag tests.

The -c/--color and -C/--mono flags control args.color. Default is mono (False).
These tests cover the three user-facing cases: explicit color, explicit mono,
and the default.
"""

# local repo modules
import hilbert_curve_brick.cli


#============================================
def test_color_flag_sets_color_true() -> None:
	"""
	Passing -c yields args.color True.
	"""
	args = hilbert_curve_brick.cli.parse_args(['-d', '8', '-c'])
	assert args.color is True


#============================================
def test_mono_flag_sets_color_false() -> None:
	"""
	Passing -C yields args.color False.
	"""
	args = hilbert_curve_brick.cli.parse_args(['-d', '8', '-C'])
	assert args.color is False


#============================================
def test_default_color_is_false() -> None:
	"""
	When no color flag is passed, args.color defaults to False (mono).
	"""
	args = hilbert_curve_brick.cli.parse_args(['-d', '8'])
	assert args.color is False
