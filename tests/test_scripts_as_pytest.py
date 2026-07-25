"""Expose the two script-style test modules to pytest.

`test_match_strata.py` and `test_e2e.py` were written as standalone scripts with
a `main()` returning a POSIX exit code, because they also run on the cluster
where pytest is not installed in the analysis environment. Without these
wrappers `pytest tests/` silently collects neither, so a reviewer running the
suite would see only the estimator tests and conclude the quantile-matching
property and the end-to-end pipeline are unverified. The scripts remain runnable
directly; this file only makes `pytest` see them.
"""
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for p in (ROOT, HERE):
    if p not in sys.path:
        sys.path.insert(0, p)


def test_match_strata_property():
    """Quantile matching must drive the shortcut feature's AUC to ~0.5."""
    import test_match_strata
    assert test_match_strata.main() == 0


def test_end_to_end_pipeline():
    import importlib.util
    if importlib.util.find_spec("torch") is None:
        pytest.skip("torch not installed in this environment")
    import test_e2e
    assert test_e2e.main() == 0
