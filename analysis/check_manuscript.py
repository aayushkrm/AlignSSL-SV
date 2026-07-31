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

# Table 1 now reports the three deep arms under the conventional fixed-0.5
# scoring, sourced from the corrected-protocol runs (table12) rather than from
# table1_label_efficiency.csv, which predates the protocol correction. The
# classical control moved to its own table because it is scored threshold-free.
ARM_COLUMNS = ["AlignSSL-pretrained", "AlignSSL-scratch",
               "DeepSV-representation"]


def q3(x: float) -> str:
    """Render at 3 dp with round-half-away-from-zero."""
    return str(Decimal(repr(float(x))).quantize(Decimal("0.001"),
                                                rounding=ROUND_HALF_UP))


def load_table1(results: Path) -> dict:
    """Manuscript Table 1 = fixed-0.5 F1 on the uniform benchmark, from table12."""
    src = {}
    with open(results / "table12_label_efficiency_fixed.csv") as fh:
        for r in csv.DictReader(fh):
            if r["benchmark"] != "uniform":
                continue
            src[(float(r["label_frac"]), r["arm"])] = (
                float(r["f1_at_half_mean"]), float(r["f1_at_half_sd"]))
    return src


def load_table13(results: Path) -> dict:
    """Manuscript Table 13 = the 1%-label contrast under three scoring rules."""
    with open(results / "table13_threshold_sensitivity.csv") as fh:
        for r in csv.DictReader(fh):
            if r["benchmark"] == "uniform" and abs(float(r["label_frac"]) - 0.01) < 1e-9:
                return r
    return {}


def check_table13(md: str, src: dict) -> list[str]:
    """Each row states pretrained, scratch, ratio and p for one scoring rule."""
    if not src:
        return ["Table 13: no uniform 1% row in table13_threshold_sensitivity.csv"]
    rules = [
        ("F1 at fixed 0.5 cut", "AlignSSL-pretrained_F1@0.5",
         "AlignSSL-scratch_F1@0.5", "ratio_F1@0.5", "p_F1@0.5"),
        ("F1 at selected \u03c4", "AlignSSL-pretrained_F1@tau",
         "AlignSSL-scratch_F1@tau", "ratio_F1@tau", "p_F1@tau"),
        ("AUPRC (threshold-free)", "AlignSSL-pretrained_AUPRC",
         "AlignSSL-scratch_AUPRC", "ratio_AUPRC", "p_AUPRC"),
    ]
    errs = []
    for label, kp, ks, kr, kpv in rules:
        m = re.search(r"^\| " + re.escape(label) + r" \|(.*)$", md, re.M)
        if m is None:
            errs.append(f"Table 13: row '{label}' not found")
            continue
        cells = [c.strip().replace("**", "") for c in m.group(1).strip("|").split("|")]
        for shown, key, fmt in ((cells[0], kp, q3), (cells[1], ks, q3)):
            want = fmt(src[key])
            if shown != want:
                errs.append(f"Table 13 {label} {key}: '{shown}' != source '{want}'")
        want_ratio = f"{float(src[kr]):.2f}\u00d7"
        if cells[2] != want_ratio:
            errs.append(f"Table 13 {label} ratio: '{cells[2]}' != '{want_ratio}'")
        want_p = f"{float(src[kpv]):.3f}"
        if cells[3] != want_p:
            errs.append(f"Table 13 {label} p: '{cells[3]}' != '{want_p}'")
    return errs


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
    """Every p-value quoted in prose must appear in a stats CSV.

    Section 4 quotes stats_tests.csv; Section 6 (the candidate-filtered
    benchmark) quotes stats_hardneg.csv, whose p-column is named `p`;
    Section 4.8 quotes the three per-rule p-columns of table13; Section 4.2
    quotes the control-versus-deep p-column of table14. All are pooled so the
    check covers the whole manuscript.
    """
    src = []
    with open(results / "stats_tests.csv") as fh:
        src += [float(r["p_value"]) for r in csv.DictReader(fh)]
    hn = results / "stats_hardneg.csv"
    if hn.exists():
        with open(hn) as fh:
            src += [float(r["p"]) for r in csv.DictReader(fh)]
    for name, cols in (("table13_threshold_sensitivity.csv",
                        ("p_F1@0.5", "p_F1@tau", "p_AUPRC")),
                       ("table14_control_vs_deep.csv", ("p_value",))):
        f = results / name
        if not f.exists():
            continue
        with open(f) as fh:
            for r in csv.DictReader(fh):
                for c in cols:
                    if r.get(c) not in (None, "", "nan"):
                        src.append(float(r[c]))
    errs = []
    # decimal form, e.g. "p = 0.025"
    for tok in re.findall(r"\*p\* = (0\.[0-9]+)", md):
        v = float(tok)
        if not any(abs(v - s) <= 5e-4 or
                   (s > 0 and abs(v - float(f"{s:.{max(1, len(tok) - 2)}f}")) < 1e-12)
                   for s in src):
            errs.append(f"p-value {tok} quoted in prose has no match in "
                        f"either stats CSV")
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


