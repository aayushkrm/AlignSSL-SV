#!/usr/bin/env python3
"""Low-label cross-population generalization eval.

Tests the multi-ancestry claim in the LOW-LABEL regime (the honest caveat that
the full-label cross_pop_eval could not address). Mirrors finetune_eval.py's
label-fraction subsampling EXACTLY, but evaluates each trained model on TWO
held-out test sets at every label fraction:

  (A) in-distribution : chr12-22 of the two African training samples
      NA19238[YRI]+NA19625[ASW]  (shard-dir `tensors_all6` ... but see note)
  (B) cross-population : chr12-22 of NA12878 (CEU/European), a held-out
      INDIVIDUAL of a held-out ANCESTRY (shard-dir `tensors_na12878`).

For pretrained vs scratch, averaged over seeds by the caller. The gap (A - B)
at each label fraction quantifies whether SSL pretraining buys ancestry
robustness specifically when labels are scarce.

Training subsampling is identical to finetune_eval.py: same rng(seed),
same n = max(batch_size, int(frac*len(train))), same permutation slice.
"""
from __future__ import annotations
import argparse, os, time, json
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Subset

from alignssl.data import ShardDataset
from alignssl.encoder import AlignEncoder
from alignssl.heads import (SVHeads, finetune_loss, TemperatureScaler,
                            expected_calibration_error)


class Model(nn.Module):
    def __init__(self, d_model=128):
        super().__init__()
        self.enc = AlignEncoder(d_model=d_model)
        self.heads = SVHeads(d_model)

    def forward(self, x):
        return self.heads(self.enc(x))


def collate(batch):
    return {
        "x": torch.stack([b["x"] for b in batch]),
        "label": torch.stack([b["label"] for b in batch]),
        "geno": torch.stack([b["geno"] for b in batch]),
        "bp": torch.stack([b["bp"] for b in batch]),
        "del_len": torch.stack([b["del_len"] for b in batch]),
    }


def train_one(model, dl, dev, epochs, lr, freeze_encoder=False):
    if freeze_encoder:
        for p in model.enc.parameters():
            p.requires_grad = False
    params = [p for p in model.parameters() if p.requires_grad]
    opt = torch.optim.AdamW(params, lr=lr, weight_decay=1e-4)
    model.train()
    for ep in range(epochs):
        for batch in dl:
            batch = {k: v.to(dev) for k, v in batch.items()}
            out = model(batch["x"])
            loss, _ = finetune_loss(out, batch, a=0.5, b=0.5)
            opt.zero_grad(set_to_none=True)
            loss.backward()
            opt.step()
    return model


@torch.no_grad()
def collect_logits(model, dl, dev):
    model.eval()
    logits, labels, lens = [], [], []
    for batch in dl:
        out = model(batch["x"].to(dev))
        logits.append(out["cls_logits"].cpu())
        labels.append(batch["label"])
        lens.append(batch["del_len"])
    return torch.cat(logits), torch.cat(labels), torch.cat(lens)


def prf1(pred, label):
    tp = int(((pred == 1) & (label == 1)).sum())
    fp = int(((pred == 1) & (label == 0)).sum())
    fn = int(((pred == 0) & (label == 1)).sum())
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return p, r, f


def auprc(prob_pos, label):
    from sklearn.metrics import average_precision_score
    y = label.numpy() if hasattr(label, "numpy") else np.asarray(label)
    pp = prob_pos.numpy() if hasattr(prob_pos, "numpy") else np.asarray(prob_pos)
    if int(y.sum()) == 0 or int(y.sum()) == len(y):
        return float("nan")
    return float(average_precision_score(y, pp))


def eval_on(model, dl, dev, with_cal=False):
    logits, labels, lens = collect_logits(model, dl, dev)
    pred = logits.argmax(1)
    p, r, f = prf1(pred, labels)
    probs_raw = torch.softmax(logits, 1)[:, 1]
    out = {"P": p, "R": r, "F1": f, "AUPRC": auprc(probs_raw, labels),
           "n_pos": int((labels == 1).sum()), "n_total": int(labels.numel())}
    if with_cal:
        ts = TemperatureScaler()
        ts.fit(logits, labels)
        ece = expected_calibration_error(torch.softmax(ts(logits), 1), labels)
        out["ece"] = float(ece)
        out["temperature"] = float(ts.log_T.exp().item())
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard-dir", required=True,
                    help="training + in-dist test shards (tensors_all6)")
    ap.add_argument("--xpop-shard-dir", required=True,
                    help="NA12878 cross-population test shards")
    ap.add_argument("--encoder", default=None, help="pretrained encoder ckpt")
    ap.add_argument("--out", required=True)
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--batch-size", type=int, default=96)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--d-model", type=int, default=128)
    ap.add_argument("--label-fracs", default="0.01,0.05,0.1,0.25,0.5,1.0")
    ap.add_argument("--num-workers", type=int, default=2)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[{time.strftime('%H:%M:%S')}] device={dev}", flush=True)

    train_ds = ShardDataset(args.shard_dir, split="train", labeled=True)
    indist_ds = ShardDataset(args.shard_dir, split="test", labeled=True)
    xpop_ds = ShardDataset(args.xpop_shard_dir, split="test", labeled=True)
    print(f"  train={len(train_ds)} in-dist-test={len(indist_ds)} "
          f"xpop-test={len(xpop_ds)}", flush=True)

    dl_kw = dict(batch_size=args.batch_size, collate_fn=collate,
                 num_workers=args.num_workers)
    indist_dl = DataLoader(indist_ds, **dl_kw)
    xpop_dl = DataLoader(xpop_ds, **dl_kw)

    fracs = [float(x) for x in args.label_fracs.split(",")]
    # identical subsampling to finetune_eval.py
    rng = np.random.default_rng(args.seed)
    results = {"label_efficiency": [], "config": vars(args)}

    for frac in fracs:
        n = max(args.batch_size, int(frac * len(train_ds)))
        idx = rng.permutation(len(train_ds))[:n]
        sub = Subset(train_ds, idx.tolist())
        dl = DataLoader(sub, batch_size=args.batch_size, shuffle=True,
                        collate_fn=collate, num_workers=args.num_workers,
                        drop_last=True)
        row = {"frac": frac, "n": int(n)}
        for mode in ["pretrained", "scratch"]:
            if mode == "pretrained" and not args.encoder:
                continue
            model = Model(args.d_model).to(dev)
            if mode == "pretrained":
                ck = torch.load(args.encoder, map_location=dev)
                model.enc.load_state_dict(ck["encoder"])
            train_one(model, dl, dev, args.epochs, args.lr)
            indist = eval_on(model, indist_dl, dev,
                             with_cal=abs(frac - 1.0) < 1e-9)
            xpop = eval_on(model, xpop_dl, dev,
                           with_cal=abs(frac - 1.0) < 1e-9)
            row[mode] = {"in_dist": indist, "xpop": xpop,
                         "gap_F1": indist["F1"] - xpop["F1"]}
            print(f"  frac={frac} {mode}: in-dist F1={indist['F1']:.3f} "
                  f"xpop F1={xpop['F1']:.3f} gap={row[mode]['gap_F1']:.3f}",
                  flush=True)
        results["label_efficiency"].append(row)

    with open(args.out, "w") as fo:
        json.dump(results, fo, indent=2)
    print(f"[{time.strftime('%H:%M:%S')}] wrote {args.out}", flush=True)


if __name__ == "__main__":
    main()
