"""Tests for the corrected cross-population sweep aggregator.

Two things are worth pinning here, and they are different in kind.

The first is that the multiplicity correction is right. The repository now
contains three independent Holm implementations, and a silent disagreement
between them would produce two different answers to the same question in the
same paper -- exactly the class of defect the manuscript audit exists to catch.
These tests assert all three agree and that the mathematical invariants hold,
rather than asserting hand-computed constants, because a hand-computed
expectation is itself a place to make an arithmetic error (one was made while
writing this file, and caught by the cross-check).

The second is that the cell extractor actually finds the cells. An extractor
that silently matches nothing produces an empty table and a clean exit -- a
false pass. `test_cell_extraction_is_not_vacuous` fails if the aggregator ever
stops reaching the data.
"""
from __future__ import annotations
import importlib.util, json, subprocess, sys, csv
from pathlib import Path
import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
AGG = ROOT / "analysis" / "aggregate_xpop_lowlabel.py"
FRACS = [0.01, 0.05, 0.1, 0.25, 0.5, 1.0]


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def agg():
    return _load(AGG, "agg_xpop")


def _synthetic(json_dir: Path, bump_frac: float = 0.1, bump: float = 0.25):
    """Write a sweep with a KNOWN effect: pretrained beats scratch on AUPRC at
    one budget only. Anything the aggregator reports beyond that is spurious."""
    json_dir.mkdir(parents=True, exist_ok=True)
    # Arm keys are the REAL ones written by scripts/cross_pop_lowlabel.py
    # ("pretrained", "scratch"), verified against ckpt/xpopll_pre_seed0.json on
    # the cluster. An earlier version of this fixture used a made-up key and
    # passed only because the aggregator selected arms positionally; once
    # selection became by name, the fixture's wrongness surfaced as an empty
    # table. Keep these names in sync with the sweep script, not with taste.
    for family, arm in (("pre", "pretrained"), ("scratch", "scratch")):
        for seed in range(3):
            rows = []
            for f in FRACS:
                b = bump if (arm == "pretrained" and abs(f - bump_frac) < 1e-9) else 0.0
                def cell(shift):
                    return {"f1_at_half": 0.60 + shift, "f1_at_tau": 0.60 + shift,
                            "auprc": 0.60 + b + shift, "n_pos": 100, "n_total": 900}
                rows.append({"frac": f,
                             arm: {"in_dist": cell(0.05 + 0.001 * seed),
                                   "xpop": cell(0.001 * seed)}})
            (json_dir / f"xpopll_{family}_seed{seed}.json").write_text(
                json.dumps({"label_efficiency": rows}))


def _run(json_dir: Path, out_dir: Path):
    return subprocess.run([sys.executable, str(AGG), "--json-dir", str(json_dir),
                           "--out-dir", str(out_dir)],
                          capture_output=True, text=True, cwd=ROOT)


def test_holm_agrees_with_the_other_two_implementations(agg):
    impls = []
    for rel, name in (("analysis/apply_multiplicity.py", "mult"),
                      ("analysis/alignssl_vs_deepsv.py", "avd")):
        mod = _load(ROOT / rel, name)
        if hasattr(mod, "holm"):
            impls.append((rel, mod.holm))
    assert impls, "no other Holm implementation found; this test guards nothing"
    rng = np.random.default_rng(7)
    cases = [[0.01, 0.04, 0.03], [0.001, 0.002, 0.5], [0.05] * 4, [0.9, 0.8],
             list(rng.uniform(0, 1, 20)), list(rng.beta(0.3, 3, 15)),
             [0.0, 1.0, 0.5]]
    for rel, fn in impls:
        for c in cases:
            assert np.allclose(agg.holm(c), fn(c), atol=1e-12), (rel, c)


def test_holm_invariants(agg):
    rng = np.random.default_rng(11)
    for c in [list(rng.uniform(0, 1, n)) for n in (1, 2, 5, 30)]:
        adj = agg.holm(c)
        assert all(a >= p - 1e-12 for a, p in zip(adj, c)), "adjusted below raw"
        order = sorted(range(len(c)), key=lambda i: c[i])
        seq = [adj[i] for i in order]
        assert all(seq[i] <= seq[i + 1] + 1e-12 for i in range(len(seq) - 1)), \
            "not monotone in sorted order"
        assert all(a <= 1.0 for a in adj), "adjusted p above 1"


def test_recovers_the_planted_effect_and_nothing_else(tmp_path):
    _synthetic(tmp_path / "json")
    r = _run(tmp_path / "json", tmp_path / "out")
    assert r.returncode == 0, r.stderr
    rows = list(csv.DictReader(open(tmp_path / "out" / "table26_xpop_lowlabel.csv")))
    survivors = [x for x in rows if x["survives_holm_0.05"] == "True"]
    assert survivors, "planted effect not recovered"
    for s in survivors:
        assert s["rule"] == "auprc", s
        assert float(s["label_frac"]) == 0.1, s
        assert s["leader"] == "pretrained", s


def test_cell_extraction_is_not_vacuous(tmp_path):
    """A matcher that matches nothing exits cleanly with an empty table."""
    _synthetic(tmp_path / "json")
    r = _run(tmp_path / "json", tmp_path / "out")
    assert r.returncode == 0, r.stderr
    rows = list(csv.DictReader(open(tmp_path / "out" / "table26_xpop_lowlabel.csv")))
    contrasts = [x for x in rows if x["p_raw"] not in ("", None)]
    # 6 budgets x 3 rules x 2 sites
    assert len(contrasts) == 36, f"expected 36 contrasts, got {len(contrasts)}"
    gaps = [x for x in rows if x["site"].startswith("gap[")]
    assert len(gaps) == 36, f"expected 36 gap rows, got {len(gaps)}"
    for x in contrasts:
        assert int(x["n_seeds_pre"]) == 3 and int(x["n_seeds_scratch"]) == 3


def test_gap_direction_is_indist_minus_xpop(tmp_path):
    """A positive gap must mean 'transfers worse than it performs at home'.

    The synthetic data sets in-distribution 0.05 above cross-population for both
    arms, so every gap must be +0.05. A sign flip here would invert the
    robustness conclusion while leaving every p-value untouched.
    """
    _synthetic(tmp_path / "json")
    r = _run(tmp_path / "json", tmp_path / "out")
    assert r.returncode == 0, r.stderr
    rows = list(csv.DictReader(open(tmp_path / "out" / "table26_xpop_lowlabel.csv")))
    gaps = [x for x in rows if x["site"].startswith("gap[") and x["rule"] != "auprc"]
    assert gaps
    for g in gaps:
        assert abs(float(g["gap_mean"]) - 0.05) < 1e-6, g
