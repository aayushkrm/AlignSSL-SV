#!/usr/bin/env python3
"""Why a fixed-0.5 F1 cannot support this paper's original headline claim.

The manuscript as first written compared arms by F1 at a fixed 0.5 probability
cut, and reported a ~10x gap at 1% labels (pretrained 0.514 vs from-scratch
0.050). Recomputation under threshold-free scoring shows the gap is mostly an
artefact of *where each model's sigmoid sits*, not of how well it ranks:

    uniform benchmark, 1% labels, seed 0
      pretrained    F1@tau = 0.456   F1@0.5 = 0.362   AUPRC = 0.463
      from-scratch  F1@tau = 0.451   F1@0.5 = 0.035   AUPRC = 0.484

The from-scratch model's AUPRC is *higher*, so it ranks the test set at least
as well; its F1@0.5 collapses because it places nearly all probabilities below
0.5. The apparent order-of-magnitude gap measures calibration, not
discrimination.

This script isolates that mechanism on synthetic data, holding the ranking
signal exactly constant and moving only the sigmoid offset. Run it to see two
models with identical AUPRC and identical best-threshold F1 differ by a large
margin at the fixed cut.
"""
from __future__ import annotations

import argparse

import numpy as np
from sklearn.metrics import average_precision_score, f1_score


def demo(n=4000, pos_rate=0.25, signal=1.4, seed=0):
    """Two models, one ranking, two sigmoid offsets."""
    rng = np.random.default_rng(seed)
    y = (rng.random(n) < pos_rate).astype(int)
    # A single latent score shared by both models: ranking is held constant.
    latent = rng.normal(0.0, 1.0, n) + signal * y

    rows = []
    for name, offset in [("miscalibrated", 2.0), ("calibrated", 0.9)]:
        p = 1.0 / (1.0 + np.exp(-(latent - offset)))
        taus = np.linspace(0.01, 0.99, 197)
        rows.append({
            "model": name,
            "sigmoid_offset": offset,
            "auprc": average_precision_score(y, p),
            "f1_at_half": f1_score(y, (p >= 0.5).astype(int), zero_division=0),
            "f1_at_best_tau": max(
                f1_score(y, (p >= t).astype(int), zero_division=0) for t in taus),
        })
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()

    rows = demo(seed=a.seed)
    print(f"{'model':16s} {'offset':>7s} {'AUPRC':>8s} {'F1@0.5':>8s} {'F1@tau':>8s}")
    for r in rows:
        print(f"{r['model']:16s} {r['sigmoid_offset']:>7.1f} "
              f"{r['auprc']:>8.3f} {r['f1_at_half']:>8.3f} "
              f"{r['f1_at_best_tau']:>8.3f}")

    a0, a1 = rows[0]["auprc"], rows[1]["auprc"]
    assert abs(a0 - a1) < 1e-12, "ranking must be identical by construction"
    gap_half = abs(rows[0]["f1_at_half"] - rows[1]["f1_at_half"])
    gap_tau = abs(rows[0]["f1_at_best_tau"] - rows[1]["f1_at_best_tau"])
    print()
    print(f"AUPRC identical to machine precision ({a0:.6f}); "
          f"F1@0.5 differs by {gap_half:.3f} while F1@tau differs by {gap_tau:.3f}.")
    print("A fixed-0.5 comparison therefore cannot separate 'better "
          "representation' from 'logits nearer 0.5'.")


if __name__ == "__main__":
    main()
