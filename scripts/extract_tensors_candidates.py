"""Extract alignment tensors over a PRODUCTION SV CALLER's own candidate set.

Why this benchmark exists
-------------------------
The two earlier benchmarks both synthesise their negatives.

  * ``extract_tensors.py`` draws negatives uniformly from the genome. A single
    hand-crafted scalar (centre/flank read-depth ratio) reaches AUC 0.717 on
    the resulting test set and twelve such scalars reach AUPRC 0.870, so the
    benchmark is largely solvable without learning anything about alignment
    structure.

  * ``extract_tensors_hardneg.py`` fixes that by matching the negatives'
    depth-ratio distribution to the positives'. Measured outcome
    (results/table19_shortcut_relocation.csv): the matched axis does lose its
    information (0.717 -> 0.656), and every axis that is *not* matched gains
    it -- soft-clip rate 0.630 -> 0.800, depth max-drop 0.575 -> 0.742,
    insert-size |z| 0.558 -> 0.726. Net effect, the benchmark got *easier*
    (classical control 0.870 -> 0.914). Matching a statistic relocates the
    shortcut; it does not remove it.

That failure is not a bug in the sampler, it is a property of the approach:
any sampler that matches a fixed list of statistics can be defeated by a
statistic that is not on the list, and enumerating the list is precisely the
problem the learned representation is supposed to solve. So this module stops
sampling negatives altogether.

Instead the candidate windows are the DEL calls a production short-read caller
(Manta) actually emits on this BAM, and the label is whether GIAB Tier1 says
each call is real:

    label 1  <- caller call that reciprocally overlaps a Tier1 PASS DEL
                (a true positive of the production pipeline)
    label 0  <- caller call inside Tier1 confident regions with no truth
                support  (a real false positive of the production pipeline)

Both classes are drawn from the same generating process, so there is no
sampling asymmetry for a classifier to exploit. The negatives are hard by
construction rather than by matching: they are the windows a deployed caller
gets wrong. A model that improves on this benchmark improves the thing a user
would actually run -- the filtering step after candidate generation -- which
is the task DeepSV's own evaluation framed but its uniform negatives did not
realise.

Which caller file to point at
-----------------------------
Manta writes two DEL sets, and the choice decides whether the benchmark is
measurable at all. Measured on HG002 hs37d5 (job 1570466, image digest
sha256:48d0c246..., 29 min, 16 threads):

  diploidSV.vcf.gz, PASS only   3408 candidates in range -> 2063 TP / 55 FP
  candidateSV.vcf.gz            10414 candidates in range

The PASS set is 97.4% true, so ``--min-pos-frac`` correctly refuses it: a
callset with 55 false positives cannot measure a filtering model, and reporting
an AUPRC on it would be reporting noise. That is not a defect in Manta -- it is
what a well-tuned FILTER column is for.

The benchmark therefore uses ``candidateSV.vcf.gz``, the pool BEFORE Manta
scores and filters. That is the correct pool on the merits, not just for class
balance: candidate generation is deliberately high-recall and low-precision,
and the filtering step is the learned part a user would actually want to
replace. Evaluating on the post-filter set would ask the model to improve on a
decision the caller has already made well. Candidate records carry FILTER "."
(no filter applied), which ``pass_only`` accepts.

Ambiguity handling
------------------
A caller call that overlaps a NON-PASS Tier1 record (``NoConsensusGT``,
``ClusteredCalls``, ``LongReadHomRef``, ...) or an INS is DISCARDED, not
labelled 0. GIAB makes no assertion at those loci; scoring them as false
positives would penalise the model for calls that may well be real. Calls
outside the confident regions are discarded for the same reason. Only calls
where Tier1 asserts presence (-> 1) or asserts absence (-> 0) are kept.

Window geometry, channel layout, multi-scale binning, chromosome split and
shard schema are IDENTICAL to the other two extractors, so all three arms are
directly comparable and ``alignssl.data.ShardDataset`` reads all three.
"""
from __future__ import annotations
import argparse, os, time
import numpy as np
import pysam

from alignssl.tensorize import build_tensor, N_CHANNELS
from alignssl.data import (load_truth_giab, load_bed, estimate_isize,
                           bin_for_len, interval_contains, interval_overlaps,
                           CHROM_SPLIT)


def chrom_to_int(c):
    c = c[3:] if c.startswith("chr") else c
    try:
        return int(c)
    except ValueError:
        return {"X": 23, "Y": 24, "MT": 25, "M": 25}.get(c, 0)


