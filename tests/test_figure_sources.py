"""Gates binding each figure to the results table its section presents as primary.

Motivating defect (2026-08-12): figure5 was generated from
results/table5_cross_ancestry.csv -- the PRE-correction cross-ancestry run,
retained in the manuscript only as superseded Table 9 -- while Section 4.6
presents the corrected re-run (Table 8, results/table26_xpop_lowlabel.csv) as
its primary result. The figure additionally carried an on-image title
asserting the very robustness claim that section withdraws. Nothing caught it:
the figure regenerated deterministically and matched HEAD, because the
generator was faithfully plotting the wrong table.
"""
import re
import csv
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
GEN = (ROOT / "analysis" / "make_figures.py").read_text()
MS = (ROOT / "docs" / "AlignSSL_SV_manuscript.md").read_text()
RESULTS = ROOT / "results"


def _body(fn: str) -> str:
    """Source of one figure function, from its def to the next top-level def."""
    m = re.search(rf"^def {fn}\(.*?(?=^def |\Z)", GEN, re.M | re.S)
    assert m, f"{fn} not found in analysis/make_figures.py"
    return m.group(0)


def test_figure5_reads_the_corrected_xpop_table():
    b = _body("figure5")
    assert "table26_xpop_lowlabel.csv" in b, (
        "figure5 must plot the corrected re-run that Section 4.6 presents as primary"
    )
    assert "table5_cross_ancestry.csv" not in b, (
        "figure5 must not plot the superseded pre-correction run (manuscript Table 9)"
    )


def test_figure5_title_makes_no_robustness_claim():
    b = _body("figure5")
    title = re.search(r"set_title\((.*?)\)\n", b, re.S)
    assert title, "figure5 has no set_title"
    txt = title.group(1).lower()
    for banned in ("tracks in-distribution", "robust", "transfers well", "generalis", "generaliz"):
        assert banned not in txt, (
            f"figure5 title asserts {banned!r}; Section 4.6 withdraws that claim"
        )


def test_figure5_scoring_rule_is_stated_in_the_axis_label():
    b = _body("figure5")
    ylab = re.search(r"set_ylabel\(\"([^\"]+)\"\)", b)
    assert ylab and "0.5" in ylab.group(1), (
        "figure5 mixes rules unless the fixed 0.5 cut is named on the axis"
    )


@pytest.mark.parametrize("frac,site,col,val", [
    ("0.01", "xpop", "pretrained_mean", None),
    ("1.0", "xpop", "pretrained_mean", None),
])
def test_corrected_table_has_the_cells_figure5_plots(frac, site, col, val):
    rows = list(csv.DictReader(open(RESULTS / "table26_xpop_lowlabel.csv")))
    hit = [r for r in rows
           if r["rule"] == "f1_at_half" and r["site"] == site
           and float(r["label_frac"]) == float(frac)]
    assert len(hit) == 1 and hit[0][col], f"missing {frac}/{site}/{col}"


def test_figure5_caption_gap_direction_matches_the_data():
    """The caption counts budgets where transfer LOSES accuracy. Recount them."""
    rows = [r for r in csv.DictReader(open(RESULTS / "table26_xpop_lowlabel.csv"))
            if r["rule"] == "f1_at_half" and r["site"] in ("in_dist", "xpop")]
    by = {}
    for r in rows:
        by.setdefault(float(r["label_frac"]), {})[r["site"]] = r
    n_pre = sum(1 for f in by
                if float(by[f]["xpop"]["pretrained_mean"])
                < float(by[f]["in_dist"]["pretrained_mean"]))
    n_scr = sum(1 for f in by
                if float(by[f]["xpop"]["scratch_mean"])
                < float(by[f]["in_dist"]["scratch_mean"]))
    total = len(by)
    cap = re.search(r"!\[Figure 5\.(.*?)\]\(", MS, re.S)
    assert cap, "Figure 5 caption not found"
    words = {2: "two", 3: "three", 4: "four", 5: "five", 6: "six"}
    assert f"{words[n_pre]} of {words[total]}" in cap.group(1), (
        f"caption must say the pretrained gap is negative at {n_pre} of {total} budgets"
    )
    assert f"{words[n_scr]} of {words[total]}" in cap.group(1), (
        f"caption must say the from-scratch gap is negative at {n_scr} of {total} budgets"
    )
    assert "at every budget" not in cap.group(1), (
        "the gap is not negative at every budget; see the recount above"
    )


