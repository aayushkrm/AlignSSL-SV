#!/usr/bin/env python3
"""Bounded native-component control; no genomes, caller run or performance claim.

Fetch the reviewed, immutable upstream length-estimator class into RAM. Validate
its Git blob identity before executing only that class (not module imports or
the simulator). Compare hidden rejected lengths at identical observed evidence.
Requires the project's existing NumPy. Prints JSON; does not write files.
"""
from __future__ import annotations

import ast
import hashlib
import json
import logging
import urllib.request

import numpy as np
from numpy.typing import NDArray

COMMIT = "a5b6af8520669dd3d182bbf95021a7242a2ede4e"
BLOB = "46d29031a0d9c31518c004a15a79f190eb94943a"
URL = (
    "https://raw.githubusercontent.com/goldman-gp-ebi/BOSS-RUNS/"
    f"{COMMIT}/boss/readlengthdist.py"
)


def load_reviewed_class():
    with urllib.request.urlopen(URL, timeout=25) as response:
        source = response.read(65_537)
    if len(source) != 3_898:
        raise ValueError("Reviewed source size differs; stop, do not update pin")
    blob = hashlib.sha1(f"blob {len(source)}\0".encode() + source).hexdigest()
    if blob != BLOB:
        raise ValueError("Reviewed source blob differs; stop, do not execute")
    tree = ast.parse(source, filename=URL)
    classes = [node for node in tree.body if isinstance(node, ast.ClassDef)]
    if len(classes) != 1 or classes[0].name != "ReadlengthDist":
        raise ValueError("Reviewed class layout differs")
    selected = ast.Module(body=classes, type_ignores=[])
    namespace = {"np": np, "NDArray": NDArray, "logging": logging}
    exec(compile(selected, URL, "exec"), namespace)
    return namespace["ReadlengthDist"], hashlib.sha256(source).hexdigest()


def control(length_class):
    observed = {"kept": 4_000, "rejected": 400}
    hidden = ({"kept": 4_000, "rejected": 10_000},
              {"kept": 4_000, "rejected": 40_000})
    native_states, guarded_states = [], []
    for full_lengths in hidden:
        native = length_class()
        native.update(full_lengths)
        guarded = length_class()
        guarded.update(observed)
        native_states.append({"mean_length": float(native.lam),
                              "approx_ccl": native.approx_ccl.tolist()})
        guarded_states.append({"mean_length": float(guarded.lam),
                               "approx_ccl": guarded.approx_ccl.tolist()})
    assert [s["mean_length"] for s in native_states] == [7_000, 22_000]
    assert native_states[0]["approx_ccl"] != native_states[1]["approx_ccl"]
    assert guarded_states[0] == guarded_states[1]
    assert guarded_states[0]["mean_length"] == 4_000
    return {
        "scope": "native_length_estimator_only_synthetic_observability_control",
        "observable_lengths_in_both_cases": observed,
        "hidden_full_lengths": list(hidden),
        "native_all_sampled_length_states": native_states,
        "observed_only_guard_states": guarded_states,
        "hidden_rejected_length_changes_native_strategy_inputs": True,
        "observed_only_guard_invariant": True,
        "guard_is_not_selection_bias_correction": True,
        "full_simulator_or_live_instrument_executed": False,
        "strategy_mask_or_SV_performance_effect_measured": False,
        "genomic_input_read": False,
    }


if __name__ == "__main__":
    length_class, digest = load_reviewed_class()
    result = control(length_class)
    result["source"] = {"url": URL, "commit": COMMIT, "git_blob": BLOB,
                        "bytes": 3_898, "sha256": digest}
    result["numpy_version"] = np.__version__
    print(json.dumps(result, indent=2))
