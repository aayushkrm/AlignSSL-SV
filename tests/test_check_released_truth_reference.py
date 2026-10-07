import gzip

import pytest

from analysis.check_released_truth_reference import check_reference_stream


def fasta(tmp_path, payload):
    path = tmp_path / "reference.fa.gz"
    path.write_bytes(gzip.compress(payload, mtime=0))
    return path


def test_overlapping_original_REF_across_lines_and_all_contigs(tmp_path):
    source = b">1 description\nACG\nTAC\n>decoy\nNN\n"
    path = fasta(tmp_path, source)
    result = check_reference_stream(path, {"1": 6, "decoy": 2},
                                    {"1": [("id1", 2, b"GTAC"), ("id2", 3, b"TA")]})
    assert result["checked_REF_records"] == 2
    assert result["reference_contigs"] == 2
    assert result["reference_delivered_decoded_bytes"] == len(source)
    assert result["whole_gzip_eof_crc_verified"]
    assert not result["normalization_performed"]


@pytest.mark.parametrize("payload,lengths,queries,message", [
    (b">1\nACGT\n", {"1": 4}, {"1": [("id", 1, b"GG")]}, "REF mismatch"),
    (b">1\nACGT\n", {"1": 5}, {}, "length mismatch"),
    (b">1\nACGT\n", {"1": 3}, {}, "exceeds declared"),
    (b">1\nACGT\n", {"1": 4, "2": 1}, {}, "missing reference"),
    (b">1\nACGT\n>1\nACGT\n", {"1": 4}, {}, "duplicate"),
    (b">2\nA\n", {"1": 1}, {}, "unknown"),
    (b"ACGT\n", {"1": 4}, {}, "invalid FASTA"),
    (b">1\nAC GT\n", {"1": 4}, {}, "invalid FASTA"),
    (b">1\nACGT\n", {"1": 4}, {"1": [("id", 3, b"GT")]}, "bounds"),
    (b">1\nACGT\n", {"1": 4}, {"1": [("id", 0, b"N")]}, "ambiguous"),
    (b">1\nACGT\n", {"1": 4}, {"2": []}, "query contig"),
])
def test_fail_without_repair(tmp_path, payload, lengths, queries, message):
    with pytest.raises(ValueError, match=message):
        check_reference_stream(fasta(tmp_path, payload), lengths, queries)


def test_decoded_cap_rejects_prefix(tmp_path):
    with pytest.raises(ValueError, match="decoded-byte cap"):
        check_reference_stream(fasta(tmp_path, b">1\nACGT\n"), {"1": 4}, {}, max_decoded=7)


def test_gzip_trailing_member_CRC_is_checked(tmp_path):
    path = fasta(tmp_path, b">1\nACGT\n")
    bad = bytearray(gzip.compress(b">2\nA\n", mtime=0))
    bad[-8] ^= 1
    path.write_bytes(path.read_bytes() + bad)
    with pytest.raises(gzip.BadGzipFile):
        check_reference_stream(path, {"1": 4, "2": 1}, {})


@pytest.mark.parametrize("limits", [{"max_decoded": 0}, {"max_decoded": True},
                                    {"max_decoded": 4 * 1024**3 + 1},
                                    {"max_contig": -1}, {"max_contig": 2.0},
                                    {"max_contig": 256 * 1024**2 + 1}])
def test_invalid_limit_overrides_fail(tmp_path, limits):
    with pytest.raises(ValueError, match="limit"):
        check_reference_stream(fasta(tmp_path, b">1\nA\n"), {"1": 1}, {}, **limits)


def test_query_count_and_REF_byte_limits(tmp_path, monkeypatch):
    import analysis.check_released_truth_reference as checker
    path = fasta(tmp_path, b">1\nACGT\n")
    monkeypatch.setattr(checker, "MAX_QUERY_RECORDS", 1)
    with pytest.raises(ValueError, match="query count"):
        check_reference_stream(path, {"1": 4}, {"1": [("a", 0, b"A"), ("b", 1, b"C")]})
    monkeypatch.setattr(checker, "MAX_QUERY_REF_BYTES", 1)
    with pytest.raises(ValueError, match="REF-byte"):
        check_reference_stream(path, {"1": 4}, {"1": [("a", 0, b"AC")]})
