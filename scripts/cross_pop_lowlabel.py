#!/usr/bin/env python3
"""Low-label cross-population generalization eval.

Tests the multi-ancestry claim in the LOW-LABEL regime (the honest caveat that
the full-label cross_pop_eval could not address). Mirrors finetune_eval.py's
label-fraction subsampling EXACTLY, but evaluates each trained model on TWO
held-out test sets at every label fraction:

  (A) in-distribution : chr12-22 of the SAME six-sample fine-tuning panel the
      model was trained on (`--shard-dir`, i.e. `tensors_all6`: NA19238[YRI],
      NA19625[ASW], NA18525[CHB], NA19648[MXL], NA20502[TSI], NA20845[GIH]).
      Held out by CHROMOSOME (train chr1-11 / test chr12-22), not by sample or
      ancestry -- so (A) is the in-distribution reference point.
  (B) cross-population : chr12-22 of NA12878 (CEU/European), a held-out
      INDIVIDUAL of a held-out ANCESTRY (shard-dir `tensors_na12878`).
      CEU appears in NEITHER the SSL pretrain corpus NOR the fine-tune panel,
      so (B) is held out by sample AND by ancestry.

For pretrained vs scratch, averaged over seeds by the caller. The gap (A - B)
at each label fraction quantifies whether SSL pretraining buys ancestry
robustness specifically when labels are scarce.

Label accounting is delegated to `alignssl.protocol`, the same module
finetune_eval.py imports, so this arm cannot drift from the label-efficiency
curves it is compared against: `label_budget` sets the budget with no
batch-size floor, `split_budget` carves the threshold-selection split OUT OF
that budget, and `loader_params` sizes the loader so no subset is padded up to
a batch. An earlier version of this script used
`n = max(batch_size, int(frac * len(train)))`, which is the inflated-budget
defect diagnosed in Section 3.8 of the manuscript: at the 1% point it granted
96 labels where the protocol grants far fewer, and it granted the validation
split for free on top of the budget.

The decision threshold tau is selected on the in-distribution validation split
and then applied UNCHANGED to both test sets. Selecting a separate threshold on
the cross-population set would use held-out-ancestry labels that a deployment
would not have, and would measure a different quantity than transfer.
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
from alignssl.metrics import score_arm, prf1_at, select_threshold
from alignssl.protocol import label_budget, split_budget, loader_params


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


def eval_on(model, dl, dev, with_cal=False, tau=None):
    """Score one test set. `tau` is the threshold selected on the
    in-distribution validation split; it is applied unchanged here so the
    in-distribution and cross-population numbers are directly comparable.
    Passing tau=None falls back to the fixed 0.5 cut and the record says so
    via `tau_selected: False`."""
    logits, labels, lens = collect_logits(model, dl, dev)
    probs_raw = torch.softmax(logits, 1)[:, 1]
    out = score_arm(probs_raw, labels)
    if tau is not None:
        pt, rt, ft = prf1_at(probs_raw, labels, tau)
        out.update({"tau": float(tau), "P_at_tau": pt, "R_at_tau": rt,
                    "f1_at_tau": ft, "tau_selected": True})
    out.update({"n_pos": int((labels == 1).sum()),
                "n_total": int(labels.numel())})
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
    ap.add_argument("--val-frac", type=float, default=0.2,
                    help="share of the LABEL BUDGET carved out for "
                         "threshold selection (not granted for free)")
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
    # Label accounting delegated to alignssl.protocol -- identical to
    # finetune_eval.py, so this arm and the label-efficiency curves cannot
    # drift apart. See the module docstring.
    rng = np.random.default_rng(args.seed)
    results = {"label_efficiency": [], "config": vars(args)}

    for frac in fracs:
        n = label_budget(frac, len(train_ds))
        idx = rng.permutation(len(train_ds))[:n]
        # The threshold-selection split is carved OUT OF the budget.
        n_val, _n_tr, _did = split_budget(n, args.val_frac)
        val_idx, tr_idx = idx[:n_val], idx[n_val:]
        sub = Subset(train_ds, tr_idx.tolist())
        _bs, _drop = loader_params(len(tr_idx), args.batch_size)
        dl = DataLoader(sub, batch_size=_bs, shuffle=True,
                        collate_fn=collate, num_workers=args.num_workers,
                        drop_last=_drop)
        val_dl = (DataLoader(Subset(train_ds, val_idx.tolist()),
                             batch_size=max(1, min(args.batch_size, len(val_idx))),
                             collate_fn=collate, num_workers=args.num_workers)
                  if len(val_idx) else None)
        row = {"frac": frac, "n": int(n), "n_train": int(len(tr_idx)),
               "n_val": int(len(val_idx)), "batch_size_eff": int(_bs),
               "drop_last": bool(_drop)}
        for mode in ["pretrained", "scratch"]:
            if mode == "pretrained" and not args.encoder:
                continue
            model = Model(args.d_model).to(dev)
            if mode == "pretrained":
                ck = torch.load(args.encoder, map_location=dev)
                model.enc.load_state_dict(ck["encoder"])
            train_one(model, dl, dev, args.epochs, args.lr)
            # tau is selected ONCE, on the in-distribution validation split,
            # and reused for both test sets (see module docstring).
            tau = None
            if val_dl is not None:
                v_logits, v_labels, _ = collect_logits(model, val_dl, dev)
                v_probs = torch.softmax(v_logits, 1)[:, 1]
                tau = float(select_threshold(v_probs, v_labels))
            cal = abs(frac - 1.0) < 1e-9
            indist = eval_on(model, indist_dl, dev, with_cal=cal, tau=tau)
            xpop = eval_on(model, xpop_dl, dev, with_cal=cal, tau=tau)
            row[mode] = {"in_dist": indist, "xpop": xpop,
                         "gap_F1": indist["f1_at_tau"] - xpop["f1_at_tau"],
                         "gap_auprc": indist["auprc"] - xpop["auprc"],
                         "gap_F1_at_half": indist["f1_at_half"] - xpop["f1_at_half"]}
            print(f"  frac={frac} {mode}: in-dist F1@tau={indist['f1_at_tau']:.3f} "
                  f"xpop F1@tau={xpop['f1_at_tau']:.3f} "
                  f"gap={row[mode]['gap_F1']:.3f} "
                  f"xpop AUPRC={xpop['auprc']:.3f} tau={indist['tau']:.3f}",
                  flush=True)
        results["label_efficiency"].append(row)

    with open(args.out, "w") as fo:
        json.dump(results, fo, indent=2)
    print(f"[{time.strftime('%H:%M:%S')}] wrote {args.out}", flush=True)


if __name__ == "__main__":
    main()
