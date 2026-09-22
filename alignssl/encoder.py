"""
Encoder for AlignSSL-SV (roadmap section 4.3).

Design intent: the backbone is deliberately ordinary. The scientific
contribution is the self-supervised objective and the learnable channel
encoding, NOT the network topology, so we avoid any "encoder-swap" novelty
claim.

    LearnedStem : 1x1 conv fusing the C input channels  ->  DeepSV's RGB
                  colour map replaced by a learned linear mix.
    CNN body    : small residual conv tower over [C', R, W] capturing
                  read-level / breakpoint texture (the DeepSV-lineage part).
    Row pool    : collapse the read-row axis (permutation-agnostic).
    Long-context: a few Transformer-encoder layers over the W (column) axis
                  so breakpoint-spanning context beats DeepSV's fixed window.
    Head        : pooled per-locus embedding + per-column features.
"""
from __future__ import annotations
import torch
import torch.nn as nn

from .encoding import ROW_POOL_MODES
from .tensorize import Q_MASK


class LearnedStem(nn.Module):
    """1x1 conv that fuses raw alignment channels into a learned encoding."""

    def __init__(self, in_ch: int, out_ch: int = 32):
        super().__init__()
        self.proj = nn.Conv2d(in_ch, out_ch, kernel_size=1)
        self.act = nn.GELU()

    def forward(self, x):  # x: [B, C, R, W]
        return self.act(self.proj(x))


class ResBlock2d(nn.Module):
    def __init__(self, ch):
        super().__init__()
        self.c1 = nn.Conv2d(ch, ch, 3, padding=1)
        self.c2 = nn.Conv2d(ch, ch, 3, padding=1)
        self.n1 = nn.BatchNorm2d(ch)
        self.n2 = nn.BatchNorm2d(ch)
        self.act = nn.GELU()

    def forward(self, x, row_weight=None):
        h = self.act(self.n1(self.c1(x)))
        if row_weight is not None:
            h = h * row_weight
        h = self.n2(self.c2(h))
        if row_weight is not None:
            h = h * row_weight
        out = self.act(x + h)
        return out if row_weight is None else out * row_weight


class AlignEncoder(nn.Module):
    def __init__(
        self,
        in_ch: int = 18,
        stem_ch: int = 32,
        body_ch: int = 64,
        n_res: int = 3,
        d_model: int = 128,
        n_tx: int = 2,
        n_heads: int = 4,
        row_pool_mode: str = "legacy",
    ):
        super().__init__()
        if row_pool_mode not in ROW_POOL_MODES:
            raise ValueError(f"Unknown row_pool_mode: {row_pool_mode}")
        self.stem = LearnedStem(in_ch, stem_ch)
        self.inconv = nn.Conv2d(stem_ch, body_ch, 3, padding=1)
        # ModuleList retains the released ``body.N.*`` state-dict keys while
        # allowing a padding mask to be applied inside each residual block.
        self.body = nn.ModuleList([ResBlock2d(body_ch) for _ in range(n_res)])
        # project pooled-row features to transformer width
        self.col_proj = nn.Linear(body_ch, d_model)
        layer = nn.TransformerEncoderLayer(
            d_model=d_model, nhead=n_heads, dim_feedforward=4 * d_model,
            batch_first=True, activation="gelu",
        )
        self.tx = nn.TransformerEncoder(layer, num_layers=n_tx)
        self.d_model = d_model
        self.row_pool_mode = row_pool_mode

    def forward(self, x, return_cols: bool = False):
        # x: [B, C, R, W]
        row_valid = None
        row_weight = None
        if self.row_pool_mode == "mask_aware":
            # Tensorization broadcasts reference/depth through padded rows.
            # Gate those rows before convolution so appending padding is a
            # semantic no-op, then exclude them from the row reduction.
            row_valid = x[:, Q_MASK].any(dim=-1)
            row_weight = row_valid[:, None, :, None].to(dtype=x.dtype)
            x = x * row_weight
        h = self.stem(x)
        if row_weight is not None:
            h = h * row_weight
        h = self.inconv(h)
        if row_weight is not None:
            h = h * row_weight
        for block in self.body:
            h = block(h, row_weight=row_weight)
        # h: [B, body_ch, R, W]
        if row_valid is None:
            h = h.mean(dim=2)           # historical row-pool
        else:
            weight = row_valid[:, None, :, None].to(dtype=h.dtype)
            h = (h * weight).sum(dim=2) / weight.sum(dim=2).clamp_min(1.0)
        h = h.transpose(1, 2)           # [B, W, body_ch]
        h = self.col_proj(h)            # [B, W, d_model]
        cols = self.tx(h)               # [B, W, d_model]
        pooled = cols.mean(dim=1)       # [B, d_model] per-locus embedding
        if return_cols:
            return pooled, cols
        return pooled
