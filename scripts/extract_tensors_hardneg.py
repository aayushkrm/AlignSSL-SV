#!/usr/bin/env python3
"""Labelled alignment tensors with HARD negatives (candidate-filtering task).

Why this script exists
----------------------
`scripts/extract_tensors.py` samples negative windows uniformly at random from
the genome, rejecting only those that overlap or abut a truth deletion. A
control experiment (`scripts/classical_baseline_eval.py`) showed that benchmark
is close to trivially separable: the single feature "centre-vs-flank read depth
ratio" reaches ROC-AUC 0.955 on the held-out chromosomes with no training at
all, and a 12-feature gradient-boosted tree reaches F1 = 0.894 from 210 labels
-- above every deep arm at that budget. A random genomic window simply does not
look like a deletion, so the task measured "is there a depth drop here", not
"is this candidate a real deletion".

This script replaces uniform negatives with the false positives of a
depth-based candidate generator, which is the decision an SV caller actually
faces. For each chromosome we draw a large pool of non-truth windows, score
each by the same centre/flank depth ratio, and keep the most deletion-like
ones. Negatives are therefore, by construction, windows where the shortcut
feature fires. The task becomes: given that a depth dip was proposed here,
is it a real deletion?

The positive set, window geometry, channel layout, multi-scale binning,
chromosome split, and shard format are unchanged, so results are directly
comparable to the uniform-negative benchmark arm for arm.

Cost note: scoring is one BAM fetch per candidate over read *coordinates* only
(no tensor build), so a pool multiplier of ~12 costs roughly the same as the
tensor build it feeds.
"""
from __future__ import annotations
import argparse, os, time
import numpy as np
import pysam

from alignssl.tensorize import build_tensor, N_CHANNELS
from alignssl.data import load_truth_dels, bin_for_len, estimate_isize, CHROM_SPLIT


def chrom_to_int(c):
    c = str(c).replace("chr", "")
    return {"X": 23, "Y": 24, "MT": 25, "M": 25}.get(c, int(c) if c.isdigit() else 0)


def depth_ratio(bam, chrom, s, span):
    """centre-vs-flank read-depth ratio from read coordinates only.

    Returns ratio in [0, inf); a real deletion drives it toward 0. Mirrors
    `depth_centre_flank_ratio` in classical_baseline_eval.py, which is the
    feature that made the uniform-negative benchmark separable.
    """
    q0, q1 = s + span // 4, s + 3 * span // 4          # centre half
    cov_c = cov_f = 0
    try:
        for r in bam.fetch(chrom, max(0, s), s + span):
            if r.is_unmapped or r.reference_end is None:
                continue
            a, b = r.reference_start, r.reference_end
            # overlap with centre half, and with the two flanking quarters
            oc = max(0, min(b, q1) - max(a, q0))
            of = max(0, min(b, q0) - max(a, s)) + max(0, min(b, s + span) - max(a, q1))
            cov_c += oc
            cov_f += of
        # normalise by the width of each region (centre = span/2, flanks = span/2)
        dc = cov_c / (span / 2.0)
        df = cov_f / (span / 2.0)
    except (ValueError, KeyError):
        return np.inf
    if df <= 0:
        return np.inf          # no flanking coverage -> uninformative, not hard
    return dc / df


