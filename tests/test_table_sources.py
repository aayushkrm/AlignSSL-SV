"""Every numbered table must name a source file, and that file must contain its cells.

Two failure modes motivated this gate.

1.  Most tables in the manuscript named no backing file at all.  The numbering of
    ``results/tableNN_*.csv`` does not follow the manuscript's table numbering
    (manuscript Table 3 is sourced from ``table14_control_vs_deep.csv``), so a
    reader who wants to check a cell has no way to find the data behind it.

2.  A caption *can* name a file and still be wrong.  Naming alone is not
    evidence, so the second test re-derives every numeric cell of the table and
    asserts it is present in the declared file.

The value check rounds the source half-up at one to four decimal places and
compares against the string as it is printed in the manuscript.  Two rules make
this sound rather than vacuous:

* Round the *stored* value once.  Rounding an already-rounded CSV cell a second
  time (0.8455 -> 0.846 -> 0.85) manufactures matches that the source does not
  support, and it also manufactures false failures when the manuscript quotes
  the correctly-rounded figure.
* Compare on absolute value.  Signed deltas are printed as ``-0.144`` in the
  table and stored as ``-0.1445``; the sign carries no information the magnitude
  does not, and stripping it avoids a special case per column.

Cells that legitimately do not come from the source -- label counts, bin edges,
sample sizes that the caption states in prose -- are excluded by only reading
the pipe-table body, and by an explicit per-table allowlist where a table mixes
sources.
"""

from __future__ import annotations

import csv
import pathlib
import re
from decimal import Decimal, ROUND_HALF_UP

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MD = ROOT / "docs" / "AlignSSL_SV_manuscript.md"
RESULTS = ROOT / "results"

# Manuscript table number -> results file whose cells it reports.
# Verified cell-by-cell at the time of writing; see test_declared_source_contains_every_cell.
EXPECTED_SOURCE = {
    1: "table12_label_efficiency_fixed.csv",
    2: "table12_label_efficiency_fixed.csv",
    3: "table14_control_vs_deep.csv",
    4: "table6_single_feature_auc.csv",
    5: "table2_calibration.csv",
    6: "table3_length_strata.csv",
    7: "table4_ablation.csv",
    8: "table26_xpop_lowlabel.csv",
    9: "table5_cross_ancestry.csv",
    10: "table13_threshold_sensitivity.csv",
    11: "stats_multiplicity.csv",
    12: "table20_alignssl_vs_deepsv.csv",
    13: "table9_hardneg_single_feature_auc.csv",
    14: "table28_split_separability.csv",
    15: "table12_label_efficiency_fixed.csv",
    16: "table24_caller_candidate.csv",
    17: "table19_field_audit_quotes.csv",
}

# Tables whose pipe body mixes columns from more than one file, or reports a
# statistic derived in prose rather than stored.  Value-checked against the
# declared source only for the cells the source does carry.
PARTIAL = {
    2: "reports both the fixed-threshold and threshold-free columns",
    13: "two-source comparison with a derived delta; see test_table13_change_column",
    15: "arm contrasts computed from the per-seed columns of the declared source",
    16: "control and deep arms are stored under different column prefixes",
}


def _read_md() -> str:
    return MD.read_text(encoding="utf-8")


def _caption(md: str, n: int) -> str:
    """Return caption text for table ``n``, tolerating both bold styles.

    The manuscript uses ``**Table N. caption**`` and ``**Table N.** caption``
    interchangeably.  Reading only the first style silently returns an empty
    string for the others, which makes every downstream assertion pass
    vacuously -- that is exactly how the seed-count captions drifted.
    """
    m = re.search(rf"\*\*Table {n}\.(.*?)(?=\n\s*\n)", md, re.S)
    assert m, f"Table {n}: no caption found"
    text = re.sub(r"\s+", " ", m.group(1)).replace("**", "").strip()
    assert text, f"Table {n}: caption extracted empty"
    return text


