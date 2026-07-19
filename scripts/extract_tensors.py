#!/usr/bin/env python3
"""Precompute labelled alignment tensors for AlignSSL-SV fine-tuning.

For a sample's BAM + the genotyped SV VCF, build 18-channel tensors around
truth deletions (positives, multi-scale via bin_for_len) plus E3-style
negatives, and write sharded .npz to --out-dir.

Coordinates: GRCh37, contigs named 1,2,...,X (no 'chr'). 1000G VCF is
1-based; pysam gives 0-based half-open loci (handled in load_truth_dels).
"""
from __future__ import annotations
import argparse, os, time
import numpy as np
import pysam

from alignssl.tensorize import build_tensor, N_CHANNELS
from alignssl.data import load_truth_dels, bin_for_len, estimate_isize, CHROM_SPLIT


def build_items(truth_by_chrom, fa, win_width, n_neg_per_pos, multiscale, seed):
    rng = np.random.default_rng(seed)
    items = []  # (chrom, start, width, bin_size, label, geno, bp0, bp1, del_len)
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
        for _ in range(len(dels) * n_neg_per_pos):
            bs = int(rng.choice(bins_used))
            span = win_width * bs
            for _try in range(30):
                s = int(rng.integers(0, max(1, clen - span)))
                if not any(s < de and s + span > ds for ds, de, _ in dels) and \
                   not any(abs(s - ps) < span for ps, _ in pos_spans):
                    items.append((chrom, s, win_width, bs, 0, 0, np.nan, np.nan, 0))
                    break
    return items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bam", required=True)
    ap.add_argument("--bai", default=None,
                    help="explicit .bai path if not beside the BAM")
    ap.add_argument("--fasta", required=True)
    ap.add_argument("--vcf", required=True)
    ap.add_argument("--sample", required=True)
    ap.add_argument("--split", choices=["train", "test", "all"], default="all")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--win-width", type=int, default=256)
    ap.add_argument("--max-rows", type=int, default=64)
    ap.add_argument("--n-neg-per-pos", type=int, default=3)
    ap.add_argument("--shard-size", type=int, default=1024)
    ap.add_argument("--limit", type=int, default=0, help="0 = no limit (smoke test)")
    ap.add_argument("--no-multiscale", action="store_true")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    if args.split == "all":
        chroms = CHROM_SPLIT["train"] + CHROM_SPLIT["test"]
    else:
        chroms = CHROM_SPLIT[args.split]

    print(f"[{time.strftime('%H:%M:%S')}] loading truth for {args.sample} "
          f"split={args.split} ({len(chroms)} chroms)", flush=True)
    truth = load_truth_dels(args.vcf, args.sample, chroms=chroms)
    n_dels = sum(len(v) for v in truth.values())
    print(f"  truth DELs: {n_dels} across {len(truth)} chroms", flush=True)

    fa = pysam.FastaFile(args.fasta)
    items = build_items(truth, fa, args.win_width, args.n_neg_per_pos,
                        not args.no_multiscale, args.seed)
    # deterministic shuffle so shards mix pos/neg and chroms
    rng = np.random.default_rng(args.seed + 1)
    perm = rng.permutation(len(items))
    items = [items[i] for i in perm]
    if args.limit > 0:
        items = items[:args.limit]
    n_pos = sum(1 for it in items if it[4] == 1)
    print(f"  items: {len(items)} ({n_pos} pos / {len(items)-n_pos} neg)", flush=True)

    # per-chrom insert-size stats (cache)
    isize = {}
    bam = pysam.AlignmentFile(args.bam, "rb", index_filename=args.bai)

    def get_isize(chrom):
        if chrom not in isize:
            isize[chrom] = estimate_isize(args.bam, chrom, bai=args.bai)
        return isize[chrom]

    W = args.win_width
    shard, meta = [], []
    shard_idx, n_written = 0, 0
    manifest = []
    t0 = time.time()
    for k, (chrom, s, w, bs, label, geno, bp0, bp1, ln) in enumerate(items):
        span = w * bs
        reads = list(bam.fetch(chrom, max(0, s), s + span))
        ref = fa.fetch(chrom, s, s + span)
        im, isd = get_isize(chrom)
        X = build_tensor(reads, ref, s, w, max_rows=args.max_rows,
                         isize_mean=im, isize_sd=isd, bin_size=bs)
        shard.append(X.astype(np.float16))
        meta.append((label, geno, bp0, bp1, bs, ln, int(chrom_to_int(chrom)), s))
        if len(shard) >= args.shard_size:
            shard_idx, n_written = flush_shard(
                args.out_dir, args.sample, args.split, shard_idx, shard, meta,
                manifest)
            shard, meta = [], []
        if (k + 1) % 500 == 0:
            dt = time.time() - t0
            print(f"  [{k+1}/{len(items)}] {dt:.0f}s "
                  f"({(k+1)/dt:.1f} loci/s)", flush=True)
    if shard:
        shard_idx, n_written = flush_shard(
            args.out_dir, args.sample, args.split, shard_idx, shard, meta,
            manifest)

    # write manifest
    man_path = os.path.join(
        args.out_dir, f"manifest_{args.sample}_{args.split}.tsv")
    with open(man_path, "w") as f:
        f.write("shard\tn\tn_pos\n")
        for row in manifest:
            f.write("\t".join(str(x) for x in row) + "\n")
    total = sum(r[1] for r in manifest)
    print(f"[{time.strftime('%H:%M:%S')}] DONE: {total} tensors in "
          f"{len(manifest)} shards -> {args.out_dir}", flush=True)
    print(f"  manifest: {man_path}", flush=True)


def chrom_to_int(c):
    m = {"X": 23, "Y": 24, "MT": 25, "M": 25}
    if c in m:
        return m[c]
    return int(c) if c.isdigit() else -1


def flush_shard(out_dir, sample, split, idx, shard, meta, manifest):
    X = np.stack(shard).astype(np.float16)
    M = np.array(meta, dtype=np.float64)
    fn = os.path.join(out_dir, f"{sample}_{split}_shard{idx:04d}.npz")
    np.savez_compressed(
        fn, X=X,
        label=M[:, 0].astype(np.int64), geno=M[:, 1].astype(np.int64),
        bp=M[:, 2:4].astype(np.float32), bin_size=M[:, 4].astype(np.int64),
        del_len=M[:, 5].astype(np.int64), chrom=M[:, 6].astype(np.int64),
        start=M[:, 7].astype(np.int64))
    n_pos = int((M[:, 0] == 1).sum())
    manifest.append((os.path.basename(fn), len(shard), n_pos))
    return idx + 1, len(shard)


if __name__ == "__main__":
    main()
