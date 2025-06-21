# pyright: reportUnsupportedDunderAll=false
"""
ZeusDB - A modular database ecosystem.

This package provides lazy access to database modules like `VectorDatabase`,
which are optionally installable plugins. Modules are only imported when
accessed, and their versions are checked against PyPI for freshness.

Example:
    >>> from zeusdb import VectorDatabase  # Only imports if zeusdb-vector-database is installed
    >>> db = VectorDatabase()

Available database types are dynamically determined based on installed packages.
If a required package is missing, helpful installation instructions are provided.

Environment Variables:
    ZEUSDB_SKIP_VERSION_CHECK: Set to '1' to disable version checking
    CI / PYTHONOFFLINE / NO_NETWORK / ZEUSDB_OFFLINE_MODE: 
        These common environment flags also automatically disable version checks 
        in CI pipelines or offline environments.
"""
from typing import Any
from ._utils import import_database_class

__version__ = "0.0.3"

# Explicit export list to satisfy Pylance and other static analyzers
__all__ = [
    "__version__",
    "VectorDatabase",
    # "RelationalDatabase",      # Uncomment when supported
    # "GraphDatabase",           # Uncomment when supported
    # "DocumentDatabase",        # Uncomment when supported
]

def __getattr__(name: str) -> Any:
    """Dynamically import database classes on first access."""
    try:
        return import_database_class(name)
    except AttributeError:
        raise AttributeError(f"module 'zeusdb' has no attribute '{name}'")


def __dir__():
    """Return available attributes for tab completion."""
    return __all__