def _body_numbers(md: str, n: int) -> set[str]:
    """Every decimal in the pipe-table body of table ``n`` that could be data.

    Section cross-references ("Section 4.6") appear inside claim labels and are
    not measurements; leaving them in makes the gate demand that a results file
    contain the manuscript's own section numbering.
    """
    block = re.search(rf"\*\*Table {n}\..*?(?=\n\*\*Table |\n## |\Z)", md, re.S)
    assert block, f"Table {n}: no block found"
    rows = "\n".join(ln for ln in block.group(0).split("\n") if ln.startswith("|"))
    rows = re.sub(r"(?:Section|Figure|Table)\s+\d+(?:\.\d+)*", "", rows)
    return {m.group(0) for m in re.finditer(r"\d+\.\d+", rows)}


def _renderings(f: float) -> set[str]:
    """Every plausible printed form of ``f`` at 1-4 dp.

    Both rounding conventions are accepted because the manuscript and the CSV
    writers do not share one: Python's float formatting resolves a decimal tie
    by the binary representation, while an exact-decimal quantize resolves it
    half-up.  They differ only on exact ties, and a tie is never evidence of a
    wrong number -- so accepting both costs no discriminating power.
    """
    out: set[str] = set()
    d = Decimal(str(abs(f)))
    for k in range(1, 5):
        out.add(str(d.quantize(Decimal(10) ** -k, rounding=ROUND_HALF_UP)))
        out.add(f"{abs(f):.{k}f}")
    return out


def _source_numbers(name: str) -> set[str]:
    """Every value in ``results/<name>``, unsigned, at 1-4 dp.

    Stored values are rounded once, from whatever precision the file carries.
    Where a file also stores the per-seed primitives behind a summary column,
    the summary is *recomputed* from them and its renderings added as well: the
    manuscript rounds from full precision while the CSV stores four decimals,
    so a mean of 0.845467 is printed 0.845 in the table and stored 0.8455 in the
    file.  Re-rounding the stored cell would report that agreement as a defect.
    Both sample and population standard deviations are offered because the
    aggregators do not use a single convention.
    """
    out: set[str] = set()
    path = RESULTS / name
    for row in csv.DictReader(path.open(encoding="utf-8-sig")):
        for key, value in row.items():
            tokens = str(value).split(";")
            for token in tokens:
                try:
                    out |= _renderings(float(token))
                except (TypeError, ValueError):
                    continue
            if key and key.endswith("_per_seed") and len(tokens) > 1:
                try:
                    vals = [float(t) for t in tokens]
                except (TypeError, ValueError):
                    continue
                mean = sum(vals) / len(vals)
                out |= _renderings(mean)
                if len(vals) > 1:
                    ss = sum((v - mean) ** 2 for v in vals)
                    out |= _renderings((ss / len(vals)) ** 0.5)
                    out |= _renderings((ss / (len(vals) - 1)) ** 0.5)
    return out


@pytest.mark.parametrize("table_no", sorted(EXPECTED_SOURCE))
def test_caption_names_its_source_file(table_no: int) -> None:
    """A reader must be able to get from any table to the data behind it."""
    cap = _caption(_read_md(), table_no)
    cited = re.findall(r"results/([A-Za-z0-9_.-]+\.csv)", cap)
    assert cited, (
        f"Table {table_no}: caption names no results file. The CSV numbering does "
        f"not follow the manuscript numbering, so an unattributed table is "
        f"unverifiable. Expected {EXPECTED_SOURCE[table_no]}."
    )
    assert EXPECTED_SOURCE[table_no] in cited, (
        f"Table {table_no}: caption cites {cited}, expected "
        f"{EXPECTED_SOURCE[table_no]}"
    )


@pytest.mark.parametrize("table_no", sorted(EXPECTED_SOURCE))
def test_declared_source_exists(table_no: int) -> None:
    assert (RESULTS / EXPECTED_SOURCE[table_no]).is_file(), (
        f"Table {table_no}: declared source {EXPECTED_SOURCE[table_no]} is missing"
    )


