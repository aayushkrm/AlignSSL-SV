#!/usr/bin/env python3
"""Static guard: every label-sweep evaluator must use `alignssl.protocol`.

The regression this file exists to prevent, stated concretely. Section 3.8 of
the manuscript diagnoses two label-accounting defects and fixes them in one
shared module. `finetune_eval.py`, `deepsv_baseline_eval.py` and
`classical_baseline_eval.py` were migrated to it. `cross_pop_lowlabel.py` was
NOT, and kept computing

    n = max(args.batch_size, int(frac * len(train_ds)))

for months after the fix landed. Nothing failed loudly, and the consequence is
worse than a latent risk: this script writes `xpopll_results_seed*.json`, which
`analysis/aggregate_all.py` reads to build `table5_cross_ancestry.csv` (Table 5,
Section 4.6) and the cross-ancestry Welch rows of `stats_tests.csv`. Those
published numbers were therefore produced under the inflated budget -- at the
1% fraction the sweep granted `batch_size` labels rather than the protocol's
budget, and granted the threshold split for free on top. The manuscript labels
Sections 4.3-4.7 as predating the correction for exactly this reason; the
migration guarded here is what a re-run needs in order to be comparable with
the corrected tables. A unit test on `protocol.py` cannot catch the omission --
the module was correct; the caller simply did not call it.

So the guard is structural rather than numerical. For every evaluator that
sweeps label fractions we parse the source and require:

  1. it imports `label_budget` and `split_budget` from `alignssl.protocol`,
     plus `loader_params` if and only if it constructs a torch `DataLoader`
     (the classical control is scikit-learn and has no loader to size, so
     demanding the import there would be a guard that fires on correct code);
  2. it actually CALLS `label_budget` (an unused import is not adoption);
  3. the retired `max(<batch>, ...)` budget idiom appears nowhere in it.

(3) is deliberately syntactic, and narrow: it matches a `max()` call whose
arguments mention BOTH a batch-size name AND the label fraction. That
conjunction is the shape of the retired rule and of nothing else. Matching on
the batch-size name alone was tried first and produced a false positive on the
sanctioned `batch_size=max(1, min(args.batch_size, len(val_idx)))` that sizes
the validation loader in three evaluators -- a legitimate place for a batch
size and a subset size to meet. A guard that fires on correct code gets
disabled, so the conjunction is load-bearing.
"""
import ast
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import pytest
except ModuleNotFoundError:  # cluster env (deepsv2_new) has no pytest
    class _P:
        class mark:
            @staticmethod
            def parametrize(*a, **k):
                def deco(f):
                    return f
                return deco
    pytest = _P()  # type: ignore

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Evaluators that sweep --label-fracs and therefore make a label-efficiency
# claim. Any new one belongs here; that is the point of the list.
SWEEP_EVALUATORS = (
    "scripts/finetune_eval.py",
    "scripts/deepsv_baseline_eval.py",
    "scripts/classical_baseline_eval.py",
    "scripts/cross_pop_lowlabel.py",
)

# Required of every sweep evaluator.
REQUIRED_IMPORTS = {"label_budget", "split_budget"}
# Required only of evaluators that build a torch DataLoader.
LOADER_IMPORT = "loader_params"
BATCH_NAMES = ("batch_size", "batch-size")
# The label fraction: a budget expression must reference it. Sizing a loader
# does not.
FRAC_NAMES = ("frac", "fraction", "label_frac")


def _tree(rel):
    with open(os.path.join(ROOT, rel)) as fh:
        return ast.parse(fh.read()), fh


def _imported_from_protocol(tree):
    got = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "alignssl.protocol":
            got |= {a.name for a in node.names}
    return got


def _called_names(tree):
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            f = node.func
            if isinstance(f, ast.Name):
                out.add(f.id)
            elif isinstance(f, ast.Attribute):
                out.add(f.attr)
    return out


def _budget_floor_calls(tree):
    """Every `max(...)` mentioning both a batch-size name and a label fraction.

    Both conditions are required. `max(1, min(batch_size, len(val_idx)))` sizes
    a loader and is correct; `max(batch_size, int(frac * n_pool))` floors a
    label budget and is the defect.
    """
    hits = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id == "max"):
            continue
        src = " ".join(ast.dump(a) for a in node.args)
        if any(b in src for b in BATCH_NAMES) and any(f in src for f in FRAC_NAMES):
            hits.append(getattr(node, "lineno", -1))
    return hits


def _builds_dataloader(tree):
    return "DataLoader" in _called_names(tree)


@pytest.mark.parametrize("rel", SWEEP_EVALUATORS)
def test_evaluator_imports_protocol(rel):
    tree, _ = _tree(rel)
    got = _imported_from_protocol(tree)
    need = set(REQUIRED_IMPORTS)
    if _builds_dataloader(tree):
        need.add(LOADER_IMPORT)
    missing = need - got
    assert not missing, (
        f"{rel} does not import {sorted(missing)} from alignssl.protocol. "
        "Every label-sweep evaluator must share one label-accounting path; "
        "see Section 3.8.")


@pytest.mark.parametrize("rel", SWEEP_EVALUATORS)
def test_evaluator_calls_label_budget(rel):
    tree, _ = _tree(rel)
    assert "label_budget" in _called_names(tree), (
        f"{rel} imports the protocol but never calls label_budget(); "
        "an unused import is not adoption.")


@pytest.mark.parametrize("rel", SWEEP_EVALUATORS)
def test_no_batch_size_floor_on_budget(rel):
    """The retired idiom `n = max(batch_size, int(frac * n_pool))`.

    A batch-size floor on the label budget is the defect itself: at the 1%
    point on the filtered benchmark it granted 96 labels where the protocol
    grants 35. `loader_params` is the only sanctioned place where a batch size
    and a subset size meet.
    """
    tree, _ = _tree(rel)
    hits = _budget_floor_calls(tree)
    assert not hits, (
        f"{rel} has max(...) over a batch-size name at line(s) {hits}: this is "
        "the retired budget floor. Use label_budget() for the budget and "
        "loader_params() for the loader.")


if __name__ == "__main__":
    n = 0
    for _rel in SWEEP_EVALUATORS:
        for _fn in (test_evaluator_imports_protocol,
                    test_evaluator_calls_label_budget,
                    test_no_batch_size_floor_on_budget):
            _fn(_rel)
            n += 1
        print(f"  ok  {_rel}")
    print(f"PASS: {n} evaluator-protocol-adoption checks")
