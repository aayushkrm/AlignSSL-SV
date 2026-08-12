# Released encoder weights — v0.1.0

`WEIGHTS_MANIFEST.tsv` is the authoritative index of the 22 pretrained encoder
checkpoints that accompany this paper. The checkpoints themselves ship as one
archive:

| | |
|---|---|
| Archive | `alignssl_sv_weights_v0.1.0.tar.gz` |
| Size | 52,913,192 bytes |
| SHA-256 | `9a62ea5199c51336779d57489587f56fe0f60f22103698eeb95106284e0eb84d` |
| Contents | `weights_v0.1.0/ckpt/*.pt` plus per-checkpoint `*.hist.json` training curves, and `MANIFEST.tsv` / `MANIFEST.json` |

## What is in it, and what it is for

All 22 checkpoints share one architecture: 647,078 encoder parameters, embedding
width 128, 25 epochs. They differ only in pretraining objective and in which
corpus generation they saw. Roles, as recorded in the manifest:

| Role | n | Serves |
|---|---|---|
| `main` | 4 | `encoder_ssl_seed{0..3}.pt` — MAM + VICReg. Every reported pretrained arm (Sections 4.1, 4.8, 4.10, 6.x, and the combined arm of Table 4). |
| `ablation` | 9 | Objective ablation, Section 4.5. Only the `_120k` files serve the reported numbers. |
| `sas` | 8 | Statistic-anchored pretraining (`scripts/pretrain_sas.py`). |
| `superseded` | 1 | `encoder_ssl.pt`, the first single-seed run. No reported number uses it. |

Checkpoints that serve no reported number are **kept and labelled**, not
dropped. A reader who finds a file in the archive should be able to learn from
the manifest whether it backs a published claim, and nine of the 22 do not.

## Two things the manifest records that are easy to get wrong

**The `_120k` suffix is a corpus size, not a schedule.** The two ablation
generations were launched with byte-identical hyperparameters (25 epochs, batch
96, lr 1.5e-4, mask ratio 0.6, view-keep 0.5); the only difference is that the
later ones saw the rebuilt 120,000-window six-sample pretraining corpus, while
the unsuffixed ones saw the earlier 80,000-window two-sample corpus. This is
inferred from the logged step counts (31,200 vs 20,800 steps, which at batch 96
over 25 epochs implies 119,808 vs 79,872 windows) and confirmed against the
memmap metadata. Section 4.5 reports the `_120k` family.

**The `sas` checkpoints carry their own normaliser.** `pretrain_sas.py`
accumulates feature-normaliser statistics over the pretraining stream and stores
them in the checkpoint as `feat_mean` / `feat_var`. Downstream code must use the
stored values; recomputing them on a different stream silently changes the
standardisation the encoder was trained under.

## Loading

Each file is a dict with keys `encoder` (the state dict), `epoch`, `d_model`, and
for `sas` additionally `objective`, `feat_mean`, `feat_var`:

```python
import torch
from alignssl.encoder import AlignEncoder

ck = torch.load("ckpt/encoder_ssl_seed0.pt", map_location="cpu")
enc = AlignEncoder(d_model=ck["d_model"])
enc.load_state_dict(ck["encoder"], strict=True)   # verified for all 22 at release
```

Every checkpoint in the manifest was verified to load this way under
`strict=True` at the time the manifest was built; the `strict_load_into_AlignEncoder`
column records the outcome per file.

## Provenance caveat

These weights were pretrained on 1000 Genomes high-coverage PCR-free alignments
(GRCh37/hs37d5). Read `docs/AlignSSL_SV_manuscript.md` Sections 4.2, 6 and 8
before using them for anything: the benchmark they were evaluated on is
separable by a single depth heuristic, and the paper's finding is that
self-supervised initialisation does **not** measurably help once that shortcut is
attenuated and scoring is threshold-free. They are released so that result can be
reproduced and contested, not as a recommended production initialisation.

## Where the archive lives

The archive is published as a GitHub release asset, not committed to the repository
(52 MB of binary weights do not belong in git history):

    https://github.com/aayushkrm/AlignSSL-SV/releases/tag/v0.1.0-weights

Download and verify before use:

    curl -L -o alignssl_sv_weights_v0.1.0.tar.gz \
      https://github.com/aayushkrm/AlignSSL-SV/releases/download/v0.1.0-weights/alignssl_sv_weights_v0.1.0.tar.gz
    shasum -a 256 alignssl_sv_weights_v0.1.0.tar.gz
    # expect 9a62ea5199c51336779d57489587f56fe0f60f22103698eeb95106284e0eb84d
    tar xzf alignssl_sv_weights_v0.1.0.tar.gz

If the digest does not match, the download is truncated or corrupt — do not use the
checkpoints, because a silently truncated `.pt` can still deserialise partially.