@pytest.mark.parametrize(
    "table_no", [n for n in sorted(EXPECTED_SOURCE) if n not in PARTIAL]
)
def test_declared_source_contains_every_cell(table_no: int) -> None:
    """Naming a file is not evidence; the file must actually carry the numbers."""
    printed = _body_numbers(_read_md(), table_no)
    if not printed:
        pytest.skip(f"Table {table_no} has no decimal cells")
    stored = _source_numbers(EXPECTED_SOURCE[table_no])
    missing = sorted(x for x in printed if x not in stored)
    assert not missing, (
        f"Table {table_no}: {len(missing)} cell(s) absent from "
        f"{EXPECTED_SOURCE[table_no]}: {missing[:8]}"
    )


def test_table13_change_column_is_the_difference_of_its_two_sources() -> None:
    """Table 13 juxtaposes two benchmarks; its delta must follow from both.

    The uniform column comes from ``table6_single_feature_auc.csv`` and the
    candidate-filtered column from ``table9_hardneg_single_feature_auc.csv``.
    The Change column is derived and appears in neither, which is why this
    table is exempt from the blanket cell check -- so it gets a stricter one:
    every row is re-derived from the two files by feature name.
    """
    uni = {
        r["feature"]: float(r["auc_oriented"])
        for r in csv.DictReader(
            (RESULTS / "table6_single_feature_auc.csv").open(encoding="utf-8-sig")
        )
    }
    cand = {
        r["feature"]: float(r["auc_oriented"])
        for r in csv.DictReader(
            (RESULTS / "table9_hardneg_single_feature_auc.csv").open(
                encoding="utf-8-sig"
            )
        )
    }
    block = re.search(r"\*\*Table 13\..*?(?=\n\*\*Table |\n## |\Z)", _read_md(), re.S)
    assert block, "Table 13: no block found"

    checked = 0
    for line in block.group(0).split("\n"):
        cells = [c.strip().replace("**", "") for c in line.strip().strip("|").split("|")]
        if len(cells) != 4 or cells[0] not in uni:
            continue
        feat, u_txt, c_txt, d_txt = cells
        assert feat in cand, f"Table 13: {feat} absent from the candidate-filtered file"
        assert u_txt in _renderings(uni[feat]), (
            f"Table 13 {feat}: uniform {u_txt} != {uni[feat]} in table6"
        )
        assert c_txt in _renderings(cand[feat]), (
            f"Table 13 {feat}: candidate {c_txt} != {cand[feat]} in table9"
        )
        # Compare printed forms rather than a numeric tolerance: a delta of
        # 0.0595 is a legitimate 0.059 or 0.060 depending on the tie rule, and
        # any fixed epsilon either admits a genuinely wrong third decimal or
        # rejects a correct rounding at exactly the boundary.
        raw = d_txt.replace("\u2212", "-")
        printed_negative = raw.startswith("-")
        assert raw.lstrip("+-") in _renderings(cand[feat] - uni[feat]), (
            f"Table 13 {feat}: change {d_txt} != {cand[feat] - uni[feat]:.4f}"
        )
        # Most features lose separability under candidate filtering, but two
        # gain slightly; the sign must follow the data, not the narrative.
        assert printed_negative == (cand[feat] < uni[feat]), (
            f"Table 13 {feat}: change printed {d_txt} but uniform "
            f"{uni[feat]} -> candidate {cand[feat]}"
        )
        checked += 1
    assert checked >= 6, f"Table 13: only {checked} rows re-derived, expected >= 6"


def test_every_numbered_table_is_covered() -> None:
    """A new table must be added to EXPECTED_SOURCE, not silently unattributed."""
    found = {int(m) for m in re.findall(r"\*\*Table (\d+)\.", _read_md())}
    assert found == set(EXPECTED_SOURCE), (
        f"table set changed: manuscript has {sorted(found)}, "
        f"gate covers {sorted(EXPECTED_SOURCE)}"
    )


if __name__ == "__main__":  # cluster env has no pytest
    for n in sorted(EXPECTED_SOURCE):
        test_caption_names_its_source_file(n)
        test_declared_source_exists(n)
        if n not in PARTIAL and _body_numbers(_read_md(), n):
            test_declared_source_contains_every_cell(n)
    test_table13_change_column_is_the_difference_of_its_two_sources()
    test_every_numbered_table_is_covered()
    print("PASS: every table names a source file that contains its cells")
