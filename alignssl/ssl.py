"""
Self-supervised objectives for AlignSSL-SV (roadmap section 4).

Objective A - Masked-region modelling (MAE-style, section 4.1):
    mask a fraction of the alignment tensor; reconstruct masked values.
    MSE on continuous channels + BCE/CE on categorical channels.

Objective B - VICReg (section 4.2 / verified precedent: CSV-Filter,
    Xia et al. 2024, uses VICReg; original Bardes et al. 2021):
    variance + invariance + covariance regularisation on two augmented
    views. Chosen over plain InfoNCE for collapse resistance without a
    large negative-sample batch.

Augmentation views (section 4.2):
    coverage-invariance : subsample read rows to two depths.
    (cross-sample views require orthologous loci and are applied at the
     data layer, not here.)
"""
from __future__ import annotations
import torch
import torch.nn as nn
import torch.nn.functional as F

from .tensorize import (
    BASE_ONEHOT, REF_ONEHOT, Q_MASK, N_CHANNELS,
    Q_BASEQUAL, Q_MAPQ, Q_STRAND, Q_DISC, Q_CLIP, Q_ISIZE, Q_DEPTH,
)

CONT_CHANNELS = [Q_BASEQUAL, Q_MAPQ, Q_ISIZE, Q_DEPTH]
BIN_CHANNELS = [Q_STRAND, Q_DISC, Q_CLIP]


# --------------------------- MAE ---------------------------
class MAEDecoder(nn.Module):
    """Light decoder: reconstruct the full [C, W] column profile from
    per-column encoder features. Row detail is summarised to column stats,
    which is what the reconstruction target also uses (row-pooled)."""

    def __init__(self, d_model: int, out_ch: int = N_CHANNELS):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(d_model, d_model), nn.GELU(),
            nn.Linear(d_model, out_ch),
        )

    def forward(self, cols):  # cols: [B, W, d_model]
        return self.net(cols)  # [B, W, out_ch]


def column_targets(x):
    """Row-pooled reconstruction target: [B, C, W] -> [B, W, C].

    For base one-hot and ref one-hot we take the mask-weighted mean over
    rows (a soft base-composition target); for continuous/binary signals
    the masked mean over rows.
    """
    B, C, R, W = x.shape
    mask = x[:, Q_MASK:Q_MASK + 1, :, :]          # [B,1,R,W]
    denom = mask.sum(dim=2).clamp_min(1.0)         # [B,1,W]
    pooled = (x * mask).sum(dim=2) / denom         # [B,C,W]
    # depth & ref channels are already column-broadcast; take plain mean
    pooled[:, Q_DEPTH, :] = x[:, Q_DEPTH, :, :].mean(dim=1)
    for i in range(REF_ONEHOT.start, REF_ONEHOT.stop):
        pooled[:, i, :] = x[:, i, :, :].mean(dim=1)
    return pooled.transpose(1, 2)                  # [B, W, C]


def mae_mask(x, mask_ratio: float, generator=None):
    """Zero out a fraction of column spans across all rows; return masked
    input and a boolean column-mask [B, W] (True = masked/predict)."""
    B, C, R, W = x.shape
    n_mask = int(round(mask_ratio * W))
    colmask = torch.zeros(B, W, dtype=torch.bool, device=x.device)
    for b in range(B):
        idx = torch.randperm(W, generator=generator, device=x.device)[:n_mask]
        colmask[b, idx] = True
    xm = x.clone()
    xm[:, :, :, :] = torch.where(
        colmask[:, None, None, :], torch.zeros_like(xm), xm
    )
    return xm, colmask


def mae_loss(pred, target, colmask):
    """pred/target: [B, W, C]; colmask: [B, W] (True = predict there)."""
    m = colmask.unsqueeze(-1)  # [B,W,1]
    if m.sum() == 0:
        return pred.sum() * 0.0
    # continuous channels -> MSE
    cont = torch.tensor(CONT_CHANNELS + BIN_CHANNELS, device=pred.device)
    lc = F.mse_loss(pred[..., cont][m.expand_as(pred)[..., cont]],
                    target[..., cont][m.expand_as(target)[..., cont]])
    # base + ref composition -> soft cross-entropy (KL to target dist)
    def soft_ce(sl):
        p = pred[..., sl]
        t = target[..., sl]
        logp = F.log_softmax(p, dim=-1)
        ce = -(t * logp).sum(-1)          # [B,W]
        return (ce * colmask).sum() / colmask.sum().clamp_min(1)
    lb = soft_ce(BASE_ONEHOT) + soft_ce(REF_ONEHOT)
    return lc + lb


# --------------------------- VICReg ---------------------------
class Projector(nn.Module):
    def __init__(self, d_in: int, d_hid: int = 512, d_out: int = 512):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(d_in, d_hid), nn.BatchNorm1d(d_hid), nn.GELU(),
            nn.Linear(d_hid, d_hid), nn.BatchNorm1d(d_hid), nn.GELU(),
            nn.Linear(d_hid, d_out),
        )

    def forward(self, x):
        return self.net(x)


def vicreg_loss(z1, z2, sim_coef=25.0, var_coef=25.0, cov_coef=1.0, eps=1e-4):
    """VICReg (Bardes et al. 2021). z1, z2: [B, D] embeddings of two views."""
    B, D = z1.shape
    # invariance
    sim = F.mse_loss(z1, z2)
    # variance (hinge at 1)
    def var_term(z):
        std = torch.sqrt(z.var(dim=0) + eps)
        return torch.mean(F.relu(1.0 - std))
    var = var_term(z1) + var_term(z2)
    # covariance
    def cov_term(z):
        z = z - z.mean(dim=0)
        cov = (z.T @ z) / (B - 1)
        off = cov - torch.diag(torch.diag(cov))
        return (off ** 2).sum() / D
    cov = cov_term(z1) + cov_term(z2)
    return sim_coef * sim + var_coef * var + cov_coef * cov, {
        "inv": sim.item(), "var": var.item(), "cov": cov.item(),
    }


def subsample_rows(x, keep_frac: float, generator=None):
    """Coverage-invariance augmentation: randomly keep a fraction of the
    real read rows (mask channel gates which rows are real)."""
    B, C, R, W = x.shape
    out = x.clone()
    for b in range(B):
        real = (x[b, Q_MASK].sum(dim=1) > 0).nonzero(as_tuple=True)[0]
        if len(real) == 0:
            continue
        n_keep = max(1, int(round(keep_frac * len(real))))
        perm = torch.randperm(len(real), generator=generator, device=x.device)
        drop = real[perm[n_keep:]]
        out[b, :, drop, :] = 0.0
    return out
