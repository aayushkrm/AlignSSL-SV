"""Static guard: no figure may read a superseded results table.

Sections 3.8 and 4.8 of the manuscript establish that two result files were
produced under a defective protocol and are kept only as provenance:

  table1_label_efficiency.csv        F1 at a fixed 0.5 probability cut, and
                                     unequal label budgets across arms
  table7_hardneg_label_efficiency.csv  same, on candidate-filtered negatives
  table8_hardneg_vs_uniform.csv        derived from the two above

Their corrected replacements are table12/13/14/15. A figure that still reads
a superseded file will render values that contradict the manuscript table it
sits under — which is exactly the defect this test was written after finding
in figure 1 (it separated the pretrained arm from the DeepSV baseline at the
1% budget, 0.514 vs 0.435, where the corrected run has them tied at
0.478 vs 0.479).

The check is AST-based rather than textual so that a mention inside a comment
or docstring — the explanations above, for instance — does not trip it. Only
a real string literal reaching a `read(...)`-style call counts.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

FIGURES = Path(__file__).resolve().parents[1] / "analysis" / "make_figures.py"

SUPERSEDED = {
    "table1_label_efficiency.csv",
    "table7_hardneg_label_efficiency.csv",
    "table8_hardneg_vs_uniform.csv",
}


def _string_literals(node: ast.AST) -> list[str]:
    return [n.value for n in ast.walk(node)
            if isinstance(n, ast.Constant) and isinstance(n.value, str)]


def figure_functions() -> dict[str, ast.FunctionDef]:
    """Top-level `figureN` definitions in analysis/make_figures.py."""
    tree = ast.parse(FIGURES.read_text())
    out = {}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name.startswith("figure"):
            out[node.name] = node
    return out


def test_make_figures_defines_figures():
    fns = figure_functions()
    assert fns, "no figureN functions found in analysis/make_figures.py"


@pytest.mark.parametrize("name", sorted(figure_functions()))
def test_figure_does_not_read_superseded_table(name):
    """Every CSV a figure names must be a non-superseded results table.

    Docstrings are stripped first: the corrected functions explain in prose
    which file they no longer read, and that explanation must not fail the
    test it documents.
    """
    fn = figure_functions()[name]
    body = list(fn.body)
    if (body and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)):
        body = body[1:]

    named_csvs = {s for stmt in body for s in _string_literals(stmt)
                  if s.endswith(".csv")}
    bad = named_csvs & SUPERSEDED
    assert not bad, (
        f"{name} reads superseded table(s) {sorted(bad)}; use the corrected "
        f"replacement (table12/13/14/15) so the figure agrees with the "
        f"manuscript table it accompanies"
    )


if __name__ == "__main__":  # runnable on the cluster, which has no pytest
    fns = figure_functions()
    assert fns, "no figureN functions found"
    failures = []
    for name, fn in sorted(fns.items()):
        body = list(fn.body)
        if (body and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)):
            body = body[1:]
        csvs = {s for stmt in body for s in _string_literals(stmt)
                if s.endswith(".csv")}
        bad = csvs & SUPERSEDED
        if bad:
            failures.append(f"{name}: {sorted(bad)}")
    if failures:
        raise SystemExit("FAIL: figures read superseded tables:\n  "
                         + "\n  ".join(failures))
    print(f"PASS: {len(fns)} figures read no superseded results table")
