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

    def forward(self, x):
        h = self.act(self.n1(self.c1(x)))
        h = self.n2(self.c2(h))
        return self.act(x + h)


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
    ):
        super().__init__()
        self.stem = LearnedStem(in_ch, stem_ch)
        self.inconv = nn.Conv2d(stem_ch, body_ch, 3, padding=1)
        self.body = nn.Sequential(*[ResBlock2d(body_ch) for _ in range(n_res)])
        # project pooled-row features to transformer width
        self.col_proj = nn.Linear(body_ch, d_model)
        layer = nn.TransformerEncoderLayer(
            d_model=d_model, nhead=n_heads, dim_feedforward=4 * d_model,
            batch_first=True, activation="gelu",
        )
        self.tx = nn.TransformerEncoder(layer, num_layers=n_tx)
        self.d_model = d_model

    def forward(self, x, return_cols: bool = False):
        # x: [B, C, R, W]
        h = self.stem(x)
        h = self.inconv(h)
        h = self.body(h)                # [B, body_ch, R, W]
        h = h.mean(dim=2)               # row-pool -> [B, body_ch, W]
        h = h.transpose(1, 2)           # [B, W, body_ch]
        h = self.col_proj(h)            # [B, W, d_model]
        cols = self.tx(h)               # [B, W, d_model]
        pooled = cols.mean(dim=1)       # [B, d_model] per-locus embedding
        if return_cols:
            return pooled, cols
        return pooled
