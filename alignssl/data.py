"""
Candidate-locus extraction + PyTorch datasets (roadmap sections 2-3, 8).

Two dataset flavours:
    PretrainDataset  : yields alignment tensors at genome-tiled windows for
                       self-supervised training (no labels needed).
    FinetuneDataset  : yields (tensor, label, geno, bp) using a truth set;
                       negatives sampled from label-free windows.

Windows are multi-scale: each item carries a `bin_size` so one fixed-width
tensor can represent a short deletion at base resolution (bin_size=1) or a
long deletion at coarse resolution (bin_size>1, genomic span =
win_width * bin_size). This serves the PULSE-SV amendment-1 length-stratified
multi-scale ablation and lets long DELs be seen at a matching scale.

Real-data helpers:
    load_truth_dels    : per-sample non-ref DELETION loci from a genotyped
                         SV VCF (pysam), returned per chromosome.
    CHROM_SPLIT        : DeepSV convention train chr1-11 / test chr12-22.
"""
from __future__ import annotations
import os
import numpy as np
import pysam
import torch
from torch.utils.data import Dataset

from .tensorize import build_tensor, N_CHANNELS

# DeepSV convention: train on chr1-11, held-out test on chr12-22.
TRAIN_CHROMS = [str(i) for i in range(1, 12)]
TEST_CHROMS = [str(i) for i in range(12, 23)]
CHROM_SPLIT = {"train": TRAIN_CHROMS, "test": TEST_CHROMS}


def load_truth_dels(vcf_path, sample, chroms=None, min_len=50, max_len=1_000_000):
    """Per-sample non-reference DELETIONs from a genotyped SV VCF.

    Returns dict: chrom -> list of (start0, end0, geno) with 0-based
    half-open coords and geno in {1: het, 2: hom-alt}. Only records whose
    SVTYPE is DEL and whose genotype for `sample` carries an ALT allele are
    kept. END is taken from the INFO/END field; SVLEN used as fallback.
    """
    out = {}
    vcf = pysam.VariantFile(vcf_path)
    if sample not in list(vcf.header.samples):
        raise ValueError(f"{sample} not in VCF samples")
    want = set(chroms) if chroms is not None else None
    for rec in vcf.fetch():
        if want is not None and rec.chrom not in want:
            continue
        svtype = rec.info.get("SVTYPE")
        if svtype != "DEL":
            continue
        start0 = rec.start  # pysam: 0-based
        end0 = rec.stop     # pysam: 0-based half-open (uses INFO/END)
        if end0 <= start0:
            svlen = rec.info.get("SVLEN")
            if svlen is not None:
                svlen = svlen[0] if isinstance(svlen, tuple) else svlen
                end0 = start0 + abs(int(svlen))
        ln = end0 - start0
        if ln < min_len or ln > max_len:
            continue
        gt = rec.samples[sample].get("GT")
        if gt is None:
            continue
        alt = sum(1 for a in gt if a is not None and a > 0)
        if alt == 0:
            continue
        geno = 2 if alt >= 2 else 1  # hom-alt vs het
        out.setdefault(rec.chrom, []).append((start0, end0, geno))
    vcf.close()
    for c in out:
        out[c].sort()
    return out


def estimate_isize(bam_path, chrom, n=2000, bai=None):
    """Estimate insert-size mean/sd from proper pairs."""
    vals = []
    with pysam.AlignmentFile(bam_path, "rb", index_filename=bai) as bam:
        for r in bam.fetch(chrom):
            if r.is_proper_pair and not r.is_reverse and r.template_length > 0:
                vals.append(r.template_length)
            if len(vals) >= n:
                break
    if not vals:
        return 450.0, 100.0
    v = np.asarray(vals)
    return float(v.mean()), float(v.std() + 1e-6)


def bin_for_len(ln, win_width=256):
    """Pick the smallest bin_size (power of 2) so win_width*bin covers `ln`.

    Ensures a deletion of length `ln` fits inside the tensor's genomic span
    with margin (~half the window on each side).
    """
    target = ln * 2  # want ~2x the event length as span
    b = 1
    while win_width * b < target and b < 64:
        b *= 2
    return b


def tile_windows(chrom_len, win_width, stride, bin_size=1):
    span = win_width * bin_size
    starts = list(range(0, max(1, chrom_len - span), stride))
    return [(s, win_width, bin_size) for s in starts]


def _fetch_reads(bam, chrom, start, span):
    return list(bam.fetch(chrom, max(0, start), start + span))


