"""
The declared dependency constraint against what it actually resolves to.

This package re-exports names it does not define, so its constraint and its
surface are one thing. A floor below the release that introduced a name means a
valid install where that name does not resolve, which is the state 0.0.8 was in:
it declared `zeusdb-vector-database>=0.4.1` uncapped, resolved 0.5.0 in
practice, and re-exported one name out of six.

These tests read the requirement from installed distribution metadata, which is
what a user resolves against, so the package must be installed rather than only
placed on `sys.path`.
"""

import importlib.metadata

import pytest
import zeusdb_vector_database
from packaging.requirements import Requirement
from packaging.version import Version

import zeusdb

DEPENDENCY = "zeusdb-vector-database"

# The release that first exported shutdown_logging. 0.5.0 introduced the other
# five forwarded names, so below 0.8.0 at least one name in `zeusdb.__all__`
# cannot resolve.
REQUIRED_FLOOR = Version("0.8.0")


def _declared_requirement() -> Requirement:
    """The zeusdb-vector-database requirement this package declares."""
    try:
        declared = importlib.metadata.requires("zeusdb") or []
    except importlib.metadata.PackageNotFoundError:
        pytest.fail(
            "zeusdb is not installed, so its declared requirements cannot be "
            "read. Install the package first, for example `uv pip install -e .`."
        )

    for entry in declared:
        requirement = Requirement(entry)
        if requirement.name == DEPENDENCY:
            return requirement

    pytest.fail(f"zeusdb declares no requirement on {DEPENDENCY}")


def test_the_floor_is_at_least_the_release_that_provides_every_name():
    """A floor below 0.8.0 admits an install missing part of `__all__`."""
    specifier = _declared_requirement().specifier
    floors = [
        Version(clause.version)
        for clause in specifier
        if clause.operator in (">=", "==", "~=")
    ]
    assert floors, f"{DEPENDENCY} is declared with no lower bound: {specifier}"
    assert min(floors) >= REQUIRED_FLOOR


def test_the_constraint_is_capped():
    """An uncapped floor is how 0.5.0's breaking changes reached 0.0.8 users.

    This package mirrors a public surface it does not control, so the next
    minor of that surface must not reach users before this package has been
    checked against it.
    """
    specifier = _declared_requirement().specifier
    assert any(clause.operator in ("<", "<=", "==", "~=") for clause in specifier), (
        f"{DEPENDENCY} is declared uncapped: {specifier}"
    )


def test_the_installed_dependency_satisfies_the_declared_constraint():
    """What the tests ran against is what the constraint permits."""
    requirement = _declared_requirement()
    installed = importlib.metadata.version(DEPENDENCY)
    assert requirement.specifier.contains(installed, prereleases=True), (
        f"{DEPENDENCY} {installed} is installed, which does not satisfy "
        f"{requirement.specifier}"
    )


def test_the_resolved_dependency_provides_every_reexported_name():
    """Every name this package promises exists in the version it resolved to.

    This is the test that would have caught the 0.0.8 state, where the surface
    and the floor had drifted two minors apart.
    """
    missing = [
        name
        for name in zeusdb.__all__
        if name != "__version__" and not hasattr(zeusdb_vector_database, name)
    ]
    installed = importlib.metadata.version(DEPENDENCY)
    assert not missing, (
        f"{DEPENDENCY} {installed} does not provide {missing}, which "
        f"zeusdb.__all__ promises"
    )


def test_the_umbrella_version_is_reported_and_is_its_own():
    """The two packages version independently."""
    assert zeusdb.__version__ == importlib.metadata.version("zeusdb")
    assert zeusdb.__version__ != zeusdb_vector_database.__version__
