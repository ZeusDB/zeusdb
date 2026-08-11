"""
Every version claim on the documentation site against a declared constraint.

The sample suite executes the site's Python fences, so a stale API call fails
loudly. Version claims are prose and are invisible to it, which is how the
LangChain page carried an uncapped `langchain-core` floor while the package
declared `>=0.3.74,<0.4`.

This suite closes that gap. It collects every version constraint written on the
site and asserts each one is a constraint that `zeusdb`, `zeusdb-vector-database`,
`langchain-zeusdb` or `llama-index-vector-stores-zeusdb` actually declares.

How references are located, since a regular expression over markdown finds
recall figures and embedding literals as readily as versions:

- A constraint attached to a package name, such as `zeusdb>=0.0.8`, is matched
  by name and taken as a claim about that package. Requiring an operator
  immediately after a known name admits nothing else.
- A bare constraint, such as `>=2.2.6,<3.0.0`, counts only inside backticks and
  only when exactly one package is named on the same line. Markdown link
  targets are stripped first, so a repository URL does not name a second
  package. Zero names or more than one is a failure asking the author to make
  the line unambiguous, never a silent skip.
- Everything else is ignored. `0.000988` in a search result, `lambda_mult=0.7`
  and `<1ms` in a benchmark table carry no operator and no package name.

Where the truth comes from, given CI has no sibling checkouts:

- `zeusdb` and `zeusdb-vector-database` are installed, so their requirements and
  their `Requires-Python` are read from distribution metadata.
- The two integration packages are not installed here and are not dependencies
  of this one. Their constraints are held in EXPECTED_INTEGRATION_METADATA
  below, and a separate test reads their `pyproject.toml` from the sibling
  checkouts and asserts the table matches, skipping when the checkouts are
  absent. CI therefore enforces the site against the table, and a developer
  with the checkouts enforces the table against the packages.
"""

import importlib.metadata
import re
from pathlib import Path

import pytest
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.version import Version

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs" / "source"
CONF = DOCS / "conf.py"

# The integration checkouts, siblings of this repository, absent in CI.
PACKAGES_DIR = ROOT.parents[2]
SIBLING_PYPROJECTS = {
    "langchain-zeusdb": (
        PACKAGES_DIR
        / "package-langchain-zeusdb"
        / "repository"
        / "langchain-zeusdb"
        / "libs"
        / "zeusdb"
        / "pyproject.toml"
    ),
    "llama-index-vector-stores-zeusdb": (
        PACKAGES_DIR
        / "package-llama-index-vector-stores-zeusdb"
        / "repository"
        / "llama-index-vector-stores-zeusdb"
        / "pyproject.toml"
    ),
}

# What the two integration packages declare. Checked against the sibling
# checkouts by test_the_expected_integration_metadata_matches_the_checkouts.
EXPECTED_INTEGRATION_METADATA = {
    "langchain-zeusdb": {
        "python": ">=3.10",
        "zeusdb": ">=0.0.8",
        "langchain-core": ">=0.3.74,<0.4",
    },
    "llama-index-vector-stores-zeusdb": {
        "python": ">=3.10,<4.0",
        "zeusdb": ">=0.0.8",
        "llama-index-core": ">=0.14.6",
    },
}

# Longest first, so `zeusdb-vector-database` is not tokenised as `zeusdb`.
KNOWN_NAMES = [
    "llama-index-vector-stores-zeusdb",
    "zeusdb-vector-database",
    "llama-index-core",
    "langchain-zeusdb",
    "langchain-core",
    "zeusdb",
    "numpy",
    "python",
]

_CLAUSE = r"[<>!~=]=?\s*[0-9][0-9A-Za-z.*+!]*"
_SPEC = rf"(?:{_CLAUSE})(?:\s*,\s*{_CLAUSE})*"

