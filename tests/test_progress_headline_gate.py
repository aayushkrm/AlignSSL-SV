"""The PROGRESS.md headline gate must fire, not merely pass.

`check_progress_headline` was written after finding that Part I of the progress
record -- the section that tells the reader "this is authoritative, read this"
-- had drifted from `results/` in every deep-arm cell, disagreed with source on
four of six leader verdicts, omitted the caller-candidate benchmark entirely,
and stated the uniform full-supervision comparison in the *reverse* direction.
It passed the suite because nothing checked it: the manuscript and README
renderings of the same two tables were gated, this third rendering was not.

A gate that passes on correct input proves nothing; the failure mode that
matters is a gate whose row matcher silently skips every row (a wrong column
count, a changed separator) and therefore reports success on stale numbers.
This test injects each defect class and asserts the gate reports it. It pins
observable behaviour -- one diagnostic naming the document, the budget and the
disagreeing field -- not the implementation.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "analysis" / "check_manuscript.py"
PROGRESS = ROOT / "PROGRESS.md"

# (case name, exact substring present once in PROGRESS.md, replacement)
CASES = [
    (
        "stale deep mean (candidate-filtered)",
        "| 25% | 863 | Classical-GBT | 0.803 ± 0.013 | AlignSSL-scratch | 0.724 ± 0.055 |",
        "| 25% | 863 | Classical-GBT | 0.803 ± 0.013 | AlignSSL-scratch | 0.799 ± 0.055 |",
    ),
    (
        "flipped leader verdict",
        "| 0.5140 | tie |",
        "| 0.5140 | control |",
    ),
    (
        "dropped full-supervision row (caller-candidate)",
        "| 100% | 3346 | Classical-GBT | 0.982 ± 0.001 "
        "| AlignSSL-scratch | 0.956 ± 0.010 | 0.0455 | control |\n",
        "",
    ),
    (
        "wrong control arm name",
        "| 1% | 33 | Classical-logreg |",
        "| 1% | 33 | Classical-GBT |",
    ),
    (
        "stale p-value",
        "| 0.982 ± 0.002 | AlignSSL-scratch | 0.953 ± 0.010 | 0.0337 |",
        "| 0.982 ± 0.002 | AlignSSL-scratch | 0.953 ± 0.010 | 0.0299 |",
    ),
    (
        "dropped sparsest row (candidate-filtered)",
        # The p here reads '<0.0001', not '0.0000': the true value was
        # destroyed by an older script's write-time rounding, so the
        # source records the censoring bound and the table renders the
        # inequality. Anchor on the document as it actually reads.
        "| 1% | 35 | Classical-logreg | 0.476 ± 0.076 "
        "| DeepSV-representation | 0.316 ± 0.032 | <0.0001 | control |\n",
        "",
    ),
]


def _run() -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(CHECKER)],
        cwd=ROOT, capture_output=True, text=True,
    )


def _progress_lines(out: str) -> list[str]:
    return [ln for ln in out.splitlines() if "progress" in ln]


@pytest.mark.skipif(not PROGRESS.exists(), reason="PROGRESS.md absent")
def test_gate_passes_on_committed_state():
    """The committed record must reconcile with results/."""
    r = _run()
    assert not _progress_lines(r.stdout), r.stdout


@pytest.mark.skipif(not PROGRESS.exists(), reason="PROGRESS.md absent")
@pytest.mark.parametrize("name,old,new", CASES, ids=[c[0] for c in CASES])
def test_gate_fires_on_injected_defect(tmp_path, name, old, new):
    backup = tmp_path / "PROGRESS.md.orig"
    shutil.copy(PROGRESS, backup)
    try:
        text = PROGRESS.read_text(encoding="utf-8")
        assert text.count(old) == 1, (
            f"fixture drift: {name!r} anchor occurs {text.count(old)}x. "
            "Update CASES to match the current table rendering."
        )
        PROGRESS.write_text(text.replace(old, new), encoding="utf-8")
        hits = _progress_lines(_run().stdout)
        assert hits, f"gate did not fire on: {name}"
    finally:
        shutil.copy(backup, PROGRESS)
    assert not _progress_lines(_run().stdout), "restore failed"


@pytest.mark.skipif(not PROGRESS.exists(), reason="PROGRESS.md absent")
def test_part_two_is_not_gated(tmp_path):
    """Part II is a dated log; superseded entries there are not errors.

    Corrections to Part II are appended as dated notes rather than applied by
    rewriting, so the gate must scope itself to Part I. If it ever stopped
    doing so, every historical entry would become a build failure and the
    honest practice of leaving superseded numbers visible would be punished.
    """
    text = PROGRESS.read_text(encoding="utf-8")
    marker = "# PART II"
    assert marker in text, "Part II heading missing; gate scoping is undefined"
    backup = tmp_path / "PROGRESS.md.orig"
    shutil.copy(PROGRESS, backup)
    try:
        head, tail = text.split(marker, 1)
        stale = (
            "\n| 1% | 35 | Classical-logreg | 0.999 ± 0.001 "
            "| DeepSV-representation | 0.111 ± 0.001 | 0.9999 | deep |\n"
        )
        PROGRESS.write_text(head + marker + stale + tail, encoding="utf-8")
        assert not _progress_lines(_run().stdout), (
            "gate reached into Part II; it must scope to Part I"
        )
    finally:
        shutil.copy(backup, PROGRESS)