class PretrainDataset(Dataset):
    """Unlabelled genome-tiled windows for SSL, over one or more chromosomes.

    `chroms` may be a single chrom string or a list. Windows are tiled at
    `win_width`/`stride` and (optionally) at several `bin_sizes` so the SSL
    encoder sees both fine and coarse scales.
    """

    def __init__(self, bam_path, fasta_path, chroms, win_width=256, stride=128,
                 max_rows=128, bin_sizes=(1,), limit=None):
        self.bam_path = bam_path
        self.fa = pysam.FastaFile(fasta_path)
        self.chroms = [chroms] if isinstance(chroms, str) else list(chroms)
        self.win_width = win_width
        self.max_rows = max_rows
        self._bam = None
        self.isize_mean, self.isize_sd = estimate_isize(bam_path, self.chroms[0])
        self.windows = []  # (chrom, start, width, bin_size)
        for c in self.chroms:
            clen = self.fa.get_reference_length(c)
            for b in bin_sizes:
                for (s, w, bs) in tile_windows(clen, win_width, stride, b):
                    self.windows.append((c, s, w, bs))
        if limit:
            rng = np.random.default_rng(0)
            idx = rng.permutation(len(self.windows))[:limit]
            self.windows = [self.windows[i] for i in sorted(idx)]

    def _bamh(self):
        if self._bam is None:
            self._bam = pysam.AlignmentFile(self.bam_path, "rb")
        return self._bam

    def __len__(self):
        return len(self.windows)

    def __getitem__(self, i):
        c, s, w, bs = self.windows[i]
        span = w * bs
        reads = _fetch_reads(self._bamh(), c, s, span)
        ref = self.fa.fetch(c, s, s + span)
        X = build_tensor(reads, ref, s, w, max_rows=self.max_rows,
                         isize_mean=self.isize_mean, isize_sd=self.isize_sd,
                         bin_size=bs)
        return torch.from_numpy(X)


