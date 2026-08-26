# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.0] - 2026-08-11

### Added

- `HNSWIndex`, `AddResult`, `init_logging`, `init_file_logging` and `is_logging_initialized` are now importable from `zeusdb`. The package re-exports the whole public surface of `zeusdb-vector-database` apart from its `__version__`.
- `zeusdb.logging_config` submodule, providing `get_logger` and `operation_context`. `get_logger` returns a `LoggerAdapter` that accepts arbitrary keyword fields and wraps the logger `zeusdb-vector-database` configures.
- Test suite covering the exported surface, the import forms used by `langchain-zeusdb` and `llama-index-vector-stores-zeusdb`, and the declared dependency constraint against what it resolves to. 40 tests.
- `ci.yml`, running the test suite on Python 3.10 through 3.14 on push and pull request against `main` and `development`.
- Tag-triggered publishing, TestPyPI routing for prerelease tags, and a `workflow_dispatch` dry run path in `publish-pypi.yml`.
- Version consistency gate and a built-wheel import check in the publish workflow.
- `dev` optional dependency group.
- `Programming Language :: Python :: 3.14` classifier.
- Integrations landing page with overview and quick links.
- LangChain integration guide: install steps, quick start, advanced search (similarity scores, MMR), metadata filtering (with docs link), persistence (hard link to persistence docs), and async examples for scripts & notebooks.
- LlamaIndex Integration Guide: Comprehensive documentation (`llamaindex.md`) with 9 tested, copy-paste ready examples

### Changed

- `zeusdb-vector-database` constraint from `>=0.4.1` to `>=0.5.0,<0.6.0`.
- `__all__` is an explicit literal list rather than one computed from the package registry.
- The `AttributeError` raised for an unknown attribute lists every available attribute, including `__version__`.
- Licence declaration from the `{file = 'LICENSE'}` table form to the SPDX expression `Apache-2.0`, with `license-files` naming `LICENSE` and `NOTICE`.
- `__getattr__` caches a resolved name on the module, so each name is imported once.
- `__dir__` returns its names sorted.
- Regenerated `uv.lock`, which recorded `zeusdb-vector-database>=0.3.0` and pinned 0.3.0.

### Fixed

- `import zeusdb.logging_config` resolves. `langchain-zeusdb` and `llama-index-vector-stores-zeusdb` both import `get_logger` and `operation_context` from it, and both were silently falling back to a private copy.
- `test_missing_attribute_message_format` asserted an error string the package stopped producing when the message gained its list of available attributes.

### Removed

- `License :: OSI Approved :: Apache Software License` classifier, superseded by the SPDX licence expression.
- `publish-check.yml`. Its build and metadata check are the `build` job of `publish-pypi.yml`, reached by a `workflow_dispatch` run with the publish input left unticked.

---

## [0.0.8] - 2025-08-20

### Changed
- Updated dependency: `zeusdb-vector-database` from `0.4.0` to `0.4.1` to ensure critical overwrite and memory leak fixes are applied.

### Fixed
- **Critical:** Fixed duplicate document bug where `overwrite=True` created multiple entries instead of replacing existing ones  
- Fixed memory leak from accumulated duplicate vectors in HNSW graph during overwrites  
- Fixed Product Quantization codes and training state not properly cleaned up during document removal  
- Fixed vector count inconsistencies when removing documents during overwrite operations  

### Removed
- Legacy overwrite behavior that created duplicates instead of proper replacements

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

## [0.2.0] - 2026-08-26

### Added

- `shutdown_logging` is importable from `zeusdb`, completing the re-export of `zeusdb-vector-database` 0.8.0's public surface.
- Documentation for the 0.8.0 surface: `space="dot"`, boolean filter composition, the `nin`, `any`, `all`, `exists`, `is_missing` and `is_null` operators, `indexed_fields`, `len()`, `in`, `count()`, `remove_points()`, `remove_where()`, `delete()`, `clear()`, `update_metadata()`, `rebuild()`, `shrink_to_fit()`, `list()` paging with `offset` and `after`, `get_records(strict=True)`, `AddResult.ids`, the read-only index properties, `shutdown_logging()` and the exit drain, atomic saves and per-artefact digests, the ceilings on `dim`, `ef_construction`, `top_k` and `ef_search`, and the quantization refusals for `l1` and `dot`.
- Documentation for `zeusdb.logging_config.get_logger` and `operation_context` on the logging page.
- An "Upgrading to 0.8.0" section on the upgrading page.
- The vector database landing page's code samples run under the documentation sample test.

### Changed

- `zeusdb-vector-database` constraint from `>=0.5.0,<0.6.0` to `>=0.8.0,<0.9.0`.
- Regenerated `uv.lock`, which pins `zeusdb-vector-database` 0.8.0.
- The dependency floor test requires 0.8.0, the release that first exported `shutdown_logging`.
- Documentation corrected for 0.8.0: `dim` is required, a filter decides which records are ranked, the saved graph is one file, saves are atomic and verified, `save()` and `load()` print nothing, every log level spelling is accepted, `list()` returns arrival order, `quantized_with_raw` holds more memory than an unquantized index, and the memory, search and training figures are re-measured.
- README quick start output matches what the current release prints, and the Python badge lists 3.14.

### Fixed

- The LlamaIndex guide listed `IS_EMPTY` as a supported filter operator; the adapter translates it to an operator the backend refuses.

### Removed
<!-- Add removals/deprecations here -->

---