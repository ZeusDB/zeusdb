"""
Internal utilities for ZeusDB package management.
"""
import json
import os
import urllib.request
import warnings
from functools import lru_cache
from typing import Optional, Any
from importlib.metadata import version, PackageNotFoundError


@lru_cache(maxsize=None)
def get_latest_pypi_version(package: str) -> Optional[str]:
    """
    Get latest version from PyPI with caching and error handling.
    
    Args:
        package: Package name on PyPI
        
    Returns:
        Latest version string or None if unable to fetch
    """
    try:
        url = f"https://pypi.org/pypi/{package}/json"
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.load(response)
            return data["info"]["version"]
    except Exception:
        # Silently fail - don't break imports due to network issues
        return None


def should_check_versions() -> bool:
    """
    Check if version checking should be performed based on environment variables.
    
    Returns:
        True if version checking is enabled, False otherwise
    """
    # Respect common Python/CI patterns for disabling network operations
    disable_conditions = [
        os.getenv("ZEUSDB_SKIP_VERSION_CHECK", "").lower() in ("1", "true", "yes", "on"),
        os.getenv("CI", "").lower() in ("1", "true", "yes", "on"),  # Most CI systems
        os.getenv("PYTHONOFFLINE", "").lower() in ("1", "true", "yes", "on"),  # Python offline mode
        os.getenv("NO_NETWORK", "").lower() in ("1", "true", "yes", "on"),  # General no-network flag
        os.getenv("ZEUSDB_OFFLINE_MODE", "").lower() in ("1", "true", "yes", "on"),  # ZeusDB specific
    ]
    
    return not any(disable_conditions)


def _warn_if_outdated(package_name: str, installed_version: str) -> None:
    """
    Warn user if package version is outdated.
    
    Args:
        package_name: Name of the package to check
        installed_version: Currently installed version
    """
    latest_version = get_latest_pypi_version(package_name)
    
    if latest_version and installed_version != latest_version:
        warnings.warn(
            f"{package_name} may be outdated "
            f"(installed: {installed_version}, latest: {latest_version}). "
            f"Consider upgrading with: uv pip install -U {package_name}",
            UserWarning,
            stacklevel=4  # Adjust to point to user's import statement
        )


def check_package_version(package_name: str, warn_on_outdated: bool = True) -> str:
    """
    Check if a package is installed and optionally warn if outdated.
    
    Args:
        package_name: Name of the package to check
        warn_on_outdated: Whether to warn if package is outdated
        
    Returns:
        Installed version string if available, otherwise raises ImportError
        
    Raises:
        ImportError: If package is not installed
    """
    try:
        installed_version = version(package_name)
    except PackageNotFoundError:
        raise ImportError(
            f"{package_name} is required but not installed.\n"
            f"Install with: uv pip install {package_name}"
        )
    
    # Only check versions if enabled and user wants warnings
    if warn_on_outdated and should_check_versions():
        _warn_if_outdated(package_name, installed_version)
    
    return installed_version


# Package configuration - easily extendable
ZEUSDB_PACKAGES = {
    "VectorDatabase": {
        "package": "zeusdb-vector-database",
        "module": "zeusdb_vector_database",
        "class": "VectorDatabase"
    },
    # Future packages - uncomment when available
    # "RelationalDatabase": {
    #     "package": "zeusdb-relational-database", 
    #     "module": "zeusdb_relational_database",
    #     "class": "RelationalDatabase"
    # },
    # "GraphDatabase": {
    #     "package": "zeusdb-graph-database",
    #     "module": "zeusdb_graph_database", 
    #     "class": "GraphDatabase"
    # },
    # "DocumentDatabase": {
    #     "package": "zeusdb-document-database",
    #     "module": "zeusdb_document_database",
    #     "class": "DocumentDatabase"
    # },
}


def import_database_class(db_type: str) -> Any:
    """
    Dynamically import a database class with version checking.
    
    Args:
        db_type: Database type (e.g., 'VectorDatabase')
        
    Returns:
        The imported database class
        
    Raises:
        AttributeError: If db_type is not supported
        ImportError: If required package is not installed
    """
    if db_type not in ZEUSDB_PACKAGES:
        available = list(ZEUSDB_PACKAGES.keys())
        raise AttributeError(
            f"'{db_type}' is not available. "
            f"Available types: {', '.join(available)}"
        )
    
    config = ZEUSDB_PACKAGES[db_type]
    
    # Check package version (with environment-aware warnings)
    check_package_version(config["package"])
    
    # Import the class
    module = __import__(config["module"], fromlist=[config["class"]])
    return getattr(module, config["class"])