def check_hardneg_tables(md: str, results: Path) -> list[str]:
    """Tables 7 and 9: the candidate-filtered benchmark.

    Table 9 is checked cell-by-cell against its source (including the signed
    change column, which is derived and therefore easy to get wrong by hand).
    Table 7 is checked on mean +/- sd per (label fraction, arm).
    """
    errs: list[str] = []

    t9 = results / "table9_hardneg_single_feature_auc.csv"
    t6 = results / "table6_single_feature_auc.csv"
    if t9.exists() and t6.exists():
        with open(t9) as fh:
            hn = {r["feature"]: float(r["auc_oriented"]) for r in csv.DictReader(fh)}
        with open(t6) as fh:
            un = {r["feature"]: float(r["auc_oriented"]) for r in csv.DictReader(fh)}
        block = re.search(r"\| Feature \| Uniform \| Candidate-filtered.*?\n\n",
                          md, re.S)
        if block is None:
            errs.append("Table 9 block not found in manuscript")
        else:
            seen = set()
            for line in block.group(0).strip().splitlines()[2:]:
                c = [x.strip().replace("**", "")
                     for x in line.strip().strip("|").split("|")]
                feat = c[0]
                seen.add(feat)
                if feat not in hn:
                    errs.append(f"Table 9: unknown feature {feat}")
                    continue
                for shown, want, what in ((c[1], un[feat], "uniform"),
                                          (c[2], hn[feat], "filtered")):
                    if f"{want:.3f}" != f"{float(shown):.3f}":
                        errs.append(f"Table 9 {feat} {what}: shows {shown}, "
                                    f"source {want:.3f}")
                delta = hn[feat] - un[feat]
                if f"{delta:+.3f}".replace("-", "\u2212") != c[3]:
                    errs.append(f"Table 9 {feat} change: shows {c[3]}, "
                                f"source {delta:+.3f}")
            missing = set(hn) - seen
            if missing:
                errs.append(f"Table 9 omits features: {sorted(missing)}")

    t7 = results / "table7_hardneg_label_efficiency.csv"
    if t7.exists():
        with open(t7) as fh:
            src = {(f'{float(r["label_frac"]):g}', r["arm"]):
                   (float(r["F1_mean"]), float(r["F1_sd"]))
                   for r in csv.DictReader(fh)}
        cols = ["AlignSSL-combined", "AlignSSL-scratch", "DeepSV-representation",
                "Classical-logreg", "Classical-GBT"]
        block = re.search(r"\| Labels \| \*n\* \| AlignSSL \(pretrained\).*?\n\n",
                          md, re.S)
        if block is None:
            errs.append("Table 7 block not found in manuscript")
        else:
            for line in block.group(0).strip().splitlines()[2:]:
                c = [x.strip().replace("**", "")
                     for x in line.strip().strip("|").split("|")]
                frac = f'{float(c[0].rstrip("%")) / 100:g}'
                for arm, cell in zip(cols, c[2:]):
                    key = (frac, arm)
                    if key not in src:
                        errs.append(f"Table 7: no source row for {arm} @ {frac}")
                        continue
                    m, sd = src[key]
                    want = f"{m:.3f} \u00b1 {sd:.3f}"
                    if cell != want:
                        errs.append(f"Table 7 {arm} @ {c[0]}: shows '{cell}', "
                                    f"source '{want}'")
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
    errs += check_table13(md, load_table13(res))
    errs += check_calibration(md, res)
    errs += check_pvalues(md, res)
    errs += check_single_feature_auc(md, res)
    errs += check_hardneg_tables(md, res)
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
