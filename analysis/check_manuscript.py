#!/usr/bin/env python3
"""Verify that every number in the manuscript's tables matches the generated
result tables, and that every p-value quoted in the prose exists in
results/stats_tests.csv.

This exists because an earlier draft contained a calibration table with no
backing file and a baseline column whose values came from a superseded
experiment generation. Any manuscript edit must keep this check passing.

Rounding: tables are rendered at 3 decimal places using round-half-away-from-
zero (the convention a reader assumes), which differs from Python's
round() at exact half-boundaries -- hence the explicit quantiser below rather
than round().

Usage:
    python analysis/check_manuscript.py [--md docs/AlignSSL_SV_manuscript.md]
                                        [--results results]
Exit code 0 = all checks pass, 1 = at least one mismatch.
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ARM_COLUMNS = ["AlignSSL-combined", "AlignSSL-scratch", "DeepSV-representation",
               "Classical-logreg", "Classical-GBT"]


def q3(x: float) -> str:
    """Render at 3 dp with round-half-away-from-zero."""
    return str(Decimal(repr(float(x))).quantize(Decimal("0.001"),
                                                rounding=ROUND_HALF_UP))


def load_table1(results: Path) -> dict:
    src = {}
    with open(results / "table1_label_efficiency.csv") as fh:
        for r in csv.DictReader(fh):
            src[(float(r["label_frac"]), r["arm"])] = (float(r["F1_mean"]),
                                                       float(r["F1_sd"]))
    return src


def check_table1(md: str, src: dict) -> list[str]:
    """Table 1 has columns: frac | n | <5 arms in ARM_COLUMNS order>."""
    m = re.search(r"\| Label fraction \| n train \|.*?\n\n", md, re.S)
    if m is None:
        return ["Table 1 block not found in manuscript"]
    errs = []
    for line in m.group(0).splitlines():
        if not line.startswith("| ") or "---" in line or "Label fraction" in line:
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        frac = float(cells[0].rstrip("%")) / 100
        for i, arm in enumerate(ARM_COLUMNS):
            shown = cells[2 + i].replace("**", "")
            key = (frac, arm)
            if key not in src:
                errs.append(f"Table 1: no source row for {arm} @ {frac}")
                continue
            sm, ss = src[key]
            want = f"{q3(sm)} ± {q3(ss)}"
            if shown != want:
                errs.append(f"Table 1 {arm} @{frac}: manuscript '{shown}' "
                            f"!= source '{want}'")
    return errs


def check_calibration(md: str, results: Path) -> list[str]:
    with open(results / "table2_calibration.csv") as fh:
        src = {r["arm"]: r for r in csv.DictReader(fh)}
    errs = []
    # every per-seed ECE list quoted in prose or table must match source
    for arm, r in src.items():
        seeds = r["ECE_per_seed"].split(";")
        rendered = "; ".join(f"{float(s):.4f}" for s in seeds)
        if rendered not in md:
            errs.append(f"Calibration: per-seed ECE for {arm} "
                        f"('{rendered}') absent from manuscript")
    return errs


def check_pvalues(md: str, results: Path) -> list[str]:
    """Every p-value quoted in prose must appear in stats_tests.csv."""
    with open(results / "stats_tests.csv") as fh:
        src = [float(r["p_value"]) for r in csv.DictReader(fh)]
    errs = []
    # decimal form, e.g. "p = 0.025"
    for tok in re.findall(r"\*p\* = (0\.[0-9]+)", md):
        v = float(tok)
        if not any(abs(v - s) <= 5e-4 or
                   (s > 0 and abs(v - float(f"{s:.{max(1, len(tok) - 2)}f}")) < 1e-12)
                   for s in src):
            errs.append(f"p-value {tok} quoted in prose has no match in "
                        f"stats_tests.csv")
    # scientific form, e.g. "9.2 x 10^-4"
    for mant, exp in re.findall(r"\*p\* = ([0-9.]+) × 10⁻([0-9⁻]+)", md):
        e = int(exp.replace("⁻", ""))
        v = float(mant) * 10 ** (-e)
        if not any(abs(v - s) < 0.15 * max(v, s) for s in src):
            errs.append(f"p-value {mant}e-{e} quoted in prose has no match")
    return errs


def check_single_feature_auc(md: str, results: Path) -> list[str]:
    """Table 6: every feature's AUC and oriented AUC must match source.

    These are the paper's separability-control numbers and are quoted in the
    abstract, contributions, results and conclusion, so they get the strictest
    check: every row of the source table must appear verbatim in the manuscript,
    at the same rounding.
    """
    path = results / "table6_single_feature_auc.csv"
    if not path.exists():
        return [f"{path} missing (run scripts/single_feature_auc.py)"]
    errs = []
    with open(path) as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        auc, ori = float(r["auc"]), float(r["auc_oriented"])
        if f"{auc:.3f}" not in md:
            errs.append(f"Table 6: AUC {auc:.3f} for {r['feature']} absent "
                        "from manuscript")
        if f"{ori:.3f}" not in md:
            errs.append(f"Table 6: oriented AUC {ori:.3f} for {r['feature']} "
                        "absent from manuscript")
    # the headline number must be the maximum, not merely present
    top = max(rows, key=lambda r: float(r["auc_oriented"]))
    if f"ROC-AUC = {float(top['auc_oriented']):.3f}" not in md:
        errs.append(f"Table 6: headline 'ROC-AUC = "
                    f"{float(top['auc_oriented']):.3f}' "
                    f"({top['feature']}) not stated in manuscript")
    return errs


def check_markers(md: str) -> list[str]:
    bad = re.findall(r"\{\{artifact:[^}]*[A-Z_]{4,}[^}]*\}\}", md)
    return [f"unresolved artifact placeholder: {b}" for b in bad]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--md", default="docs/AlignSSL_SV_manuscript.md")
    p.add_argument("--results", default="results")
    a = p.parse_args()

    md = Path(a.md).read_text()
    res = Path(a.results)

    errs: list[str] = []
    errs += check_table1(md, load_table1(res))
    errs += check_calibration(md, res)
    errs += check_pvalues(md, res)
    errs += check_single_feature_auc(md, res)
    errs += check_markers(md)

    if errs:
        print(f"FAIL: {len(errs)} manuscript/source mismatches")
        for e in errs:
            print("  -", e)
        return 1
    print("PASS: manuscript tables and quoted p-values reconcile with "
          f"{a.results}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