def load_candidate_dels(vcf_path, chroms=None, min_len=50, max_len=1_000_000,
                        pass_only=True):
    """Read a caller's VCF -> {chrom: [(start0, end0)]} of DEL candidates.

    Length bounds match the truth loader's, so a caller call is never labelled
    against a truth record the truth loader itself filtered out.
    """
    out = {}
    vcf = pysam.VariantFile(vcf_path)
    want = set(chroms) if chroms is not None else None
    n_read = n_kept = 0
    for rec in vcf.fetch():
        n_read += 1
        c = rec.chrom[3:] if rec.chrom.startswith("chr") else rec.chrom
        if want is not None and c not in want:
            continue
        if rec.info.get("SVTYPE") != "DEL":
            continue
        if pass_only and (set(rec.filter.keys()) - {"PASS"}):
            continue
        start0, end0 = rec.start, rec.stop
        svlen = rec.info.get("SVLEN")
        if svlen is not None:
            svlen = abs(int(svlen[0] if isinstance(svlen, tuple) else svlen))
        if end0 <= start0 and svlen:
            end0 = start0 + svlen
        ln = end0 - start0
        if ln < min_len or ln > max_len:
            continue
        out.setdefault(c, []).append((start0, end0))
        n_kept += 1
    for c in out:
        out[c].sort()
    return out, n_read, n_kept


def reciprocal_overlap(a0, a1, b0, b1):
    """Fraction of the LARGER interval that the two share (Truvari-style).

    Using the larger interval as denominator is the strict choice: a 200 bp
    call nested inside a 5 kb truth deletion scores 0.04, not 1.0, so a caller
    is not credited with resolving an event it only clipped the edge of.
    """
    inter = min(a1, b1) - max(a0, b0)
    if inter <= 0:
        return 0.0
    return inter / max(a1 - a0, b1 - b0)


def label_candidates(cands, truth, exclude, confident, min_reciprocal=0.5,
                     slop=0):
    """Label caller calls against GIAB Tier1. Returns (items, stats).

    items entries are ``(chrom, cand_start, cand_end, label, geno)``; geno is
    the truth genotype for matched calls and 0 for false positives.
    """
    items = []
    st = dict(n_cand=0, n_tp=0, n_fp=0, drop_unconfident=0, drop_ambiguous=0,
              drop_below_reciprocal=0)
    for chrom, calls in sorted(cands.items()):
        tr = truth.get(chrom, [])
        tarr = (np.asarray([(s, e) for (s, e, _g) in tr], dtype=np.int64)
                if tr else np.zeros((0, 2), dtype=np.int64))
        tgeno = [g for (_s, _e, g) in tr]
        exc = exclude.get(chrom)
        conf = confident.get(chrom)
        for (cs, ce) in calls:
            st["n_cand"] += 1
            # Tier1 must make a claim here at all.
            if conf is None or not interval_contains(conf, cs - slop,
                                                     ce + slop):
                st["drop_unconfident"] += 1
                continue
            # Does any truth DEL match reciprocally?
            best, best_i = 0.0, -1
            if tarr.shape[0]:
                near = np.where((tarr[:, 0] < ce + max_span_slack(ce - cs)) &
                                (tarr[:, 1] > cs - max_span_slack(ce - cs)))[0]
                for i in near:
                    r = reciprocal_overlap(cs, ce, int(tarr[i, 0]),
                                           int(tarr[i, 1]))
                    if r > best:
                        best, best_i = r, int(i)
            if best >= min_reciprocal:
                items.append((chrom, cs, ce, 1, tgeno[best_i]))
                st["n_tp"] += 1
                continue
            # No truth match. Only call it a false positive if Tier1 asserts
            # ABSENCE -- i.e. the call touches no record of any type/filter.
            if exc is not None and interval_overlaps(exc, cs, ce):
                st["drop_ambiguous"] += 1
                continue
            if best > 0:
                # Overlapped a truth DEL but below the reciprocal threshold:
                # partially right, so neither a clean TP nor a clean FP.
                st["drop_below_reciprocal"] += 1
                continue
            items.append((chrom, cs, ce, 0, 0))
            st["n_fp"] += 1
    return items, st


def max_span_slack(ln):
    """Search radius for nearby truth records when matching a call."""
    return max(1000, 2 * ln)


