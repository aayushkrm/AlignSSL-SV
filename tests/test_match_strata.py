#!/usr/bin/env python3
"""Verify that quantile-matched negative selection destroys the depth shortcut.

The whole point of scripts/extract_tensors_hardneg.py is that the feature which
made the uniform-negative benchmark separable (centre-vs-flank depth ratio,
ROC-AUC 0.955 untrained) should carry near-zero information after matching. If
that property does not hold, the re-extraction is pointless and the manuscript's
Section 4.2 remediation claim is unsupported -- so it is asserted here rather
than merely inspected after a 6-hour extraction job.

Run: python tests/test_match_strata.py
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from extract_tensors_hardneg import (  # noqa: E402
    match_strata, ratio_from_profile, BIN_BP,
)


def auc(pos, neg):
    """ROC-AUC of a single feature separating pos from neg, via rank statistic.

    Oriented so that lower feature values predicting 'positive' gives AUC > 0.5.
    0.5 = the feature is uninformative.
    """
    pos, neg = np.asarray(pos), np.asarray(neg)
    allv = np.concatenate([pos, neg])
    r = np.argsort(np.argsort(-allv))          # descending -> low value = high rank
    rp = r[: pos.size].sum()
    n1, n2 = pos.size, neg.size
    return (rp - n1 * (n1 - 1) / 2.0) / (n1 * n2)


def main():
    rng = np.random.default_rng(0)
    fail = []

    # Simulate the real geometry: positives are a mixture of homozygous
    # (ratio ~ 0.05) and heterozygous (ratio ~ 0.5) deletions; the genome-wide
    # candidate pool is dominated by copy-neutral windows (ratio ~ 1.0) with a
    # mappability-dropout tail near 0.
    n_pos = 2000
    hom = rng.normal(0.05, 0.03, n_pos // 3)
    het = rng.normal(0.50, 0.10, n_pos - n_pos // 3)
    pos = np.clip(np.concatenate([hom, het]), 0.0, None)

    # Candidate supply from an EXHAUSTIVE stride scan of a chromosome
    # (~10^6 windows), not the ~10^4 a per-window fetch budget allows. The
    # informative 0.2-0.8 band is a small fraction of windows, so the absolute
    # count available there is what decides whether matching can succeed --
    # this is precisely why chrom_coverage() replaced per-window fetches.
    n_pool = 1_000_000
    neutral = rng.normal(1.00, 0.15, int(n_pool * 0.93))
    dropout = np.abs(rng.normal(0.02, 0.02, int(n_pool * 0.04)))
    # real genomes carry CNV/repeat windows across the intermediate band
    middling = rng.uniform(0.05, 0.95, n_pool - neutral.size - dropout.size)
    pool = np.clip(np.concatenate([neutral, dropout, middling]), 0.0, None)

    n_keep = n_pos * 3

    # 1. Uniform sampling (the OLD benchmark) must be highly separable --
    #    this reproduces the pathology the control exposed.
    unif = pool[rng.choice(pool.size, n_keep, replace=False)]
    a_unif = auc(pos, unif)
    if a_unif < 0.90:
        fail.append(f"uniform-negative AUC {a_unif:.3f} < 0.90 -- simulation "
                    "does not reproduce the reported pathology")

    # 2. Lowest-tail sampling (the REJECTED fix) must also be separable, with
    #    the sign inverted -- this is why tail selection was not used.
    tail = np.sort(pool)[:n_keep]
    a_tail = auc(pos, tail)
    if abs(a_tail - 0.5) < 0.15:
        fail.append(f"tail-selected AUC {a_tail:.3f} is unexpectedly close to "
                    "0.5; the argument against tail selection needs revisiting")

    # 3. Quantile matching must leave the feature near-uninformative.
    idx = match_strata(pos, pool, n_keep, rng, n_strata=10)
    matched = pool[np.asarray(idx)]
    a_match = auc(pos, matched)
    if len(idx) != n_keep:
        fail.append(f"matched selection returned {len(idx)} of {n_keep}")
    if abs(a_match - 0.5) > 0.10:
        fail.append(f"matched AUC {a_match:.3f} is not within 0.10 of 0.5 -- "
                    "the shortcut survives matching")

    # 4. Degenerate inputs must not raise.
    for p, n, k in [([], [1.0, 2.0], 5), ([1.0], [], 5), ([1.0], [1.0], 0),
                    ([2.0] * 50, [2.0] * 50, 10)]:
        try:
            match_strata(p, n, k, rng)
        except Exception as exc:                      # noqa: BLE001
            fail.append(f"match_strata({p!r:.20}, ..., {k}) raised {exc!r}")

    # 5. Quota must never exceed the available pool.
    small = match_strata(pos, pool[:100], 999, rng)
    if len(small) > 100:
        fail.append(f"returned {len(small)} indices from a pool of 100")

    # 6. ratio_from_profile must agree with a brute-force sum over the profile.
    cov = rng.random(4000).astype(np.float32) * 30.0
    cov[900:940] = 0.0                        # a deletion-like dropout
    span, bb = 1024, BIN_BP
    starts = np.array([0, 1000, 57000, 60000, 3_000_000], dtype=np.int64)
    got = ratio_from_profile(cov, starts, span, bin_bp=bb)
    for i, s in enumerate(starts):
        q0, q1 = s + span // 4, s + 3 * span // 4
        lo = lambda x: int(np.clip(x // bb, 0, cov.size))  # noqa: E731
        # accumulate in float64: the function uses a float64 cumsum, so a
        # float32 reference sum would differ by ~1e-7 for numerical reasons
        # rather than logical ones.
        c = cov[lo(q0):lo(q1)].sum(dtype=np.float64)
        f = (cov[lo(s):lo(q0)].sum(dtype=np.float64)
             + cov[lo(q1):lo(s + span)].sum(dtype=np.float64))
        want = (c / f) if f > 0 else np.inf
        if not (np.isinf(want) and np.isinf(got[i])) and \
           abs(got[i] - want) > 1e-6 * max(1.0, abs(want)):
            fail.append(f"ratio_from_profile[{s}] = {got[i]!r}, brute force {want!r}")

    print(f"uniform-negative AUC   = {a_unif:.3f}   (pathology, expect >0.90)")
    print(f"tail-selected AUC      = {a_tail:.3f}   (rejected fix, expect far from 0.5)")
    print(f"quantile-matched AUC   = {a_match:.3f}   (expect ~0.5)")
    print(f"pos median {np.median(pos):.3f} vs matched median "
          f"{np.median(matched):.3f}")

    if fail:
        print("\nFAIL")
        for f in fail:
            print("  -", f)
        return 1
    print("\nPASS: quantile matching removes the depth-ratio shortcut")
    return 0


if __name__ == "__main__":
    sys.exit(main())
