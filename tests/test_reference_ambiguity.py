import hashlib
from io import BytesIO, StringIO

import pytest

from scripts.scan_reference_ambiguity import scan_fasta


def expected(sequence):
    return (len(sequence), hashlib.md5(sequence).hexdigest())


def test_ambiguous_runs_merge_across_fasta_lines():
    bed = StringIO()
    sequence = b"AANNNNNACR"
    result = scan_fasta(BytesIO(b">chr1 description\naaNNN\nNNacR\n"), bed,
                        {"chr1": expected(sequence)})
    assert bed.getvalue() == "chr1\t2\t7\nchr1\t9\t10\n"
    assert result["n_ambiguous_bases"] == 6
    assert result["n_ambiguous_intervals"] == 2
    assert result["bed_sha256"] == hashlib.sha256(bed.getvalue().encode()).hexdigest()


def test_contig_boundaries_do_not_merge_ambiguous_runs():
    bed = StringIO()
    result = scan_fasta(BytesIO(b">a\nAN\n>b\nNC\n"), bed,
                        {"a": expected(b"AN"), "b": expected(b"NC")})
    assert bed.getvalue() == "a\t1\t2\nb\t0\t1\n"
    assert result["n_contigs"] == 2


def test_rejects_m5_mismatch_and_missing_expected_contig():
    with pytest.raises(ValueError, match="length or M5"):
        scan_fasta(BytesIO(b">chr1\nAN\n"), StringIO(),
                   {"chr1": expected(b"AA")})
    with pytest.raises(ValueError, match="contig sets differ"):
        scan_fasta(BytesIO(b">chr1\nAN\n"), StringIO(),
                   {"chr1": expected(b"AN"), "chr2": expected(b"AC")})
