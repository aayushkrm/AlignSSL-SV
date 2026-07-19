#!/usr/bin/env python3
"""Phase 0.3 — DeepSV-lineage supervised baseline, head-to-head on our split.

Trains DeepSVNet (hand-designed RGB pileup + supervised CNN) on the SAME
labeled ShardDataset, chrom split (train chr1-11 / test chr12-22), focal
classification loss, and prf1 metric used by finetune_eval.py. Runs the full
label-efficiency sweep so the DeepSV baseline curve is directly overlayable on
the AlignSSL money plot. Reports F1/P/R per fraction, plus calibration (ECE,
temperature) and length-stratified recall at 100% labels.

This answers exactly one question: does DeepSV's aged representation+CNN, given
the identical data and budget, match our learned-encoder model? It is the
missing head-to-head that unblocks any "vs DeepSV" statement.
"""
from __future__ import annotations
import argparse, os, time, json
import numpy as np
import torch
from torch.utils.data import DataLoader, Subset

from alignssl.data import ShardDataset
from alignssl.deepsv_baseline import DeepSVNet
from alignssl.heads import (focal_loss, TemperatureScaler,
                            expected_calibration_error)


def collate(batch):
    return {
        "x": torch.stack([b["x"] for b in batch]),
        "label": torch.stack([b["label"] for b in batch]),
        "del_len": torch.stack([b["del_len"] for b in batch]),
    }


def train_one(model, dl, dev, epochs, lr):
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    model.train()
    for ep in range(epochs):
        for batch in dl:
            x = batch["x"].to(dev)
            y = batch["label"].to(dev)
            out = model(x)
            loss = focal_loss(out["cls_logits"], y, gamma=2.0)
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


SIZE_BINS = [(50, 200), (200, 500), (500, 1000), (1000, 5000), (5000, 10**9)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard-dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--batch-size", type=int, default=128)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--label-fracs", default="0.01,0.05,0.1,0.25,0.5,1.0")
    ap.add_argument("--num-workers", type=int, default=2)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    torch.manual_seed(args.seed)
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[{time.strftime('%H:%M:%S')}] device={dev}", flush=True)

    train_ds = ShardDataset(args.shard_dir, split="train", labeled=True)
    test_ds = ShardDataset(args.shard_dir, split="test", labeled=True)
    print(f"  train={len(train_ds)} test={len(test_ds)}", flush=True)
    test_dl = DataLoader(test_ds, batch_size=args.batch_size, collate_fn=collate,
                         num_workers=args.num_workers)

    fracs = [float(x) for x in args.label_fracs.split(",")]
    rng = np.random.default_rng(args.seed)
    results = {"label_efficiency": [], "config": vars(args),
               "model": "DeepSVNet (RGB pileup + supervised CNN)"}

    for frac in fracs:
        n = max(args.batch_size, int(frac * len(train_ds)))
        idx = rng.permutation(len(train_ds))[:n]
        sub = Subset(train_ds, idx.tolist())
        dl = DataLoader(sub, batch_size=args.batch_size, shuffle=True,
                        collate_fn=collate, num_workers=args.num_workers,
                        drop_last=True)
        model = DeepSVNet().to(dev)
        train_one(model, dl, dev, args.epochs, args.lr)
        logits, labels, lens = collect_logits(model, test_dl, dev)
        pred = logits.argmax(1)
        p, r, f = prf1(pred, labels)
        row = {"frac": frac, "n": int(n), "deepsv": {"P": p, "R": r, "F1": f}}
        if abs(frac - 1.0) < 1e-9:
            ts = TemperatureScaler()
            ts.fit(logits, labels)
            ece = expected_calibration_error(torch.softmax(ts(logits), 1), labels)
            strat = {}
            for (lo, hi) in SIZE_BINS:
                m = (labels == 1) & (lens >= lo) & (lens < hi)
                if m.sum() == 0:
                    continue
                strat[f"{lo}-{hi}"] = {"n": int(m.sum()),
                                       "recall": float((pred[m] == 1).float().mean())}
            row["deepsv"]["ece"] = float(ece)
            row["deepsv"]["temperature"] = float(ts.log_T.exp().item())
            row["deepsv"]["length_strata"] = strat
        print(f"  frac={frac} deepsv: F1={f:.3f} P={p:.3f} R={r:.3f}", flush=True)
        results["label_efficiency"].append(row)

    with open(args.out, "w") as fo:
        json.dump(results, fo, indent=2)
    print(f"[{time.strftime('%H:%M:%S')}] wrote {args.out}", flush=True)


if __name__ == "__main__":
    main()
