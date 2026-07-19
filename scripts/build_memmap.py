#!/usr/bin/env python3
"""Consolidate compressed .npz shards into one flat float16 memmap + metadata.

Random-access training over many 1.2 GB compressed shards thrashes any
per-shard cache and forces repeated decompression. A single raw memmap gives
O(1) random reads straight from the OS page cache, so the DataLoader needs no
worker processes (avoids the CUDA-fork deadlock) and no shuffle reload cost.

Writes:
  <out>.f16   raw float16, shape (N, C, R, W) row-major
  <out>.meta.npz   chrom,bin_size,start,label,shape  (small)
"""
from __future__ import annotations
import argparse, glob, os, time
import numpy as np


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard-dir", required=True)
    ap.add_argument("--glob", default="*.npz")
    ap.add_argument("--out", required=True, help="output prefix (writes .f16 + .meta.npz)")
    args = ap.parse_args()

    files = sorted(glob.glob(os.path.join(args.shard_dir, args.glob)))
    if not files:
        raise FileNotFoundError(f"no shards in {args.shard_dir}/{args.glob}")

    # first pass: total N and per-window shape
    n_total = 0
    shp = None
    for f in files:
        with np.load(f) as d:
            n_total += d["X"].shape[0]
            if shp is None:
                shp = d["X"].shape[1:]
    print(f"shards={len(files)} N={n_total} per_window={shp}", flush=True)

    mm = np.lib.format.open_memmap(
        args.out + ".f16", mode="w+", dtype=np.float16,
        shape=(n_total,) + tuple(shp))
    chrom = np.empty(n_total, np.int64)
    binsz = np.empty(n_total, np.int64)
    start = np.empty(n_total, np.int64)
    label = np.empty(n_total, np.int64)

    off = 0
    t0 = time.time()
    for fi, f in enumerate(files):
        with np.load(f) as d:
            n = d["X"].shape[0]
            mm[off:off + n] = d["X"].astype(np.float16)
            chrom[off:off + n] = d["chrom"]
            binsz[off:off + n] = d["bin_size"]
            start[off:off + n] = d["start"]
            label[off:off + n] = d["label"] if "label" in d else -1
        off += n
        if fi % 5 == 0:
            print(f"  {fi+1}/{len(files)} off={off} {time.time()-t0:.0f}s", flush=True)
    mm.flush()
    np.savez(args.out + ".meta.npz", chrom=chrom, bin_size=binsz,
             start=start, label=label, shape=np.array((n_total,) + tuple(shp)))
    print(f"DONE memmap -> {args.out}.f16  ({off} windows, {time.time()-t0:.0f}s)", flush=True)


if __name__ == "__main__":
    main()