def flush_shard(out_dir, sample, split, shard_idx, shard, meta, manifest):
    X = np.stack(shard).astype(np.float16)
    M = np.asarray(meta, dtype=np.float64)
    path = os.path.join(out_dir, f"{sample}_{split}_shard{shard_idx:04d}.npz")
    # Schema must match scripts/extract_tensors.py EXACTLY -- alignssl.data
    # .ShardDataset is shared by all three arms and reads "X" and a
    # two-column "bp". tests/test_shard_schema.py enforces this statically.
    np.savez_compressed(
        path, X=X,
        label=M[:, 0].astype(np.int64), geno=M[:, 1].astype(np.int64),
        bp=M[:, 2:4].astype(np.float32), bin_size=M[:, 4].astype(np.int64),
        del_len=M[:, 5].astype(np.int64), chrom=M[:, 6].astype(np.int64),
        start=M[:, 7].astype(np.int64))
    manifest.append((os.path.basename(path), len(shard), int(M[:, 0].sum())))
    return shard_idx + 1, len(shard)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bam", required=True)
    ap.add_argument("--bai", default=None)
    ap.add_argument("--fasta", required=True)
    ap.add_argument("--vcf", required=True,
                    help="GIAB Tier1 truth VCF")
    ap.add_argument("--candidate-vcf", required=True,
                    help="production caller output (e.g. Manta diploidSV)")
    ap.add_argument("--confident-bed", required=True,
                    help="GIAB Tier1 confident-region BED")
    ap.add_argument("--sample", required=True)
    ap.add_argument("--split", choices=["train", "test", "all"], default="all")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--win-width", type=int, default=256)
    ap.add_argument("--max-rows", type=int, default=64)
    ap.add_argument("--shard-size", type=int, default=1024)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--no-multiscale", action="store_true")
    ap.add_argument("--min-reciprocal", type=float, default=0.5,
                    help="reciprocal-overlap threshold for calling a caller "
                         "call a true positive")
    ap.add_argument("--min-pos-frac", type=float, default=0.05,
                    help="fail if the labelled set is more degenerate than "
                         "this in either direction; a benchmark with almost "
                         "no FPs cannot measure filtering")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    chroms = (CHROM_SPLIT["train"] + CHROM_SPLIT["test"]
              if args.split == "all" else CHROM_SPLIT[args.split])
    print(f"[{time.strftime('%H:%M:%S')}] CANDIDATE extraction {args.sample} "
          f"split={args.split}", flush=True)

    truth, exclude = load_truth_giab(args.vcf, chroms=chroms)
    confident = load_bed(args.confident_bed, chroms=chroms)
    cands, n_read, n_kept = load_candidate_dels(args.candidate_vcf,
                                                chroms=chroms)
    print(f"  truth DELs: {sum(len(v) for v in truth.values())}; "
          f"confident intervals: {sum(len(v) for v in confident.values())}; "
          f"exclusion zones: {sum(len(v) for v in exclude.values())}",
          flush=True)
    print(f"  caller records read {n_read}, DEL/PASS/len-in-range {n_kept}",
          flush=True)

    items, st = label_candidates(cands, truth, exclude, confident,
                                 min_reciprocal=args.min_reciprocal)
    print("  labelling: " + " ".join(f"{k}={v}" for k, v in st.items()),
          flush=True)
    if not items:
        raise SystemExit("no labelled candidates -- check coordinate systems "
                         "(caller VCF vs BAM vs truth all on same build?)")
    pf = st["n_tp"] / len(items)
    if pf < args.min_pos_frac or pf > 1 - args.min_pos_frac:
        raise SystemExit(
            f"degenerate benchmark: positive fraction {pf:.4f} outside "
            f"[{args.min_pos_frac}, {1-args.min_pos_frac}]. A caller callset "
            f"with almost no false positives cannot measure a filtering "
            f"model; check the reciprocal threshold and the confident-region "
            f"intersection before proceeding.")

    fa = pysam.FastaFile(args.fasta)
    bam = pysam.AlignmentFile(args.bam, "rb", index_filename=args.bai)

    rng = np.random.default_rng(args.seed + 1)
    items = [items[i] for i in rng.permutation(len(items))]
    if args.limit > 0:
        items = items[:args.limit]
    print(f"  items: {len(items)} ({st['n_tp']} pos / {st['n_fp']} neg, "
          f"pos_frac={pf:.4f})", flush=True)

    isize = {}

    def get_isize(chrom):
        if chrom not in isize:
            isize[chrom] = estimate_isize(args.bam, chrom, bai=args.bai)
        return isize[chrom]

    shard, meta, manifest = [], [], []
    shard_idx = 0
    t0 = time.time()
    for k, (chrom, cs, ce, label, geno) in enumerate(items):
        ln = ce - cs
        # Window geometry is chosen from the CANDIDATE's length, not the
        # truth's: at inference time the truth length is unknown, so using it
        # here would leak. Positives and negatives are therefore framed
        # identically, by the caller's own coordinates.
        bs = bin_for_len(ln, args.win_width) if not args.no_multiscale else 1
        span = args.win_width * bs
        clen = fa.get_reference_length(chrom)
        mid = (cs + ce) // 2
        s = max(0, min(mid - span // 2, clen - span))
        bp0, bp1 = (cs - s) / span, (ce - s) / span
        reads = list(bam.fetch(chrom, max(0, s), s + span))
        ref = fa.fetch(chrom, s, s + span)
        im, isd = get_isize(chrom)
        X = build_tensor(reads, ref, s, args.win_width, max_rows=args.max_rows,
                         isize_mean=im, isize_sd=isd, bin_size=bs)
        shard.append(X.astype(np.float16))
        meta.append((label, geno, bp0, bp1, bs, ln, int(chrom_to_int(chrom)),
                     s))
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
          f"{sum(r[1] for r in manifest)} tensors -> {args.out_dir}",
          flush=True)


if __name__ == "__main__":
    main()
