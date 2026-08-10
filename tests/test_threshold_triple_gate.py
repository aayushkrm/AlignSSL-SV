"""Regression tests for check_threshold_triple.

The three-scoring-rule table is the paper's central negative result and is
rendered in four documents. Only the manuscript was gated; the README, the
project plan and the progress record had all drifted to pre-correction
figures, and the README additionally asserted the fixed-cut result *fails*
multiplicity when source says it survives -- inverting the paper's own
argument.

What these tests pin is not "the gate rejects bad input". It is that the gate's
row matcher actually *reaches* each document's rendering. A matcher that
silently matches nothing reports success on stale numbers, which is precisely
how this defect survived three previous audits. Each case therefore asserts a
specific diagnostic string, not merely a non-zero exit.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "analysis" / "check_manuscript.py"
DOCS = {
    "readme": ROOT / "README.md",
    "progress": ROOT / "PROGRESS.md",
    "project": ROOT / "docs" / "project.md",
    "manuscript": ROOT / "docs" / "AlignSSL_SV_manuscript.md",
}


def run_checker() -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(CHECKER)],
        cwd=ROOT, capture_output=True, text=True,
    )


@pytest.fixture
def patch_doc(tmp_path):
    """Swap one substring into one document, restoring it afterwards."""
    saved: list[tuple[Path, Path]] = []

    def _patch(key: str, old: str, new: str) -> None:
        path = DOCS[key]
        backup = tmp_path / f"{key}.bak"
        shutil.copy(path, backup)
        saved.append((path, backup))
        text = path.read_text(encoding="utf-8")
        assert text.count(old) == 1, (
            f"fixture anchor appears {text.count(old)}x in {path.name}; "
            f"the document changed and this test needs updating"
        )
        path.write_text(text.replace(old, new), encoding="utf-8")

    yield _patch
    for path, backup in saved:
        shutil.copy(backup, path)


def test_committed_state_passes():
    """The gate must pass on committed state, or every case below is vacuous."""
    r = run_checker()
    assert r.stdout.startswith("PASS"), r.stdout


CASES = [
    pytest.param(
        "readme",
        "| F1 at fixed 0.5 cut | 0.464 | 0.106 | **4.38\u00d7** | **0.0002** |",
        "| F1 at fixed 0.5 cut | 0.478 | 0.044 | **10.89\u00d7** | **0.009** |",
        "README threshold table [0.5 cut]: pretrained '0.478'",
        id="readme-pre-correction-triple",
    ),
    pytest.param(
        "project",
        "| F1 at a fixed 0.5 cut (as originally scored) | 0.464 | 0.106 | 4.38x | 0.0002 |",
        "| F1 at a fixed 0.5 cut (as originally scored) | 0.476 | 0.045 | 10.5x | 0.009 |",
        "project plan threshold table [0.5 cut]",
        id="project-plan-stale-triple",
    ),
    pytest.param(
        "progress",
        "F1@0.5 ratio 4.38x (*p* = 0.0002)",
        "F1@0.5 ratio 10.9x (*p* = 0.009)",
        "progress record threshold prose [0.5 cut]",
        id="progress-stale-prose-ratio",
    ),
    pytest.param(
        "manuscript",
        "| AUPRC (threshold-free) | 0.504 | 0.495 | 1.02\u00d7 | 0.853 |",
        "| AUPRC (threshold-free) | 0.524 | 0.427 | 1.23\u00d7 | 0.348 |",
        "Table 13 AUPRC (threshold-free)",
        id="manuscript-stale-auprc",
    ),
    pytest.param(
        "readme",
        "| F1 at validation-selected \u03c4 | 0.481 | 0.456 | 1.06\u00d7 | 0.527 |\n",
        "",
        "README threshold table: no row for rule 'selected'",
        id="readme-row-omitted",
    ),
]


@pytest.mark.parametrize("key,old,new,expect", CASES)
def test_gate_fires(patch_doc, key, old, new, expect):
    patch_doc(key, old, new)
    r = run_checker()
    assert r.stdout.startswith("FAIL"), (
        f"gate stayed silent on an injected defect in {key}: {r.stdout[:200]}"
    )
    assert expect in r.stdout, (
        f"gate fired but with the wrong diagnosis.\nexpected substring: "
        f"{expect!r}\ngot:\n{r.stdout}"
    )


def test_withdrawn_multiplicity_value_is_caught(patch_doc):
    """The README once claimed the fixed-cut result fails Holm at 0.055.

    Source says it survives (raw 0.0002, Holm 0.0012). This is the defect that
    matters most, because it understates the project's own result and
    contradicts the manuscript -- an error in our favour would be caught by a
    reviewer, and an error against us would not, so only a gate catches it.
    """
    patch_doc(
        "readme",
        "adjusted for the family it was selected from, the fixed-cut result "
        "**survives** (raw *p* = 0.0002, Holm *p* = 0.0012)",
        "corrected for the family it was selected from, it is **0.055** and "
        "does not clear 0.05 under Holm",
    )
    r = run_checker()
    assert r.stdout.startswith("FAIL"), r.stdout
    assert "withdrawn Holm value 0.055" in r.stdout, r.stdout


def test_standard_deviation_0055_is_not_a_false_positive():
    """0.055 also occurs legitimately as a standard deviation.

    The gate must key on the value being asserted *as* the correction, not on
    the digits appearing anywhere on a line. Committed state contains such an
    sd, so a passing checker on committed state proves this.
    """
    readme = DOCS["readme"].read_text(encoding="utf-8")
    assert "0.055" in readme, (
        "expected a legitimate 0.055 (a standard deviation) in README.md; "
        "if it is gone this test no longer guards anything"
    )
    assert run_checker().stdout.startswith("PASS")


def test_dated_record_banner_gate_fires_when_banner_removed(patch_doc, tmp_path):
    """docs/REVIEWER_REPORT.md is a dated record and is deliberately ungated.

    Its numbers are not checked against source, because rewriting a review's
    findings after the fact would destroy the evidence that they were made.
    What IS checked is that the document declares itself a dated record and
    points at the machine-checked sources -- a reader who trusts an ungated
    results document needs to be told it is one.
    """
    path = ROOT / "docs" / "REVIEWER_REPORT.md"
    backup = tmp_path / "rr.bak"
    shutil.copy(path, backup)
    try:
        text = path.read_text(encoding="utf-8")
        needle = "> **STATUS: DATED RECORD, NOT A CURRENT RESULTS DOCUMENT.**"
        assert text.count(needle) == 1
        path.write_text(text.replace(needle, "> **Review notes.**"),
                        encoding="utf-8")
        r = run_checker()
        assert r.stdout.startswith("FAIL"), r.stdout
        assert "missing 'STATUS: DATED RECORD' banner" in r.stdout, r.stdout
    finally:
        shutil.copy(backup, path)


def test_superseded_value_needs_a_dated_correction_note(tmp_path):
    """A superseded figure may stay, but only if marked as superseded."""
    path = ROOT / "docs" / "REVIEWER_REPORT.md"
    backup = tmp_path / "rr2.bak"
    shutil.copy(path, backup)
    try:
        text = path.read_text(encoding="utf-8")
        needle = "<!-- correction 2026-08-10 --> **Superseded tallies and verdict.**"
        assert text.count(needle) == 1
        path.write_text(text.replace(needle, "**Note.**"), encoding="utf-8")
        r = run_checker()
        assert r.stdout.startswith("FAIL"), r.stdout
        assert "no dated correction note" in r.stdout, r.stdout
    finally:
        shutil.copy(backup, path)
