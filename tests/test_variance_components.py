"""Gates for the variance decomposition reported in Section 4.9.1.

The decomposition rests on one factual premise: the two from-scratch runs in
each pair share the labelled subset and differ only in the torch RNG stream. If
that premise ever breaks -- someone reseeds inside the arm loop, or the label
generator stops being re-created per invocation -- the "within split" column
silently starts measuring data variation too, and the reported run-noise share
becomes wrong in a way no test downstream would catch. These gates fail loudly
instead.
"""
from __future__ import annotations

import csv
import json
import pathlib
import re

import pytest

JSON_DIR = pathlib.Path("results/json_xpop_lowlabel")
TABLE = pathlib.Path("results/table27_variance_components.csv")
MS = pathlib.Path("docs/AlignSSL_SV_manuscript.md")
SEEDS = (0, 1, 2)

pytestmark = pytest.mark.skipif(
    not JSON_DIR.exists() or not TABLE.exists(),
    reason="cross-population low-label sweep artefacts not present",
)


def _pairs():
    for s in SEEDS:
        p = JSON_DIR / f"xpopll_pre_seed{s}.json"
        q = JSON_DIR / f"xpopll_scratch_seed{s}.json"
        if p.exists() and q.exists():
            yield s, json.load(open(p)), json.load(open(q))


def _rows():
    return list(csv.DictReader(open(TABLE)))


def test_pairs_share_label_budget_and_seed():
    """The controlled-contrast premise: same split, same seed, different stream."""
    n = 0
    for s, p, q in _pairs():
        a = [r["n_train"] for r in p["label_efficiency"]]
        b = [r["n_train"] for r in q["label_efficiency"]]
        assert a == b, f"seed {s}: label budgets differ -- not a controlled pair"
        assert p["config"]["seed"] == q["config"]["seed"] == s
        # The ONLY substantive config difference may be the encoder.
        diff = {k for k in set(p["config"]) | set(q["config"])
                if p["config"].get(k) != q["config"].get(k)}
        assert diff <= {"encoder", "out"}, f"seed {s}: unexpected config drift {diff}"
        n += 1
    assert n >= 2, f"need >=2 pairs for a decomposition, got {n}"


def test_scratch_runs_are_not_duplicates():
    """If the two runs were bit-identical the decomposition would be vacuous.

    Duplication is a property of a PAIR, so it is asserted per pair. An earlier
    version of this test pooled all cells and required <50% identical overall;
    that version passed when an entire seed was duplicated, because one fully
    duplicated seed out of three reads as 33%. A duplicated pair contributes
    sd_within == 0 at every budget and silently deflates the reported run-noise
    share, which is exactly the failure this gate exists to catch.
    """
    n_pairs = 0
    for s, p, q in _pairs():
        A = {r["frac"]: r for r in p["label_efficiency"]}
        B = {r["frac"]: r for r in q["label_efficiency"]}
        identical = total = 0
        for f in sorted(set(A) & set(B)):
            a, b = A[f].get("scratch"), B[f].get("scratch")
            if not (isinstance(a, dict) and isinstance(b, dict)):
                continue
            for site in ("in_dist", "xpop"):
                for rule in ("f1_at_half", "f1_at_tau", "auprc"):
                    total += 1
                    if abs(float(a[site][rule]) - float(b[site][rule])) < 1e-12:
                        identical += 1
        assert total > 0, f"seed {s}: no comparable cells"
        assert identical < 0.5 * total, (
            f"seed {s}: {identical}/{total} cells bit-identical -- these are "
            "duplicates, not independent training replicates"
        )
        n_pairs += 1
    assert n_pairs >= 2


def test_no_within_split_sd_is_degenerate():
    """A zero within-split sd would mean a duplicated pair reached the table."""
    zeros = [r for r in _rows() if float(r["sd_within_split"]) == 0.0]
    assert not zeros, f"{len(zeros)} cells have sd_within_split == 0: {zeros[:2]}"


def test_table_columns_are_internally_consistent():
    for r in _rows():
        sw, sb, st = (float(r["sd_within_split"]), float(r["sd_between_split"]),
                      float(r["sd_total"]))
        assert abs(st - (sb ** 2 + sw ** 2) ** 0.5) < 5e-4, r
        if r["run_noise_share"]:
            assert abs(float(r["run_noise_share"]) - sw ** 2 / st ** 2) < 5e-3, r
        assert float(r["mde_paired_n3"]) > 0
        assert int(r["runs_per_split"]) == 2


def test_manuscript_numbers_match_the_table():
    """Section 4.9.1 quotes a median ratio, a dominance count and a median MDE."""
    import statistics

    rows = _rows()
    ratios = [float(r["within_over_between"]) for r in rows if r["within_over_between"]]
    shares = [float(r["run_noise_share"]) for r in rows if r["run_noise_share"]]
    mdes = [float(r["mde_paired_n3"]) for r in rows]
    text = MS.read_text()

    med_ratio = statistics.median(ratios)
    dominates = sum(1 for x in ratios if x >= 1.0)
    med_share = statistics.median(shares)
    med_mde = statistics.median(mdes)

    assert f"median ratio {med_ratio:.2f}" in text, med_ratio
    assert f"{dominates} of {len(ratios)} cells" in text, (dominates, len(ratios))
    assert f"{round(med_share * 100)}% of total variance" in text, med_share
    assert f"**{med_mde:.2f} AUPRC**" in text, med_mde


def test_manuscript_reports_the_corrected_not_the_pseudoreplicated_test():
    """The discarded sign test must be presented as discarded, with both numbers."""
    text = MS.read_text()
    assert "13 of 18" in text
    assert "pseudo-replication" in text
    # The bad p-value may appear only as the thing being corrected, never alone.
    i = text.find("*p* = 0.005")
    assert i > 0
    window = text[i:i + 900]
    assert "pseudo-replication" in window, "the discarded p-value lacks its correction nearby"


def test_section_exists_and_is_numbered_under_49():
    text = MS.read_text()
    assert re.search(r"^### 4\.9\.1 ", text, re.M), "Section 4.9.1 heading missing"
