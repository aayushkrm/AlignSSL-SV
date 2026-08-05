"""Properties the statistic-anchored objective must have to be trainable.

These are behavioural guards, not smoke tests: each one encodes a failure mode
that would silently produce a null result (the exact outcome the SAS objective
exists to fix).
"""
from __future__ import annotations
import torch

from alignssl.encoder import AlignEncoder
from alignssl.features import batch_features, FeatureNormalizer
from alignssl.ssl import Projector
from alignssl.statssl import (StatHead, occlude, sas_loss, W_STAT_DEFAULT,
                              W_CONSIST_DEFAULT, W_VICREG_DEFAULT)

D = 128


def _batch(n=6, seed=0):
    g = torch.Generator().manual_seed(seed)
    x = torch.rand(n, 18, 64, 256, generator=g)
    x[:, 17] = (torch.rand(n, 64, 256, generator=g) > 0.4).float()
    return x


def _parts(x, mask_ratio=0.6, **kw):
    torch.manual_seed(0)
    enc, head, proj = AlignEncoder(d_model=D), StatHead(D), Projector(D)
    norm = FeatureNormalizer()
    f = batch_features(x)
    norm.observe(f)
    za, zb = enc(occlude(x, mask_ratio)), enc(occlude(x, mask_ratio))
    return sas_loss(head(za), head(zb), norm(f), proj(za), proj(zb), **kw)


def test_occlusion_removes_requested_fraction():
    x = _batch()
    xo = occlude(x, 0.5)
    # occluded columns are zeroed across every channel
    zeroed = (xo.abs().sum(dim=(1, 2)) == 0).float().mean(dim=1).mean()
    assert 0.35 < float(zeroed) < 0.65, f"occluded column fraction {zeroed:.3f}"


def test_occlusion_is_stochastic():
    x = _batch()
    a, b = occlude(x, 0.5), occlude(x, 0.5)
    assert not torch.equal(a, b), "two occlusions produced identical views"


def test_occlusion_preserves_unmasked_columns():
    x = _batch()
    xo = occlude(x, 0.5)
    keep = xo.abs().sum(dim=(1, 2)) != 0
    for i in range(x.shape[0]):
        k = keep[i]
        assert torch.allclose(xo[i, :, :, k], x[i, :, :, k]), \
            "unmasked columns were altered"


def test_loss_is_finite_and_terms_present():
    loss, parts = _parts(_batch())
    assert torch.isfinite(loss)
    assert {"stat", "consist", "vicreg"} <= set(parts)
    assert "inv" not in parts, \
        "VICReg invariance term must be zeroed (occlusion consistency covers it)"


def test_default_weights_keep_terms_commensurate():
    """The whole point of the objective is that the statistic term drives it.

    With unit weights VICReg contributes ~98% of the loss and the pretext task
    is not learned -- that is the bug this default guards against.
    """
    _loss, p = _parts(_batch())
    contrib = {
        "stat": W_STAT_DEFAULT * p["stat"],
        "consist": W_CONSIST_DEFAULT * p["consist"],
        "vicreg": W_VICREG_DEFAULT * p["vicreg"],
    }
    total = sum(contrib.values())
    assert contrib["stat"] / total > 0.15, \
        f"statistic term is only {contrib['stat']/total:.1%} of the loss"
    assert contrib["vicreg"] / total < 0.75, \
        f"VICReg term dominates at {contrib['vicreg']/total:.1%}"


def test_gradients_reach_the_encoder():
    torch.manual_seed(0)
    enc, head, proj = AlignEncoder(d_model=D), StatHead(D), Projector(D)
    norm = FeatureNormalizer()
    x = _batch()
    f = batch_features(x)
    norm.observe(f)
    za, zb = enc(occlude(x, 0.6)), enc(occlude(x, 0.6))
    loss, _ = sas_loss(head(za), head(zb), norm(f), proj(za), proj(zb))
    loss.backward()
    gnorm = sum(float(p.grad.norm()) for p in enc.parameters()
                if p.grad is not None)
    assert gnorm > 0, "no gradient reached the encoder"


def test_statistic_term_responds_to_target():
    """A permuted target must cost more than the true one.

    If it does not, the head is predicting the batch mean and the pretext task
    carries no per-window information.
    """
    torch.manual_seed(0)
    enc, head, proj = AlignEncoder(d_model=D), StatHead(D), Projector(D)
    norm = FeatureNormalizer()
    x = _batch(n=16)
    f = batch_features(x)
    norm.observe(f)
    tgt = norm(f)
    za, zb = enc(occlude(x, 0.6)), enc(occlude(x, 0.6))
    pa, pb = head(za), head(zb)
    # fit the head briefly so it is not at random init
    opt = torch.optim.Adam(head.parameters(), lr=1e-2)
    for _ in range(200):
        opt.zero_grad()
        l, _ = sas_loss(head(za.detach()), head(zb.detach()), tgt,
                        proj(za).detach(), proj(zb).detach(), w_vicreg=0.0)
        l.backward()
        opt.step()
    pa, pb = head(za.detach()), head(zb.detach())
    true_l, _ = sas_loss(pa, pb, tgt, proj(za), proj(zb), w_vicreg=0.0,
                         w_consist=0.0)
    perm = tgt[torch.randperm(tgt.shape[0], generator=torch.Generator().manual_seed(1))]
    perm_l, _ = sas_loss(pa, pb, perm, proj(za), proj(zb), w_vicreg=0.0,
                         w_consist=0.0)
    assert float(true_l) < float(perm_l), (
        f"permuted target ({float(perm_l):.4f}) not worse than true "
        f"({float(true_l):.4f}) -- head is not using per-window information")
