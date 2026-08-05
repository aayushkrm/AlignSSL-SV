#!/usr/bin/env python3
"""Hand-crafted-feature control baseline for AlignSSL-SV.

Purpose (reviewer control, not a competing method): quantify how much of the
deletion-calling benchmark is solvable by the classical alignment signatures
that pre-deep-learning callers use -- a depth drop, an excess of discordant
pairs, and soft-clip/split-read enrichment -- summarised as a handful of
scalar features and fed to a linear model and a gradient-boosted tree.

If these shallow models approach the deep models' F1, the benchmark is easy
and the deep-learning contribution is overstated. If they fall well short,
the learned representation is doing real work. Either answer belongs in the
paper; this script produces it.

Runs on exactly the same shards, the same chromosome-disjoint split, the same
label fractions, and the same seeds as scripts/finetune_eval.py, so numbers
drop straight into the label-efficiency table as an extra column.

Feature set (per window, from the 18-channel alignment tensor):
  depth (ch 11)     : mean, sd, min, centre-vs-flank ratio, max local drop
  discordant (ch 8) : rate over valid bases
  soft-clip  (ch 9) : rate over valid bases
  insert-size(ch10) : mean |z|, max |z|
  MAPQ       (ch 6) : mean
  coverage   (ch17) : n valid read rows, valid-base fraction
"""
from __future__ import annotations
import argparse, json, sys, time
import numpy as np

sys.path.insert(0, "/scratch/igorno-alignssl_sv/code")
from alignssl.data import open_shards
from alignssl.protocol import label_budget, split_budget
from alignssl.metrics import score_arm  # noqa: E402

Q_MAPQ, Q_DISC, Q_CLIP, Q_ISIZE, Q_DEPTH, Q_VALID = 6, 8, 9, 10, 11, 17
FEAT_NAMES = ["depth_mean", "depth_sd", "depth_min", "depth_centre_flank_ratio",
              "depth_max_drop", "discordant_rate", "clip_rate",
              "isize_absz_mean", "isize_absz_max", "mapq_mean",
              "n_read_rows", "valid_frac"]


