"""Gates on manuscript table numbering and the corrected cross-ancestry sweep.

Motivation (2026-08-12): the corrected cross-ancestry re-run was first inserted
as "Table 26", borrowing the number from its results CSV (`table26_*.csv`). The
results/ files are numbered in the order they were *produced*; manuscript tables
are numbered in the order they are *read*. The two sequences are unrelated, and
the manuscript had no Table 16-26 at all, so the reference dangled. Renumbering
it to Table 8 required shifting the old 8-15 up by one.

These gates keep both invariants: numbering follows document position, and every
reference resolves. The CSV keeps its own name -- files are not renumbered when
the prose is, so `table26_xpop_lowlabel.csv` backing manuscript Table 8 is
expected, not a bug.
"""
import csv
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
MS = (ROOT / "docs" / "AlignSSL_SV_manuscript.md").read_text()
sys.path.insert(0, str(ROOT / "analysis"))
from pfmt import p_fmt  # noqa: E402


CAPTIONS = [(m.start(), int(m.group(1))) for m in re.finditer(r"^\*\*Table (\d+)\.", MS, re.M)]


def test_captions_are_numbered_in_document_order():
    nums = [n for _, n in CAPTIONS]
    assert nums == sorted(nums), f"table captions out of order: {nums}"
    assert nums == list(range(1, len(nums) + 1)), f"numbering is not 1..N contiguous: {nums}"


def test_every_table_reference_resolves_to_a_caption():
    defined = {n for _, n in CAPTIONS}
    referenced = {int(m.group(1)) for m in re.finditer(r"Table (\d+)\b", MS)}
    dangling = sorted(referenced - defined)
    assert not dangling, f"references to nonexistent tables: {dangling}"


def test_corrected_xpop_table_supersedes_the_precorrection_one():
    """The corrected re-run must precede, and explicitly supersede, Table 9."""
    corrected = re.search(r"\*\*Table (\d+)\. Cross-ancestry transfer, corrected protocol", MS)
    pre = re.search(r"\*\*Table (\d+)\. Cross-ancestry transfer, pre-correction protocol", MS)
    assert corrected and pre, "both cross-ancestry tables must be present"
    c, p = int(corrected.group(1)), int(pre.group(1))
    assert c < p, f"corrected table (#{c}) must be presented before pre-correction (#{p})"
    assert f"Supersedes Table {p}" in MS, "corrected caption must say it supersedes the older one"


# PROGRESS.md quotes its own superseded reasoning; those blocks are fenced with
# the same marker the GIAB gates use and are excluded here too.
EXEMPT = re.compile(
    r"<!-- giab-scope-gate: quoted-history-below -->.*?"
    r"<!-- giab-scope-gate: quoted-history-above -->",
    re.S,
)


def test_no_document_still_calls_the_xpop_rerun_deferred():
    """The re-run was performed; nothing may still list it as an open item.

    Scope note: this gate was first written per *sentence*, and it missed the
    real defect it exists for. PROGRESS.md's deferral bullet named the sweep in
    one sentence and called it "the cheapest open item in the paper" two
    sentences later, so no single sentence contained both halves. It passed
    while the document was wrong, and only looked healthy because the
    falsification injected both halves into one sentence. The unit of a claim
    like this is the paragraph (here, the markdown bullet), so scan paragraphs.
    """
    DEFER = re.compile(
        r"cheapest .{0,40}open item|has not been re-?run|did not re-?run"
        r"|remains? (?:to be )?re-?run|deferred, not dismissed",
        re.I,
    )
    # A paragraph may carry the phrase only while explicitly marking it as past.
    SUPERSEDED = re.compile(
        r"\bDONE\b|superseding|superseded|has since been|was wrong|kept for audit",
        re.I,
    )
    for name in ("docs/AlignSSL_SV_manuscript.md", "README.md", "PROGRESS.md"):
        text = EXEMPT.sub(" ", (ROOT / name).read_text())
        for para in re.split(r"\n\s*\n|\n(?=[-*] )", text):
            if not re.search(r"cross[- ]ancestry|cross[- ]population", para, re.I):
                continue
            if DEFER.search(para):
                assert SUPERSEDED.search(para), (
                    f"{name} still defers the cross-ancestry re-run:\n"
                    f"{para.strip()[:300]}"
                )


def test_manuscript_xpop_numbers_match_the_results_csv():
    """Every quoted held-out-CEU statistic must come from table26_xpop_lowlabel.csv."""
    rows = {
        (r["label_frac"], r["rule"]): r
        for r in csv.DictReader((ROOT / "results" / "table26_xpop_lowlabel.csv").open())
        if r["site"] == "xpop" and r["p_raw"] != ""
    }
    assert len(rows) == 18, f"expected 18 held-out CEU cells, got {len(rows)}"

    # Parse the two sentences that quote a triple of p-values and compare each
    # in position against the CSV. An earlier version of this gate only asserted
    # that the number appeared *somewhere* in the manuscript, which a misquote of
    # 0.500 -> 0.400 survived because "0.500" also occurs elsewhere; falsification
    # caught it. Order below is (fixed cut, tuned tau, threshold-free).
    RULES = ("f1_at_half", "f1_at_tau", "auprc")

    ten = re.search(
        r"not significant under any rule \(held-out CEU: "
        r"\*p\* = ([\d.]+) at the fixed cut, ([\d.]+) at tuned .{1,3}, ([\d.]+) threshold-free\)",
        MS,
    )
    assert ten, "the 10%-cell sentence quoting three p-values is missing or reworded"
    for rule, quoted in zip(RULES, ten.groups()):
        # Compare against the shared renderer, not round(): a rounded
        # comparison would demand "0.000" if this p ever got small.
        want = p_fmt(float(rows[("0.1", rule)]["p_raw"]))
        assert quoted == want, (
            f"10% {rule}: manuscript quotes p={quoted}, CSV renders {want}"
        )

    one = re.search(
        r"it is \*p\* = ([\d.]+) at the fixed 0\.5 cut, \*p\* = ([\d.]+) at a "
        r"tuned threshold, and \*p\* = ([\d.]+) threshold-free",
        MS,
    )
    assert one, "the 1%-cell sentence quoting three p-values is missing or reworded"
    for rule, quoted in zip(RULES, one.groups()):
        # Compare against the shared renderer, not round(): a rounded
        # comparison would demand "0.000" if this p ever got small.
        want = p_fmt(float(rows[("0.01", rule)]["p_raw"]))
        assert quoted == want, (
            f"1% {rule}: manuscript quotes p={quoted}, CSV renders {want}"
        )

    # No cell may survive Holm -- the section's central claim.
    all_rows = list(csv.DictReader((ROOT / "results" / "table26_xpop_lowlabel.csv").open()))
    survivors = [r for r in all_rows if r["survives_holm_0.05"] == "True"]
    assert not survivors, f"a cell now survives Holm; Section 4.6 must be rewritten: {survivors}"
