#!/usr/bin/env python3
"""Stage 2 — fine-tune the DEL head, calibrate, and evaluate.

Produces the two headline results:
  (1) label-efficiency curve  : F1 vs label-fraction, pretrained vs scratch
  (2) length-stratified table  : F1 by deletion-size bin (amendment 1)
Plus calibration (temperature scaling, ECE, conformal coverage).

Trains on TRAIN chroms (chr1-11), evaluates on TEST chroms (chr12-22).
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
                            expected_calibration_error, ConformalBinary)
from alignssl.metrics import score_arm


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
    return (torch.cat(logits), torch.cat(labels), torch.cat(lens))


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
    import numpy as _np
    y = label.numpy() if hasattr(label, "numpy") else _np.asarray(label)
    pp = prob_pos.numpy() if hasattr(prob_pos, "numpy") else _np.asarray(prob_pos)
    if int(y.sum()) == 0 or int(y.sum()) == len(y):
        return float("nan")
    return float(average_precision_score(y, pp))


SIZE_BINS = [(50, 200), (200, 500), (500, 1000), (1000, 5000), (5000, 10**9)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard-dir", required=True)
    ap.add_argument("--encoder", default=None, help="pretrained encoder ckpt")
    ap.add_argument("--out", required=True, help="results json")
    ap.add_argument("--epochs", type=int, default=20)
    ap.add_argument("--batch-size", type=int, default=128)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--d-model", type=int, default=128)
    ap.add_argument("--freeze-encoder", action="store_true")
    ap.add_argument("--label-fracs", default="0.01,0.05,0.1,0.25,0.5,1.0")
    ap.add_argument("--num-workers", type=int, default=8)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--val-frac", type=float, default=0.2,
                    help="fraction of the LABELLED budget held out to "
                         "select the decision threshold")
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
    results = {"label_efficiency": [], "config": vars(args)}

    for frac in fracs:
        n = max(args.batch_size, int(frac * len(train_ds)))
        idx = rng.permutation(len(train_ds))[:n]
        # Carve a validation split OUT OF the labelled budget -- it is not
        # granted for free. Used only to pick the decision threshold; the
        # test chromosomes are never touched for threshold selection.
        n_val = int(round(args.val_frac * n))
        if n_val >= args.batch_size and n - n_val >= args.batch_size:
            val_idx, tr_idx = idx[:n_val], idx[n_val:]
        else:
            val_idx, tr_idx = idx[:0], idx  # budget too small to split
        sub = Subset(train_ds, tr_idx.tolist())
        dl = DataLoader(sub, batch_size=args.batch_size, shuffle=True,
                        collate_fn=collate, num_workers=args.num_workers,
                        drop_last=True)
        val_dl = (DataLoader(Subset(train_ds, val_idx.tolist()),
                             batch_size=args.batch_size, collate_fn=collate,
                             num_workers=args.num_workers)
                  if len(val_idx) else None)
        row = {"frac": frac, "n": int(n), "n_train": int(len(tr_idx)),
               "n_val": int(len(val_idx))}
        for mode in ["pretrained", "scratch"]:
            if mode == "pretrained" and not args.encoder:
                continue
            model = Model(args.d_model).to(dev)
            if mode == "pretrained":
                ck = torch.load(args.encoder, map_location=dev)
                model.enc.load_state_dict(ck["encoder"])
            train_one(model, dl, dev, args.epochs, args.lr,
                      freeze_encoder=args.freeze_encoder)
            logits, labels, lens = collect_logits(model, test_dl, dev)
            probs_raw = torch.softmax(logits, 1)[:, 1]
            if val_dl is not None:
                v_logits, v_labels, _ = collect_logits(model, val_dl, dev)
                v_probs = torch.softmax(v_logits, 1)[:, 1]
            else:
                v_probs = v_labels = None
            row[mode] = score_arm(probs_raw, labels, v_probs, v_labels)
            pred = (probs_raw >= row[mode]["tau"]).long()
            f = row[mode]["f1_at_tau"]
            p, r = row[mode]["P_at_tau"], row[mode]["R_at_tau"]
            # calibration + length strata only for the full-label runs
            if abs(frac - 1.0) < 1e-9:
                ts = TemperatureScaler()
                ts.fit(logits, labels)
                probs = torch.softmax(ts(logits), 1)[:, 1]
                ece = expected_calibration_error(
                    torch.softmax(ts(logits), 1), labels)
                strat = {}
                for (lo, hi) in SIZE_BINS:
                    m = (labels == 1) & (lens >= lo) & (lens < hi)
                    if m.sum() == 0:
                        continue
                    recall = float((pred[m] == 1).float().mean())
                    strat[f"{lo}-{hi}"] = {"n": int(m.sum()), "recall": recall}
                row[mode]["ece"] = float(ece)
                row[mode]["temperature"] = float(ts.log_T.exp().item())
                row[mode]["length_strata"] = strat
                _dump = os.path.splitext(args.out)[0] + f"_logits_{mode}.npz"
                np.savez_compressed(_dump, logits=logits.numpy(),
                    labels=labels.numpy(), lens=lens.numpy())
            print(f"  frac={frac} {mode}: F1@tau={f:.3f} P={p:.3f} R={r:.3f} tau={row[mode]['tau']:.3f} "
                  f"AUPRC={row[mode]['auprc']:.3f} F1@0.5={row[mode]['f1_at_half']:.3f}",
                  flush=True)
        results["label_efficiency"].append(row)

    with open(args.out, "w") as f:
        json.dump(results, f, indent=2)
    print(f"[{time.strftime('%H:%M:%S')}] wrote {args.out}", flush=True)


if __name__ == "__main__":
    main()
