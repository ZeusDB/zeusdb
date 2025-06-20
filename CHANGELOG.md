# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

## [0.0.3]

### Added
- Introduced modular `__init__.py` in the `zeusdb` package. This change improves robustness for partial installations and prepares the master package for a plugin-based or modular architecture.

- Added version constant `__version__ = "0.0.3"`.

- Implemented module-level `__getattr__` to support **lazy loading** of database backends (PEP 562).

- Added `__dir__()` for better introspection and tab-completion in REPLs and IDEs.

- Included clear and actionable error messages when optional submodules are accessed but not installed.


### Changed
- Replaced `try/except ImportError` eager imports with `__getattr__` to defer loading of submodules until explicitly accessed.

- `VectorDatabase` is currently active; other backends (`RelationalDatabase`, `GraphDatabase`, `DocumentDatabase`) are present as commented placeholders for future releases.

- Dynamic population of `__all__` now occurs inside `__getattr__` after successful imports to keep it accurate and reflective of availability.


### Fixed
<!-- Add bug fixes here -->

### Removed
- Removed eager import pattern using `try/except` blocks from `__init__.py`.

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

### Fixed

