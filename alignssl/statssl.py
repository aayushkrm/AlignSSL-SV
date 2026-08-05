"""Statistic-anchored self-supervision (SAS).

Motivation
----------
Generic self-supervision on alignment tensors -- masked reconstruction of the
alignment pixels plus a VICReg view-invariance term -- produced no measurable
label-efficiency benefit in our own experiments once the scoring protocol was
corrected (manuscript Sections 4.8, 4.9 and 6.3).  The control experiment of
Section 4.2 explains why: the discriminative signal in this benchmark is
low-dimensional and concentrated in a handful of alignment summary statistics,
so an objective that spends capacity reconstructing every masked pixel is
optimising a target that is largely orthogonal to the downstream task.

SAS replaces the pixel-reconstruction target with a *statistic* target.  Given a
heavily masked view of a window, the encoder must predict the twelve summary
statistics of the **unmasked** window -- the same twelve that the classical
control uses.  This is deliberately the signal we proved sufficient
(``depth_centre_flank_ratio`` alone reaches ROC-AUC 0.955 untrained), so the
pretext task cannot be solved without internalising it.  Unlike the fixed
twelve-dimensional tree, however, the encoder retains the full alignment
context and can learn statistics the hand-crafted set does not express.

Two auxiliary terms keep the representation from collapsing onto twelve
numbers:

``occlusion consistency``
    two independent masks of the same window must yield embeddings that agree,
    which forces the prediction to be inferred from context rather than read
    off whichever columns happen to survive a mask; and

``VICReg variance/covariance``
    retained from the original objective (without its invariance term, which
    occlusion consistency subsumes) to keep embedding dimensions decorrelated
    and non-degenerate.

This is a *targeted* pretext task, not a better generic one; the claim it
supports is that pretext-task/­downstream-signal alignment matters more than
pretext-task sophistication.
"""
from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F

from .features import N_FEATURES
from .ssl import vicreg_loss


class StatHead(nn.Module):
    """Predicts the twelve standardised summary statistics from an embedding."""

    def __init__(self, d_model: int, n_out: int = N_FEATURES, p_drop: float = 0.1):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(d_model, 256), nn.GELU(), nn.Dropout(p_drop),
            nn.Linear(256, 256), nn.GELU(),
            nn.Linear(256, n_out),
        )

    def forward(self, z):
        return self.net(z)


def occlude(x: torch.Tensor, mask_ratio: float, generator=None):
    """Zero a contiguous-block random subset of columns, and the valid plane.

    Column-block occlusion (rather than i.i.d. column dropout) is what makes
    the pretext task non-trivial: isolated missing columns can be interpolated
    from their neighbours, whereas a contiguous gap must be inferred from the
    surrounding alignment context -- the same inference the downstream task
    requires when a breakpoint falls in a low-coverage region.
    """
    B, C, R, W = x.shape
    n_mask = int(round(mask_ratio * W))
    if n_mask <= 0:
        return x.clone()
    out = x.clone()
    blk = max(1, W // 16)
    n_blocks = max(1, n_mask // blk)
    starts = torch.randint(0, max(1, W - blk), (B, n_blocks),
                           generator=generator, device=x.device)
    cols = torch.zeros(B, W, dtype=torch.bool, device=x.device)
    ar = torch.arange(W, device=x.device)
    for b in range(n_blocks):
        s = starts[:, b:b + 1]
        cols |= (ar[None, :] >= s) & (ar[None, :] < s + blk)
    out[cols.unsqueeze(1).unsqueeze(2).expand_as(out)] = 0.0
    return out


# Default term weights are set from the measured magnitudes of the three terms
# at initialisation on random alignment tensors: stat 0.416, consistency 0.213,
# VICReg 38.10 (the last is large because VICReg's variance term carries
# coefficient 25 by construction).  Left at unit weight the VICReg term would
# supply ~98% of the gradient and the pretext task would not be learned at all.
# w_vicreg = 0.01 puts all three within a factor of two of one another, so the
# statistic target -- the point of the objective -- actually drives training.
# The ablation in the manuscript varies these one at a time.
W_STAT_DEFAULT, W_CONSIST_DEFAULT, W_VICREG_DEFAULT = 1.0, 1.0, 0.01


def sas_loss(
    pred_a, pred_b, target, z_a, z_b,
    w_stat: float = W_STAT_DEFAULT,
    w_consist: float = W_CONSIST_DEFAULT,
    w_vicreg: float = W_VICREG_DEFAULT,
):
    """Statistic regression + occlusion consistency + VICReg var/cov.

    ``target`` is the standardised statistic vector of the UNMASKED window.
    Huber rather than MSE: several of the twelve statistics are heavy-tailed
    (``isize_absz_max`` especially), and squared error on those dominates the
    gradient without improving the representation.
    """
    l_stat = 0.5 * (F.smooth_l1_loss(pred_a, target)
                    + F.smooth_l1_loss(pred_b, target))
    l_consist = F.mse_loss(z_a, z_b)
    # invariance is carried by l_consist, so zero VICReg's own sim term
    l_vic, parts = vicreg_loss(z_a, z_b, sim_coef=0.0)
    total = w_stat * l_stat + w_consist * l_consist + w_vicreg * l_vic
    return total, {
        "stat": float(l_stat.detach()),
        "consist": float(l_consist.detach()),
        "vicreg": float(l_vic.detach()),
        **{k: v for k, v in parts.items() if k != "inv"},
    }
