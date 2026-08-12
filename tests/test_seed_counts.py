"""Every seed count stated in a caption must match its source CSV.

Four captions in the manuscript understated replication before this gate
existed: Table 1 said "3 seeds per arm" where the source records 4 for the
pretrained arm and 10 for the other two; Table 10 said "4 seeds per arm"
for a 4-versus-10 comparison; Table 15 said "3 seeds for the deep arms";
and Table 12 said "four seeds per deep arm, ten for the classical
controls" for a table whose source contains no classical arm at all.

All four errors understated the work done, which is why no reviewer would
have caught them from the numbers alone -- the means and standard
deviations were correct. The failure was in the prose describing how they
were obtained, and that is exactly what a value-provenance check (which
asks only whether a decimal exists in some CSV) cannot see.

The gate is deliberately two-sided. It asserts that the source still
records the seed counts we claim (so a re-run that changes replication
fails here rather than silently invalidating the caption), and that the
caption still states them (so an edit that reverts to a round "3 seeds
per arm" fails too).
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MD = ROOT / "docs" / "AlignSSL_SV_manuscript.md"
RESULTS = ROOT / "results"


def _seeds(filename: str, key_cols: tuple[str, ...], seed_col: str) -> dict[tuple, set[str]]:
    """Map the key columns of a results CSV to the seed counts recorded."""
    out: dict[tuple, set[str]] = {}
    path = RESULTS / filename
    with path.open(newline="", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            out.setdefault(tuple(row[c] for c in key_cols), set()).add(row[seed_col])
    return out


def _caption(table_no: int) -> str:
    """The caption of a numbered table.

    Two styles are in use and both must be read, because an extractor
    that handles only one silently returns an empty string for the other
    -- which would make every assertion below fail for a reason that has
    nothing to do with seed counts:

        **Table 1. caption text.**   bold encloses the whole caption
        **Table 12.** caption text.  bold closes after the number

    So: take everything from the table number to the blank line that
    precedes the table body, then strip bold markers.
    """
    md = MD.read_text(encoding="utf-8")
    m = re.search(rf"\*\*Table {table_no}\.(.*?)(?=\n\s*\n)", md, re.S)
    assert m, f"Table {table_no}: no caption found"
    cap = re.sub(r"\s+", " ", m.group(1)).replace("**", "").strip()
    assert cap, f"Table {table_no}: caption extracted empty"
    return cap


# (table number, source file, {arm: expected seed count})
CASES = [
    (1, "table12_label_efficiency_fixed.csv",
     {"AlignSSL-pretrained": "4", "AlignSSL-scratch": "10",
      "DeepSV-representation": "10"}),
    (15, "table12_label_efficiency_fixed.csv",
     {"AlignSSL-pretrained": "4", "AlignSSL-scratch": "10",
      "DeepSV-representation": "10", "Classical-logreg": "10",
      "Classical-GBT": "10"}),
    (12, "table20_alignssl_vs_deepsv.csv",
     {"AlignSSL-pretrained": "4", "AlignSSL-scratch": "10"}),
]


@pytest.mark.parametrize("table_no,source,expected", CASES,
                         ids=[f"table{c[0]}" for c in CASES])
def test_source_still_records_the_claimed_seed_counts(table_no, source, expected):
    """The CSV is the authority: if replication changed, this fails first."""
    seeds = _seeds(source, ("arm",), "n_seeds")
    for arm, n in expected.items():
        got = seeds.get((arm,))
        assert got == {n}, (
            f"Table {table_no}: {source} records n_seeds={got} for {arm}, "
            f"caption is written for {n}")


@pytest.mark.parametrize("table_no,source,expected", CASES,
                         ids=[f"table{c[0]}" for c in CASES])
def test_caption_states_every_distinct_seed_count(table_no, source, expected):
    """The caption must name each distinct count and its source file."""
    cap = _caption(table_no)
    for n in sorted(set(expected.values()), key=int):
        assert re.search(rf"(?<![\d.]){n}(?![\d.])", cap), (
            f"Table {table_no} caption does not state the seed count {n}: {cap!r}")
    assert source in cap, (
        f"Table {table_no} caption does not name its source {source}: {cap!r}")


def test_table10_states_the_unequal_group_sizes():
    """Table 10 compares 4 pretrained seeds against 10 from-scratch seeds.

    Stated separately from CASES because its source is the threshold
    sweep, which stores arms as columns rather than rows, so there is no
    per-arm seed column to read.
    """
    cap = _caption(10)
    assert "4 pretrained seeds" in cap and "10 from-scratch seeds" in cap, cap
    assert "table13_threshold_sensitivity.csv" in cap, cap
    assert not re.search(r"\d+ seeds per arm", cap), (
        "Table 10 groups are unequal; 'N seeds per arm' misstates the design")


def test_table12_does_not_claim_classical_controls():
    """Its source compares the two learned arms only -- no classical rows."""
    with (RESULTS / "table20_alignssl_vs_deepsv.csv").open(
            newline="", encoding="utf-8-sig") as fh:
        arms = {r["arm"] for r in csv.DictReader(fh)}
    assert not any(a.startswith("Classical") for a in arms), arms
    cap = _caption(12)
    assert re.search(r"classical controls do not appear", cap, re.I), cap


def test_no_caption_claims_three_seeds_per_arm():
    """The specific wrong phrasing that four captions carried."""
    md = MD.read_text(encoding="utf-8")
    for m in re.finditer(r"\*\*Table \d+\.(.*?)\*\*", md, re.S):
        cap = re.sub(r"\s+", " ", m.group(1))
        assert not re.search(r"\b3 seeds per arm\b", cap), cap


if __name__ == "__main__":  # runnable without pytest (cluster env has none)
    for tno, src, exp in CASES:
        test_source_still_records_the_claimed_seed_counts(tno, src, exp)
        test_caption_states_every_distinct_seed_count(tno, src, exp)
    test_table10_states_the_unequal_group_sizes()
    test_table12_does_not_claim_classical_controls()
    test_no_caption_claims_three_seeds_per_arm()
    print("PASS: every caption seed count matches its source CSV")
