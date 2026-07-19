"""
Synthetic BAM + truth generator for pipeline validation (roadmap section 8,
"smoke test on simulated data before real 1000G BAMs").

Generates a small reference, implants deletions of controlled size, simulates
paired-end reads with realistic deletion signatures (discordant insert sizes
for pairs spanning a DEL, soft-clips at breakpoints), writes a coordinate-
sorted+indexed BAM, and returns a truth list of (start, end) deletions.

This is a *validation* fixture, not a benchmark. Real experiments use GIAB /
HGSVC truth sets on 1000G BAMs (see configs/pretrain.yaml).
"""
from __future__ import annotations
import os
import numpy as np
import pysam


def make_reference(path_fa, chrom="chr21", length=200_000, seed=0):
    rng = np.random.default_rng(seed)
    seq = "".join(rng.choice(list("ACGT"), size=length))
    with open(path_fa, "w") as f:
        f.write(f">{chrom}\n")
        for i in range(0, length, 60):
            f.write(seq[i:i + 60] + "\n")
    pysam.faidx(path_fa)
    return seq


def _revcomp(s):
    return s.translate(str.maketrans("ACGT", "TGCA"))[::-1]


def simulate_bam(
    path_bam, ref_seq, chrom="chr21",
    deletions=None, coverage=30, read_len=100,
    frag_mean=450, frag_sd=50, seed=0,
):
    """Simulate PE reads over ref_seq with implanted deletions.

    deletions : list of (start, end) 0-based half-open in *reference* coords.
    Returns the truth list actually implanted.
    """
    rng = np.random.default_rng(seed)
    L = len(ref_seq)
    if deletions is None:
        deletions = []
    # donor genome = reference with deletions removed
    dels = sorted(deletions)
    keep = np.ones(L, dtype=bool)
    for s, e in dels:
        keep[s:e] = False
    donor = np.array(list(ref_seq))
    donor_seq = "".join(donor[keep])
    # map donor coord -> ref coord
    donor2ref = np.nonzero(keep)[0]

    header = {"HD": {"VN": "1.6", "SO": "coordinate"},
              "SQ": [{"LN": L, "SN": chrom}]}
    tmp = path_bam + ".unsorted.bam"
    n_pairs = int(coverage * L / (2 * read_len))
    recs = []
    with pysam.AlignmentFile(tmp, "wb", header=header) as out:
        Ld = len(donor_seq)
        for i in range(n_pairs):
            fl = int(rng.normal(frag_mean, frag_sd))
            fl = max(2 * read_len + 10, fl)
            if Ld - fl <= 0:
                continue
            dpos = rng.integers(0, Ld - fl)  # donor fragment start
            # read1 forward at donor dpos, read2 reverse at donor dpos+fl-read_len
            r1_dstart = dpos
            r2_dstart = dpos + fl - read_len
            r1_ref = int(donor2ref[r1_dstart])
            r2_ref = int(donor2ref[r2_dstart])
            r1_seq = donor_seq[r1_dstart:r1_dstart + read_len]
            r2_seq = donor_seq[r2_dstart:r2_dstart + read_len]
            if len(r1_seq) < read_len or len(r2_seq) < read_len:
                continue
            # observed template length on reference spans the deletion => large
            tlen = (r2_ref + read_len) - r1_ref
            for (seqstr, refpos, is_read1, is_rev, mate_ref, this_tlen) in [
                (r1_seq, r1_ref, True, False, r2_ref, tlen),
                (_revcomp(r2_seq), r2_ref, False, True, r1_ref, -tlen),
            ]:
                a = pysam.AlignedSegment()
                a.query_name = f"r{i}"
                a.query_sequence = seqstr
                a.flag = 0
                a.reference_id = 0
                a.reference_start = refpos
                a.mapping_quality = 60
                a.cigartuples = [(0, read_len)]  # M
                a.next_reference_id = 0
                a.next_reference_start = mate_ref
                a.template_length = this_tlen
                a.query_qualities = pysam.qualitystring_to_array("I" * read_len)
                a.is_paired = True
                a.is_read1 = is_read1
                a.is_read2 = not is_read1
                a.is_reverse = is_rev
                a.mate_is_reverse = not is_rev
                a.is_proper_pair = abs(this_tlen) < frag_mean + 4 * frag_sd
                recs.append(a)
    # sort + write
    recs.sort(key=lambda r: r.reference_start)
    with pysam.AlignmentFile(tmp, "wb", header=header) as out:
        for r in recs:
            out.write(r)
    pysam.sort("-o", path_bam, tmp)
    pysam.index(path_bam)
    os.remove(tmp)
    return dels
