"""
Learnable alignment-tensor construction (AlignSSL-SV, roadmap section 3).

Replaces DeepSV's hand-designed 64-colour RGB pileup encoding with a
multi-channel float tensor in which every alignment signal keeps its own
channel at full fidelity. A learned 1x1-conv stem (see encoder.py) then
fuses the channels, so nothing is quantised away before learning begins.

Tensor layout per candidate locus:  X  with shape [C, R, W]
    C  channels (see CHANNELS below)
    R  read rows      (padded / subsampled to a fixed depth)
    W  window columns (reference positions spanning the candidate)

Channel map (C = 18 by default):
    0-4   base one-hot  {A, C, G, T, gap}         (per read x column)
    5     base quality  (Phred, normalised /60)
    6     mapping quality (MAPQ, normalised /60)
    7     strand        (0 = +, 1 = -)
    8     discordant-pair flag
    9     soft-clip / split-read flag
    10    insert-size z-score (clipped to +/-5, scaled)
    11    per-column read depth (normalised, broadcast down rows)
    12-16 reference base one-hot {A,C,G,T,N} (broadcast down rows)
    17    valid mask (1 where a real read base is present)

The reference and depth channels are column-level signals broadcast across
rows so a purely convolutional stem can access them per position.
"""
from __future__ import annotations
import numpy as np

# channel indices
BASE_ONEHOT = slice(0, 5)      # A C G T gap
Q_BASEQUAL = 5
Q_MAPQ = 6
Q_STRAND = 7
Q_DISC = 8
Q_CLIP = 9
Q_ISIZE = 10
Q_DEPTH = 11
REF_ONEHOT = slice(12, 17)     # A C G T N
Q_MASK = 17
N_CHANNELS = 18

_BASE_IDX = {"A": 0, "C": 1, "G": 2, "T": 3}
_REF_IDX = {"A": 0, "C": 1, "G": 2, "T": 3, "N": 4}


def _base_to_idx(ch: str) -> int:
    return _BASE_IDX.get(ch.upper(), -1)  # -1 => not A/C/G/T (e.g. N)


