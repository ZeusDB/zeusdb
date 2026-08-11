# pyright: reportUnsupportedDunderAll=false
"""
ZeusDB - A modular database ecosystem.

This package is the public entry point for the ZeusDB products. It re-exports
the public surface of `zeusdb-vector-database`, which is the only ZeusDB
product today, and imports it only when one of those names is first touched.

Example:
    >>> from zeusdb import VectorDatabase
    >>> vdb = VectorDatabase()

The lazy import is deliberate. Importing `zeusdb_vector_database` loads a Rust
extension, sets `ZEUSDB_LOG_LEVEL`, `ZEUSDB_LOG_FORMAT` and `ZEUSDB_LOG_TARGET`
in the process environment, and installs a handler on the `zeusdb.vector`
logger. Deferring that until a caller asks for a name keeps `import zeusdb`
free of side effects, and keeps it working when the vector database is not
installed. If a name is missing, the raised error names the package to install.

Structured logging helpers live in the `zeusdb.logging_config` submodule, which
is imported separately and is not part of `__all__`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any

__version__ = "0.1.0"

# The names re-exported from zeusdb-vector-database. This is exactly that
# package's own `__all__` at 0.5.0, less `__version__`, which the umbrella
# defines for itself above.
#
# HNSWIndex and AddResult cannot be constructed directly; they are here so a
# caller can name the types `create()` and `add()` hand back. The three logging
# functions are here because the documented logging recipe calls them at
# package level.
_VECTOR_DATABASE_EXPORTS = (
    "AddResult",
    "HNSWIndex",
    "VectorDatabase",
    "init_file_logging",
    "init_logging",
    "is_logging_initialized",
)

# Exported name -> (pip package name for the install hint, module to import).
# The attribute name inside the module matches the exported name in every case.
# A second product is added by extending this mapping and `__all__` together;
# `test_surface.py` fails when the two disagree.
_PACKAGE_MAP: dict[str, tuple[str, str]] = {
    name: ("zeusdb-vector-database", "zeusdb_vector_database")
    for name in _VECTOR_DATABASE_EXPORTS
}

# Explicit export list for static analysers and tab completion.
__all__ = [
    "AddResult",
    "HNSWIndex",
    "VectorDatabase",
    "__version__",
    "init_file_logging",
    "init_logging",
    "is_logging_initialized",
]


def __getattr__(name: str) -> Any:
    """Import a re-exported name from its providing package on first access."""
    entry = _PACKAGE_MAP.get(name)
    if entry is None:
        raise AttributeError(
            f"module 'zeusdb' has no attribute '{name}'. "
            f"Available attributes: {', '.join(__all__)}"
        )

    package, module_name = entry
    try:
        module = __import__(module_name, fromlist=[name])
        value = getattr(module, name)
    except ImportError as e:
        raise ImportError(
            f"{name} requires {package} package.\n"
            f"Install with one of:\n"
            f"  uv pip install {package}\n"
            f"  pip install {package}\n"
            f"Original error: {e}"
        ) from e

    # Cache on the module so __getattr__ runs once per name (PEP 562).
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    """Return available attributes for tab completion."""
    return sorted(__all__)