def featurise(x: np.ndarray) -> np.ndarray:
    """x: (18, R, W) float32 -> (12,) float64 classical feature vector."""
    valid = x[Q_VALID]                      # (R, W) 1 where a real base sits
    nvalid = float(valid.sum())
    denom = max(nvalid, 1.0)

    # depth is a column signal broadcast down rows; row 0 is the profile
    prof = x[Q_DEPTH, 0].astype(np.float64)          # (W,)
    W = prof.shape[0]
    c0, c1 = W // 3, 2 * W // 3
    centre = prof[c0:c1].mean()
    flank = np.concatenate([prof[:c0], prof[c1:]]).mean()
    ratio = centre / flank if flank > 1e-9 else 1.0
    # largest sustained drop: min of a sliding 1/8-window mean vs global mean
    k = max(1, W // 8)
    kern = np.ones(k) / k
    smooth = np.convolve(prof, kern, mode="valid")
    gmean = prof.mean()
    max_drop = float(gmean - smooth.min()) if smooth.size else 0.0

    return np.array([
        gmean, float(prof.std()), float(prof.min()), float(ratio), max_drop,
        float((x[Q_DISC] * valid).sum() / denom),
        float((x[Q_CLIP] * valid).sum() / denom),
        float((np.abs(x[Q_ISIZE]) * valid).sum() / denom),
        float(np.abs(x[Q_ISIZE] * valid).max()),
        float((x[Q_MAPQ] * valid).sum() / denom),
        float((valid.sum(axis=1) > 0).sum()),
        float(nvalid / valid.size),
    ], dtype=np.float64)


def build(shard_dir: str, split: str):
    ds = open_shards(shard_dir, split=split, labeled=True)
    n = len(ds)
    X = np.zeros((n, len(FEAT_NAMES)), dtype=np.float64)
    y = np.zeros(n, dtype=np.int64)
    dl = np.zeros(n, dtype=np.float64)
    t0 = time.time()
    for i in range(n):
        item = ds[i]          # dict: x, label, geno, bp, bin_size, del_len
        X[i] = featurise(np.asarray(item["x"], dtype=np.float32))
        y[i] = int(item["label"])
        dl[i] = float(item["del_len"])
        if (i + 1) % 2000 == 0:
            print(f"  {split} {i+1}/{n}  {time.time()-t0:.0f}s", flush=True)
    print(f"  {split}: X={X.shape} pos={int(y.sum())} neg={int((y==0).sum())}", flush=True)
    return X, y, dl


def prf1(y, p):
    tp = int(((p == 1) & (y == 1)).sum()); fp = int(((p == 1) & (y == 0)).sum())
    fn = int(((p == 0) & (y == 1)).sum())
    P = tp / (tp + fp) if tp + fp else 0.0
    R = tp / (tp + fn) if tp + fn else 0.0
    F = 2 * P * R / (P + R) if P + R else 0.0
    return P, R, F


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard-dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--label-fracs", default="0.01,0.05,0.1,0.25,0.5,1.0")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--val-frac", type=float, default=0.2)
    a = ap.parse_args()

    from sklearn.linear_model import LogisticRegression
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import average_precision_score

    Xtr, ytr, _ = build(a.shard_dir, "train")
    Xte, yte, _ = build(a.shard_dir, "test")
    Xtr = np.nan_to_num(Xtr, nan=0.0, posinf=0.0, neginf=0.0)
    Xte = np.nan_to_num(Xte, nan=0.0, posinf=0.0, neginf=0.0)

    fracs = [float(f) for f in a.label_fracs.split(",")]
    rng = np.random.default_rng(a.seed)
    order = rng.permutation(len(ytr))
    rows = []
    for f in fracs:
        n = label_budget(f, len(ytr))
        idx = order[:n]
        # Validation split carved OUT OF the labelled budget, exactly as in
        # scripts/finetune_eval.py, so the threshold every arm uses is
        # selected under the same label cost.
        n_val, _n_tr, _did = split_budget(n, a.val_frac)
        if n_val >= 2 and n - n_val >= 2:
            v_idx, t_idx = idx[:n_val], idx[n_val:]
        else:
            v_idx, t_idx = idx[:0], idx
        Xs, ys = Xtr[t_idx], ytr[t_idx]
        Xv, yv = Xtr[v_idx], ytr[v_idx]
        rec = {"frac": f, "n": int(n), "n_train": int(len(t_idx)),
               "n_val": int(len(v_idx))}
        if len(np.unique(ys)) < 2:
            zero = score_arm(np.zeros(len(yte)), yte)
            rec["logreg"] = rec["hgb"] = zero
            rows.append(rec); continue
        sc = StandardScaler().fit(Xs)
        lr = LogisticRegression(max_iter=2000, class_weight="balanced")
        lr.fit(sc.transform(Xs), ys)
        pv = lr.predict_proba(sc.transform(Xv))[:, 1] if len(yv) else None
        rec["logreg"] = score_arm(
            lr.predict_proba(sc.transform(Xte))[:, 1], yte, pv,
            yv if len(yv) else None)
        hgb = HistGradientBoostingClassifier(random_state=a.seed)
        hgb.fit(Xs, ys)
        hv = hgb.predict_proba(Xv)[:, 1] if len(yv) else None
        rec["hgb"] = score_arm(hgb.predict_proba(Xte)[:, 1], yte, hv,
                               yv if len(yv) else None)
        print(f"frac={f} n={n} logreg F1@tau={rec['logreg']['f1_at_tau']:.4f} "
              f"AUPRC={rec['logreg']['auprc']:.4f} | "
              f"hgb F1@tau={rec['hgb']['f1_at_tau']:.4f} "
              f"AUPRC={rec['hgb']['auprc']:.4f}", flush=True)
        rows.append(rec)

    json.dump({"label_efficiency": rows, "features": FEAT_NAMES,
               "config": vars(a), "n_train_pool": int(len(ytr)),
               "n_test": int(len(yte))}, open(a.out, "w"), indent=1)
    print("WROTE", a.out, flush=True)


if __name__ == "__main__":
    main()
