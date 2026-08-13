"""A p-value is never zero, in a table cell or in a results file.

Motivating defect (2026-08-13). Fourteen table cells across the manuscript
rendered a p-value as ``0.000``. No p-value can take that value; the true
magnitudes ranged from 5.7e-07 to 5.0e-04, and every one of them was a
*significant* result reported as though the test had returned nothing
interpretable.

The defect had already been diagnosed once, in a figure caption, and fixed
there: ``analysis/make_figures.py`` grew ``p_fmt`` specifically to stop it.
The manuscript's own tables were never brought under that formatter, so the
identical defect survived one layer over. That is the reason this gate reads
the *document*, not the plotting code.

It has a second half, which is the part that actually cost something. Three
analysis scripts rounded their p-values with ``round(p, 4)`` at write time,
which sends anything below 5e-5 to exactly ``0.0`` *in the CSV*. For
``table14_control_vs_deep.csv`` that rounding was not recoverable: the
per-seed JSONs it derives from were lost with the cluster scratch workspace,
so the true p is now known only as a bound. A rendering bug is a typo; a
write-time rounding bug destroys data. Both directions are gated.
"""

from __future__ import annotations

import csv
import io
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
DOCS = [
    ROOT / "docs" / "AlignSSL_SV_manuscript.md",
    ROOT / "README.md",
    ROOT / "docs" / "project.md",
    ROOT / "PROGRESS.md",
]
RESULTS = ROOT / "results"

# A cell is a p-value cell when its column header says so. Headers in this
# corpus appear as "*p*", "Holm *p*", "p", "p_holm", "p_value".
_P_HEADER = re.compile(r"^\**(holm\s+)?\**p\**(_holm|_value|-value)?\**$", re.I)

# Zero at any rendered precision: 0, 0.0, 0.000, 0.00000 -- and the signed and
# padded forms a formatter can emit.
_ZERO = re.compile(r"^[+-]?0(\.0+)?$")


def _tables(text: str):
    """Yield (header_cells, row_cells, line_no) for every markdown table row."""
    header: list[str] | None = None
    for i, line in enumerate(text.split("\n"), start=1):
        if not line.lstrip().startswith("|"):
            header = None
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if header is None:
            header = cells
            continue
        if all(set(c) <= set("-: ") for c in cells):
            continue  # separator row
        yield header, cells, i


def _doc_ids():
    return [d.name for d in DOCS]


@pytest.mark.parametrize("doc", DOCS, ids=_doc_ids())
def test_no_document_renders_a_p_value_as_zero(doc: Path) -> None:
    if not doc.exists():
        pytest.skip(f"{doc.name} not present")
    bad = []
    for header, cells, line_no in _tables(doc.read_text(encoding="utf-8")):
        for k, cell in enumerate(cells):
            if k >= len(header) or not _P_HEADER.match(header[k]):
                continue
            if _ZERO.match(cell):
                bad.append(f"{doc.name}:{line_no} column {header[k]!r} = {cell!r}")
    assert not bad, (
        "a p-value is rendered as zero, which is not a value it can take -- "
        "use one significant figure below 0.001, or a '<' bound where the "
        "source itself has lost the precision:\n  " + "\n  ".join(bad)
    )


def _p_columns(fieldnames):
    return [f for f in (fieldnames or []) if _P_HEADER.match(f)]


@pytest.mark.parametrize(
    "csv_path",
    sorted(RESULTS.glob("*.csv")),
    ids=lambda p: p.name,
)
def test_no_results_file_stores_a_p_value_as_zero(csv_path: Path) -> None:
    """The write-time half. A zero here is destroyed data, not a typo."""
    with csv_path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        cols = _p_columns(reader.fieldnames)
        if not cols:
            pytest.skip("no p-value columns")
        bad = []
        for n, row in enumerate(reader, start=2):
            for col in cols:
                v = (row.get(col) or "").strip()
                if v and _ZERO.match(v):
                    bad.append(f"{csv_path.name}:{n} {col} = {v!r}")
    assert not bad, (
        "a results file stores a p-value as exactly zero. This is what "
        "round(p, 4) does to anything below 5e-5, and it is irreversible "
        "once the per-seed inputs are gone. Write full precision; round at "
        "render time:\n  " + "\n  ".join(bad)
    )


def test_no_analysis_script_rounds_a_p_value_at_write_time() -> None:
    """Close the door the CSV gate can only notice after the fact.

    A ``round(p, 4)`` whose inputs happen to all exceed 5e-5 today passes the
    CSV check and silently destroys the next run's smallest cell.
    """
    pat = re.compile(r"round\(\s*float\(\s*(p|pval|pvalue)\s*\)\s*,\s*\d+\s*\)")
    offenders = []
    for src in sorted((ROOT / "analysis").glob("*.py")):
        for n, line in enumerate(src.read_text(encoding="utf-8").split("\n"), 1):
            if pat.search(line):
                offenders.append(f"{src.name}:{n}: {line.strip()}")
    assert not offenders, (
        "p-values must be written at full precision and rounded only at "
        "render time:\n  " + "\n  ".join(offenders)
    )


