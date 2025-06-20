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
- Introduced modular __init__.py in the zeusdb package. This change improves robustness for partial installations and prepares the master package for a plugin-based or modular architecture.

- Added version constant __version__ = "0.0.3".

### Changed
- __init__.py now uses try/except ImportError blocks to gracefully handle optional submodule imports:
  - VectorDatabase from zeusdb_vector_database
  - (Placeholders for RelationalDatabase, GraphDatabase, and DocumentDatabase included and commented out)

- Dynamically builds __all__ to expose only successfully imported components.

- Suppressed Ruff F401 linter warning for unused imports by using # noqa: F401 inline, since imports are re-exported via __all__. The inline suppression (# noqa: F401) avoids disabling linting globally, keeping lint checks strict and helpful elsewhere in the codebase.

### Fixed
<!-- Add bug fixes here -->

### Removed
<!-- Add removals/deprecations here -->

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

