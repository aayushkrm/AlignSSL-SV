"""Bind Section 6.2's train-vs-test separability claim to its source CSV.

Motivating defect (2026-08-12): Section 6.1 stated the matched training pool
measures ROC-AUC 0.504 with near-identical class medians, and Section 6.2 built
its mechanism on that -- matching equalises the ratio on the training pool, the
residual survives into held-out chromosomes. Both were false. 0.504 was the
*extractor's self-check on its own matching statistic*, printed by a synthetic
unit-test fixture at the head of the extraction log, not a measurement on
sequencing data. Measured on the real matched training pool the tensor-side
ratio gives 0.715, against 0.719 on test -- no asymmetry at all.

analysis/check_manuscript.py could not catch the replacement claim: it asks only
whether each quoted number appears in SOME results/*.csv, and 0.615/0.954/0.324
all collide with unrelated cells. A claim about a specific benchmark x split
must be checked against that row, so this gate reads the row the prose names.
"""
import csv
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
MS = ROOT / "docs" / "AlignSSL_SV_manuscript.md"
SRC = ROOT / "results" / "table28_split_separability.csv"


def rows():
    return {(r["benchmark"], r["split"]): r for r in csv.DictReader(SRC.open())}


def test_source_covers_both_benchmarks_and_splits():
    got = set(rows())
    want = {(b, s) for b in ("uniform", "candidate-filtered") for s in ("train", "test")}
    assert got == want, f"missing rows: {want - got}"


def test_prose_train_and_test_auc_match_the_matched_rows():
    s = MS.read_text()
    r = rows()
    tr = float(r[("candidate-filtered", "train")]["auc_oriented"])
    te = float(r[("candidate-filtered", "test")]["auc_oriented"])
    m = re.search(r"gives (\d+\.\d+) on the matched \*training\* pool against (\d+\.\d+) on the held-out",
                  s)
    assert m, "Section 6.2's train-vs-test sentence is missing or reworded"
    assert abs(float(m.group(1)) - tr) < 5e-4, f"prose {m.group(1)} vs source {tr:.4f}"
    assert abs(float(m.group(2)) - te) < 5e-4, f"prose {m.group(2)} vs source {te:.4f}"


def test_prose_uniform_pair_matches_the_uniform_rows():
    s = MS.read_text()
    r = rows()
    m = re.search(r"uniform benchmark likewise gives (\d+\.\d+) against (\d+\.\d+)", s)
    assert m, "Section 6.2's uniform comparison is missing or reworded"
    for got, key in ((m.group(1), "train"), (m.group(2), "test")):
        want = float(r[("uniform", key)]["auc_oriented"])
        assert abs(float(got) - want) < 5e-4, f"prose {got} vs source {want:.4f} ({key})"


def test_prose_class_medians_match_the_source():
    """The medians carry the mechanism: negatives move toward positives, not onto them."""
    s = MS.read_text()
    r = rows()
    checks = [
        (r"negative median is (\d+\.\d+) — copy-neutral", ("uniform", "test"), "median_neg"),
        (r"against (\d+\.\d+) for positives", ("uniform", "test"), "median_pos"),
        (r"negative median falls to (\d+\.\d+)", ("candidate-filtered", "test"), "median_neg"),
        (r"positive median is unchanged at (\d+\.\d+)", ("candidate-filtered", "test"), "median_pos"),
    ]
    for pat, key, col in checks:
        m = re.search(pat, s)
        assert m, f"prose pattern absent: {pat}"
        want = float(r[key][col])
        assert abs(float(m.group(1)) - want) < 5e-4, f"{pat}: prose {m.group(1)} vs source {want:.4f}"


def test_no_document_still_reports_the_withdrawn_0504_claim():
    """0.504 is a legitimate number elsewhere (an AUPRC cell); what must not
    return is the assertion that the matched *pool* measures it."""
    for doc in ("docs/AlignSSL_SV_manuscript.md", "README.md", "docs/project.md"):
        t = (ROOT / doc).read_text()
        for bad in ("matched training pool the depth ratio measures ROC-AUC 0.504",
                    "0.504 with near-identical class medians"):
            assert bad not in t, f"{doc} still states the withdrawn claim: {bad}"