def build_tensor(
    reads,
    ref_seq: str,
    win_start: int,
    win_width: int,
    max_rows: int = 128,
    isize_mean: float = 450.0,
    isize_sd: float = 100.0,
    depth_norm: float = 60.0,
    bin_size: int = 1,
    rng: np.random.Generator | None = None,
):
    """Build the [C, R, W] alignment tensor for one window.

    Parameters
    ----------
    reads : iterable of pysam.AlignedSegment overlapping the window.
    ref_seq : reference bases for the full genomic span
              [win_start, win_start + win_width * bin_size).
    win_start : 0-based reference start of the window.
    win_width : W, number of output columns (fixed regardless of scale).
    max_rows : R, fixed read-row budget (subsample / pad to this).
    isize_mean, isize_sd : library insert-size stats for the z-score channel.
    depth_norm : divisor to normalise per-column depth.
    bin_size : reference bp aggregated per output column (multi-scale). The
        genomic span of the window is ``win_width * bin_size`` bp. bin_size=1
        gives per-base columns (fine scale); larger values give coarse scales
        that let one fixed-size tensor span long deletions. Per-position
        channels (base one-hot, base quality) are averaged within a bin;
        depth is summed then normalised; read-level channels (mapq, strand,
        discordant, clip, isize) are averaged over the read's bins.

    Returns
    -------
    X : float32 array [C, R, W].
    """
    if rng is None:
        rng = np.random.default_rng(0)
    W = int(win_width)
    R = int(max_rows)
    b = max(1, int(bin_size))
    span = W * b  # genomic bp covered by the window
    X = np.zeros((N_CHANNELS, R, W), dtype=np.float32)

    # ---- reference + depth are column-level; fill first ----
    # For bin_size>1, ref one-hot is the base composition within each bin.
    ref_seq = (ref_seq or "").upper()
    if b == 1:
        for c in range(min(W, len(ref_seq))):
            X[12 + _REF_IDX.get(ref_seq[c], 4), :, c] = 1.0
    else:
        refcnt = np.zeros((5, W), dtype=np.float32)
        for i in range(min(span, len(ref_seq))):
            refcnt[_REF_IDX.get(ref_seq[i], 4), i // b] += 1.0
        colsum = refcnt.sum(axis=0, keepdims=True)
        reffrac = refcnt / np.clip(colsum, 1.0, None)
        X[12:17, :, :] = reffrac[:, None, :]  # broadcast down rows
    depth = np.zeros(W, dtype=np.float32)

    # ---- collect per-read rows first, then subsample to R ----
    rows = []
    for read in reads:
        if read.is_unmapped or read.is_secondary or read.is_supplementary:
            continue
        row = _read_row(read, win_start, W, isize_mean, isize_sd, b)
        if row is not None:
            rows.append(row)
            # accumulate per-column depth (each covered bin counts once/read)
            depth[row["ucols"]] += 1.0

    # depth channel (broadcast), normalised by bin size so coarse bins stay ~[0,1]
    dnorm = np.clip(depth / (depth_norm * b), 0.0, 1.0)
    X[Q_DEPTH, :, :] = dnorm[None, :]

    if rows:
        if len(rows) > R:
            keep = rng.choice(len(rows), size=R, replace=False)
            rows = [rows[i] for i in keep]
        for r, row in enumerate(rows):
            cols = row["cols"]        # per-position bin index
            bidx = row["bidx"]
            cnt = row["cnt"]          # per-column base count for averaging
            ok = bidx >= 0
            # base one-hot accumulated per bin, then normalised to a fraction
            np.add.at(X[BASE_ONEHOT, r], (bidx[ok], cols[ok]), 1.0)
            safe = np.clip(cnt, 1.0, None)
            X[BASE_ONEHOT, r, :] /= safe[None, :]
            # base quality: accumulate then average per bin
            np.add.at(X[Q_BASEQUAL, r], cols, row["bq"])
            X[Q_BASEQUAL, r, :] /= safe
            ucols = row["ucols"]      # unique bins the read touches
            X[Q_MAPQ, r, ucols] = row["mapq"]
            X[Q_STRAND, r, ucols] = row["strand"]
            X[Q_DISC, r, ucols] = row["disc"]
            X[Q_CLIP, r, ucols] = row["clip"]
            X[Q_ISIZE, r, ucols] = row["isize_z"]
            X[Q_MASK, r, ucols] = 1.0
    return X


def _read_row(read, win_start, W, isize_mean, isize_sd, bin_size=1):
    """Extract per-column signals for one read within the window."""
    seq = read.query_sequence
    quals = read.query_qualities
    if seq is None:
        return None
    mapq = min(read.mapping_quality or 0, 60) / 60.0
    strand = 1.0 if read.is_reverse else 0.0
    # discordant: paired but not in a proper FR pair
    disc = 0.0
    if read.is_paired and not read.is_proper_pair:
        disc = 1.0
    # soft/hard clip present in cigar => breakpoint-spanning evidence
    clip = 0.0
    if read.cigartuples:
        for op, ln in read.cigartuples:
            if op in (4, 5):  # S, H
                clip = 1.0
                break
    # insert-size z-score
    tlen = read.template_length or 0
    isize_z = 0.0
    if tlen != 0 and isize_sd > 0:
        isize_z = np.clip((abs(tlen) - isize_mean) / isize_sd, -5, 5) / 5.0

    b = max(1, int(bin_size))
    span = W * b
    cols, bidx, bq = [], [], []
    for qpos, rpos in read.get_aligned_pairs(matches_only=True):
        if rpos is None or qpos is None:
            continue
        off = rpos - win_start
        if 0 <= off < span:
            cols.append(off // b)  # bin index
            bidx.append(_base_to_idx(seq[qpos]))
            q = 0 if quals is None else min(int(quals[qpos]), 60)
            bq.append(q / 60.0)
    if not cols:
        return None
    cols = np.asarray(cols, dtype=np.int64)
    # per-column count of aligned bases (for averaging within a bin)
    cnt = np.bincount(cols, minlength=W).astype(np.float32)
    ucols = np.unique(cols)
    return {
        "cols": cols,
        "ucols": ucols,
        "cnt": cnt,
        "bidx": np.asarray(bidx, dtype=np.int64),
        "bq": np.asarray(bq, dtype=np.float32),
        "mapq": mapq,
        "strand": strand,
        "disc": disc,
        "clip": clip,
        "isize_z": float(isize_z),
    }
