"""Guards on the GIAB truth-set path.

The GIAB Tier1 call set differs from the 1000G genotyped VCF in ways that
silently corrupt a benchmark if mishandled:

  * ~25k of its 74k records are non-PASS (unresolved), and treating the
    territory they occupy as negative credits a model for agreeing with a
    label the truth set does not assert;
  * it declares a confident BED outside which it makes no claim at all;
  * its insertions have no reference span but disturb local alignment just
    as deletions do, so they must be excluded from negative sampling.

Each test below pins one of those rules.  If a refactor drops one, the
benchmark keeps running and quietly reports a better number than it earned.
"""
import numpy as np
import pytest

from alignssl.data import (load_bed, interval_contains, interval_overlaps,
                           load_truth_giab)


# ---------------------------------------------------------------- intervals

def test_load_bed_merges_and_sorts(tmp_path):
    p = tmp_path / "c.bed"
    # deliberately unsorted, with an overlap (100-200 / 150-250) and an
    # abutting pair (300-400 / 400-500) -- both must merge.
    p.write_text("1\t300\t400\n1\t100\t200\n1\t150\t250\n1\t400\t500\n"
                 "chr2\t10\t20\n")
    bed = load_bed(str(p))
    assert set(bed) == {"1", "2"}, "chr-prefix not normalised"
    assert bed["1"].tolist() == [[100, 250], [300, 500]]


def test_load_bed_respects_chrom_filter(tmp_path):
    p = tmp_path / "c.bed"
    p.write_text("1\t0\t10\n2\t0\t10\n3\t0\t10\n")
    assert set(load_bed(str(p), chroms=["1", "3"])) == {"1", "3"}


@pytest.mark.parametrize("s,e,want", [
    (100, 200, True),    # exactly an interval
    (120, 180, True),    # strictly inside
    (90, 150, False),    # straddles the left edge
    (180, 260, False),   # straddles the right edge
    (250, 300, False),   # in the gap
    (100, 251, False),   # spans two intervals -- the gap is not confident
])
def test_interval_contains(s, e, want):
    arr = np.array([[100, 250], [300, 500]], dtype=np.int64)
    assert interval_contains(arr, s, e) is want or \
           bool(interval_contains(arr, s, e)) == want


@pytest.mark.parametrize("s,e,want", [
    (0, 50, False),
    (0, 101, True),
    (150, 160, True),
    (250, 300, False),   # half-open: [250,300) touches neither
    (249, 260, True),
    (299, 310, True),
])
def test_interval_overlaps(s, e, want):
    arr = np.array([[100, 250], [300, 500]], dtype=np.int64)
    assert bool(interval_overlaps(arr, s, e)) == want


def test_interval_helpers_on_empty():
    for fn in (interval_contains, interval_overlaps):
        assert not fn(None, 0, 10)
        assert not fn(np.zeros((0, 2), dtype=np.int64), 0, 10)


# ------------------------------------------------------------- GIAB parsing

def _write_vcf(path):
    """Minimal Tier1-shaped VCF exercising every rule."""
    import pysam
    hdr = pysam.VariantHeader()
    hdr.add_line('##contig=<ID=1,length=1000000>')
    hdr.add_line('##INFO=<ID=SVTYPE,Number=1,Type=String,Description="t">')
    hdr.add_line('##INFO=<ID=SVLEN,Number=1,Type=Integer,Description="l">')
    hdr.add_line('##INFO=<ID=END,Number=1,Type=Integer,Description="e">')
    hdr.add_line('##FILTER=<ID=NoConsensusGT,Description="x">')
    hdr.add_line('##FILTER=<ID=lt50bp,Description="x">')
    hdr.add_line('##FORMAT=<ID=GT,Number=1,Type=String,Description="g">')
    hdr.add_sample("HG002")
    recs = [
        # (pos1, ref_end, svtype, svlen, filters, gt)   -- pos1 is 1-based
        (1000, 1300, "DEL", -300, [],                (0, 1)),  # keep: het
        (5000, 5600, "DEL", -600, [],                (1, 1)),  # keep: hom
        (9000, 9400, "DEL", -400, ["NoConsensusGT"], (0, 1)),  # drop: filtered
        (11000, 11020, "DEL", -20, ["lt50bp"],       (0, 1)),  # drop: filtered
        (13000, 13300, "DEL", -300, [],              (0, 0)),  # drop: hom-ref
        (17000, 17001, "INS", 900, [],               (0, 1)),  # drop: not DEL
        (21000, 21060, "DEL", -60, [],               (None, None)),  # drop
    ]
    with pysam.VariantFile(str(path), "w", header=hdr) as out:
        for pos1, end, svt, svlen, filters, gt in recs:
            r = out.new_record(contig="1", start=pos1 - 1, stop=end,
                               alleles=("N", "<%s>" % svt))
            r.info["SVTYPE"] = svt
            r.info["SVLEN"] = svlen
            for f in filters:
                r.filter.add(f)
            if not filters:
                r.filter.add("PASS")
            r.samples["HG002"]["GT"] = gt
            out.write(r)
    pysam.tabix_index(str(path), preset="vcf", force=True)
    return str(path) + ".gz"


