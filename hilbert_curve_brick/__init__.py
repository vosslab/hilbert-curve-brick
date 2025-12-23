"""
Hilbert curve helpers for LEGO-compatible brick outputs.
"""

# Standard Library
import importlib


__all__ = ["cli", "curve", "ldraw", "volume"]


#============================================
def __getattr__(name: str):
	"""
	Lazy-load submodules to keep the top-level namespace lightweight.

	Args:
		name: Attribute name to load.

	Returns:
		module: Imported module.
	"""
	if name in __all__:
		module = importlib.import_module(f"{__name__}.{name}")
		globals()[name] = module
		return module
	raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
