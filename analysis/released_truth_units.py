"""Pure, development-only helpers for the frozen released-callset screen."""

from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass
from hashlib import sha256
import random
from types import MappingProxyType
from typing import Iterable, Mapping

MIN_EVENT_BP = 50
FLANK_BP = 2_000
BLOCK_BP = 1_000_000
BOOTSTRAP_DRAWS = 2_000
BOOTSTRAP_SEED = 20261004
MIN_VALID_DRAWS = 1_900
Interval = tuple[str, int, int]
_AUTOSOMES = frozenset(str(n) for n in range(1, 23)) | frozenset(f"chr{n}" for n in range(1, 23))


def is_autosome(chrom: str) -> bool:
    return isinstance(chrom, str) and chrom in _AUTOSOMES


def truth_identity(source_sha256: str, ordinal: int) -> str:
    """Return the full SHA-256 identity for one original, one-based VCF row."""
    if (not isinstance(source_sha256, str) or len(source_sha256) != 64
            or any(c not in "0123456789abcdefABCDEF" for c in source_sha256)):
        raise ValueError("source_sha256 must be 64 hexadecimal characters")
    if type(ordinal) is not int or ordinal < 1:
        raise ValueError("ordinal must be a positive one-based integer")
    return sha256(f"{source_sha256.lower()}|{ordinal}".encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class TruthUnit:
    identity: str
    chrom: str
    pos: int
    ref: str
    alt: str
    gt: str
    phased: bool
    kind: str
    length: int

    def full_span(self, flank: int = FLANK_BP) -> Interval:
        if type(flank) is not int or flank < 0:
            raise ValueError("flank must be a nonnegative integer")
        start = self.pos - 1
        return self.chrom, start - flank, start + len(self.ref) + flank


@dataclass(frozen=True)
class TruthClassification:
    identity: str
    unit: TruthUnit | None
    exclusion_reason: str | None


def classify_truth_record(
    source_sha256: str, ordinal: int, chrom: str, pos: int,
    ref: str, alt: str | None, gt: str | None,
) -> TruthClassification:
    """Classify one record without imputing alleles, genotype, or phase."""
    identity = truth_identity(source_sha256, ordinal)

    def excluded(reason: str) -> TruthClassification:
        return TruthClassification(identity, None, reason)

    if type(pos) is not int or pos < 1:
        return excluded("invalid_position")
    if not isinstance(chrom, str) or not is_autosome(chrom):
        return excluded("out_of_scope_chromosome")
    if alt is None or alt == ".":
        return excluded("no_alternate")
    if not isinstance(alt, str):
        return excluded("invalid_allele")
    if "," in alt:
        return excluded("multiallelic")
    if alt == "*" or (alt.startswith("<") and alt.endswith(">")) or "[" in alt or "]" in alt:
        return excluded("symbolic_or_star")
    if not isinstance(ref, str) or not ref or not isinstance(alt, str) or not alt:
        return excluded("empty_allele")
    ref_u, alt_u = ref.upper(), alt.upper()
    if any(base not in "ACGT" for base in ref_u + alt_u):
        return excluded("ambiguous_base")
    if not isinstance(gt, str) or not gt or gt == ".":
        return excluded("missing_or_partial_gt")
    if "/" in gt and "|" in gt:
        return excluded("invalid_gt")
    sep = "|" if "|" in gt else "/"
    alleles = gt.split(sep)
    if len(alleles) != 2:
        return excluded("non_diploid_gt")
    if "." in alleles:
        return excluded("missing_or_partial_gt")
    if any(a not in {"0", "1"} for a in alleles):
        return excluded("unsupported_gt_allele")
    if alleles == ["0", "0"]:
        return excluded("reference_only")
    if ref_u == alt_u:
        return excluded("no_sequence_change")

    # Scan maximal suffix first, then prefix, and slice each allele only once.
    suffix = 0
    while suffix < min(len(ref_u), len(alt_u)) and ref_u[-suffix - 1] == alt_u[-suffix - 1]:
        suffix += 1
    ref_end, alt_end, prefix = len(ref_u) - suffix, len(alt_u) - suffix, 0
    while prefix < ref_end and prefix < alt_end and ref_u[prefix] == alt_u[prefix]:
        prefix += 1
    ref_u, alt_u = ref_u[prefix:ref_end], alt_u[prefix:alt_end]
    if not ref_u and alt_u:
        kind, length = "INS", len(alt_u)
    elif ref_u and not alt_u:
        kind, length = "DEL", len(ref_u)
    elif not ref_u and not alt_u:
        return excluded("no_sequence_change")
    else:
        return excluded("complex_replacement")
    if length < MIN_EVENT_BP:
        return excluded("below_min_length")
    unit = TruthUnit(identity, chrom, pos, ref, alt, gt, sep == "|", kind, length)
    return TruthClassification(identity, unit, None)


def merge_bed(intervals: Iterable[Interval]) -> list[Interval]:
    """Merge overlapping and adjacent 0-based, half-open intervals."""
    rows = list(intervals)
    for row in rows:
        if (len(row) != 3 or not isinstance(row[0], str) or not row[0]
                or type(row[1]) is not int or type(row[2]) is not int
                or row[1] < 0 or row[2] <= row[1]):
            raise ValueError(f"invalid BED interval: {row!r}")
    merged: list[Interval] = []
    for chrom, start, end in sorted(rows):
        if merged and merged[-1][0] == chrom and start <= merged[-1][2]:
            prev = merged[-1]
            merged[-1] = (chrom, prev[1], max(prev[2], end))
        else:
            merged.append((chrom, start, end))
    return merged


def _group(intervals: list[Interval]) -> dict[str, list[tuple[int, int]]]:
    grouped: dict[str, list[tuple[int, int]]] = {}
    for chrom, start, end in intervals:
        grouped.setdefault(chrom, []).append((start, end))
    return grouped


@dataclass(frozen=True, init=False)
class TerritoryIndex:
    """Immutable merged BED snapshot for repeated interval-containment queries."""
    intervals: tuple[Interval, ...]
    _by_chrom: Mapping[str, tuple[tuple[int, ...], tuple[int, ...]]]

    def __init__(self, intervals: Iterable[Interval]):
        merged = tuple(merge_bed(intervals))
        grouped = _group(list(merged))
        indexed = {
            chrom: (tuple(start for start, _ in spans), tuple(end for _, end in spans))
            for chrom, spans in grouped.items()
        }
        object.__setattr__(self, "intervals", merged)
        object.__setattr__(self, "_by_chrom", MappingProxyType(indexed))

    def contains_interval(self, chrom: str, start: int, end: int) -> bool:
        if (not isinstance(chrom, str) or type(start) is not int or type(end) is not int
                or start < 0 or end <= start):
            return False
        bounds = self._by_chrom.get(chrom)
        if bounds is None:
            return False
        starts, ends = bounds
        index = bisect_right(starts, start) - 1
        return index >= 0 and end <= ends[index]


def subtract_bed(left: Iterable[Interval], right: Iterable[Interval]) -> list[Interval]:
    a, b = _group(merge_bed(left)), _group(merge_bed(right))
    out: list[Interval] = []
    for chrom, spans in a.items():
        cuts, j = b.get(chrom, []), 0
        for start, end in spans:
            cursor = start
            while j < len(cuts) and cuts[j][1] <= cursor:
                j += 1
            k = j
            while k < len(cuts) and cuts[k][0] < end:
                cut_start, cut_end = cuts[k]
                if cut_start > cursor:
                    out.append((chrom, cursor, min(cut_start, end)))
                cursor = max(cursor, cut_end)
                if cursor >= end:
                    break
                k += 1
            if cursor < end:
                out.append((chrom, cursor, end))
    return merge_bed(out)


def intersect_bed(left: Iterable[Interval], right: Iterable[Interval]) -> list[Interval]:
    a, b = _group(merge_bed(left)), _group(merge_bed(right))
    out: list[Interval] = []
    for chrom, spans in a.items():
        other, i, j = b.get(chrom, []), 0, 0
        while i < len(spans) and j < len(other):
            start, end = spans[i]
            other_start, other_end = other[j]
            lo, hi = max(start, other_start), min(end, other_end)
            if lo < hi:
                out.append((chrom, lo, hi))
            if end <= other_end:
                i += 1
            else:
                j += 1
    return merge_bed(out)


def contains_interval(
    chrom: str, start: int, end: int, territory: Iterable[Interval] | TerritoryIndex,
) -> bool:
    """Containment on a BED iterable, or on a merged/reusable ``TerritoryIndex``."""
    index = territory if isinstance(territory, TerritoryIndex) else TerritoryIndex(territory)
    return index.contains_interval(chrom, start, end)


def territory_sets(current: Iterable[Interval], tier1: Iterable[Interval]) -> tuple[list[Interval], list[Interval]]:
    """Return autosomal (current minus Tier1, current intersect Tier1) territories."""
    current_auto = merge_bed(x for x in current if is_autosome(x[0]))
    tier1_auto = merge_bed(x for x in tier1 if is_autosome(x[0]))
    return subtract_bed(current_auto, tier1_auto), intersect_bed(current_auto, tier1_auto)


def territory_status(
    unit: TruthUnit, territory: Iterable[Interval] | TerritoryIndex, flank: int = FLANK_BP,
) -> str:
    chrom, start, end = unit.full_span(flank)
    return "eligible" if contains_interval(chrom, start, end, territory) else "boundary_or_mixed"


@dataclass(frozen=True)
class ScreenObservation:
    chrom: str
    pos: int
    residual: bool
    secondary_residual: bool | None = None


@dataclass(frozen=True)
class BootstrapResult:
    hard_records: int
    ordinary_records: int
    hard_residuals: int
    ordinary_residuals: int
    hard_blocks: int
    ordinary_blocks: int
    union_blocks: int
    difference: float | None
    interval: tuple[float, float] | None
    valid_draws: int
    zero_denominator_draws: int
    secondary_provided: bool
    status: str


def _block_counts(records: Iterable[ScreenObservation], secondary: bool) -> dict[tuple[str, int], tuple[int, int]]:
    counts: dict[tuple[str, int], list[int]] = {}
    for record in records:
        if type(record.pos) is not int or record.pos < 1 or not is_autosome(record.chrom):
            raise ValueError("screen observations need autosomal chrom and positive 1-based POS")
        value = record.secondary_residual if secondary else record.residual
        if type(value) is not bool:
            raise ValueError("each selected arm needs an explicit residual bool")
        key = (record.chrom, (record.pos - 1) // BLOCK_BP)
        pair = counts.setdefault(key, [0, 0])
        pair[0] += 1
        pair[1] += int(value)
    return {key: (value[0], value[1]) for key, value in counts.items()}


def _percentile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    rank = (len(ordered) - 1) * probability
    lo = int(rank)
    hi = min(lo + 1, len(ordered) - 1)
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (rank - lo)


def joint_block_bootstrap(
    hard: Iterable[ScreenObservation], ordinary: Iterable[ScreenObservation],
    *, secondary_provided: bool = False,
) -> BootstrapResult:
    """Fixed 2,000-draw paired-block interval for hard minus ordinary residual rate."""
    if type(secondary_provided) is not bool:
        raise ValueError("secondary_provided must be bool")
    h, o = _block_counts(hard, secondary_provided), _block_counts(ordinary, secondary_provided)
    blocks = sorted(set(h) | set(o))
    h_n, h_r = sum(x[0] for x in h.values()), sum(x[1] for x in h.values())
    o_n, o_r = sum(x[0] for x in o.values()), sum(x[1] for x in o.values())
    observed = h_r / h_n - o_r / o_n if h_n and o_n else None
    rng, samples, zero = random.Random(BOOTSTRAP_SEED), [], 0
    for _ in range(BOOTSTRAP_DRAWS):
        hd = hr = od = ore = 0
        for _ in blocks:
            key = blocks[rng.randrange(len(blocks))]
            x, y = h.get(key, (0, 0)), o.get(key, (0, 0))
            hd, hr, od, ore = hd + x[0], hr + x[1], od + y[0], ore + y[1]
        if not hd or not od:
            zero += 1
        else:
            samples.append(hr / hd - ore / od)
    valid = len(samples)
    interval = None
    if observed is not None and valid >= MIN_VALID_DRAWS:
        interval = (_percentile(samples, 0.025), _percentile(samples, 0.975))
    status = "undefined_observed_denominator" if observed is None else (
        "inconclusive" if valid < MIN_VALID_DRAWS else "ok"
    )
    return BootstrapResult(
        h_n, o_n, h_r, o_r, len(h), len(o), len(blocks), observed, interval,
        valid, zero, secondary_provided, status,
    )
