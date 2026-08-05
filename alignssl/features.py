"""Batched, torch-native alignment summary statistics.

These are the SAME twelve scalars the classical control uses
(``scripts/classical_baseline_eval.py:featurise``).  They exist here in
batched torch form for two purposes that the numpy version cannot serve:

  1. as the *regression target* of statistic-anchored self-supervision
     (``alignssl.statssl``) -- the encoder is asked to predict the summary
     statistics of the unmasked window from a masked view; and
  2. as the *fusion input* of the late-fusion deletion head, which
     concatenates them to the pooled embedding.

Because the control baseline is the arm to beat, any drift between this
implementation and the numpy one would make the comparison meaningless.
``tests/test_feature_parity.py`` asserts they agree elementwise to 1e-5 on
random tensors; do not edit one without the other.
"""
from __future__ import annotations

import torch
import torch.nn.functional as F

from .tensorize import Q_MAPQ, Q_DISC, Q_CLIP, Q_ISIZE, Q_DEPTH, Q_MASK

# Q_MASK is the valid-base plane; the classical script calls it Q_VALID.
Q_VALID = Q_MASK

FEAT_NAMES = [
    "depth_mean", "depth_sd", "depth_min", "depth_centre_flank_ratio",
    "depth_max_drop", "discordant_rate", "clip_rate",
    "isize_absz_mean", "isize_absz_max", "mapq_mean",
    "n_read_rows", "valid_frac",
]
N_FEATURES = len(FEAT_NAMES)


def batch_features(x: torch.Tensor) -> torch.Tensor:
    """x: [B, 18, R, W] -> [B, 12] float32, mirroring ``featurise`` exactly."""
    if x.dim() != 4:
        raise ValueError(f"expected [B,C,R,W], got {tuple(x.shape)}")
    x = x.float()
    B, _, R, W = x.shape

    valid = x[:, Q_VALID]                                  # [B, R, W]
    nvalid = valid.sum(dim=(1, 2))                         # [B]
    denom = nvalid.clamp(min=1.0)

    # depth is a column signal broadcast down the rows; row 0 is the profile
    prof = x[:, Q_DEPTH, 0]                                # [B, W]
    c0, c1 = W // 3, 2 * W // 3
    centre = prof[:, c0:c1].mean(dim=1)
    flank = torch.cat([prof[:, :c0], prof[:, c1:]], dim=1).mean(dim=1)
    ratio = torch.where(flank.abs() > 1e-9, centre / flank,
                        torch.ones_like(flank))

    # largest sustained drop: global mean minus the smallest 1/8-window mean
    k = max(1, W // 8)
    smooth = F.avg_pool1d(prof.unsqueeze(1), kernel_size=k, stride=1).squeeze(1)
    gmean = prof.mean(dim=1)
    max_drop = gmean - smooth.min(dim=1).values

    feats = torch.stack([
        gmean,
        prof.std(dim=1, unbiased=False),
        prof.min(dim=1).values,
        ratio,
        max_drop,
        (x[:, Q_DISC] * valid).sum(dim=(1, 2)) / denom,
        (x[:, Q_CLIP] * valid).sum(dim=(1, 2)) / denom,
        (x[:, Q_ISIZE].abs() * valid).sum(dim=(1, 2)) / denom,
        (x[:, Q_ISIZE] * valid).abs().amax(dim=(1, 2)),
        (x[:, Q_MAPQ] * valid).sum(dim=(1, 2)) / denom,
        (valid.sum(dim=2) > 0).sum(dim=1).float(),
        nvalid / float(R * W),
    ], dim=1)
    return feats


VAR_FLOOR = 1e-8


class FeatureNormalizer(torch.nn.Module):
    """Running standardiser for the twelve statistics.

    The raw scalars span several orders of magnitude (``n_read_rows`` is O(50),
    ``valid_frac`` is O(0.1)).  Regressing them unnormalised would let one term
    dominate the pretext loss, so we standardise with statistics accumulated
    over the pretraining stream and then freeze them into the checkpoint.
    """

    def __init__(self, n: int = N_FEATURES, momentum: float = 0.01):
        super().__init__()
        self.momentum = momentum
        self.register_buffer("mean", torch.zeros(n))
        self.register_buffer("var", torch.ones(n))
        self.register_buffer("n_seen", torch.zeros(1))

    @torch.no_grad()
    def observe(self, f: torch.Tensor) -> None:
        m, v = f.mean(dim=0), f.var(dim=0, unbiased=False)
        if float(self.n_seen) == 0.0:
            self.mean.copy_(m)
            self.var.copy_(v)
        else:
            self.mean.mul_(1 - self.momentum).add_(self.momentum * m)
            self.var.mul_(1 - self.momentum).add_(self.momentum * v)
        self.n_seen += 1

    def forward(self, f: torch.Tensor) -> torch.Tensor:
        # Clamp rather than divide by the raw variance: a feature that is
        # constant on a given stream (n_read_rows on fixed-height tensors, say)
        # would otherwise be amplified into pure noise and dominate the
        # statistic-regression loss. Under-scaling a near-constant feature is
        # the safe failure direction.
        return (f - self.mean) / self.var.clamp(min=VAR_FLOOR).sqrt()
