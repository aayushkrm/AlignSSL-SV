"""Exact synthetic checks for the tensor depth channel."""

import numpy as np
import pysam
import pytest

from alignssl.tensorize import Q_DEPTH, build_tensor


_QUERY_CONSUMING = {0, 1, 4, 7, 8}


def _read(name, start, cigar, flag=0):
    """Construct an in-memory read without going through BAM serialization."""
    read = pysam.AlignedSegment()
    read.query_name = name
    read.flag = flag
    read.reference_id = 0
    read.reference_start = start
    read.mapping_quality = 60
    read.cigartuples = tuple(cigar)
    query_length = sum(length for op, length in cigar if op in _QUERY_CONSUMING)
    read.query_sequence = "A" * query_length
    read.query_qualities = pysam.qualitystring_to_array("I" * query_length)
    return read


@pytest.mark.parametrize("bin_size", [1, 2, 4, 8, 16, 64])
def test_mean_base_coverage_exact_at_boundaries(bin_size):
    """A bin reports aligned bases per reference base, not touched reads."""
    win_start = 100
    win_width = 4
    span = win_width * bin_size
    reads = [
        _read("full", win_start, [(0, span)]),
        _read("crosses-left-boundary", win_start + bin_size - 1, [(0, 2)]),
        _read("exact-bin-1", win_start + bin_size, [(0, bin_size)]),
        _read("exact-bin-2", win_start + 2 * bin_size, [(0, bin_size)]),
        _read("right-boundary-outside", win_start + span, [(0, 1)]),
        _read("left-boundary-outside", win_start - 1, [(0, 1)]),
    ]

    tensor = build_tensor(
        reads,
        "A" * span,
        win_start,
        win_width,
        max_rows=64,
        depth_norm=100.0,
        bin_size=bin_size,
        depth_mode="mean_base_coverage",
    )

    expected_mean = np.array(
        [1.0 + 1.0 / bin_size, 2.0 + 1.0 / bin_size, 2.0, 1.0],
        dtype=np.float32,
    )
    np.testing.assert_allclose(tensor[Q_DEPTH, 0], expected_mean / 100.0)
    np.testing.assert_allclose(
        tensor[Q_DEPTH], np.broadcast_to(expected_mean / 100.0, (64, win_width))
    )


def test_legacy_default_preserves_touching_read_outputs():
    bin_size = 4
    win_start = 100
    reads = [
        _read("full", win_start, [(0, 16)]),
        _read("crosses-left-boundary", win_start + 3, [(0, 2)]),
        _read("exact-bin-1", win_start + 4, [(0, 4)]),
        _read("exact-bin-2", win_start + 8, [(0, 4)]),
    ]
    kwargs = dict(
        ref_seq="A" * 16,
        win_start=win_start,
        win_width=4,
        max_rows=64,
        depth_norm=100.0,
        bin_size=bin_size,
    )

    default = build_tensor(reads, **kwargs)
    explicit_legacy = build_tensor(reads, depth_mode="legacy", **kwargs)
    expected = np.array([2.0, 3.0, 2.0, 1.0], dtype=np.float32) / (100.0 * bin_size)

    np.testing.assert_array_equal(default, explicit_legacy)
    np.testing.assert_allclose(default[Q_DEPTH, 0], expected)


@pytest.mark.parametrize(
    ("win_start", "expected"),
    [
        (100, [1.0, 2.0, 1.0, 1.0]),
        (101, [1.25, 1.75, 1.0, 1.0]),
        (102, [1.5, 1.5, 1.0, 1.0]),
        (103, [1.75, 1.25, 1.0, 1.0]),
    ],
)
def test_mean_base_coverage_respects_bin_phase(win_start, expected):
    reads = [
        _read("full", 100, [(0, 20)]),
        _read("phase-sensitive", 104, [(0, 4)]),
    ]
    tensor = build_tensor(
        reads,
        "A" * 16,
        win_start,
        4,
        max_rows=64,
        depth_norm=100.0,
        bin_size=4,
        depth_mode="mean_base_coverage",
    )
    np.testing.assert_allclose(
        tensor[Q_DEPTH, 0], np.asarray(expected, dtype=np.float32) / 100.0
    )


def test_mean_base_coverage_is_invariant_to_row_truncation():
    reads = [
        _read("r0", 100, [(0, 4)]),
        _read("r1", 104, [(0, 4)]),
        _read("r2", 104, [(0, 8)]),
        _read("r3", 100, [(0, 12)]),
    ]
    kwargs = dict(
        ref_seq="A" * 16,
        win_start=100,
        win_width=4,
        depth_norm=10.0,
        bin_size=4,
        depth_mode="mean_base_coverage",
    )
    truncated = build_tensor(
        reads, max_rows=1, rng=np.random.default_rng(7), **kwargs
    )
    untruncated = build_tensor(
        reads, max_rows=64, rng=np.random.default_rng(7), **kwargs
    )

    expected = np.array([0.2, 0.3, 0.2, 0.0], dtype=np.float32)
    np.testing.assert_allclose(truncated[Q_DEPTH, 0], expected)
    np.testing.assert_array_equal(truncated[Q_DEPTH, 0], untruncated[Q_DEPTH, 0])


@pytest.mark.parametrize("gap_op", [2, 3])  # deletion and reference skip
def test_cigar_gaps_do_not_count_as_covered_bases(gap_op):
    read = _read("gap", 100, [(0, 4), (gap_op, 4), (0, 4)])
    tensor = build_tensor(
        [read],
        "A" * 12,
        100,
        3,
        max_rows=8,
        depth_norm=1.0,
        bin_size=4,
        depth_mode="mean_base_coverage",
    )
    np.testing.assert_allclose(tensor[Q_DEPTH, 0], [1.0, 0.0, 1.0])


def test_empty_reads_produce_zero_depth():
    empty = pysam.AlignedSegment()
    inserted_only = _read("insertion-only", 100, [(1, 4)])
    unmapped = _read("unmapped", 100, [(0, 4)], flag=4)
    tensor = build_tensor(
        [empty, inserted_only, unmapped],
        "A" * 8,
        100,
        2,
        max_rows=8,
        depth_norm=1.0,
        bin_size=4,
        depth_mode="mean_base_coverage",
    )
    np.testing.assert_array_equal(tensor[Q_DEPTH], 0.0)


def test_invalid_depth_mode_is_rejected():
    with pytest.raises(ValueError, match="depth_mode"):
        build_tensor([], "A", 100, 1, depth_mode="not-a-mode")