# ---------------------------------------------------------------------------
# The defect one layer down: a *gate* that demands the defective rendering.
#
# On 2026-08-13 the manuscript's zero-rendered p-values were corrected, and
# the suite went red -- because analysis/check_manuscript.py compared each
# cell against f"{p:.3f}", which renders any p below 0.0005 as '0.000'. The
# checker was requiring the very defect the manuscript had been corrected
# for. Three copies of one formatting rule existed; two were wrong.
#
# There is now exactly one definition, analysis/pfmt.py. These tests keep it
# that way: no module may re-derive the rule locally, and the shared rule
# must never emit a zero at any precision.
# ---------------------------------------------------------------------------

# A fixed-decimal format applied to a p-value.
#
# Scope is the BRACE, not the line: a line may legitimately format a test
# statistic at fixed decimals while merely mentioning a p-value elsewhere
# (`f"{r.statistic:.3f}", f"{r.pvalue:.2e}"` is correct -- `.2e` keeps the
# magnitude). What is never correct is a p-value inside `:.Nf`.
#
# The token list is explicit rather than a `p*` prefix because the defect
# first slipped past a prefix pattern as `f"{float(src[kpv]):.3f}"`.
_P_TOKENS = r"(?:p|pval|pvalue|p_value|p_raw|p_holm|q_bh|kpv|pv)"
_PFMT_RE = re.compile(
    r'\{[^{}"]*(?:\b' + _P_TOKENS + r'\b|\.pvalue\b)[^{}"]*:[-+ ]?\.\d+f\}'
)


def test_no_module_formats_a_p_value_with_a_bare_fixed_format():
    """A local f"{p:.3f}" is how the defect re-entered the checker."""
    offenders = []
    for d in ("analysis", "tests"):
        for src in sorted((ROOT / d).glob("*.py")):
            if src.name == "pfmt.py":
                continue          # the one place the rule is allowed to live
            for n, line in enumerate(src.read_text(encoding="utf-8").split("\n"), 1):
                stripped = line.strip()
                # Prose describing the rule is not an application of it.
                if stripped.startswith("#") or stripped.startswith('"""'):
                    continue
                if _PFMT_RE.search(line):
                    offenders.append(f"{d}/{src.name}:{n}: {stripped}")
    assert not offenders, (
        "p-values must be rendered through analysis/pfmt.py, not re-derived "
        "locally:\n  " + "\n  ".join(offenders)
    )


@pytest.mark.parametrize("places", [2, 3, 4, 6])
def test_shared_renderer_never_emits_a_zero(places):
    """Whatever the precision, no input may render as all-zeros."""
    sys.path.insert(0, str(ROOT / "analysis"))
    from pfmt import p_fmt

    for v in (0.5, 0.05, 0.001, 5e-04, 1e-05, 2.268e-06, 5.722e-07, 1e-12):
        out = p_fmt(v, places)
        assert float(out) > 0.0, f"p_fmt({v}, {places}) = {out!r}"


def test_a_censored_p_renders_as_an_inequality():
    """A bound is not a measurement and must not be printed as one."""
    sys.path.insert(0, str(ROOT / "analysis"))
    from pfmt import p_render

    assert p_render(5e-05, "True").startswith("<")
    assert not p_render(5e-05, "False").startswith("<")


@pytest.mark.parametrize("csv_name,pcol", [
    ("table14_control_vs_deep.csv", "p_value"),
    ("table15_hardneg_arm_contrasts.csv", "p"),
])
def test_censored_p_values_carry_their_bound_flag(csv_name, pcol):
    """A file holding censored p-values must say which ones they are.

    Without the companion flag a reader cannot tell a measured 5e-05 from
    a value whose true magnitude was destroyed, and every downstream
    renderer would have to guess.
    """
    path = ROOT / "results" / csv_name
    if not path.exists():
        pytest.skip(f"{csv_name} absent")
    rows = list(csv.DictReader(io.StringIO(path.read_text(encoding="utf-8-sig"))))
    flag = pcol + "_is_upper_bound"
    assert flag in rows[0], f"{csv_name} has no {flag} column"
    bounded = [r for r in rows if r[flag] == "True"]
    assert bounded, f"{csv_name}: flag column present but no row uses it"
    for r in bounded:
        assert float(r[pcol]) == pytest.approx(5e-05), (
            f"{csv_name}: censored row records p={r[pcol]}, but round(p, 4) "
            f"censors at 5e-05 -- the bound must match the rounding that "
            f"destroyed the value"
        )
