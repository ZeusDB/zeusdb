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
output must appear in the captured stdout, in order. This tolerates the
progress lines save() and load() print, which the pages state are omitted.
"""

import io
import re
import warnings
from contextlib import redirect_stdout
from pathlib import Path

import pytest

DOCS = Path(__file__).resolve().parent.parent / "docs" / "source"

# Pages whose samples are executable as written, in reading order.
PAGES = [
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


def assert_subsequence(expected: str, actual: str, page: str, lineno: int):
    """Every non-empty expected line appears in the actual output, in order."""
    actual_lines = [line.rstrip() for line in actual.splitlines()]
    pos = 0
    for want in expected.splitlines():
        want = want.rstrip()
        if not want:
            continue
        try:
            pos = actual_lines.index(want, pos) + 1
        except ValueError:
            pytest.fail(
                f"{page}:{lineno}: documented output line not produced:\n"
                f"  expected: {want!r}\n"
                f"  captured stdout:\n{actual}"
            )


@pytest.mark.parametrize("page", PAGES)
def test_page_samples_run_and_match_documented_output(page, tmp_path, monkeypatch):
    """Run a page's samples in order; printed output must match the page."""
    # .zdb directories and any other artifacts land in the temp directory.
    monkeypatch.chdir(tmp_path)

    text = (DOCS / page).read_text(encoding="utf-8")
    blocks = extract_blocks(text)
    assert blocks, f"{page} has no executable python fences"

    namespace = {"__name__": "__main__"}
    for lineno, code, expected in blocks:
        captured = io.StringIO()
        with warnings.catch_warnings():
            # create() warns by design on some documented configurations.
            warnings.simplefilter("ignore")
            with redirect_stdout(captured):
                try:
                    exec(compile(code, f"{page}:{lineno}", "exec"), namespace)
                except Exception as e:  # noqa: BLE001 - report the sample that broke
                    pytest.fail(f"{page}:{lineno}: sample raised {type(e).__name__}: {e}")
        if expected is not None:
            assert_subsequence(expected, captured.getvalue(), page, lineno)
