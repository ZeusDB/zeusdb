"""
Executes the Python code samples on the documentation site.

The site drifted because nothing executed its samples. This suite extracts
every ```python fence from the core pages under docs/source, runs each page's
fences top to bottom in one shared namespace, exactly as a reader pasting them
in order would, and compares what they print against the *Output* block shown
on the page.

Not executed:
- fences in a language other than python (bash, text, json)
- fences preceded by an HTML comment `<!-- zeusdb:skip -->`, used for
  fragments that depend on import order or process environment
- logging.md, whose samples configure process-global logging state and only
  behave as written in a fresh interpreter
- the two integration guides, which require an OpenAI key and the integration
  packages

Output comparison is a subsequence match: every non-empty line of the shown
output must appear in the captured stdout, in order. This tolerates a sample
that prints more than the page shows, such as a result whose values the page
says depend on the data.

A page runs to the end whatever happens. Every failing block is collected and
reported together, so one run of the suite lists everything wrong on a page
rather than the first thing. Because the blocks share a namespace, a block that
raises leaves later blocks without the names it would have bound, and those
later blocks fail in turn. Such a failure is reported as following from the
earlier one, with the names involved, so that a single broken sample is not
read as several.
"""

import ast
import builtins
import io
import re
import warnings
from contextlib import redirect_stdout
from pathlib import Path

import pytest

DOCS = Path(__file__).resolve().parent.parent / "docs" / "source"

# Pages whose samples are executable as written, in reading order.
PAGES = [
    "vector_database/index.md",
    "vector_database/getting_started.md",
    "vector_database/usage/create.md",
    "vector_database/usage/add.md",
    "vector_database/usage/search.md",
    "vector_database/product_quantization.md",
    "vector_database/metadata_filtering.md",
    "vector_database/utilities.md",
    "vector_database/persistence.md",
]

SKIP_MARKER = "<!-- zeusdb:skip -->"

# A line that announces the output block that follows the code fence.
OUTPUT_LABEL = re.compile(r"\*(Output|Results Output:?)[^*]*\*")


def extract_blocks(text: str):
    """Yield (lineno, code, expected_output_or_None) for each python fence."""
    lines = text.splitlines()
    i = 0
    blocks = []
    while i < len(lines):
        stripped = lines[i].strip()
        if stripped.startswith("```python"):
            skip = any(
                SKIP_MARKER in lines[j]
                for j in range(max(0, i - 3), i)
            )
            start = i + 1
            i += 1
            code_lines = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            i += 1  # closing fence
            if skip:
                continue
            # Look ahead for an *Output* label and its fence.
            expected = None
            j = i
            seen_label = False
            while j < len(lines) and j < i + 4:
                s = lines[j].strip()
                if not s:
                    j += 1
                    continue
                if not seen_label and OUTPUT_LABEL.search(s):
                    seen_label = True
                    j += 1
                    continue
                if seen_label and s.startswith("```"):
                    j += 1
                    out_lines = []
                    while j < len(lines) and not lines[j].strip().startswith("```"):
                        out_lines.append(lines[j])
                        j += 1
                    expected = "\n".join(out_lines)
                break
            blocks.append((start + 1, "\n".join(code_lines), expected))
        else:
            i += 1
    return blocks


def missing_output_line(expected: str, actual: str):
    """The first documented output line absent from the actual output, or None.

    Every non-empty expected line must appear in the actual output, in order.
    """
    actual_lines = [line.rstrip() for line in actual.splitlines()]
    pos = 0
    for want in expected.splitlines():
        want = want.rstrip()
        if not want:
            continue
        try:
            pos = actual_lines.index(want, pos) + 1
        except ValueError:
            return want
    return None


def bound_names(code: str):
    """Names a block binds at any depth: assignments, imports, defs, classes."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return set()
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            names.add(node.id)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                names.add((alias.asname or alias.name).split(".")[0])
    return names


def free_names(code: str):
    """Names a block reads without binding them itself.

    A comprehension variable or a loop target is bound by the block that uses
    it, so it is not a dependency on any earlier block.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return set()
    loaded = {
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
    }
    return loaded - bound_names(code)


