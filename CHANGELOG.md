# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.0.7] - 2025-08-14

### Added
- New logging guide added to documentation

### Changed
- Updated minimum required version of `zeusdb-vector-database` to v0.4.0

---

## [0.0.6] - 2025-08-08

### Added
- Comprehensive API documentation with detailed examples and parameter references
- Read the Docs integration with custom domain (docs.zeusdb.com)
- Documentation pages for Create, Add Data, Search, and Persistence operations
- Product Quantization configuration guide with usage examples
- Sphinx-based documentation system with MyST parser and pydata theme
- Interactive code examples with expected outputs for all core operations
- Documentation badge in README linking to hosted docs

---

## [0.0.5] - 2025-08-06

### Changed
- Updated the `README.md` to include a revised Quick Start example that better reflects the current ZeusDB Vector Database API
- Updated dependency to require `zeusdb-vector-database>=0.3.0` in `pyproject.toml`

---

## [0.0.4] - 2025-06-27

### Added
- Introduced a plugin architecture in `__init__.py` using `_PACKAGE_MAP` for dynamic class resolution.
- Implemented lazy loading via `__getattr__()` to import database modules only when accessed.
- Automatically synced `__all__` with available plugin names for static analyzers and IDE tab-completion.
- Enhanced `ImportError` messages with actionable install instructions (`uv` and `pip`).
- Added `__dir__()` override to improve developer experience when exploring the package interactively.

### Changed
- `__init__.py` is now fully self-contained and no longer relies on `_utils.py`.
- Removed runtime version checking in favor of relying on proper dependency management through `pyproject.toml`.

### Fixed
- Future plugins can be added to `_PACKAGE_MAP` without changing the core logic
- The package now avoids all network operations during import

### Removed
- Removed `_utils.py` and all related logic:
  - Version checking logic against PyPI (`get_latest_pypi_version`, `check_package_version`)
  - Environment variable support for disabling version checks (`ZEUSDB_SKIP_VERSION_CHECK`, `CI`, etc.)
  - PyPI network dependency on import

---

## [0.0.3] - 2025-06-27

### Added
- Introduced modular `__init__.py` using `__getattr__()` for PEP 562-style lazy loading of database backends like `VectorDatabase`. This change improves robustness for partial installations and prepares the master package for a plugin-based or modular architecture.
- Added version constant `__version__ = "0.0.3"`.
- Implemented module-level `__getattr__` to support **lazy loading** of database backends (PEP 562).
- Added `__dir__()` for better introspection and tab-completion in REPLs and IDEs.
- Included clear and actionable error messages when optional submodules are accessed but not installed.
- Added helpful runtime warnings when installed packages are outdated compared to PyPI.
- Added `import_database_class()` to dynamically import database classes based on configuration.
- Added `_utils.py` containing:
  - `get_latest_pypi_version()` for cached PyPI version retrieval.
  - `check_package_version()` for installed package validation and warning if outdated.
  - `should_check_versions()` to suppress version checks in CI, offline, or env-flagged contexts.
  - `ZEUSDB_PACKAGES` registry to manage and extend backend database support.
- Added `test_missing_modules.py` with tests covering:
  - AttributeError messaging for undefined database types.
  - Case sensitivity of attribute access.
  - Expected attributes in `__all__` and `__dir__`.

### Changed
- Replaced eager `try/except ImportError` block-based loading with centralized, dynamic imports using `import_database_class()` from `_utils.py`.
- Reorganized `__all__` to be static and Pylance-compatible, with type hints provided separately for static analysis.
- Suppressed Pyright warnings using `# pyright: reportUnsupportedDunderAll=false` to support dynamic symbol declarations.
- `VectorDatabase` remains the only active backend; additional backends (`RelationalDatabase`, `GraphDatabase`, `DocumentDatabase`) are included as placeholders in configuration and docstrings for future expansion.

### Removed
- Removed outdated eager import logic from `__init__.py`, reducing import-time overhead and making the package plugin-friendly.

---

## [0.0.2] - 2025-06-19

### Added
- Declared zeusdb-vector-database>=0.0.1 as a required dependency in pyproject.toml to ensure correct module availability during import.

### Fixed
- Fixed and clarified the code example in the README.

---

## [0.0.1] - 2025-06-11

### Added
- Initial project structure and configuration.
- `pyproject.toml` with Hatchling build backend and project metadata.
- `.gitignore` for Python, build, and editor artifacts.
- GitHub Actions workflows:
  - `publish-pypi.yml` for trusted publishing to PyPI.
  - `publish-check.yml` for build verification without publishing.
- `CHANGELOG.md` following Keep a Changelog format.

---

## [Unreleased]

### Added
<!-- Add new features here -->

### Changed
<!-- Add changed behavior here -->

### Fixed
<!-- Add bug fixes here -->

### Removed
<!-- Add removals/deprecations here -->

---