NAME_RE = re.compile(r"\b(" + "|".join(re.escape(n) for n in KNOWN_NAMES) + r")\b", re.I)
ANCHORED_RE = re.compile(
    r"\b(" + "|".join(re.escape(n) for n in KNOWN_NAMES) + rf")\s*({_SPEC})", re.I
)
BACKTICKED_RE = re.compile(rf"`({_SPEC})`")
SERIES_RE = re.compile(r"\b(\d+\.\d+)\.x\b")
PY_MINOR_RE = re.compile(r"\b3\.(\d+)\b")
LINK_TARGET_RE = re.compile(r"\]\([^)]*\)")


def canonical(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).strip().lower()


def markdown_pages():
    return sorted(DOCS.rglob("*.md"))


def declared_constraints() -> dict[str, list[SpecifierSet]]:
    """Every constraint the four packages declare, keyed by canonical name."""
    declared: dict[str, list[SpecifierSet]] = {}

    def record(name: str, spec: str) -> None:
        specifier = SpecifierSet(spec)
        bucket = declared.setdefault(canonical(name), [])
        if specifier not in bucket:
            bucket.append(specifier)

    for distribution in ("zeusdb", "zeusdb-vector-database"):
        try:
            metadata = importlib.metadata.metadata(distribution)
        except importlib.metadata.PackageNotFoundError:
            pytest.fail(
                f"{distribution} is not installed, so its declared constraints "
                f"cannot be read. Install this package first, for example "
                f"`uv pip install -e .`."
            )
        requires_python = metadata.get("Requires-Python")
        if requires_python:
            record("python", requires_python)
        for entry in importlib.metadata.requires(distribution) or []:
            requirement = Requirement(entry)
            # Extras are not what a plain install resolves, so they are not
            # constraints the site may quote.
            if requirement.marker is None and str(requirement.specifier):
                record(requirement.name, str(requirement.specifier))

    for declarations in EXPECTED_INTEGRATION_METADATA.values():
        for name, spec in declarations.items():
            record(name, spec)

    return declared


def claims_on(line: str):
    """Yield (package, specifier_text) for every version claim on one line."""
    stripped = LINK_TARGET_RE.sub("]", line)

    consumed: list[tuple[int, int]] = []
    for match in ANCHORED_RE.finditer(stripped):
        consumed.append(match.span(2))
        yield canonical(match.group(1)), match.group(2)

    bare = [
        match
        for match in BACKTICKED_RE.finditer(stripped)
        if not any(start <= match.start(1) and match.end(1) <= end for start, end in consumed)
    ]
    series = list(SERIES_RE.finditer(stripped))
    if not bare and not series:
        return

    names = {canonical(match.group(1)) for match in NAME_RE.finditer(stripped)}
    if bare and len(names) != 1:
        pytest.fail(
            f"a version constraint is written on a line naming {sorted(names) or 'no package'}, "
            f"so it cannot be attributed. Name exactly one package on the line, or "
            f"attach the constraint to its name.\n  {line.strip()}"
        )
    if len(names) != 1:
        # A series written without a package on the line, such as the heading
        # "Upgrading from 0.4.x", takes its subject from the page rather than
        # the line. It is not a constraint and is left alone.
        return
    name = names.pop()
    for match in bare:
        yield name, match.group(1)
    for match in series:
        # A `0.5.x` series claim is satisfied when the declared constraint
        # admits the first release of that series.
        yield name, f"=={match.group(1)}.0"