def cascade_note(code: str, namespace: dict, raised_blocks: list):
    """Explain a block's exception as a consequence of an earlier one, or None.

    A block that raised did not bind everything it would have. When a later
    block reads one of those names and the name is absent from the shared
    namespace, the later failure follows from the earlier one.
    """
    if not raised_blocks:
        return None
    wanted = {
        name
        for name in free_names(code)
        if name not in namespace and not hasattr(builtins, name)
    }
    if not wanted:
        return None
    causes = []
    for lineno, names in raised_blocks:
        hit = sorted(wanted & names)
        if hit:
            causes.append(f"line {lineno} binds {', '.join(hit)}")
    if not causes:
        return None
    return "follows from the earlier failure: " + "; ".join(causes)


def indent(text: str, prefix: str = "    ") -> str:
    return "\n".join(prefix + line for line in text.splitlines())


def run_page(page: str, blocks: list):
    """Run a page's blocks in order in one namespace; return (lineno, message) failures."""
    namespace = {"__name__": "__main__"}
    failures = []
    raised_blocks = []  # (lineno, names the block would have bound)
    for lineno, code, expected in blocks:
        captured = io.StringIO()
        with warnings.catch_warnings():
            # create() warns by design on some documented configurations.
            warnings.simplefilter("ignore")
            with redirect_stdout(captured):
                try:
                    exec(compile(code, f"{page}:{lineno}", "exec"), namespace)
                except Exception as e:  # noqa: BLE001 - report the sample that broke
                    note = cascade_note(code, namespace, raised_blocks)
                    message = f"sample raised {type(e).__name__}: {e}"
                    if note:
                        message += f"\n  {note}"
                    failures.append((lineno, message))
                    raised_blocks.append((lineno, bound_names(code)))
                    continue
        if expected is not None:
            missing = missing_output_line(expected, captured.getvalue())
            if missing is not None:
                failures.append((
                    lineno,
                    "documented output line not produced:\n"
                    f"  expected: {missing!r}\n"
                    "  captured stdout:\n"
                    f"{indent(captured.getvalue())}",
                ))
    return failures


@pytest.mark.parametrize("page", PAGES)
def test_page_samples_run_and_match_documented_output(page, tmp_path, monkeypatch):
    """Run a page's samples in order; every block must run and match the page."""
    # .zdb directories and any other artifacts land in the temp directory.
    monkeypatch.chdir(tmp_path)

    text = (DOCS / page).read_text(encoding="utf-8")
    blocks = extract_blocks(text)
    assert blocks, f"{page} has no executable python fences"

    failures = run_page(page, blocks)
    if failures:
        report = "\n".join(f"{page}:{lineno}: {message}" for lineno, message in failures)
        pytest.fail(
            f"{page}: {len(failures)} of {len(blocks)} blocks failed\n{report}",
            pytrace=False,
        )


HARNESS_PROOF_PAGE = """\
# Proof page

```python
first = 1
print("first ran")
```

*Output*
```text
first ran
```

```python
raise RuntimeError("second block breaks before binding")
second = 2
```

```python
print("third reads", second)
```

```python
print("fourth prints", first)
```

*Output*
```text
fourth prints something else
```

```python
print("fifth ran")
```

*Output*
```text
fifth ran
```
"""


def test_every_failing_block_on_a_page_is_reported():
    """A page runs to the end and every failure is reported, causes attributed.

    Five blocks. The second raises before binding `second`, the third reads
    `second` and fails as a consequence, the fourth prints something the page
    does not show, and the first and fifth are fine. All three failures must
    appear in one report, and the third must be attributed to the second.
    """
    blocks = extract_blocks(HARNESS_PROOF_PAGE)
    assert len(blocks) == 5

    failures = run_page("proof.md", blocks)
    reported = [lineno for lineno, _ in failures]
    messages = dict(failures)

    second, third, fourth = blocks[1][0], blocks[2][0], blocks[3][0]
    assert reported == [second, third, fourth]
    assert messages[second].startswith("sample raised RuntimeError")
    assert messages[third].startswith("sample raised NameError")
    assert f"follows from the earlier failure: line {second} binds second" in messages[third]
    assert "documented output line not produced" in messages[fourth]
    assert "follows from" not in messages[fourth]
