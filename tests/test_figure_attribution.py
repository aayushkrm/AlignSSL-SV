"""Every figure caption must name the results files its panels are drawn from.

Same defect as the tables: six of ten figure captions named no backing file,
and the ``figureN_*.png`` numbering does not follow the ``tableNN_*.csv``
numbering, so a reader could not get from a panel to its data.

What makes this gate different from a hand-maintained mapping is that the
expected sources are *parsed out of the generator*, not written down here.
``analysis/make_figures.py`` is the only thing that knows which CSV feeds which
PNG; a list duplicated in a test would silently go stale the first time a panel
changed its input, which is the failure mode the gate exists to prevent.  The
parse walks each ``def figureN(...)`` body for ``read(res / "...csv")`` and for
the ``fig.savefig(out / "...png")`` that names its output, so the mapping is
keyed on the file the figure actually writes rather than on the function name
(``figure4()`` writes ``figure5_cross_ancestry.png``).
"""

from __future__ import annotations

import ast
import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MD = ROOT / "docs" / "AlignSSL_SV_manuscript.md"
GEN = ROOT / "analysis" / "make_figures.py"
RESULTS = ROOT / "results"

# Files a caption may cite that the generator does not read.  A figure caption
# legitimately points at provenance beyond its plotted input -- Figure 10 plots
# the audit counts but cites the verbatim quotations that justify each coding.
# Listing them explicitly keeps the drift check strict for plotted inputs while
# admitting evidence citations, rather than dropping the check for everyone.
SUPPORTING = {
    10: {"table19_field_audit_quotes.csv"},  # per-paper quotations behind the coding
}


def _generator_mapping() -> dict[str, set[str]]:
    """png filename -> set of results CSVs read by the function that writes it.

    Parsed from the AST rather than by regex over the source, so a CSV named in
    a comment or docstring (``make_figures`` discusses the superseded
    ``table1_label_efficiency.csv`` in a docstring) is not mistaken for an
    input.
    """
    tree = ast.parse(GEN.read_text(encoding="utf-8"))
    mapping: dict[str, set[str]] = {}
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        csvs, pngs = set(), set()
        for sub in ast.walk(node):
            if isinstance(sub, ast.Constant) and isinstance(sub.value, str):
                if sub.value.endswith(".csv"):
                    csvs.add(sub.value)
                elif sub.value.endswith(".png"):
                    pngs.add(sub.value)
        # A docstring's strings are Constants too, so drop the docstring node.
        doc = ast.get_docstring(node) or ""
        csvs -= {t for t in re.findall(r"[a-z0-9_]+\.csv", doc)}
        pngs -= {t for t in re.findall(r"[a-z0-9_]+\.png", doc)}
        if len(pngs) == 1 and csvs:
            mapping[pngs.pop()] = csvs
    return mapping


def _captions() -> dict[int, str]:
    """Figure number -> caption text, read from the embedded image markers.

    Captions live inside ``![Figure N. ...]({{artifact:...}})``; there are no
    standalone bolded figure captions, so a caption-pattern search that assumes
    the table style finds nothing and passes vacuously.
    """
    md = MD.read_text(encoding="utf-8")
    out: dict[int, str] = {}
    for cap, _ in re.findall(r"!\[(.*?)\]\(\{\{artifact:([^}]+)\}\}\)", md, re.S):
        m = re.match(r"\s*Figure (\d+)\.", cap)
        assert m, f"embedded image with no 'Figure N.' caption: {cap[:60]!r}"
        out[int(m.group(1))] = re.sub(r"\s+", " ", cap).strip()
    return out


def _png_for(fig_no: int) -> str:
    matches = sorted(RESULTS.glob(f"figure{fig_no}_*.png"))
    assert len(matches) == 1, f"Figure {fig_no}: expected one png, found {matches}"
    return matches[0].name


FIGURES = sorted(_captions())


def test_every_figure_is_embedded_once() -> None:
    caps = _captions()
    assert caps, "no embedded figures found"
    assert FIGURES == list(range(1, len(FIGURES) + 1)), (
        f"figure numbering is not contiguous from 1: {FIGURES}"
    )
    md = MD.read_text(encoding="utf-8")
    for n in FIGURES:
        assert len(re.findall(rf"!\[\s*Figure {n}\.", md)) == 1, (
            f"Figure {n} is embedded more than once"
        )


@pytest.mark.parametrize("fig_no", FIGURES)
def test_caption_names_every_source_the_generator_reads(fig_no: int) -> None:
    """The caption must name each CSV the generating function actually reads."""
    expected = _generator_mapping().get(_png_for(fig_no))
    assert expected, (
        f"Figure {fig_no}: analysis/make_figures.py declares no CSV input for "
        f"{_png_for(fig_no)}"
    )
    cited = set(re.findall(r"results/([A-Za-z0-9_.-]+\.csv)", _captions()[fig_no]))
    missing = sorted(expected - cited)
    assert not missing, (
        f"Figure {fig_no}: caption does not name {missing}, which "
        f"make_figures.py reads to build it. The png and csv numbering differ, "
        f"so an unattributed panel is unverifiable."
    )
    stale = sorted(cited - expected - SUPPORTING.get(fig_no, set()))
    assert not stale, (
        f"Figure {fig_no}: caption names {stale}, which the generator no longer "
        f"reads. If this is supporting provenance rather than a plotted input, "
        f"add it to SUPPORTING with a reason."
    )


@pytest.mark.parametrize("fig_no", FIGURES)
def test_declared_sources_exist(fig_no: int) -> None:
    for name in re.findall(r"results/([A-Za-z0-9_.-]+\.csv)", _captions()[fig_no]):
        assert (RESULTS / name).is_file(), (
            f"Figure {fig_no}: cited source {name} does not exist"
        )


if __name__ == "__main__":  # cluster env has no pytest
    test_every_figure_is_embedded_once()
    for n in FIGURES:
        test_caption_names_every_source_the_generator_reads(n)
        test_declared_sources_exist(n)
    print("PASS: every figure caption names the sources its generator reads")
