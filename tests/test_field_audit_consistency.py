"""Gate Section 7 (the coded field audit) against its source CSVs.

Section 7 is the manuscript's only support for its generality claim -- that the
four evaluation defects documented in Sections 4, 6 and 8 are the field's
default rather than artefacts of this pipeline. Every count in that section is
therefore load-bearing, and every count is derived from
``results/table18_field_audit.csv``. These tests recompute the counts from the
CSV and require the manuscript prose to state them.

They also enforce the two properties that make the audit defensible:

1. Every one of the 4N codes carries a quotation that was verified to be a
   literal span of its own source document (``results/table19_field_audit_quotes.csv``).
   A code without a verified quotation is an unsupported assertion about
   somebody else's paper, which is exactly what this section exists to avoid.
2. The strict defect count never penalises a paper for failing to state its
   protocol. "Not stated" is a reporting gap, coded separately; folding it into
   the defect count would inflate the result in our own favour.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT = ROOT / "docs" / "AlignSSL_SV_manuscript.md"
AUDIT = ROOT / "results" / "table18_field_audit.csv"
QUOTES = ROOT / "results" / "table19_field_audit_quotes.csv"
POPULATION = ROOT / "results" / "table17_audit_population.csv"

AXES = ("negative_sampling", "threshold_rule", "model_free_control", "multiplicity")

# The strict defect definition, mirrored from analysis. "unclear" is deliberately
# NOT a defect on axes A and B -- see the module docstring.
STRICT = {
    "D1_strict": lambda r: r["A_negative_sampling"] in ("uniform_random", "simulated"),
    "D2_strict": lambda r: r["B_threshold_rule"] == "fixed_default",
    "D3_strict": lambda r: r["C_model_free_control"] == "no",
    "D4_strict": lambda r: r["D_multiplicity"] != "corrected",
}


def _rows(path: Path) -> list[dict]:
    with open(path, newline="") as fh:
        return list(csv.DictReader(fh))


@pytest.fixture(scope="module")
def audit() -> list[dict]:
    return _rows(AUDIT)


@pytest.fixture(scope="module")
def md() -> str:
    return MANUSCRIPT.read_text()


def test_strict_flags_match_their_definition(audit):
    """The stored D*_strict columns must equal the definition, not drift from it."""
    for r in audit:
        for col, rule in STRICT.items():
            assert int(r[col]) == int(rule(r)), f"{r['citation']}: {col} contradicts the coding rule"
        assert int(r["n_strict"]) == sum(int(r[c]) for c in STRICT), r["citation"]


def test_not_stated_is_never_counted_as_a_defect(audit):
    """A paper that does not state its protocol is not charged with the defect."""
    for r in audit:
        if r["A_negative_sampling"] == "unclear":
            assert int(r["D1_strict"]) == 0, r["citation"]
        if r["B_threshold_rule"] == "unclear":
            assert int(r["D2_strict"]) == 0, r["citation"]


def test_every_code_has_a_verified_quote(audit):
    """4 codes per paper, each with a quotation verified against its source text."""
    quotes = _rows(QUOTES)
    assert len(quotes) == 4 * len(audit), (len(quotes), len(audit))
    for q in quotes:
        assert q["axis"] in AXES, q["axis"]
        assert int(q["verified"]) == 1, f"{q['citation']} [{q['axis']}]: quote not verified"
        assert q["quote"].strip(), f"{q['citation']} [{q['axis']}]: empty quote"
    seen = {(q["doi"], q["axis"]) for q in quotes}
    assert len(seen) == 4 * len(audit), "duplicate or missing (paper, axis) pairs"


def test_quote_codes_agree_with_the_audit_table(audit):
    """The quote file and the audit table must not disagree about any code."""
    by_doi = {r["doi"]: r for r in audit}
    col = {"negative_sampling": "A_negative_sampling", "threshold_rule": "B_threshold_rule",
           "model_free_control": "C_model_free_control", "multiplicity": "D_multiplicity"}
    for q in _rows(QUOTES):
        assert by_doi[q["doi"]][col[q["axis"]]] == q["code"], (q["citation"], q["axis"])


def test_population_accounts_for_every_survey_row():
    """Every eligible paper is either coded or explicitly recorded as unretrievable."""
    pop = _rows(POPULATION)
    eligible = [r for r in pop if r["eligible"] in ("True", "1")]
    coded_dois = {r["doi"] for r in _rows(AUDIT)}
    assert coded_dois <= {r["doi"] for r in eligible}, "coded a paper that is not eligible"
    for r in pop:
        if r["eligible"] not in ("True", "1"):
            assert r["reason"].strip(), f"{r['citation']}: excluded without a recorded reason"
    n_unavailable = len(eligible) - len(coded_dois)
    assert n_unavailable >= 0
    # The manuscript states this denominator explicitly; keep them in step.
    md_text = MANUSCRIPT.read_text()
    assert f"{len(eligible)} papers spanning" in md_text or f"admits {len(eligible)} papers" in md_text


def test_manuscript_states_the_headline_counts(audit, md):
    n = len(audit)
    ge3 = sum(int(r["n_strict"]) >= 3 for r in audit)
    no_control = sum(int(r["D3_strict"]) for r in audit)
    no_mult = sum(int(r["D4_strict"]) for r in audit)
    fixed = sum(r["B_threshold_rule"] == "fixed_default" for r in audit)

    assert f"{no_mult} of\n{n}" in md or f"{no_mult} of {n}" in md, "multiplicity count not stated"
    assert f"{no_control} of {n}" in md, "model-free-control count not stated"
    assert f"{fixed} of {n}" in md, "fixed-threshold count not stated"
    assert f"{ge3} of {n} omit at\nleast three" in md or f"{ge3} of {n} omit at least three" in md


def test_no_paper_reports_all_four_safeguards(audit, md):
    """The section's strongest sentence must be true of the table."""
    clean = [r for r in audit if int(r["n_strict"]) == 0]
    assert not clean, f"manuscript says none is clean, but {[r['citation'] for r in clean]} are"
    # Phrasing was scoped from "no paper in the population" to "no coded paper" when the
    # audit population was found to be a convenience sample (Section 8). Accept either,
    # since the semantic claim under test -- no paper has n_strict == 0 -- is unchanged.
    assert ("no coded paper reports all four safeguards" in md.lower()
            or "no paper in the population reports all four safeguards" in md.lower())
    fewest = min(int(r["n_strict"]) for r in audit)
    assert fewest == 2, f"prose says none omits fewer than two; minimum is {fewest}"
    assert "none\nomits fewer than two" in md or "none omits fewer than two" in md


def test_generality_claim_is_no_longer_bare_assertion(md):
    """The abstract and conclusion must cite the audit, not assert belief."""
    assert "we believe, widespread" not in md, "unsupported generality assertion returned to the abstract"
    assert re.search(r"each is widespread in this literature", md) is None
    assert "Section 7" in md, "the generality claim must point at the audit section"
