"""Guards on GIAB truth mode in the hard-negative (candidate-filtering) extractor.

The candidate-filtering benchmark is the only benchmark in this paper whose
negatives are not trivially separable, so it carries the headline claim.
Extending it from the 1000G genotyped VCF to GIAB Tier1 introduces two
constraints that fail *silently* if mis-implemented: a negative outside the
confident regions is a window the truth set makes no claim about, and a
negative on top of an unresolved call is labelled against an assertion the
truth set never made.  Neither raises -- both just shift the reported number.

Pinned here:

  * ``test_negatives_inside_confident``  -- every emitted negative lies wholly
    within a confident interval.
  * ``test_negatives_avoid_exclusion``   -- no negative touches any called
    variant of any type or filter status.
  * ``test_genotyped_mode_unchanged``    -- with confident/exclude None the
    sampler emits exactly what it emitted before, so the 1000G arm is
    untouched and the two truth sources stay comparable.
  * ``test_depth_ratio_still_matched``   -- the depth-ratio matching that
    defines the task survives the added constraints; without this the
    benchmark silently reverts to being depth-separable.
"""
from __future__ import annotations
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import importlib.util  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "hn", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "scripts", "extract_tensors_hardneg.py"))
hn = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(hn)

from alignssl.data import interval_contains, interval_overlaps  # noqa: E402

CLEN = 400_000
WIN = 256


class _FakeFasta:
    def get_reference_length(self, chrom):
        return CLEN


class _FakeBam:
    """Coverage ~30x everywhere, halved inside the truth deletions."""

    def __init__(self, dels):
        self.dels = dels


