import hashlib
from io import BytesIO, StringIO

import pytest

from scripts.compare_reference_contig import compare_streams, sequence_chunks


def test_sequence_chunks_normalizes_case_and_line_width():
    chunks = list(sequence_chunks(BytesIO(b">chr1\naC\ngTn\n"), chunk_size=3))
    assert chunks == [b"ACG", b"TN"]


def test_compare_streams_reports_one_based_differences():
    left = BytesIO(b">chr1\nacgtn\n")
    right = BytesIO(b">chr1\nACGTA\n")
    result = compare_streams(left, right)
    assert result["length"] == 5
    assert result["n_different_bases"] == 1
    assert result["difference_types"] == {"N>A": 1}
    assert result["first_differences"] == [
        {"position_1based": 5, "left": "N", "right": "A"}
    ]


def test_compare_streams_rejects_length_difference():
    with pytest.raises(ValueError, match="different lengths"):
        compare_streams(BytesIO(b">chr1\nACG\n"), BytesIO(b">chr1\nAC\n"))


def test_difference_bed_merges_runs_across_chunks_and_uses_half_open_coordinates():
    # The first run straddles the 1 MiB comparison chunk boundary.
    left = BytesIO(b">chr2\n" + b"A" * (1024 * 1024 - 1) + b"CCGA\n")
    right = BytesIO(b">chr2\n" + b"A" * (1024 * 1024 - 1) + b"TTGT\n")
    bed = StringIO()
    result = compare_streams(left, right, contig="chr2", bed=bed)
    expected = f"chr2\t{1024 * 1024 - 1}\t{1024 * 1024 + 1}\nchr2\t{1024 * 1024 + 2}\t{1024 * 1024 + 3}\n"
    assert bed.getvalue() == expected
    assert result["n_different_bases"] == 3
    assert result["n_difference_intervals"] == 2
    assert result["difference_bed_sha256"] == hashlib.sha256(
        expected.encode("ascii")
    ).hexdigest()


def test_difference_bed_empty_when_references_match():
    bed = StringIO()
    result = compare_streams(BytesIO(b">chr1\nACGT\n"),
                             BytesIO(b">chr1\nACGT\n"), contig="chr1", bed=bed)
    assert bed.getvalue() == ""
    assert result["n_difference_intervals"] == 0
    assert result["difference_bed_sha256"] == hashlib.sha256(b"").hexdigest()