def test_every_constraint_on_the_site_is_one_a_package_declares():
    """A version claim is correct only if some package declares it.

    This is the check that would have caught `langchain-core: 0.3.74 or
    higher`, written while `langchain-zeusdb` declared `>=0.3.74,<0.4`.
    """
    declared = declared_constraints()
    wrong = []
    checked = 0

    for page in markdown_pages():
        for number, line in enumerate(page.read_text(encoding="utf-8").splitlines(), 1):
            for name, spec in claims_on(line):
                checked += 1
                known = declared.get(name)
                if known is None:
                    wrong.append(
                        f"{page.relative_to(ROOT)}:{number} names {name}, which none "
                        f"of the four packages depends on"
                    )
                    continue
                if spec.startswith("=="):
                    # A series claim, checked by containment rather than equality.
                    if not any(
                        constraint.contains(Version(spec[2:]), prereleases=True)
                        for constraint in known
                    ):
                        wrong.append(
                            f"{page.relative_to(ROOT)}:{number} claims {name} {spec[2:]}, "
                            f"outside {[str(c) for c in known]}"
                        )
                    continue
                if SpecifierSet(spec) not in known:
                    wrong.append(
                        f"{page.relative_to(ROOT)}:{number} states {name} {spec}, "
                        f"declared as {[str(c) for c in known]}"
                    )

    assert checked, "no version constraints were found, so this test proves nothing"
    assert not wrong, "version claims that no package declares:\n" + "\n".join(wrong)


def test_every_python_version_named_on_the_site_is_supported():
    """A minor named next to the word Python must be one the package claims."""
    supported = {
        classifier.rsplit(" :: ", 1)[1]
        for classifier in importlib.metadata.metadata("zeusdb").get_all("Classifier") or []
        if classifier.startswith("Programming Language :: Python :: 3.")
    }
    assert supported, "zeusdb declares no per-minor Python classifiers"

    wrong = []
    for page in markdown_pages():
        for number, line in enumerate(page.read_text(encoding="utf-8").splitlines(), 1):
            if not re.search(r"\bpython\b", line, re.I):
                continue
            for match in PY_MINOR_RE.finditer(line):
                if match.group(0) not in supported:
                    wrong.append(
                        f"{page.relative_to(ROOT)}:{number} names Python "
                        f"{match.group(0)}, which is not a supported minor "
                        f"{sorted(supported)}"
                    )

    assert not wrong, "unsupported Python versions on the site:\n" + "\n".join(wrong)


def test_the_documented_release_is_the_installed_version():
    """`conf.py` sets the version the theme renders, and it drifted before."""
    match = re.search(r"^release\s*=\s*['\"]([^'\"]+)['\"]", CONF.read_text(encoding="utf-8"), re.M)
    assert match, "conf.py declares no release"
    assert Version(match.group(1)) == Version(importlib.metadata.version("zeusdb"))


@pytest.mark.parametrize("package", sorted(EXPECTED_INTEGRATION_METADATA))
def test_the_expected_integration_metadata_matches_the_checkouts(package):
    """The table above against the packages it stands in for.

    Skips in CI, which has no sibling checkouts. Locally this is what keeps the
    table from going stale behind the site.
    """
    pyproject = SIBLING_PYPROJECTS[package]
    if not pyproject.is_file():
        pytest.skip(f"{package} is not checked out at {pyproject}")

    text = pyproject.read_text(encoding="utf-8")
    block = re.search(r"^dependencies\s*=\s*\[(.*?)^\]", text, re.S | re.M)
    assert block, f"{package} declares no top level dependencies list"
    actual = {}
    for entry in re.findall(r"[\"']([^\"']+)[\"']", block.group(1)):
        requirement = Requirement(entry)
        actual[canonical(requirement.name)] = requirement.specifier

    requires_python = re.search(
        r"^requires-python\s*=\s*[\"']([^\"']+)[\"']", text, re.M
    )
    assert requires_python, f"{package} declares no requires-python"
    actual["python"] = SpecifierSet(requires_python.group(1))

    expected = {
        canonical(name): SpecifierSet(spec)
        for name, spec in EXPECTED_INTEGRATION_METADATA[package].items()
    }
    for name, specifier in expected.items():
        assert name in actual, f"{package} no longer declares {name}"
        assert actual[name] == specifier, (
            f"{package} declares {name}{actual[name]}, while "
            f"EXPECTED_INTEGRATION_METADATA and the site say {name}{specifier}. "
            f"Update the table and the site together."
        )
