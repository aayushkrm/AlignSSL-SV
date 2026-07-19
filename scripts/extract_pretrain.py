#!/usr/bin/env python3
"""Sample UNLABELED alignment-tensor windows for SSL pretraining.

Draws random windows across the requested chromosomes at mixed bin_sizes
(so the encoder sees multiple genomic scales), builds 18-channel tensors,
and shards them. No truth set required — this is the abundant pretraining
signal that the labeled fine-tuning set is too small to provide.
"""
from __future__ import annotations
import argparse, os, time
import numpy as np
import pysam

from alignssl.tensorize import build_tensor
from alignssl.data import estimate_isize, CHROM_SPLIT

# skip low-mappability telomere/centromere-ish edges crudely by margin
EDGE_MARGIN = 100_000


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bam", required=True)
    ap.add_argument("--bai", default=None)
    ap.add_argument("--fasta", required=True)
    ap.add_argument("--sample", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--split", choices=["train", "test", "all"], default="train")
    ap.add_argument("--n-windows", type=int, default=100_000)
    ap.add_argument("--win-width", type=int, default=256)
    ap.add_argument("--max-rows", type=int, default=64)
    ap.add_argument("--bin-sizes", default="1,2,4,8,16,32,64")
    ap.add_argument("--bin-weights", default="0.35,0.25,0.15,0.10,0.08,0.05,0.02",
                    help="sampling weights per bin_size; small-biased to match the "
                         "real deletion-length distribution (most DELs are short) "
                         "and to avoid over-sampling expensive large-span windows")
    ap.add_argument("--min-reads", type=int, default=5,
                    help="drop windows with fewer real reads (gaps/N regions)")
    ap.add_argument("--shard-size", type=int, default=2048)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    if args.split == "all":
        chroms = CHROM_SPLIT["train"] + CHROM_SPLIT["test"]
    else:
        chroms = CHROM_SPLIT[args.split]
    bin_sizes = [int(b) for b in args.bin_sizes.split(",")]
    bin_w = np.array([float(w) for w in args.bin_weights.split(",")], dtype=float)
    assert len(bin_w) == len(bin_sizes), "bin-weights must match bin-sizes"
    bin_w /= bin_w.sum()
    rng = np.random.default_rng(args.seed)

    fa = pysam.FastaFile(args.fasta)
    bam = pysam.AlignmentFile(args.bam, "rb", index_filename=args.bai)
    # weight chroms by usable length so sampling is ~uniform over the genome
    clens = {}
    for c in chroms:
        try:
            clens[c] = fa.get_reference_length(c)
        except Exception:
            pass
    chroms = [c for c in chroms if clens.get(c, 0) > 3 * EDGE_MARGIN]
    weights = np.array([clens[c] for c in chroms], dtype=float)
    weights /= weights.sum()

    isize = {}

    def get_isize(chrom):
        if chrom not in isize:
            isize[chrom] = estimate_isize(args.bam, chrom, bai=args.bai)
        return isize[chrom]

    W = args.win_width
    shard, meta = [], []
    shard_idx, kept, tried = 0, 0, 0
    manifest = []
    t0 = time.time()
    while kept < args.n_windows:
        tried += 1
        chrom = chroms[rng.choice(len(chroms), p=weights)]
        bs = int(rng.choice(bin_sizes, p=bin_w))
        span = W * bs
        clen = clens[chrom]
        s = int(rng.integers(EDGE_MARGIN, max(EDGE_MARGIN + 1, clen - span - EDGE_MARGIN)))
        reads = list(bam.fetch(chrom, s, s + span))
        if len(reads) < args.min_reads:
            continue
        ref = fa.fetch(chrom, s, s + span)
        im, isd = get_isize(chrom)
        X = build_tensor(reads, ref, s, W, max_rows=args.max_rows,
                         isize_mean=im, isize_sd=isd, bin_size=bs)
        shard.append(X.astype(np.float16))
        meta.append((bs, chrom_to_int(chrom), s))
        kept += 1
        if len(shard) >= args.shard_size:
            shard_idx = flush(args.out_dir, args.sample, args.split,
                              shard_idx, shard, meta, manifest)
            shard, meta = [], []
        if kept % 2000 == 0:
            dt = time.time() - t0
            print(f"  [{kept}/{args.n_windows}] {dt:.0f}s "
                  f"({kept/dt:.1f}/s, {tried-kept} skipped)", flush=True)
    if shard:
        shard_idx = flush(args.out_dir, args.sample, args.split,
                          shard_idx, shard, meta, manifest)

    man = os.path.join(args.out_dir, f"pretrain_manifest_{args.sample}_{args.split}.tsv")
    with open(man, "w") as f:
        f.write("shard\tn\n")
        for row in manifest:
            f.write(f"{row[0]}\t{row[1]}\n")
    total = sum(r[1] for r in manifest)
    print(f"[{time.strftime('%H:%M:%S')}] DONE: {total} unlabeled windows "
          f"in {len(manifest)} shards -> {args.out_dir}", flush=True)


def chrom_to_int(c):
    m = {"X": 23, "Y": 24, "MT": 25, "M": 25}
    if c in m:
        return m[c]
    return int(c) if c.isdigit() else -1


def flush(out_dir, sample, split, idx, shard, meta, manifest):
    X = np.stack(shard).astype(np.float16)
    M = np.array(meta, dtype=np.int64)
    fn = os.path.join(out_dir, f"pretrain_{sample}_{split}_shard{idx:04d}.npz")
    # store dummy label/chrom fields so ShardDataset can filter by chrom
    np.savez_compressed(fn, X=X, bin_size=M[:, 0], chrom=M[:, 1], start=M[:, 2],
                        label=np.full(len(shard), -1, dtype=np.int64))
    manifest.append((os.path.basename(fn), len(shard)))
    return idx + 1


if __name__ == "__main__":
    main()