class FinetuneDataset(Dataset):
    """Labelled windows over one or more chromosomes.

    Positives are centred on truth deletions; each positive picks a bin_size
    (via bin_for_len) so the deletion fits the tensor span. Negatives are
    E3-style: windows with no truth overlap, at the same bin_sizes as the
    positives so the classifier can't cheat on scale.

    `truth_by_chrom` : dict chrom -> list of (start0, end0, geno).
    """

    def __init__(self, bam_path, fasta_path, truth_by_chrom,
                 win_width=256, max_rows=128, n_neg_per_pos=3,
                 multiscale=True, seed=0):
        self.bam_path = bam_path
        self.fa = pysam.FastaFile(fasta_path)
        self.win_width = win_width
        self.max_rows = max_rows
        self._bam = None
        self.multiscale = multiscale
        rng = np.random.default_rng(seed)
        # items: (chrom, start, width, bin_size, label, geno, bp0, bp1, del_len)
        self.items = []
        self._isize = {}
        for chrom, dels in truth_by_chrom.items():
            if not dels:
                continue
            self._isize[chrom] = estimate_isize(bam_path, chrom)
            clen = self.fa.get_reference_length(chrom)
            bins_used = set()
            pos_spans = []  # (start, span) to avoid when sampling negatives
            for (ds, de, geno) in dels:
                ln = de - ds
                bs = bin_for_len(ln, win_width) if multiscale else 1
                bins_used.add(bs)
                span = win_width * bs
                mid = (ds + de) // 2
                s = max(0, min(mid - span // 2, clen - span))
                bp0 = (ds - s) / span   # breakpoint as fraction of genomic span
                bp1 = (de - s) / span
                self.items.append((chrom, s, win_width, bs, 1, geno, bp0, bp1, ln))
                pos_spans.append((s, span))
            bins_used = sorted(bins_used) or [1]
            n_neg = len(dels) * n_neg_per_pos
            for _ in range(n_neg):
                bs = int(rng.choice(bins_used))
                span = win_width * bs
                for _try in range(30):
                    s = int(rng.integers(0, max(1, clen - span)))
                    if not any(s < de and s + span > ds for ds, de, _ in dels) and \
                       not any(abs(s - ps) < span for ps, _ in pos_spans):
                        self.items.append(
                            (chrom, s, win_width, bs, 0, 0, np.nan, np.nan, 0))
                        break

    def _bamh(self):
        if self._bam is None:
            self._bam = pysam.AlignmentFile(self.bam_path, "rb")
        return self._bam

    def __len__(self):
        return len(self.items)

    def __getitem__(self, i):
        chrom, s, w, bs, label, geno, bp0, bp1, ln = self.items[i]
        span = w * bs
        reads = _fetch_reads(self._bamh(), chrom, s, span)
        ref = self.fa.fetch(chrom, s, s + span)
        im, isd = self._isize.get(chrom, (450.0, 100.0))
        X = build_tensor(reads, ref, s, w, max_rows=self.max_rows,
                         isize_mean=im, isize_sd=isd, bin_size=bs)
        return {
            "x": torch.from_numpy(X),
            "label": torch.tensor(label, dtype=torch.long),
            "geno": torch.tensor(geno, dtype=torch.long),
            "bp": torch.tensor([bp0, bp1], dtype=torch.float32),
            "bin_size": torch.tensor(bs, dtype=torch.long),
            "del_len": torch.tensor(ln, dtype=torch.long),
        }


# ---------------- shard-based datasets (precomputed .npz) ----------------

def _chrom_ints(split):
    """Integer chrom ids for a split (matches chrom_to_int in extraction)."""
    names = CHROM_SPLIT[split] if split in CHROM_SPLIT else \
        CHROM_SPLIT["train"] + CHROM_SPLIT["test"]
    return set(int(c) for c in names)


class ShardDataset(Dataset):
    """Read precomputed .npz shards (from scripts/extract_tensors.py).

    Filters by chromosome so the SAME shard directory serves the train
    (chr1-11) and test (chr12-22) splits without re-extraction. Loads
    lazily per-shard and caches the most recent shard in memory.

    labeled=False -> returns only the tensor (for SSL pretraining).
    labeled=True  -> returns dict with label/geno/bp/bin_size/del_len.
    """

    def __init__(self, shard_dir, split="all", labeled=True, glob_pat="*.npz"):
        import glob as _glob
        self.files = sorted(_glob.glob(os.path.join(shard_dir, glob_pat)))
        if not self.files:
            raise FileNotFoundError(f"no shards in {shard_dir}/{glob_pat}")
        self.labeled = labeled
        want = _chrom_ints(split)
        # build a flat index of (file_idx, row_idx) keeping only wanted chroms
        self.index = []
        self._meta_cache = {}
        for fi, f in enumerate(self.files):
            with np.load(f) as d:
                chrom = d["chrom"]
            keep = [j for j in range(len(chrom)) if int(chrom[j]) in want]
            for j in keep:
                self.index.append((fi, j))
        self._cur_fi = None
        self._cur = None

    def _load(self, fi):
        if self._cur_fi != fi:
            self._cur = dict(np.load(self.files[fi]))
            self._cur_fi = fi
        return self._cur

    def __len__(self):
        return len(self.index)

    def __getitem__(self, i):
        fi, j = self.index[i]
        d = self._load(fi)
        X = torch.from_numpy(d["X"][j].astype(np.float32))
        if not self.labeled:
            return X
        return {
            "x": X,
            "label": torch.tensor(int(d["label"][j]), dtype=torch.long),
            "geno": torch.tensor(int(d["geno"][j]), dtype=torch.long),
            "bp": torch.from_numpy(d["bp"][j].astype(np.float32)),
            "bin_size": torch.tensor(int(d["bin_size"][j]), dtype=torch.long),
            "del_len": torch.tensor(int(d["del_len"][j]), dtype=torch.long),
        }


class MemmapDataset(Dataset):
    """Random-access dataset over a flat float16 memmap built by
    scripts/build_memmap.py. Reads straight from the OS page cache, so it is
    safe with num_workers=0 (no CUDA-fork deadlock) and cheap under shuffle.

    labeled=False -> returns only the tensor X (SSL pretraining).
    labeled=True  -> requires geno/bp fields; for the labeled tensors dir use
                     ShardDataset instead (this class carries only chrom/bin/label).
    """

    def __init__(self, prefix, split="all", labeled=False):
        meta = np.load(prefix + ".meta.npz")
        self.shape = tuple(int(x) for x in meta["shape"])
        self.X = np.load(prefix + ".f16", mmap_mode="r")
        assert self.X.shape == self.shape, (self.X.shape, self.shape)
        chrom = meta["chrom"]
        want = _chrom_ints(split)
        self.index = np.array(
            [i for i in range(self.shape[0]) if int(chrom[i]) in want],
            dtype=np.int64)
        self.labeled = labeled
        self.label = meta["label"]
        self.bin_size = meta["bin_size"]

    def __len__(self):
        return len(self.index)

    def __getitem__(self, i):
        j = int(self.index[i])
        X = torch.from_numpy(np.ascontiguousarray(self.X[j]).astype(np.float32))
        if not self.labeled:
            return X
        return {
            "x": X,
            "label": torch.tensor(int(self.label[j]), dtype=torch.long),
            "bin_size": torch.tensor(int(self.bin_size[j]), dtype=torch.long),
        }