def build_items(truth_by_chrom, fa, bam, win_width, n_neg_per_pos, multiscale,
                seed, pool_mult, log_every=20000):
    """Positives centred on truth deletions; negatives = the most
    deletion-like non-truth windows a depth pre-filter would propose."""
    rng = np.random.default_rng(seed)
    items = []
    n_scored = 0
    t0 = time.time()
    for chrom, dels in truth_by_chrom.items():
        if not dels:
            continue
        clen = fa.get_reference_length(chrom)
        bins_used, pos_spans = set(), []
        for (ds, de, geno) in dels:
            ln = de - ds
            bs = bin_for_len(ln, win_width) if multiscale else 1
            bins_used.add(bs)
            span = win_width * bs
            mid = (ds + de) // 2
            s = max(0, min(mid - span // 2, clen - span))
            bp0, bp1 = (ds - s) / span, (de - s) / span
            items.append((chrom, s, win_width, bs, 1, geno, bp0, bp1, ln))
            pos_spans.append((s, span))
        bins_used = sorted(bins_used) or [1]

        n_neg = len(dels) * n_neg_per_pos
        # draw a pool of valid (non-truth) candidates, then keep the hardest
        pool = []
        target_pool = n_neg * pool_mult
        guard = 0
        while len(pool) < target_pool and guard < target_pool * 40:
            guard += 1
            bs = int(rng.choice(bins_used))
            span = win_width * bs
            s = int(rng.integers(0, max(1, clen - span)))
            if any(s < de and s + span > ds for ds, de, _ in dels):
                continue
            if any(abs(s - ps) < span for ps, _ in pos_spans):
                continue
            pool.append((s, bs, span))
        # score the pool; hardest = lowest centre/flank depth ratio
        scored = []
        for (s, bs, span) in pool:
            r = depth_ratio(bam, chrom, s, span)
            if np.isfinite(r):
                scored.append((r, s, bs))
            n_scored += 1
            if n_scored % log_every == 0:
                print(f"    scored {n_scored} candidates "
                      f"({n_scored/max(1e-9, time.time()-t0):.0f}/s)", flush=True)
        scored.sort(key=lambda z: z[0])
        keep = scored[:n_neg]
        for (r, s, bs) in keep:
            items.append((chrom, s, win_width, bs, 0, 0, np.nan, np.nan, 0))
        if keep:
            print(f"  chrom {chrom}: {len(dels)} pos, pool {len(pool)}, "
                  f"kept {len(keep)} neg, depth-ratio kept "
                  f"[{keep[0][0]:.3f}, {keep[-1][0]:.3f}]", flush=True)
    return items


def flush_shard(out_dir, sample, split, shard_idx, shard, meta, manifest):
    X = np.stack(shard).astype(np.float16)
    M = np.asarray(meta, dtype=np.float64)
    path = os.path.join(out_dir, f"{sample}_{split}_shard{shard_idx:04d}.npz")
    np.savez_compressed(
        path, x=X, label=M[:, 0].astype(np.int64), geno=M[:, 1].astype(np.int64),
        bp0=M[:, 2], bp1=M[:, 3], bin_size=M[:, 4].astype(np.int64),
        del_len=M[:, 5], chrom=M[:, 6].astype(np.int64),
        start=M[:, 7].astype(np.int64))
    manifest.append((os.path.basename(path), len(shard),
                     int(M[:, 0].sum())))
    return shard_idx + 1, len(shard)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bam", required=True)
    ap.add_argument("--bai", default=None)
    ap.add_argument("--fasta", required=True)
    ap.add_argument("--vcf", required=True)
    ap.add_argument("--sample", required=True)
    ap.add_argument("--split", choices=["train", "test", "all"], default="all")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--win-width", type=int, default=256)
    ap.add_argument("--max-rows", type=int, default=64)
    ap.add_argument("--n-neg-per-pos", type=int, default=3)
    ap.add_argument("--pool-mult", type=int, default=12,
                    help="candidates scored per negative kept; higher = harder")
    ap.add_argument("--shard-size", type=int, default=1024)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--no-multiscale", action="store_true")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    chroms = (CHROM_SPLIT["train"] + CHROM_SPLIT["test"]
              if args.split == "all" else CHROM_SPLIT[args.split])
    print(f"[{time.strftime('%H:%M:%S')}] HARD-NEG extraction {args.sample} "
          f"split={args.split} pool_mult={args.pool_mult}", flush=True)
    truth = load_truth_dels(args.vcf, args.sample, chroms=chroms)
    print(f"  truth DELs: {sum(len(v) for v in truth.values())}", flush=True)

    fa = pysam.FastaFile(args.fasta)
    bam = pysam.AlignmentFile(args.bam, "rb", index_filename=args.bai)
    items = build_items(truth, fa, bam, args.win_width, args.n_neg_per_pos,
                        not args.no_multiscale, args.seed, args.pool_mult)
    rng = np.random.default_rng(args.seed + 1)
    items = [items[i] for i in rng.permutation(len(items))]
    if args.limit > 0:
        items = items[:args.limit]
    n_pos = sum(1 for it in items if it[4] == 1)
    print(f"  items: {len(items)} ({n_pos} pos / {len(items)-n_pos} neg)",
          flush=True)

    isize = {}

    def get_isize(chrom):
        if chrom not in isize:
            isize[chrom] = estimate_isize(args.bam, chrom, bai=args.bai)
        return isize[chrom]

    shard, meta, manifest = [], [], []
    shard_idx = 0
    t0 = time.time()
    for k, (chrom, s, w, bs, label, geno, bp0, bp1, ln) in enumerate(items):
        span = w * bs
        reads = list(bam.fetch(chrom, max(0, s), s + span))
        ref = fa.fetch(chrom, s, s + span)
        im, isd = get_isize(chrom)
        X = build_tensor(reads, ref, s, w, max_rows=args.max_rows,
                         isize_mean=im, isize_sd=isd, bin_size=bs)
        shard.append(X.astype(np.float16))
        meta.append((label, geno, bp0, bp1, bs, ln,
                     int(chrom_to_int(chrom)), s))
        if len(shard) >= args.shard_size:
            shard_idx, _ = flush_shard(args.out_dir, args.sample, args.split,
                                       shard_idx, shard, meta, manifest)
            shard, meta = [], []
        if (k + 1) % 500 == 0:
            dt = time.time() - t0
            print(f"  [{k+1}/{len(items)}] {dt:.0f}s "
                  f"({(k+1)/dt:.1f} loci/s)", flush=True)
    if shard:
        shard_idx, _ = flush_shard(args.out_dir, args.sample, args.split,
                                   shard_idx, shard, meta, manifest)

    man = os.path.join(args.out_dir, f"manifest_{args.sample}_{args.split}.tsv")
    with open(man, "w") as f:
        f.write("shard\tn\tn_pos\n")
        for row in manifest:
            f.write("\t".join(str(x) for x in row) + "\n")
    print(f"[{time.strftime('%H:%M:%S')}] DONE: "
          f"{sum(r[1] for r in manifest)} tensors -> {args.out_dir}", flush=True)


if __name__ == "__main__":
    main()