def test_giab_keeps_only_pass_nonref_dels(tmp_path):
    vcf = _write_vcf(tmp_path / "t.vcf")
    truth, excl = load_truth_giab(vcf)
    got = [(s, e, g) for (s, e, g) in truth["1"]]
    assert got == [(999, 1300, 1), (4999, 5600, 2)], got


def test_giab_excludes_every_record_not_just_positives(tmp_path):
    vcf = _write_vcf(tmp_path / "t.vcf")
    _, excl = load_truth_giab(vcf)
    arr = excl["1"]
    assert len(arr) == 7, f"expected all 7 records excluded, got {len(arr)}"
    # the filtered deletion is excluded even though it is not a positive
    assert interval_overlaps(arr, 9100, 9200)
    # the hom-ref deletion likewise
    assert interval_overlaps(arr, 13100, 13200)


def test_giab_insertion_gets_svlen_wide_exclusion(tmp_path):
    """An INS has ref span 1 but perturbs ~SVLEN bp of local alignment."""
    vcf = _write_vcf(tmp_path / "t.vcf")
    _, excl = load_truth_giab(vcf)
    arr = excl["1"]
    assert interval_overlaps(arr, 17500, 17600), \
        "insertion footprint collapsed to its 1bp reference span"
    assert not interval_overlaps(arr, 18500, 18600)


def test_giab_chrom_filter(tmp_path):
    vcf = _write_vcf(tmp_path / "t.vcf")
    truth, excl = load_truth_giab(vcf, chroms=["2"])
    assert truth == {} and excl == {}


# --------------------------------------------------- negative-sampling rules

class _FakeFa:
    def get_reference_length(self, c):
        return 1_000_000


def test_build_items_negatives_respect_confident_and_exclusion():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "ext", "scripts/extract_tensors.py")
    ext = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ext)

    truth = {"1": [(300_000, 300_400, 1), (500_000, 500_600, 2)]}
    confident = {"1": np.array([[200_000, 600_000]], dtype=np.int64)}
    # exclude a large slab that is inside the confident region
    exclude = {"1": np.array([[350_000, 450_000]], dtype=np.int64)}

    items = ext.build_items(truth, _FakeFa(), 256, 8, True, 0,
                            confident=confident, exclude=exclude)
    negs = [it for it in items if it[4] == 0]
    assert len(negs) > 0, "no negatives placed at all"
    for (chrom, s, w, bs, label, *_rest) in negs:
        span = w * bs
        assert interval_contains(confident["1"], s, s + span), \
            f"negative at {s} escapes the confident region"
        assert not interval_overlaps(exclude["1"], s, s + span), \
            f"negative at {s} lands on an excluded record"


def test_build_items_unconstrained_path_unchanged():
    """With no BED/exclusion the sampler must behave exactly as before."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "ext", "scripts/extract_tensors.py")
    ext = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ext)
    truth = {"1": [(300_000, 300_400, 1)]}
    a = ext.build_items(truth, _FakeFa(), 256, 3, True, 7)
    b = ext.build_items(truth, _FakeFa(), 256, 3, True, 7,
                        confident=None, exclude=None)
    assert a == b
    assert sum(1 for it in a if it[4] == 0) == 3
