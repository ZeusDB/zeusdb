# pyright: reportUnsupportedDunderAll=false
"""
ZeusDB - A modular database ecosystem.

This package provides lazy access to database modules like `VectorDatabase`,
which are optionally installable plugins. Modules are only imported when accessed.

Example:
    >>> from zeusdb import VectorDatabase  # Only imports if zeusdb-vector-database is installed
    >>> vdb = VectorDatabase()

Available database types are dynamically determined based on installed packages.
If a required package is missing, helpful installation instructions are provided.
"""
from typing import Any

__version__ = "0.0.7"

# Package mapping for extensibility
_PACKAGE_MAP = {
    "VectorDatabase": {
        "package": "zeusdb-vector-database", # For pip installation instructions
        "module": "zeusdb_vector_database", # Python import path (what import uses)
        "class": "VectorDatabase" # The class name inside the module
    },
    # Future packages:

}

# Explicit export list for static analysers and tab completion
__all__ = [
    "__version__",
    *_PACKAGE_MAP.keys(),  # Automatically sync with package map
]

def __getattr__(name: str) -> Any:
    """Dynamically import database classes on first access."""
    if name in _PACKAGE_MAP:
        config = _PACKAGE_MAP[name]
        try:
            module = __import__(config["module"], fromlist=[config["class"]])
            return getattr(module, config["class"])
        except ImportError as e:
            raise ImportError(
                f"{name} requires {config['package']} package.\n"
                f"Install with one of:\n"
                f"  uv pip install {config['package']}\n"
                f"  pip install {config['package']}\n"
                f"Original error: {e}"
            ) from e
    
    # Provide helpful message for unknown attributes
    available = [k for k in _PACKAGE_MAP.keys()]
    raise AttributeError(
        f"module 'zeusdb' has no attribute '{name}'. "
        f"Available attributes: {', '.join(available)}"
    )


def __dir__():
    """Return available attributes for tab completion."""
    return __all__
