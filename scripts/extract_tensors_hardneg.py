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


BIN_BP = 64          # coverage-profile resolution; divides win_width (256)


def chrom_coverage(bam, chrom, clen, bin_bp=BIN_BP):
    """Per-bin read coverage for a whole chromosome in ONE pass over the BAM.

    Returns a float32 array of length ceil(clen / bin_bp) holding the number of
    reads overlapping each bin (proportional to depth, which is all a ratio
    needs). Built with a difference array, so cost is O(reads) with two array
    writes per read rather than a pysam fetch per candidate window.

    This is what makes exhaustive candidate scanning affordable. Scoring
    windows by individual `bam.fetch` calls costs ~1 ms each, capping a
    chromosome at ~10^4 candidates; the informative depth-ratio range covers
    well under 1% of random windows, so that budget cannot supply enough
    hard candidates to match the positive distribution (see match_strata).
    With a profile in memory, scoring is array arithmetic and every window on
    the chromosome can be considered.
    """
    n = int(clen // bin_bp) + 2
    diff = np.zeros(n + 1, dtype=np.int32)
    for r in bam.fetch(chrom):
        if r.is_unmapped or r.reference_end is None:
            continue
        a = int(r.reference_start) // bin_bp
        b = int(r.reference_end) // bin_bp + 1
        if a >= n:
            continue
        diff[a] += 1
        diff[min(b, n)] -= 1
    return np.cumsum(diff[:n]).astype(np.float32)


def ratio_from_profile(cov, starts, span, bin_bp=BIN_BP):
    """Vectorised centre-vs-flank depth ratio for many window starts.

    Mirrors `depth_centre_flank_ratio` in classical_baseline_eval.py -- the
    feature that made the uniform-negative benchmark separable -- but reads
    from the binned profile. A real deletion drives the ratio toward 0
    (homozygous) or ~0.5 (heterozygous); copy-neutral sequence sits near 1.

    Windows whose flanks carry no coverage return inf and are dropped by the
    caller: they are unmappable, not hard.
    """
    starts = np.asarray(starts, dtype=np.int64)
    csum = np.concatenate([[0.0], np.cumsum(cov, dtype=np.float64)])
    nb = cov.size

    def seg(lo, hi):
        lo = np.clip(lo // bin_bp, 0, nb)
        hi = np.clip(hi // bin_bp, 0, nb)
        return csum[hi] - csum[lo]

    q0, q1 = starts + span // 4, starts + 3 * span // 4
    centre = seg(q0, q1)
    flank = seg(starts, q0) + seg(q1, starts + span)
    out = np.full(starts.shape, np.inf, dtype=np.float64)
    ok = flank > 0
    out[ok] = centre[ok] / flank[ok]
    return out


def match_strata(pos, neg, n_keep, rng, n_strata=10):
    """Choose `n_keep` indices into `neg` so the kept values' distribution
    approximates that of `pos`.

    Stratifies on the quantiles of `pos` and allocates the quota across strata
    in proportion to the positive mass in each, drawing uniformly at random
    within a stratum. Shortfalls (a stratum the candidate pool cannot fill,
    or floor-rounding of the quota) are redistributed over the remaining
    candidates in ascending order of distance to the positive median, so a
    deficit degrades toward the bulk of the positive distribution rather than
    toward whichever extreme the pool happens to over-represent.

    Returns a list of indices into `neg`, of length min(n_keep, len(neg)).
    """
    pos = np.asarray(pos, dtype=np.float64)
    neg = np.asarray(neg, dtype=np.float64)
    if pos.size == 0 or neg.size == 0 or n_keep <= 0:
        return []
    n_keep = int(min(n_keep, neg.size))

    qs = np.linspace(0.0, 1.0, n_strata + 1)
    cuts = np.quantile(pos, qs)
    inner = np.unique(cuts[1:-1])          # collapse ties (discrete features)
    n_bin = inner.size + 1
    pos_bin = np.digitize(pos, inner, right=False)
    neg_bin = np.digitize(neg, inner, right=False)

    weights = np.bincount(pos_bin, minlength=n_bin) / float(pos.size)
    buckets = [list(np.nonzero(neg_bin == k)[0]) for k in range(n_bin)]
    for b in buckets:
        rng.shuffle(b)

    want = np.floor(weights * n_keep).astype(int)
    keep = []
    for k in range(n_bin):
        take = int(min(want[k], len(buckets[k])))
        keep.extend(buckets[k][:take])
        buckets[k] = buckets[k][take:]

    shortfall = n_keep - len(keep)
    if shortfall > 0:
        med = float(np.median(pos))
        left = [j for b in buckets for j in b]
        left.sort(key=lambda j: abs(neg[j] - med))
        keep.extend(left[:shortfall])
    return keep


def build_items(truth_by_chrom, fa, bam, win_width, n_neg_per_pos, multiscale,
                seed, pool_mult, n_strata=10, log_every=20000):
    """Positives centred on truth deletions; negatives drawn so that their
    centre/flank depth-ratio distribution MATCHES the positives'.

    Why distribution matching rather than "keep the lowest ratios"
    -------------------------------------------------------------
    An earlier version of this function kept the `n_neg` candidates with the
    smallest depth ratio. That over-corrects and does not model a candidate
    generator. The extreme lower tail of a genome-wide scan is dominated by
    mappability dropouts and centromeric gaps with ratio ~ 0, whereas a
    heterozygous deletion sits near 0.5 and a homozygous one near 0. Keeping
    the tail therefore *inverts* the shortcut -- a classifier learns "ratio
    very near zero => negative" and the benchmark stays trivially separable,
    just with the sign flipped. Reported separability would look fixed while
    the task remained an artefact.

    Instead we stratify the positives' own depth-ratio distribution into
    `n_strata` quantile bins and fill each bin with negatives drawn from the
    candidate pool at the same relative frequency. By construction the feature
    that made the uniform-negative benchmark separable then carries (close to)
    zero marginal information, and the classifier must use breakpoint
    signatures -- soft-clips, discordant insert sizes, split reads -- which is
    the decision an SV caller actually faces after a depth pre-filter has
    proposed a candidate. Section 4.2 of the manuscript reports the resulting
    control AUC as the check that this worked.

    Positive geometry, channel layout, multi-scale binning, chromosome split
    and shard format are untouched, so arms remain comparable.
    """
    rng = np.random.default_rng(seed)
    items = []
    t0 = time.time()
    stats = []
    for chrom, dels in truth_by_chrom.items():
        if not dels:
            continue
        clen = fa.get_reference_length(chrom)
        cov = chrom_coverage(bam, chrom, clen)
        print(f"  chrom {chrom}: coverage profile {cov.size} bins "
              f"({time.time()-t0:.0f}s elapsed)", flush=True)

        # ---- positives, and their depth-ratio distribution per scale -------
        by_scale = {}                      # bs -> list of positive starts
        pos_spans = []
        for (ds, de, geno) in dels:
            ln = de - ds
            bs = bin_for_len(ln, win_width) if multiscale else 1
            span = win_width * bs
            mid = (ds + de) // 2
            s = max(0, min(mid - span // 2, clen - span))
            bp0, bp1 = (ds - s) / span, (de - s) / span
            items.append((chrom, s, win_width, bs, 1, geno, bp0, bp1, ln))
            pos_spans.append((s, span))
            by_scale.setdefault(bs, []).append(s)

        # Matching is done WITHIN each multi-scale bin. Window span changes the
        # ratio's meaning (a 256 bp window inside a 4 kb deletion is fully
        # deleted; a 4 kb window around it is not), so pooling scales would
        # let the model recover the label from span alone.
        for bs, pstarts in sorted(by_scale.items()):
            span = win_width * bs
            pos_r = ratio_from_profile(cov, pstarts, span)
            pos_r = pos_r[np.isfinite(pos_r)]
            if pos_r.size == 0:
                continue
            n_neg = len(pstarts) * n_neg_per_pos

            # ---- exhaustive candidate scan on a stride-span/4 grid ---------
            step = max(win_width // 4, span // 4)
            cand = np.arange(0, max(1, clen - span), step, dtype=np.int64)
            # reject candidates overlapping ANY truth deletion (± one span) or
            # any positive window, so negatives are true non-deletions
            keepmask = np.ones(cand.size, dtype=bool)
            for (ds, de, _) in dels:
                keepmask &= ~((cand < de + span) & (cand + span > ds - span))
            for (ps, pspan) in pos_spans:
                keepmask &= ~(np.abs(cand - ps) < max(span, pspan))
            cand = cand[keepmask]
            if cand.size == 0:
                continue
            cr = ratio_from_profile(cov, cand, span)
            fin = np.isfinite(cr)
            cand, cr = cand[fin], cr[fin]
            if cand.size == 0:
                continue

            idx = match_strata(pos_r, cr, n_neg, rng, n_strata)
            for j in idx:
                items.append((chrom, int(cand[j]), win_width, bs, 0, 0,
                              np.nan, np.nan, 0))
            kr = cr[np.asarray(idx, dtype=int)] if idx else np.array([0.0])
            stats.append((chrom, bs, len(pstarts), len(idx), cand.size,
                          float(np.median(pos_r)), float(np.median(kr))))
            print(f"    scale {bs}: {len(pstarts)} pos, {cand.size} candidates "
                  f"scanned, {len(idx)} neg kept | depth-ratio median "
                  f"pos {np.median(pos_r):.3f} vs neg {np.median(kr):.3f}",
                  flush=True)

    if stats:
        dp = np.array([abs(s[5] - s[6]) for s in stats])
        print(f"  MATCH QUALITY: median |pos-neg| depth-ratio offset "
              f"{np.median(dp):.4f} over {len(stats)} chrom x scale groups "
              f"(0 = perfectly matched)", flush=True)
    return items


def flush_shard(out_dir, sample, split, shard_idx, shard, meta, manifest):
    X = np.stack(shard).astype(np.float16)
    M = np.asarray(meta, dtype=np.float64)
    path = os.path.join(out_dir, f"{sample}_{split}_shard{shard_idx:04d}.npz")
    # Schema must match scripts/extract_tensors.py EXACTLY -- alignssl.data
    # .ShardDataset is shared by the uniform-negative and hard-negative arms,
    # and it reads "X" (capital) and a two-column "bp". Writing "x"/"bp0"/"bp1"
    # here made every shard unreadable by the evaluators.
    np.savez_compressed(
        path, X=X,
        label=M[:, 0].astype(np.int64), geno=M[:, 1].astype(np.int64),
        bp=M[:, 2:4].astype(np.float32), bin_size=M[:, 4].astype(np.int64),
        del_len=M[:, 5].astype(np.int64), chrom=M[:, 6].astype(np.int64),
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
