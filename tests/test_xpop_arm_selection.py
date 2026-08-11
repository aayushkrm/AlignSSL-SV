"""The cross-population aggregator must select an arm by NAME, not by position.

``analysis/aggregate_xpop_lowlabel.py`` reads per-seed JSONs in which each label
budget carries the arm results under a mode key ("pretrained" / "scratch"). An
earlier version selected the arm as::

    modes = [k for k, v in row.items() if isinstance(v, dict) and site in v]
    value = row[modes[0]][site][rule]

which is the *first dict-valued key in insertion order*. That was right only by
coincidence: ``cross_pop_lowlabel.py`` happens to iterate ``["pretrained",
"scratch"]``, so the pretrained-encoder invocation writes ``pretrained`` first.
Nothing enforced it. Reorder that loop, serialise through a tool that sorts keys,
or hand-edit a JSON, and the pretrained column would fill with from-scratch
numbers -- silently, with no exception and no shape mismatch, producing a
publishable table of the wrong arm.

The fixtures below write the keys in REVERSED order ("scratch" before
"pretrained") and assert the aggregator still returns the values belonging to the
arm it was asked for. A positional implementation fails these tests; a
name-based one passes regardless of key order.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
AGG = ROOT / "analysis" / "aggregate_xpop_lowlabel.py"


def _module():
    spec = importlib.util.spec_from_file_location("agg_xpop", AGG)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _metrics(value: float) -> dict:
    return {"f1_at_half": value, "f1_at_tau": value, "auprc": value, "tau": 0.5}


def _run(pre_value: float, scratch_value: float, *, reversed_keys: bool) -> dict:
    """One seed's JSON for a single budget, with a chosen key order."""
    arms = [
        ("scratch", {"in_dist": _metrics(scratch_value), "xpop": _metrics(scratch_value)}),
        ("pretrained", {"in_dist": _metrics(pre_value), "xpop": _metrics(pre_value)}),
    ]
    if not reversed_keys:
        arms.reverse()
    row = {"frac": 1.0, "n": 100}
    row.update(dict(arms))
    return {"label_efficiency": [row], "config": {}}


def test_arm_is_selected_by_name_not_position():
    cell = _module().cell
    # Keys deliberately reversed: "scratch" is the FIRST dict-valued key.
    runs = [_run(0.9, 0.1, reversed_keys=True)]
    got_pre = cell(runs, 1.0, "xpop", "f1_at_tau", "pretrained")
    got_scr = cell(runs, 1.0, "xpop", "f1_at_tau", "scratch")
    assert got_pre.tolist() == [0.9], (
        f"asked for the pretrained arm, got {got_pre.tolist()} -- the aggregator is "
        "reading whichever arm appears first in the JSON")
    assert got_scr.tolist() == [0.1], got_scr.tolist()


def test_order_of_keys_does_not_change_the_result():
    cell = _module().cell
    forward = cell([_run(0.9, 0.1, reversed_keys=False)], 1.0, "in_dist",
                   "auprc", "pretrained")
    backward = cell([_run(0.9, 0.1, reversed_keys=True)], 1.0, "in_dist",
                    "auprc", "pretrained")
    assert forward.tolist() == backward.tolist() == [0.9]


def test_a_single_arm_run_contributes_nothing_to_the_other_arm():
    """The sweep's second invocation writes only ``scratch``. Asking that file for
    the pretrained arm must yield no observation, rather than falling through to
    the one arm that is present -- otherwise a scratch run would be counted as a
    pretrained seed."""
    cell = _module().cell
    scratch_only = {"label_efficiency": [
        {"frac": 1.0, "n": 100,
         "scratch": {"in_dist": _metrics(0.1), "xpop": _metrics(0.1)}}],
        "config": {}}
    got = cell([scratch_only], 1.0, "xpop", "f1_at_tau", "pretrained")
    assert got.size == 0, f"a scratch-only run supplied {got.tolist()} as a pretrained seed"


def test_missing_budget_is_skipped_not_defaulted():
    cell = _module().cell
    runs = [_run(0.9, 0.1, reversed_keys=False)]
    assert cell(runs, 0.05, "xpop", "auprc", "pretrained").size == 0
    assert isinstance(cell(runs, 1.0, "xpop", "auprc", "pretrained"), np.ndarray)
