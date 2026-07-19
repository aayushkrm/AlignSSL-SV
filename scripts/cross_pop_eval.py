#!/usr/bin/env python3
"""Cross-population generalization eval.

Fine-tune the DEL head on the FULL training set (chr1-11 of the two African
training samples NA19238[YRI]+NA19625[ASW]) and evaluate on two held-out sets:

  (A) in-distribution : chr12-22 of the SAME two African samples (shard-dir
      `tensors`, split=test) — the standard held-out-chromosome test.
  (B) cross-population : chr12-22 of NA12878 (CEU / European), a held-out
      INDIVIDUAL of a held-out ANCESTRY (shard-dir `tensors_na12878`, split=test).

Reports F1 / precision / recall on both, plus calibration (temperature+ECE) and
length-stratified recall on the cross-population set, for pretrained vs scratch,
averaged over seeds. The gap (A - B) quantifies the ancestry generalization cost.
"""
from __future__ import annotations
import argparse, os, time, json
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

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


def train_one(model, dl, dev, epochs, lr):
    opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad],
                            lr=lr, weight_decay=1e-4)
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


SIZE_BINS = [(50, 200), (200, 500), (500, 1000), (1000, 5000), (5000, 10**9)]


def eval_on(model, dl, dev, with_cal=False):
    logits, labels, lens = collect_logits(model, dl, dev)
    pred = logits.argmax(1)
    p, r, f = prf1(pred, labels)
    out = {"P": p, "R": r, "F1": f, "n_pos": int((labels == 1).sum()),
           "n_total": int(labels.numel())}
    if with_cal:
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
        out["ece"] = float(ece)
        out["temperature"] = float(ts.log_T.exp().item())
        out["length_strata"] = strat
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard-dir", required=True, help="training + in-dist test shards")
    ap.add_argument("--xpop-shard-dir", required=True, help="NA12878 test shards")
    ap.add_argument("--encoder", default=None, help="pretrained encoder ckpt")
    ap.add_argument("--out", required=True)
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--batch-size", type=int, default=128)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--d-model", type=int, default=128)
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
    train_dl = DataLoader(train_ds, shuffle=True, drop_last=True, **dl_kw)
    indist_dl = DataLoader(indist_ds, **dl_kw)
    xpop_dl = DataLoader(xpop_ds, **dl_kw)

    results = {"config": vars(args), "arms": {}}
    for mode in ["pretrained", "scratch"]:
        if mode == "pretrained" and not args.encoder:
            continue
        model = Model(args.d_model).to(dev)
        if mode == "pretrained":
            ck = torch.load(args.encoder, map_location=dev)
            model.enc.load_state_dict(ck["encoder"])
        train_one(model, train_dl, dev, args.epochs, args.lr)
        indist = eval_on(model, indist_dl, dev, with_cal=False)
        xpop = eval_on(model, xpop_dl, dev, with_cal=True)
        results["arms"][mode] = {"in_dist": indist, "xpop": xpop}
        print(f"  {mode}: in-dist F1={indist['F1']:.3f}  "
              f"xpop F1={xpop['F1']:.3f} (ECE={xpop.get('ece', 0):.3f})",
              flush=True)

    with open(args.out, "w") as fo:
        json.dump(results, fo, indent=2)
    print(f"[{time.strftime('%H:%M:%S')}] wrote {args.out}", flush=True)


if __name__ == "__main__":
    main()
