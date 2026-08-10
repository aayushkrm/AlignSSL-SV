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
from decimal import Decimal, ROUND_HALF_EVEN, ROUND_HALF_UP
import re
import sys
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


def check_cross_ancestry_count(md: str, results: Path) -> list[str]:
    """Section 4.6 states how many of six fractions favour pretraining.

    That count is a claim about table5_cross_ancestry.csv and drifted from it
    once already: the prose said four where the table shows five, with only
    the 50% fraction inverted. A hand-counted claim sitting beside its own
    table is exactly what a referee checks first, so recompute it rather than
    trust it.
    """
    f = results / "table5_cross_ancestry.csv"
    if not f.exists():
        return []
    pre: dict[str, float] = {}
    scr: dict[str, float] = {}
    with open(f) as fh:
        for r in csv.DictReader(fh):
            tgt = scr if r["arm"] == "AlignSSL-scratch" else pre
            tgt[r["label_frac"]] = float(r["heldout_CEU_F1_mean"])
    n = sum(1 for k in pre if k in scr and pre[k] > scr[k])
    words = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six"}
    want = f"exceeds the from-scratch model's at {words.get(n, n)} of six"
    if want not in md:
        return [f"Cross-ancestry: table5 has pretrained ahead at {n} of "
                f"{len(pre)} fractions; manuscript does not say '{want}'"]
    return []


