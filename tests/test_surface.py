"""
Tests for the public surface of the zeusdb umbrella package.

This package re-exports names it does not define, so its surface is its whole
job. These tests pin what `__all__` promises, that every promised name resolves
to the expected kind of object, and that the promise stays in step with the
package it forwards to.
"""

import pytest
import zeusdb_vector_database

import zeusdb

# What each re-exported name must resolve to. AddResult and HNSWIndex are types
# a caller receives rather than constructs; the three logging names are the
# functions the documented logging recipe calls at package level.
EXPECTED_KINDS = {
    "AddResult": type,
    "HNSWIndex": type,
    "VectorDatabase": type,
    "init_file_logging": callable,
    "init_logging": callable,
    "is_logging_initialized": callable,
}


def test_all_is_an_explicit_list_of_strings():
    """__all__ is written out rather than computed from the registry."""
    assert isinstance(zeusdb.__all__, list)
    assert all(isinstance(name, str) for name in zeusdb.__all__)
    assert len(zeusdb.__all__) == len(set(zeusdb.__all__)), "__all__ has duplicates"


def test_all_matches_the_registry_plus_version():
    """__all__ and _PACKAGE_MAP cannot drift apart.

    __all__ is explicit, so adding a name to one and not the other is the
    obvious mistake. This is the test that catches it.
    """
    assert set(zeusdb.__all__) == set(zeusdb._PACKAGE_MAP) | {"__version__"}


def test_every_name_in_all_resolves_to_the_expected_kind():
    """Each promised name imports, and is the kind of object it claims to be."""
    for name in zeusdb.__all__:
        value = getattr(zeusdb, name)
        if name == "__version__":
            assert isinstance(value, str) and value
            continue
        kind = EXPECTED_KINDS[name]
        if kind is type:
            assert isinstance(value, type), f"{name} is {type(value)}, expected a type"
        else:
            assert callable(value), f"{name} is {type(value)}, not callable"


def test_every_name_the_vector_database_exports_is_reachable():
    """The umbrella re-exports the whole of its dependency's public surface.

    __version__ is the one name withheld. Both packages define their own and
    the umbrella's must stay its own.
    """
    forwarded = set(zeusdb_vector_database.__all__) - {"__version__"}
    assert forwarded <= set(zeusdb.__all__), (
        f"not reachable from zeusdb: {sorted(forwarded - set(zeusdb.__all__))}"
    )


def test_reexported_names_are_the_same_objects():
    """Forwarding returns the dependency's object rather than a copy."""
    for name in set(zeusdb_vector_database.__all__) - {"__version__"}:
        assert getattr(zeusdb, name) is getattr(zeusdb_vector_database, name)


def test_repeated_access_returns_a_stable_object():
    """__getattr__ caches on the module, so a name resolves once."""
    assert zeusdb.VectorDatabase is zeusdb.VectorDatabase


def test_dir_matches_all():
    """Tab completion offers exactly what __all__ promises."""
    assert sorted(dir(zeusdb)) == sorted(zeusdb.__all__)


def test_logging_config_is_an_importable_submodule():
    """`import zeusdb.logging_config` needs a real file, not a registry entry.

    `from a.b import c` resolves `a.b` through the import system and never
    consults a module-level `__getattr__`, so this cannot be served by
    `_PACKAGE_MAP`.
    """
    import zeusdb.logging_config

    assert callable(zeusdb.logging_config.get_logger)
    assert callable(zeusdb.logging_config.operation_context)
    assert set(zeusdb.logging_config.__all__) == {"get_logger", "operation_context"}


def test_unknown_attribute_lists_what_is_available():
    """The error names every attribute, including __version__."""
    with pytest.raises(AttributeError) as exc_info:
        zeusdb.NoSuchThing

    message = str(exc_info.value)
    for name in zeusdb.__all__:
        assert name in message, f"{name} missing from the AttributeError message"