def test_figure5_caption_holm_minima_match_the_csv():
    rows = [r for r in csv.DictReader(open(RESULTS / "table26_xpop_lowlabel.csv")) if r["p_holm"]]
    overall = min(float(r["p_holm"]) for r in rows)
    plotted = min(float(r["p_holm"]) for r in rows if r["rule"] == "f1_at_half")
    cap = re.search(r"!\[Figure 5\.(.*?)\]\(", MS, re.S).group(1)
    for v in (overall, plotted):
        assert f"{v:.3f}" in cap, f"caption must quote Holm minimum {v:.3f}"
    assert str(len(rows)) in cap, f"caption must state the family size ({len(rows)} tests)"


# --------------------------------------------------------------- figure 6
# Motivating defects (2026-08-12), both in figure6's right panel:
#   (a) the annotation used a fixed 3-decimal format, so the headline
#       contrast's raw p = 0.0002 rendered as "p = 0.000" -- a value no
#       p-value can take, and one a referee would flag on sight;
#   (b) the row plotted was picked positionally as rows[0], while
#       table13_threshold_sensitivity.csv holds TWO benchmarks x six
#       budgets. Any re-sort of that CSV would have silently swapped the
#       candidate-filtered numbers into a panel the text reads as uniform.

def test_p_fmt_never_renders_a_p_value_as_zero():
    from analysis.make_figures import p_fmt
    for v in (0.0002, 1e-6, 0.0009, 0.00049):
        out = p_fmt(v)
        assert float(out) > 0, f"p_fmt({v}) -> {out!r} reads as zero"
    assert p_fmt(0.5273) == "0.527"
    assert p_fmt(0.0374) == "0.037"


def test_figure6_selects_its_row_by_key_not_position():
    src = (ROOT / "analysis" / "make_figures.py").read_text()
    body = re.search(r"^def figure6\(.*?(?=^def |\Z)", src, re.M | re.S).group(0)
    assert "rows[0]" not in body, (
        "figure6 must not pick its row positionally: "
        "table13 holds two benchmarks x six budgets"
    )
    assert 'r["benchmark"] == "uniform"' in body
    assert 'float(r["label_frac"]) == 0.01' in body


def test_table13_has_exactly_one_uniform_smallest_budget_row():
    rows = list(csv.DictReader(open(RESULTS / "table13_threshold_sensitivity.csv")))
    hit = [r for r in rows if r["benchmark"] == "uniform"
           and float(r["label_frac"]) == 0.01]
    assert len(hit) == 1
    assert float(hit[0]["p_F1@0.5"]) < 0.001, (
        "this row is the reason p_fmt exists; if its p is no longer "
        "sub-milli the formatter test above is no longer load-bearing"
    )


def test_manuscript_quotes_the_headline_p_at_full_precision():
    rows = list(csv.DictReader(open(RESULTS / "table13_threshold_sensitivity.csv")))
    hit = next(r for r in rows if r["benchmark"] == "uniform"
               and float(r["label_frac"]) == 0.01)
    assert hit["p_F1@0.5"] in MS, (
        f"manuscript must quote raw p = {hit['p_F1@0.5']}, not a rounded 0.000"
    )


def test_figure_function_names_match_the_files_they_write():
    """Each figureN() must write figureN_*.png.

    Motivating defect (2026-08-12): figure6() wrote
    figure8_hardneg_benchmark.png and figure8() wrote
    figure6_threshold_sensitivity.png. The names had drifted from the
    numbering, so a gate written against `def figure6` inspected the wrong
    panel and failed on a clean tree. Names that lie about their output are
    a standing trap for exactly this kind of review.
    """
    src = (ROOT / "analysis" / "make_figures.py").read_text()
    bodies = re.finditer(r"^def (figure\w+)\(.*?(?=^def |\Z)", src, re.M | re.S)
    checked = 0
    for m in bodies:
        name, body = m.group(1), m.group(0)
        outs = re.findall(r'savefig\(out / "([^"]+)"', body)
        assert outs, f"{name} writes no figure"
        for o in outs:
            assert o.startswith(name + "_"), f"{name}() writes {o}"
        checked += 1
    assert checked == 10, f"expected 10 figure functions, found {checked}"