def check_pvalues(md: str, results: Path) -> list[str]:
    """Every p-value quoted in prose must appear in a stats CSV.

    Section 4 quotes stats_tests.csv; Section 6 (the candidate-filtered
    benchmark) quotes stats_hardneg.csv, whose p-column is named `p`;
    Section 4.8 quotes the three per-rule p-columns of table13; Section 4.2
    quotes the control-versus-deep p-column of table14; Section 4.9 quotes
    Holm-adjusted and BH-adjusted values from stats_multiplicity.csv, which
    are NOT raw p-values and appear in no other file. All are pooled so the
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
                       ("table14_control_vs_deep.csv", ("p_value",)),
                       ("table15_hardneg_arm_contrasts.csv", ("p",)),
                       ("stats_multiplicity.csv",
                        ("p_raw", "p_holm", "q_bh")),
                       # Section 6.5: the caller-candidate benchmark's
                       # pretrained-vs-scratch family, Holm-corrected within
                       # its own four budgets.
                       ("stats_caller_candidate.csv", ("p_raw", "p_holm")),
                       ("table20_alignssl_vs_deepsv.csv", ("p", "p_holm"))):
        f = results / name
        if not f.exists():
            continue
        with open(f) as fh:
            for r in csv.DictReader(fh):
                for c in cols:
                    if r.get(c) not in (None, "", "nan"):
                        src.append(float(r[c]))
    errs = []

    def _round_half_up(x: float, nd: int) -> str:
        """Match how a human rounds when quoting: 0.3485 -> 0.349 at 3 dp.

        f-strings use round-half-to-even (0.3485 -> '0.348'), and a plain
        absolute tolerance of 5e-4 rejects exact-half cases through binary
        representation error. Decimal quantisation avoids both.
        """
        return str(Decimal(repr(x)).quantize(Decimal(1).scaleb(-nd),
                                             rounding=ROUND_HALF_UP))

    # decimal form, e.g. "p = 0.025". A quoted value matches a source value
    # if it is that value rounded half-up, OR if it lies within half a unit
    # in the quoted last place. The second clause is needed because the stats
    # CSVs themselves store p to 4 dp: an exact p of 0.34846 is stored as
    # 0.3485, and both 0.348 (correct from full precision) and 0.349 (correct
    # from the stored value) are then consistent with the source.
    for tok in re.findall(r"\*p\* = (0\.[0-9]+)", md):
        nd = len(tok) - 2
        tol = Decimal(5) * Decimal(10) ** -(nd + 1)
        if not any(_round_half_up(s, nd) == tok or
                   abs(Decimal(tok) - Decimal(repr(s))) <= tol
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

    # Table 7 is sourced from the CORRECTED protocol table (table12, filtered
    # rows, threshold-free AUPRC), not from table7_hardneg_label_efficiency.csv:
    # the latter scores F1 at a fixed 0.5 cut under the pre-correction
    # negative-sampling protocol and is superseded (Sections 3.8, 4.8).
    t7 = results / "table12_label_efficiency_fixed.csv"
    if t7.exists():
        with open(t7) as fh:
            src = {(f'{float(r["label_frac"]):g}', r["arm"]):
                   (float(r["auprc_mean"]), float(r["auprc_sd"]))
                   for r in csv.DictReader(fh)
                   if r["benchmark"] == "candidate-filtered"}
        cols = ["AlignSSL-pretrained", "AlignSSL-scratch", "DeepSV-representation",
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
    # A literal {{artifact:...}} written inside a code cell is resolved to a
    # local absolute path BEFORE the cell runs, which silently converts a
    # portable embed into a machine-specific one. This has happened; guard it.
    abs_embeds = re.findall(r"!\[[^\]]*\]\((/[^)]+)\)", md)
    if abs_embeds:
        return [f"image embed is an absolute local path, not an artifact "
                f"marker: {p}" for p in abs_embeds]
    bad = re.findall(r"\{\{artifact:[^}]*[A-Z_]{4,}[^}]*\}\}", md)
    return [f"unresolved artifact placeholder: {b}" for b in bad]


def check_table20(md: str, results: Path) -> list[str]:
    """Table 20 must show exactly the Holm-surviving rows, with true cells.

    Section 4.10 reports the paper's primary claim (learned alignment tensor
    vs the DeepSV RGB pileup). The manuscript block lists only the cells that
    survive Holm correction, so two things can silently drift: a cell value,
    and set membership -- if a re-aggregation flips a comparison's verdict,
    a row must appear or disappear. Check both.
    """
    src = results / "table20_alignssl_vs_deepsv.csv"
    if not src.exists():
        return ["Table 20: missing source table20_alignssl_vs_deepsv.csv"]
    with src.open(newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    want = {}
    for r in rows:
        if r["verdict"] != "AlignSSL better":
            continue
        key = (r["benchmark"], r["metric"],
               r["arm"].replace("AlignSSL-", ""), f"{float(r['label_frac']):g}")
        want[key] = (f"{float(r['mean_a']):.3f}", f"{float(r['mean_b']):.3f}",
                     f"{float(r['diff']):+.3f}", f"{float(r['p_holm']):.3f}")
    m = re.search(r"\|\s*Benchmark\s*\|\s*Metric\s*\|\s*Arm\s*\|\s*Labels\s*\|"
                  r".*?\n((?:\|.*\n)+)", md)
    if not m:
        return ["Table 20 block not found in manuscript"]
    seen = set()
    errs = []
    for line in m.group(1).strip().splitlines():
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(c) != 8 or set(c[0]) <= set("-: "):
            continue
        key = (c[0], c[1], c[2], c[3])
        if key not in want:
            errs.append(f"Table 20 shows row {key}, which is not a "
                        f"Holm-surviving cell in the source")
            continue
        seen.add(key)
        for got, exp, what in zip(c[4:8], want[key],
                                  ("AlignSSL", "DeepSV", "difference", "Holm p")):
            if got != exp:
                errs.append(f"Table 20 {key} {what}: shows '{got}', "
                            f"source '{exp}'")
    for key in sorted(set(want) - seen):
        errs.append(f"Table 20 omits Holm-surviving cell {key}")
    # the prose counts must match the source too
    n_win, n_tot = len(want), len(rows)
    if not re.search(rf"\b{n_win} of {n_tot}\b", md):
        errs.append(f"Table 20: prose does not state the '{n_win} of {n_tot}' "
                    f"surviving-cell count")
    return errs


def check_prose_number_provenance(md: str, results: Path) -> list[str]:
    """Every decimal quoted in prose must appear in some results table.

    The targeted checks each verify one known claim. This one is the
    net underneath them: it takes every 2-4 decimal number in the body
    text and requires it to exist somewhere in results/*.csv, at some
    rounding. A number present nowhere in the sources is either a
    transcription error or a value that has drifted from a re-aggregation
    -- both of which we shipped before this check existed.

    It found three: Figure 2's caption claimed the control was overtaken
    at full supervision (0.979, a value in no table, contradicting the
    paper's central negative result), a Table 4 caveat quoted a
    superseded Table 1 entry (0.478 for 0.464), and the candidate-filtered
    full-supervision AUPRC was quoted as 0.844 for 0.856.

    Deliberately coarse: it proves a number *exists* in the sources, not
    that it is the right one for its sentence. Cheap, and it catches the
    class that targeted checks cannot enumerate.

    Measured limitation, not a supposed one: substituting 1.41 for a
    correct 1.05 does NOT fail this check, because 1.41 happens to occur
    in table2_calibration.csv. Any claim whose *value* matters must also
    have a targeted check above. Treat a pass here as "no fabricated
    numbers", never as "every number is the right one".
    """
    src: set[str] = set()
    for path in sorted(results.glob("*.csv")):
        with path.open(newline="", encoding="utf-8-sig") as fh:
            for row in csv.reader(fh):
                for cell in row:
                    cell = cell.strip()
                    # per-seed fields are ';'-joined
                    for tok in cell.split(";"):
                        tok = tok.strip()
                        try:
                            v = float(tok)
                        except ValueError:
                            continue
                        src.add(tok)
                        src.add(f"{v:g}")
                        for nd in range(5):
                            # Python's format() rounds half-to-even; prose
                            # is written half-up (0.5035 -> "0.504"). Index
                            # both so the gate does not flag a correctly
                            # rounded quotation.
                            q = Decimal(1).scaleb(-nd)
                            for r in (f"{v:.{nd}f}",
                                      str(Decimal(tok).quantize(q, ROUND_HALF_UP))):
                                src.add(r)
                                src.add(r.rstrip("0").rstrip(".") or "0")
    if not src:
        return ["prose provenance: no numeric values found in results/"]

    body = re.sub(r"^\|.*$", "", md, flags=re.M)          # tables: gated above
    body = re.sub(r"```.*?```", "", body, flags=re.S)     # code fences
    body = re.sub(r"\{\{artifact:[^}]*\}\}", "", body)    # embed markers
    body = re.sub(r"10\.\d{4,}/\S+", "", body)            # DOIs
    body = re.sub(r"\[[^\]]*\]\([^)]*\)", "", body)       # link targets
    body = re.sub(r"Section\s+\d+\.\d+", "", body)        # section numbers
    body = re.sub(r"^#{1,6}\s*\d+(\.\d+)*", "", body, flags=re.M)  # heading numbers
    body = re.sub(r"\d+\.\d+\s*[\u2013-]\s*\d+\.\d+", "", body)  # ranges

    errs = []
    for n in sorted({m for m in re.findall(r"(?<![\w.])(\d+\.\d{2,4})(?![\w])", body)}):
        if n in src:
            continue
        m = re.search(r"[^.\n]*(?<![\w.])" + re.escape(n) + r"(?![\w])[^.\n]*", body)
        ctx = (m.group(0).strip()[:110] + "...") if m else ""
        errs.append(f"prose provenance: {n} appears in no results/*.csv "
                    f"-- \u201c{ctx}\u201d")
    return errs


def check_corrected_label_efficiency(md: str, results: Path) -> list[str]:
    """Table 2 = the Table 1 runs rescored threshold-free (AUPRC).

    Table 1 (fixed-0.5 F1) and Table 2 (AUPRC, corrected protocol) are the
    paper's central before/after pair, so every cell of both must be
    gated. Located by column header rather than by table number, because
    table numbers are assigned in document order and shift when a table
    is inserted.

    Also enforces that the bolded cell per row is the arm with the highest
    source mean -- a stale bold would misattribute the leader.
    """
    src = {}
    path = results / "table12_label_efficiency_fixed.csv"
    if not path.exists():
        return [f"Table 2: missing source {path.name}"]
    with path.open(newline="", encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            if r["benchmark"] != "uniform":
                continue
            src[(float(r["label_frac"]), r["arm"])] = (
                float(r["auprc_mean"]), float(r["auprc_sd"]))
    arms = ["Classical-GBT", "Classical-logreg", "AlignSSL-pretrained",
            "AlignSSL-scratch", "DeepSV-representation"]
    m = re.search(r"\| Label fraction \| n labels \| Classical-GBT \| "
                  r"Classical-logreg \|.*?\n\n", md, re.S)
    if m is None:
        return ["Table 2 block not found in manuscript"]
    errs = []
    seen = set()
    for line in m.group(0).splitlines():
        if not line.startswith("| ") or "---" in line or "Label fraction" in line:
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        frac = float(cells[0].rstrip("%")) / 100
        seen.add(frac)
        avail = [a for a in arms if (frac, a) in src]
        if not avail:
            errs.append(f"Table 2: no source rows at {frac}")
            continue
        best = max(avail, key=lambda a: src[(frac, a)][0])
        for i, arm in enumerate(arms):
            raw = cells[2 + i]
            shown = raw.replace("**", "")
            if (frac, arm) not in src:
                errs.append(f"Table 2: no source row for {arm} @ {frac}")
                continue
            sm, ss = src[(frac, arm)]
            want = f"{q3(sm)} ± {q3(ss)}"
            if shown != want:
                errs.append(f"Table 2 {arm} @{frac}: manuscript '{shown}' "
                            f"!= source '{want}'")
            bolded = raw.startswith("**")
            if bolded != (arm == best):
                errs.append(f"Table 2 @{frac}: bold marks "
                            f"{'' if bolded else 'not '}{arm}, "
                            f"source leader is {best}")
    missing = {f for f, _ in src} - seen
    if missing:
        errs.append(f"Table 2 omits label fractions present in source: "
                    f"{sorted(missing)}")
    return errs


def check_table_numbering(md: str) -> list[str]:
    """Table captions must be numbered 1..N in document order.

    Numbers were originally inherited from source CSV filenames, so a
    reviewer met Table 1, then Table 14, then Table 6, and two in-text
    references pointed at a table that had no caption at all. Journals
    require sequential numbering; this makes the property enforced rather
    than periodically repaired.
    """
    errs = []
    order = [int(x) for x in re.findall(r"^\*\*Table (\d+)[.\s*]", md, flags=re.M)]
    if not order:
        return ["table numbering: no '**Table N' captions found"]
    want = list(range(1, len(order) + 1))
    if order != want:
        errs.append(f"table numbering: captions appear as {order}, "
                    f"expected {want} in document order")
    # Every in-text reference must resolve to a caption. Mask source
    # filenames first (results/table12_x.csv is not a cross-reference).
    masked = re.sub(r"table\d+[a-z0-9_]*\.csv", "CSVFILE", md)
    refs = {int(x) for x in re.findall(r"Table\s+(\d+)", masked)}
    dangling = sorted(refs - set(order))
    if dangling:
        errs.append(f"table numbering: in-text references to tables with no "
                    f"caption: {dangling}")

    # Figures are currently sequential; gate them so a renumbering round
    # cannot silently break them the way the tables were broken.
    forder = [int(x) for x in re.findall(r"!\[Figure (\d+)\.", md)]
    if not forder:
        errs.append("figure numbering: no '![Figure N.' captions found")
    else:
        fwant = list(range(1, len(forder) + 1))
        if forder != fwant:
            errs.append(f"figure numbering: captions appear as {forder}, "
                        f"expected {fwant} in document order")
        fmasked = re.sub(r"figure\d+[a-z0-9_]*\.png", "PNGFILE", md)
        frefs = {int(x) for x in re.findall(r"Figure\s+(\d+)", fmasked)}
        fdangling = sorted(frefs - set(forder))
        if fdangling:
            errs.append(f"figure numbering: in-text references to figures "
                        f"with no caption: {fdangling}")
    return errs


def check_narrative_tallies(md: str, results: Path) -> list[str]:
    """Prose tallies derived from a results table must match that table.

    check_table20 verifies the table *rows* and asserts that the correct
    "N of M" string appears somewhere. Neither catches the failure mode we
    actually hit: a stale tally surviving elsewhere in the prose while the
    correct one is present too. The abstract said the headline claim
    survives Holm correction and an introduction bullet said it does not;
    Section 4.10 carried "8 of 72" in a heading with "24 of 72" spliced
    into the same paragraph. Both files reconciled, both gates passed.

    So: for each tally, compute the true value from the source and reject
    any *other* value appearing in the same grammatical frame. A tally is
    wrong not only when absent but when contradicted.
    """
    errs = []

    t20 = results / "table20_alignssl_vs_deepsv.csv"
    if t20.exists():
        with t20.open(newline="", encoding="utf-8-sig") as fh:
            rows = list(csv.DictReader(fh))
        n_tot = len(rows)
        sep = [r for r in rows if float(r["p_holm"]) < 0.05]
        ahead = [r for r in rows if float(r["diff"]) > 0]
        ns = [r for r in rows if float(r["p_holm"]) >= 0.05]
        und = [r for r in ns
               if abs(float(r["diff"])) < float(r["mde80"])]
        scr = [r for r in sep if r["arm"] == "AlignSSL-scratch"]
        # "N of 72" must always be a true count of that grid
        legal = {len(sep), len(ahead), len(ns), len(und), len(scr), n_tot}
        for got in re.findall(rf"\b(\d+) of {n_tot}\b", md):
            if int(got) not in legal:
                errs.append(
                    f"narrative tally: '{got} of {n_tot}' is not a true "
                    f"count of the Table 20 grid "
                    f"(separating={len(sep)}, ahead={len(ahead)}, "
                    f"non-separating={len(ns)}, underpowered={len(und)})")
        # arm attribution: "K of those N" / "K of the N surviving"
        for got, tot in re.findall(r"\b(\d+) of (?:those|the) (\d+)\b", md):
            if int(tot) == len(sep) and int(got) != len(scr):
                errs.append(
                    f"narrative tally: '{got} of {tot}' surviving cells "
                    f"attributed to one arm, but {len(scr)} of {len(sep)} "
                    f"are the from-scratch arm")
        # underpowered accounting
        for got, tot in re.findall(r"\b(\d+) of the (\d+) non-separating\b", md):
            if (int(got), int(tot)) != (len(und), len(ns)):
                errs.append(
                    f"narrative tally: '{got} of the {tot} non-separating' "
                    f"contradicts source ({len(und)} of {len(ns)})")

    mult = results / "stats_multiplicity.csv"
    if mult.exists():
        with mult.open(newline="", encoding="utf-8-sig") as fh:
            rows = list(csv.DictReader(fh))
        n_tests = len(rows)
        n_fam = len({r["family"] for r in rows})
        nom = sum(1 for r in rows if float(r["p_raw"]) < 0.05)
        hol = sum(1 for r in rows if float(r["p_holm"]) < 0.05)
        for a, b in re.findall(r"\b(\d+) nominal(?:ly significant)? "
                               r"(?:hits |tests )?(?:across this paper )?"
                               r"(?:in \d+ pre-declared families )?"
                               r"(?:fall|reduce) to (\d+)\b", md):
            if (int(a), int(b)) != (nom, hol):
                errs.append(
                    f"narrative tally: '{a} nominal -> {b}' contradicts "
                    f"stats_multiplicity.csv ({nom} nominal, {hol} survive "
                    f"Holm)")
        for a, b in re.findall(r"\b(\d+) tests in (\d+) families\b", md):
            if (int(a), int(b)) != (n_tests, n_fam):
                errs.append(
                    f"narrative tally: '{a} tests in {b} families' "
                    f"contradicts source ({n_tests} tests, {n_fam} families)")
        # The headline claim's survival status is asserted in three places;
        # they must agree with each other and with the source.
        head = [r for r in rows
                if "pretrained vs scratch @0.01 (F1@0.5)" in r["test"]]
        if head:
            survives = float(head[0]["p_holm"]) < 0.05
            claims_not = re.findall(
                r"headline claim is not among the survivors", md)
            if survives and claims_not:
                errs.append(
                    "narrative tally: manuscript states the headline claim "
                    "is not among the Holm survivors, but "
                    f"stats_multiplicity.csv gives Holm p="
                    f"{float(head[0]['p_holm']):.4f} (< 0.05, it survives)")
    return errs


def check_seed_counts(md: str, results: Path) -> list[str]:
    # A seed count asserted in prose or a caption is a claim about a source
    # table, and it drifts silently when a seed-expansion run lands: the
    # numbers are re-aggregated but the sentence describing them is not.
    # This has happened (a preamble claimed "four for the combined-objective
    # arm, three for every other arm" after the corrected protocol had settled
    # on 3 deep / 10 classical). Reconcile every stated count against the
    # n_seeds column of the table family it describes.
    errs: list[str] = []
    fams = {
        "pre-correction": ("table1_label_efficiency.csv", None),
        "corrected": ("table12_label_efficiency_fixed.csv",
                      lambda r: r.get("benchmark") == "uniform"),
    }
    allowed: set[int] = set()
    per_fam: dict[str, set[int]] = {}
    for fam, (fn, filt) in fams.items():
        path = results / fn
        if not path.exists():
            errs.append(f"seed check: missing source table {fn}")
            continue
        with path.open(newline="", encoding="utf-8-sig") as fh:
            got = {int(r["n_seeds"]) for r in csv.DictReader(fh)
                   if not filt or filt(r)}
        per_fam[fam] = got
        allowed |= got
    if not allowed:
        return errs
    # Every "<n> seeds" / "<word> seeds" token in the manuscript must name a
    # seed count that some source table actually uses. A token naming a count
    # no table uses is either stale prose or a typo; both are errors.
    words = {"two": 2, "three": 3, "four": 4, "five": 5,
             "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
             "eleven": 11, "twelve": 12}
    toks: list[tuple[str, int]] = []
    for m in re.finditer(r"\b(\d{1,2})\s+seeds\b", md):
        toks.append((m.group(0), int(m.group(1))))
    for w, n in words.items():
        for m in re.finditer(rf"\b{w}\s+seeds\b", md, re.I):
            toks.append((m.group(0), n))
    for tok, n in toks:
        if n not in allowed:
            errs.append(f"seed count '{tok}' names {n} seeds, but no source "
                        f"table uses that count (tables use "
                        f"{sorted(allowed)}); per family: "
                        + "; ".join(f"{k}={sorted(v)}"
                                    for k, v in per_fam.items()))
    return errs


def check_readme_tables(readme: Path, results: Path) -> list[str]:
    """The README's two results tables must reconcile with source.

    This gate exists because of a defect it would have caught. The README is
    the repository's front page -- for most readers it is the *only* thing they
    read -- but every other check here targets the manuscript, so the README
    tables were regenerated by hand and silently went stale as seeds were
    added. By the time they were audited, 20 of 30 cells in the
    candidate-filtered table disagreed with source, and both tables had drifted
    far enough to assert a *reversal* at full supervision (deep arm ahead of
    the hand-crafted control) that the source contradicts in direction. That
    is the single most consequential claim either table makes.

    Two tables are checked cell by cell, located by column header so they
    survive edits above them:

      1. Uniform-benchmark control-vs-deep (source table14, benchmark
         "uniform"): control mean/sd, the *name* of the best deep arm, its
         mean/sd, and the leader verdict. The arm name matters -- a stale name
         attributes the ceiling to the wrong architecture.
      2. Candidate-filtered label efficiency (source table12, benchmark
         "candidate-filtered"): all five arms at all six budgets, plus the
         bolded per-row leader.

    p-values are deliberately *not* compared numerically: the README rounds
    and abbreviates them ("<0.001"), and check_pvalues already gates the
    manuscript's exact values against the same source.

    Rounding: a source value that is an exact tie at three decimals (0.9665,
    0.0095) has no determined third decimal, and `f"{x:.3f}"` resolves such
    ties by the *binary* representation, not by a rule -- 0.9665 formats up
    while 0.5035 formats down. Rather than enshrine that noise, ties accept
    either neighbour. Non-tie values are still checked exactly.
    """
    if not readme.exists():
        return ["README.md not found"]
    md = readme.read_text(encoding="utf-8")
    errs: list[str] = []

    def r3(v: str) -> set[str]:
        """Acceptable 3-decimal renderings of a source value."""
        d = Decimal(v)
        return {str(d.quantize(Decimal("1.000"), rounding=m))
                for m in (ROUND_HALF_EVEN, ROUND_HALF_UP)}

    def f3(v: str) -> str:
        return f"{float(v):.3f}"

    def cell_ok(got: str, mean: str, sd: str) -> bool:
        return any(f"{a} ± {b}" == got for a in r3(mean) for b in r3(sd))

    def cell_exp(mean: str, sd: str) -> str:
        return f"{f3(mean)} ± {f3(sd)}"

    # --- 1. uniform control-vs-deep table ---
    t14 = results / "table14_control_vs_deep.csv"
    if not t14.exists():
        return ["README: missing source table14_control_vs_deep.csv"]
    with t14.open(newline="", encoding="utf-8-sig") as fh:
        want = {f"{float(r['label_frac']) * 100:g}%": r
                for r in csv.DictReader(fh) if r["benchmark"] == "uniform"}
    m = re.search(r"\|\s*Labels\s*\|\s*Classical GBT\s*\|\s*Best deep arm\s*\|"
                  r".*?\n((?:\|.*\n)+)", md)
    if not m:
        errs.append("README uniform control table block not found")
    else:
        seen = set()
        for line in m.group(1).strip().splitlines():
            c = [x.strip() for x in line.strip().strip("|").split("|")]
            if len(c) != 6 or set(c[0]) <= set("-: "):
                continue
            r = want.get(c[0])
            if r is None:
                errs.append(f"README uniform table has budget {c[0]!r}, "
                            f"absent from source")
                continue
            seen.add(c[0])
            if not cell_ok(c[1], r["control_auprc_mean"], r["control_auprc_sd"]):
                errs.append(f"README uniform {c[0]} control: {c[1]!r} != "
                            f"{cell_exp(r['control_auprc_mean'], r['control_auprc_sd'])!r}")
            if c[2] != r["best_deep_arm"]:
                errs.append(f"README uniform {c[0]} best deep arm: {c[2]!r} "
                            f"!= {r['best_deep_arm']!r}")
            if not cell_ok(c[3], r["best_deep_auprc_mean"], r["best_deep_auprc_sd"]):
                errs.append(f"README uniform {c[0]} deep AUPRC: {c[3]!r} != "
                            f"{cell_exp(r['best_deep_auprc_mean'], r['best_deep_auprc_sd'])!r}")
            got_lead = c[5].strip("* ")
            if got_lead != r["leader"]:
                errs.append(f"README uniform {c[0]} leader: {got_lead!r} "
                            f"!= {r['leader']!r}")
        missing = set(want) - seen
        if missing:
            errs.append(f"README uniform table omits budgets: {sorted(missing)}")

    # --- 2. candidate-filtered label-efficiency table ---
    t12 = results / "table12_label_efficiency_fixed.csv"
    if not t12.exists():
        return errs + ["README: missing source table12_label_efficiency_fixed.csv"]
    arms = ["AlignSSL-pretrained", "AlignSSL-scratch", "DeepSV-representation",
            "Classical-GBT", "Classical-logreg"]
    with t12.open(newline="", encoding="utf-8-sig") as fh:
        rows = [r for r in csv.DictReader(fh)
                if r["benchmark"] == "candidate-filtered"]
    by = {(f"{float(r['label_frac']) * 100:g}%", r["arm"]): r for r in rows}
    budgets = sorted({k[0] for k in by}, key=lambda x: float(x.rstrip("%")))
    m = re.search(r"\|\s*Labels\s*\|\s*AlignSSL \(pretrained\)\s*\|"
                  r".*?\n((?:\|.*\n)+)", md)
    if not m:
        errs.append("README candidate-filtered table block not found")
        return errs
    seen = set()
    for line in m.group(1).strip().splitlines():
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(c) != 6 or set(c[0]) <= set("-: "):
            continue
        lab = c[0].split("(")[0].strip()
        if (lab, arms[0]) not in by:
            errs.append(f"README candidate table has budget {lab!r}, absent from source")
            continue
        seen.add(lab)
        n_exp = by[(lab, arms[0])]["n_labelled"]
        if f"n={n_exp}" not in c[0].replace(",", ""):
            errs.append(f"README candidate {lab} label count: {c[0]!r} "
                        f"does not state n={n_exp}")
        means = {a: float(by[(lab, a)]["auprc_mean"]) for a in arms}
        best = max(means, key=means.get)
        for arm, cell in zip(arms, c[1:6]):
            r = by[(lab, arm)]
            bold = cell.startswith("**")
            if not cell_ok(cell.strip("* "), r["auprc_mean"], r["auprc_sd"]):
                errs.append(f"README candidate {lab} {arm}: "
                            f"{cell.strip('* ')!r} != "
                            f"{cell_exp(r['auprc_mean'], r['auprc_sd'])!r}")
            if bold != (arm == best):
                errs.append(f"README candidate {lab}: {arm} is "
                            f"{'bolded but not' if bold else 'not bolded but is'} "
                            f"the best arm ({best})")
    missing = set(budgets) - seen
    if missing:
        errs.append(f"README candidate table omits budgets: {sorted(missing)}")
    return errs


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--md", default="docs/AlignSSL_SV_manuscript.md")
    p.add_argument("--results", default="results")
    p.add_argument("--readme", default="README.md")
    a = p.parse_args()

    md = Path(a.md).read_text()
    res = Path(a.results)

    errs: list[str] = []
    errs += check_table1(md, load_table1(res))
    errs += check_table13(md, load_table13(res))
    errs += check_calibration(md, res)
    errs += check_cross_ancestry_count(md, res)
    errs += check_pvalues(md, res)
    errs += check_single_feature_auc(md, res)
    errs += check_hardneg_tables(md, res)
    errs += check_markers(md)
    errs += check_table20(md, res)
    errs += check_seed_counts(md, res)
    errs += check_corrected_label_efficiency(md, res)
    errs += check_table_numbering(md)
    errs += check_narrative_tallies(md, res)
    errs += check_prose_number_provenance(md, res)
    errs += check_readme_tables(Path(a.readme), res)

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
