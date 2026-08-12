"""Reconciles the statistics quoted in README.md against results/.

analysis/check_manuscript.py does this for docs/AlignSSL_SV_manuscript.md, but
nothing did it for the README -- which is what a visitor to the repository
actually reads first. The README carried the cross-ancestry withdrawal citing
only the PRE-correction run's Holm p, months after the corrected 36-cell re-run
had landed as manuscript Table 8; it was not wrong, but it was the weaker of the
two available justifications and it named neither the re-run nor the file
holding it.

These gates hold the README's quoted numbers to the CSVs, so a re-run that
changes them cannot leave the front page behind.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = (ROOT / "README.md").read_text()
RESULTS = ROOT / "results"


def _rows(name: str) -> list[dict]:
    return list(csv.DictReader(open(RESULTS / name)))


def test_readme_cites_the_corrected_xpop_rerun_not_only_the_original():
    for token in ("table26_xpop_lowlabel.csv", "stats_xpop_lowlabel.csv"):
        assert token in README, (
            f"README must name {token}: the corrected cross-ancestry re-run is "
            "the stronger justification for the withdrawal and supersedes the "
            "pre-correction Holm p as the primary citation"
        )


def test_readme_xpop_extreme_cell_matches_the_stats_csv():
    rows = _rows("stats_xpop_lowlabel.csv")
    best = min(rows, key=lambda r: float(r["p_raw"]))
    assert f"{float(best['p_raw']):.4f}" in README, (
        f"README must quote the most extreme raw p = {float(best['p_raw']):.4f}"
    )
    assert f"{float(best['p_holm']):.3f}" in README, (
        f"README must quote its Holm p = {float(best['p_holm']):.3f}"
    )
    assert best["survives_holm_0.05"] == "False", (
        "a cell now survives Holm; the README's null claim must be revisited"
    )
    assert best["leader"] == "scratch", (
        "the most extreme cell no longer favours the from-scratch arm; "
        "the README says it does"
    )


def test_readme_states_the_family_size_of_the_rerun():
    """Bare substring membership is not enough here.

    An earlier version asserted `str(len(rows)) in README` and passed while the
    README said "18 cells", because "36" also occurs inside 0.364, 0.836 and
    836. The count must be matched as a counted quantity, not as digits
    appearing anywhere in the document.
    """
    rows = _rows("stats_xpop_lowlabel.csv")
    n = len(rows)
    assert re.search(rf"\b{n}\s+cells\b", README), (
        f"README must state the family size as '{n} cells'"
    )


def _oriented_ratio_auc(name: str) -> float:
    """Held-out ROC-AUC of the centre-vs-flank depth ratio, oriented so that
    >0.5 means the feature discriminates deletions (the raw column is oriented
    the other way for this feature, at 0.045)."""
    rows = _rows(name)
    hit = [r for r in rows if "depth_centre_flank_ratio" == r["feature"]]
    assert len(hit) == 1, f"{name}: expected one ratio row, got {len(hit)}"
    return float(hit[0]["auc_oriented"])


def test_readme_shortcut_attenuation_matches_the_two_benchmarks():
    """The 0.955 -> 0.717 attenuation is the repaired benchmark's central claim.

    The two numbers come from different files -- the uniform benchmark's
    single-feature table and the candidate-filtered one's -- so quoting them
    together is exactly the kind of cross-file claim that drifts silently.
    """
    uniform = _oriented_ratio_auc("table6_single_feature_auc.csv")
    filtered = _oriented_ratio_auc("table9_hardneg_single_feature_auc.csv")
    # The README states this attenuation TWICE (Section "The repaired
    # benchmark" and the summary that follows), so asserting that one correct
    # pair exists passes while the other is wrong -- two earlier versions of
    # this gate did exactly that, one on bare membership and one on adjacency.
    # Check every "from X to Y" attenuation statement in the file.
    pairs = re.findall(
        r"from (?:ROC-AUC )?\*{0,2}(0\.\d+)\*{0,2} to \*{0,2}(0\.\d+)\*{0,2}",
        README,
    )
    assert len(pairs) >= 2, (
        f"expected the attenuation stated at least twice, found {pairs}"
    )
    want = (f"{uniform:.3f}", f"{filtered:.3f}")
    assert all(pr == want for pr in pairs), (
        f"every attenuation statement must read {want[0]} -> {want[1]}; found {pairs}"
    )
    assert filtered < uniform, "attenuation direction reversed"
    assert filtered > 0.5, (
        "the shortcut is now at chance; the README says attenuated-not-eliminated"
    )
