"""The torch featuriser must stay bit-comparable to the classical control's.

``alignssl.features.batch_features`` is both the regression target of
statistic-anchored pretraining and the fusion head's input.  The classical
control (``scripts/classical_baseline_eval.py:featurise``) is the arm the
manuscript's headline comparison is against.  If the two drift, the comparison
silently stops being an inclusion and the claim "the network was shown
everything the tree was shown" becomes false.  Hence a parity test rather than
a comment.
"""
from __future__ import annotations
import importlib.util
import os

import numpy as np
import pytest
import torch

from alignssl.features import batch_features, FEAT_NAMES, FeatureNormalizer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _featurise_ref():
    path = os.path.join(ROOT, "scripts", "classical_baseline_eval.py")
    spec = importlib.util.spec_from_file_location("_cbe_ref", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.featurise


def _random_tensors(n=9, seed=0):
    rng = np.random.default_rng(seed)
    X = rng.random((n, 18, 64, 256)).astype(np.float32)
    # channel 17 is the row-validity mask: make it genuinely binary and sparse
    X[:, 17] = (rng.random((n, 64, 256)) > 0.4).astype(np.float32)
    return X


def test_feature_names_match_control_order():
    ref = _featurise_ref()
    got = ref(_random_tensors(1)[0])
    assert len(got) == len(FEAT_NAMES), (
        f"control emits {len(got)} features, FEAT_NAMES has {len(FEAT_NAMES)}")


@pytest.mark.parametrize("seed", [0, 1, 2])
def test_batch_features_matches_control(seed):
    ref_fn = _featurise_ref()
    X = _random_tensors(seed=seed)
    ref = np.stack([ref_fn(X[i]) for i in range(X.shape[0])])
    got = batch_features(torch.from_numpy(X)).numpy()
    assert ref.shape == got.shape
    err = np.abs(ref - got).max()
    assert err < 1e-5, f"max abs diff {err:.3e} exceeds float32 tolerance"


def test_all_zero_tensor_is_finite():
    # empty windows do occur (unmapped regions); ratios must not produce nan
    got = batch_features(torch.zeros(2, 18, 64, 256))
    assert torch.isfinite(got).all(), "non-finite feature on an empty window"


def test_normalizer_standardises():
    f = batch_features(torch.from_numpy(_random_tensors(64)))
    norm = FeatureNormalizer()
    norm.observe(f)
    z = norm(f)
    assert torch.isfinite(z).all()
    # After one observation of the full batch the batch is standardised.
    # Tolerance is 1e-3, not 1e-6: the raw statistics span several orders of
    # magnitude (isize_absz_max reaches ~1e2 while depth ratios are ~1e0), so
    # float32 mean-subtraction on the large ones leaves a residual of ~3e-4.
    # That is the cancellation error of the dtype, not a normaliser defect.
    assert z.mean(0).abs().max() < 1e-3
    # Features that are constant on this input (e.g. clipped-base rate on
    # tensors with no soft clips) have zero variance; the normaliser clamps
    # their divisor and emits 0, which is correct. Unit variance is only
    # required of features that actually vary.
    # The normaliser clamps variance at VAR_FLOOR before dividing, so features
    # whose variance sits below it are deliberately under-scaled rather than
    # amplified into noise. Unit variance is required only above the floor.
    from alignssl.features import VAR_FLOOR
    varies = f.var(0, unbiased=False) > 10 * VAR_FLOOR
    assert varies.sum() >= 10, f"only {int(varies.sum())} features above floor"
    assert (z.std(0, unbiased=False)[varies] - 1).abs().max() < 1e-2