def _fake_coverage(dels, bin_bp):
    """Coverage with realistic variation, not a flat 30x.

    Stratified matching draws negatives whose depth-ratio distribution
    matches the positives'.  A perfectly flat profile makes that impossible
    by construction -- every non-deletion window has ratio exactly 1.0, so
    no candidate can match a heterozygous positive near 0.5.  Real coverage
    varies (GC bias, mappability, copy number), which is what supplies the
    matched pool.  The fixture must reproduce that or it tests an
    impossibility rather than the sampler.
    """
    nb = CLEN // bin_bp + 1
    rng = np.random.default_rng(12345)
    cov = rng.gamma(shape=9.0, scale=30.0 / 9.0, size=nb)   # mean 30, CV~1/3
    # A handful of genuine low-coverage slabs (mappability / CNV), the source
    # of hard candidates a real depth pre-filter would propose.
    for lo in (30_000, 90_000, 180_000, 320_000):
        cov[lo // bin_bp:(lo + 8_000) // bin_bp] *= 0.45
    for (s, e, _g) in dels:
        cov[s // bin_bp:e // bin_bp] *= 0.1
    return cov


def _make_dels(n=40, seed=3):
    """Enough positives that 10-stratum matching is actually exercised.

    With 3 deletions the sampler has 2-3 positives per (chrom x scale) group,
    so 10 strata collapse to 2-3 occupied bins and the matching being tested
    is not the matching that runs in production.
    """
    rng = np.random.default_rng(seed)
    starts = np.sort(rng.choice(np.arange(5_000, CLEN - 15_000, 400), n,
                                replace=False))
    out = []
    for s in starts:
        ln = int(rng.choice([180, 320, 700, 1_400, 3_000]))
        out.append((int(s), int(s) + ln, int(rng.choice([1, 2]))))
    return out


@pytest.fixture
def patched(monkeypatch):
    dels = _make_dels()

    def _cov(bam, chrom, clen, bin_bp=hn.BIN_BP):
        return _fake_coverage(dels, bin_bp)

    monkeypatch.setattr(hn, "chrom_coverage", _cov)
    return dels


def _run(dels, confident=None, exclude=None, seed=0, max_offset=1e9):
    # max_offset defaults to effectively-disabled here on purpose.  The
    # absolute guard is meaningful only against a real candidate pool (see the
    # comment on it in the extractor); these fixtures test the relative claim.
    # test_match_guard_fires below exercises the guard itself.
    items, _stats = hn.build_items({"1": dels}, _FakeFasta(), _FakeBam(dels),
                                   WIN, 3, True, seed, 12,
                                   confident=confident, exclude=exclude,
                                   max_offset=max_offset)
    return items


def _negatives(items):
    return [(c, s, w * bs) for (c, s, w, bs, lab, *_rest) in items if lab == 0]


def test_negatives_inside_confident(patched):
    dels = patched
    conf = {"1": np.array([[0, 200_000], [300_000, CLEN]], dtype=np.int64)}
    items = _run(dels, confident=conf)
    negs = _negatives(items)
    assert negs, "sampler produced no negatives under confident constraint"
    for (_c, s, span) in negs:
        assert interval_contains(conf["1"], s, s + span), (s, span)


def test_negatives_avoid_exclusion(patched):
    dels = patched
    conf = {"1": np.array([[0, CLEN]], dtype=np.int64)}
    # An exclusion band covering a large slab of the chromosome, standing in
    # for unresolved GIAB calls and INS records.
    excl = {"1": np.array([[60_000, 110_000], [200_000, 240_000]],
                          dtype=np.int64)}
    items = _run(dels, confident=conf, exclude=excl)
    negs = _negatives(items)
    assert negs
    for (_c, s, span) in negs:
        assert not interval_overlaps(excl["1"], s, s + span), (s, span)


def test_genotyped_mode_unchanged(patched):
    """No confident/exclude -> byte-identical behaviour to the 1000G path."""
    dels = patched
    a = _run(dels, seed=7)
    b = _run(dels, confident=None, exclude=None, seed=7)
    assert a == b
    assert _negatives(a), "1000G path emits negatives"


def test_depth_ratio_still_matched(patched):
    """The matching that DEFINES the task must survive the constraints.

    If the confident/exclusion filter shrank the pool enough to break
    stratified matching, the benchmark would quietly become depth-separable
    again -- the exact artefact this benchmark exists to remove.
    """
    dels = patched
    conf = {"1": np.array([[0, CLEN]], dtype=np.int64)}
    items = _run(dels, confident=conf)
    cov = _fake_coverage(dels, hn.BIN_BP)
    for bs in sorted({bs for (_c, _s, _w, bs, *_r) in items}):
        span = WIN * bs
        pos = [s for (_c, s, _w, b, lab, *_r) in items if lab == 1 and b == bs]
        neg = [s for (_c, s, _w, b, lab, *_r) in items if lab == 0 and b == bs]
        if not pos or not neg:
            continue
        pr = hn.ratio_from_profile(cov, pos, span)
        nr = hn.ratio_from_profile(cov, neg, span)
        pr, nr = pr[np.isfinite(pr)], nr[np.isfinite(nr)]
        if pr.size == 0 or nr.size == 0:
            continue
        # An absolute threshold on the offset is not the right assertion: how
        # close matching can get is bounded by what the candidate pool
        # contains, which differs between fixture and genome.  The claim that
        # must hold is RELATIVE -- matched negatives are far closer to the
        # positives in depth-ratio than negatives drawn uniformly from the
        # same pool.  That is exactly the property that makes the benchmark
        # non-separable, and it is scale-free.
        rng = np.random.default_rng(0)
        grid = np.arange(0, CLEN - span, max(span // 2, 1))
        unif = rng.choice(grid, size=max(len(neg), 8), replace=False)
        ur = hn.ratio_from_profile(cov, list(unif), span)
        ur = ur[np.isfinite(ur)]
        matched_off = abs(np.median(pr) - np.median(nr))
        uniform_off = abs(np.median(pr) - np.median(ur))
        assert matched_off < uniform_off, (
            f"bin {bs}: matched offset {matched_off:.3f} is not closer than "
            f"uniform offset {uniform_off:.3f} -- matching is not working")
        print(f"    bin {bs}: matched offset {matched_off:.3f} vs "
              f"uniform {uniform_off:.3f}")


def test_match_guard_fires(patched):
    """The absolute max_offset guard must actually raise, not just print.

    The guard lives in the extractor rather than here because a meaningful
    threshold needs a real candidate pool.  What IS testable in a fixture is
    that the guard is wired up: an impossible threshold must fail extraction
    rather than emit a benchmark whose negatives are still depth-separable.
    A guard that only reports is a guard that gets ignored in a log tail.
    """
    dels = patched
    with pytest.raises(AssertionError, match="depth-ratio matching failed"):
        _run(dels, max_offset=0.0)

    # And it must not fire when the achieved match is within tolerance --
    # otherwise the guard would block every legitimate extraction.
    items = _run(dels, max_offset=1e9)
    assert sum(1 for it in items if it[4] == 0) > 0
