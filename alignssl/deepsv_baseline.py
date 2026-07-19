"""DeepSV-lineage supervised baseline (Phase 0.3 head-to-head).

Purpose: isolate DeepSV's two aged design choices — the hand-designed RGB
pileup encoding and a plain supervised CNN — from our contribution (learned
multi-channel encoder + SSL pretraining), on the *identical* labeled split,
loss, and F1 metric used by finetune_eval.py. The only things that change
relative to the AlignSSL model are (a) the input representation and (b) the
network; the ShardDataset, chrom split (train chr1-11 / test chr12-22),
focal/finetune loss, and prf1 are reused verbatim.

DeepSV (Cai, Wu & Gao 2019, BMC Bioinformatics 20:665) rendered each 50-bp
window's pileup as a 256x256 RGB image: each nucleotide gets a base colour
(A=red, T=green, C=blue, G=black) whose low-order bits are perturbed by four
binary per-read features (is-paired, concordant/discordant, MAPQ>20,
split/not) plus column-level discordant/split counts, and classified the image
with a CNN.

We cannot bit-reproduce their exact colour packing from our tensors (we do not
store the identical per-read bit layout), so `deepsv_rgb` builds a faithful
*analog*: hue encodes base identity by DeepSV's palette, and the same per-read
binary signals we do store (MAPQ, discordant, soft-clip/split, strand)
modulate the channels in DeepSV's spirit. This is a reimplementation of the
DeepSV representation, documented as such — not the original binary.
"""
from __future__ import annotations
import torch
import torch.nn as nn

# channel indices in our 18-ch tensor (see tensorize.py)
_A, _C, _G, _T, _GAP = 0, 1, 2, 3, 4
_MAPQ, _STRAND, _DISC, _CLIP, _MASK = 6, 7, 8, 9, 17


def deepsv_rgb(x: torch.Tensor) -> torch.Tensor:
    """(B, 18, R, W) float -> (B, 3, R, W) DeepSV-style RGB in [0, 1].

    Palette: A=red, T=green, C=blue, G=black (contributes to no channel).
    Per-read modulation (DeepSV packs analogous bits into low-order colour):
      * base colour intensity is weighted by MAPQ (normalised /60 already),
        floored at 0.4 so a low-MAPQ base is dimmer but still visible;
      * discordant-pair flag adds a red tint (a classic deletion signature);
      * soft-clip/split flag adds a green tint (breakpoint signature);
      * empty (masked) cells stay black.
    Of the per-read signals DeepSV packs into low-order colour bits we use
    MAPQ, discordant, and soft-clip/split here; strand is available in the
    tensor but is not mapped into this analog encoding.
    """
    A, C, G, T = x[:, _A], x[:, _C], x[:, _G], x[:, _T]
    mapq = x[:, _MAPQ].clamp(0, 1)
    disc = x[:, _DISC].clamp(0, 1)
    clip = x[:, _CLIP].clamp(0, 1)
    mask = x[:, _MASK].clamp(0, 1)

    w = (0.4 + 0.6 * mapq)              # MAPQ intensity weight
    r = A * w + 0.5 * disc             # A=red, discordant tints red
    g = T * w + 0.5 * clip             # T=green, split/clip tints green
    b = C * w                          # C=blue; G=black -> no channel
    rgb = torch.stack([r, g, b], dim=1) * mask.unsqueeze(1)
    return rgb.clamp(0, 1)


class DeepSVNet(nn.Module):
    """A DeepSV-era supervised CNN over the RGB pileup image.

    Four conv blocks (32/64/128/256) with BN+ReLU+maxpool, global average
    pool, then a 2-logit classifier head. This stands in for "a standard
    supervised CNN on hand-designed pileup images" — the DeepSV lineage — and
    is deliberately not given our learned stem, transformer, or SSL init.
    Emits a dict with the same 'cls_logits' key finetune_loss/collect_logits
    expect, so the existing eval loop consumes it unchanged.
    """

    def __init__(self, n_classes: int = 2):
        super().__init__()

        def block(cin, cout):
            return nn.Sequential(
                nn.Conv2d(cin, cout, 3, padding=1, bias=False),
                nn.BatchNorm2d(cout), nn.ReLU(inplace=True),
                nn.MaxPool2d(2),
            )

        self.features = nn.Sequential(
            block(3, 32), block(32, 64), block(64, 128), block(128, 256),
        )
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.cls = nn.Sequential(
            nn.Flatten(), nn.Dropout(0.3), nn.Linear(256, 2),
        )

    def forward(self, x):
        rgb = deepsv_rgb(x)
        h = self.features(rgb)
        h = self.pool(h)
        logits = self.cls(h)
        # DeepSV is a binary classifier; this baseline has no breakpoint or
        # genotype head, so only 'cls_logits' is returned. It is trained with a
        # cls-only focal loss (deepsv_baseline_eval.py), never finetune_loss.
        return {"cls_logits": logits}
