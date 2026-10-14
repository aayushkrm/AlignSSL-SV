"""Synthetic-only contracts for the offline mapped-case summarizer."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import pytest


ANALYSIS_DIR = Path(__file__).resolve().parents[1] / "analysis"
if str(ANALYSIS_DIR) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_DIR))

import summarize_inv_mapped_case_input as summary  # noqa: E402


def _json_line(value):
    return (json.dumps(value, separators=(",", ":"), allow_nan=False) + "\n").encode()


def _header():
    return {
        "record_type": "header",
        "schema_version": 1,
        "region": summary.REGION,
        "coordinate_system": "zero-based half-open",
    }


def _stat(path, size=100):
    return {
        "path": str(path),
        "exists": True,
        "size_bytes": size,
        "mtime_ns": 1_700_000_000_000_000_000,
        "ctime_ns": 1_700_000_000_000_000_001,
        "device": 7,
        "inode": 9,
    }


def _make_record(
    qname="read-1",
    *,
    flag=0,
    sequence="AACG",
    quality="abcd",
    query_interval=(0, 4),
    reference_start=summary.REGION["start_zero_based_inclusive"] + 10,
    mapq=60,
    cigar=((7, 4),),
    tags=(),
):
    reverse = bool(flag & 0x10)
    sequence_hash = summary._normalized_hash(sequence, reverse)
    quality_hash = summary._normalized_hash(quality, reverse, quality=True)
    secondary = bool(flag & 0x100)
    supplementary = bool(flag & 0x800)
    hard_clipped = any(code == 5 for code, _length in cigar)
    if hard_clipped:
        payload_status = "UNKNOWN_HARD_CLIPPED_QUERY_BASES_NOT_STORED"
    elif sequence is None or quality is None:
        payload_status = "UNKNOWN_SEQUENCE_OR_QUALITY_MISSING"
    elif len(sequence) != len(quality):
        payload_status = "UNKNOWN_SEQUENCE_QUALITY_LENGTH_MISMATCH"
    elif sum(length for code, length in cigar if code in summary.QUERY_CONSUMING_CIGAR_CODES) != len(sequence):
        payload_status = "UNKNOWN_CIGAR_QUERY_LENGTH_MISMATCH"
    else:
        payload_status = "STORED_SEQUENCE_AND_QUALITY_PRESENT"
    end = reference_start + sum(length for code, length in cigar if code in {0, 2, 3, 7, 8})
    return {
        "record_type": "alignment",
        "qname": qname,
        "flag": flag,
        "is_reverse_strand_flag": reverse,
        "is_primary_by_flags": not secondary and not supplementary,
        "is_secondary_flag": secondary,
        "is_supplementary_flag": supplementary,
        "reference_name": "chr2",
        "reference_start_zero_based": reference_start,
        "reference_end_zero_based_exclusive": end,
        "mapping_quality": mapq,
        "query_length": None if sequence is None else len(sequence),
        "query_alignment_interval_forward": None if query_interval is None else list(query_interval),
        "cigar_tuples_code_length": [list(item) for item in cigar],
        "sequence_reference_oriented_bam": sequence,
        "quality_ascii_reference_oriented_bam": quality,
        "forward_query_sequence_sha256_uppercase": sequence_hash,
        "forward_query_quality_sha256": quality_hash,
        "full_query_payload_status": payload_status,
        "sequence_present": sequence is not None,
        "quality_present": quality is not None,
        "sequence_quality_lengths_match": None if sequence is None or quality is None else len(sequence) == len(quality),
        "hard_clipped": hard_clipped,
        "essential_tags_typed": list(tags),
    }


def _write_case(directory, records, *, status="COMPLETE", eof=True):
    directory.mkdir()
    records_path = directory / "alignments.jsonl"
    manifest_path = directory / "manifest.json"
    raw = _json_line(_header()) + b"".join(_json_line(row) for row in records)
    records_path.write_bytes(raw)

    bam_path = directory / "source.bam"
    index_path = directory / "source.bam.bai"
    reference_path = directory / "reference.json"
    bam_before, index_before = _stat(bam_path), _stat(index_path)
    reference_before = _stat(reference_path)
    manifest = {
        "schema_version": 1,
        "status": status,
        "region": summary.REGION,
        "region_fetch_started": True,
        "case_region_eof_reached": eof,
        "source_bam": {
            "path": str(bam_path),
            "stat_before": bam_before,
            "stat_after": dict(bam_before),
            "opened_successfully": True,
            "whole_file_sha256_computed_this_run": False,
        },
        "source_index": {
            "path": str(index_path),
            "stat_before": index_before,
            "stat_after": dict(index_before),
            "has_index_at_open": True,
        },
        "reference_json": {
            "path": str(reference_path),
            "stat_before": reference_before,
            "json_sha256": "1" * 64,
            "dna_sha256": "2" * 64,
        },
        "region_iteration": {
            "status": status,
            "stop_reason": None if status == "COMPLETE" else "record_cap_reached",
            "failure": None,
            "region_iterator_eof_reached": eof,
            "records_written": len(records),
            "records_jsonl_bytes_including_header": len(raw),
        },
        "records_file": {
            "name": "alignments.jsonl",
            "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes_including_jsonl_header": len(raw),
        },
        "failure": None,
        "failures": [],
        "biological_inv_classification_emitted": False,
        "biological_negative_claimed": False,
    }
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return records_path, manifest_path


def test_complete_census_summarizes_qname_records_in_forward_query_order(tmp_path):
    source_sequence = "AACGTTGCA"
    reverse_sequence = source_sequence.translate(summary._COMPLEMENT)[::-1]
    source_quality = "abcdefghi"
    reverse_quality = source_quality[::-1]
    sa_raw = "chr2,240675050,+,4M,60,0;"
    records = [
        _make_record(
            "read-Z", flag=0x810, sequence=reverse_sequence, quality=reverse_quality,
            query_interval=(0, 4), reference_start=summary.REGION["start_zero_based_inclusive"] + 50,
            mapq=42, cigar=((7, 4), (4, 5)),
            tags=({"name": "SA", "type": "Z", "value": sa_raw},),
        ),
        _make_record(
            "read-Z", flag=0, sequence=source_sequence, quality=source_quality,
            query_interval=(5, 9), reference_start=summary.REGION["start_zero_based_inclusive"] + 10,
            cigar=((4, 5), (7, 4)),
        ),
        _make_record(None, sequence="TT", quality="!!", query_interval=(0, 2), cigar=((7, 2),)),
    ]
    records_path, manifest_path = _write_case(tmp_path / "extract", records)
    original_records = records_path.read_bytes()
    original_manifest = manifest_path.read_bytes()
    output_path = tmp_path / "summary.json"

    result = summary.summarize_case_input(records_path, manifest_path, output_path)
    on_disk = json.loads(output_path.read_text(encoding="utf-8"))

    assert result == on_disk
    assert result["jsonl_header"] == _header()
    assert result["counts"]["observed_alignment_records"] == 3
    assert result["counts"]["unique_named_qnames"] == 1
    assert result["counts"]["unnamed_qname_alignment_records"] == 1
    assert result["counts"]["qnames_with_cross_strand_records"] == 1
    assert result["counts"]["full_query_payload_status"] == {
        "STORED_SEQUENCE_AND_QUALITY_PRESENT": 3,
    }

    qname = result["qnames"][0]
    assert qname["qname"] == "read-Z"
    assert qname["record_pattern_label"] == "multiple_records_cross_strand"
    assert qname["non_hard_clipped_hash_consistency"]["sequence"]["status"] == "CONSISTENT"
    assert qname["non_hard_clipped_hash_consistency"]["quality"]["status"] == "CONSISTENT"
    assert [row["forward_query_interval"] for row in qname["observed_alignment_records"]] == [[0, 4], [5, 9]]
    assert qname["observed_alignment_records"][0]["strand"] == "-"
    assert qname["observed_alignment_records"][0]["sa_raw_metadata"] == [
        {"type": "Z", "value": sa_raw},
    ]
    assert "No sequence or quality strings" in " ".join(result["interpretation_limits"])
    encoded = output_path.read_text(encoding="utf-8")
    assert source_sequence not in encoded
    assert reverse_sequence not in encoded
    assert source_quality not in encoded
    assert reverse_quality not in encoded
    assert "genotype claims" in " ".join(result["interpretation_limits"])
    assert result["provenance"]["records_jsonl_sha256"] == hashlib.sha256(original_records).hexdigest()
    assert result["provenance"]["extractor_manifest_sha256"] == hashlib.sha256(original_manifest).hexdigest()
    assert result["provenance"]["extractor_manifest_stat_stable_during_summary"] is True
    assert result["provenance"]["source_bam"]["stable_during_extraction"] is True
    assert result["provenance"]["source_index"]["stable_during_extraction"] is True
    assert records_path.read_bytes() == original_records
    assert manifest_path.read_bytes() == original_manifest


@pytest.mark.parametrize(
    ("status", "eof"),
    [("INCOMPLETE", False), ("FAILED", False), ("COMPLETE", False)],
)
def test_rejects_noncomplete_or_non_eof_manifest(tmp_path, status, eof):
    records_path, manifest_path = _write_case(
        tmp_path / "extract", [_make_record()], status=status, eof=eof,
    )
    output_path = tmp_path / "summary.json"

    with pytest.raises(summary.SummaryError):
        summary.summarize_case_input(records_path, manifest_path, output_path)
    assert not output_path.exists()


@pytest.mark.parametrize("tamper", ["row_count", "byte_count", "sha256", "source_stats"])
def test_rejects_manifest_integrity_mismatches(tmp_path, tamper):
    records_path, manifest_path = _write_case(tmp_path / "extract", [_make_record()])
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if tamper == "row_count":
        manifest["region_iteration"]["records_written"] += 1
    elif tamper == "byte_count":
        manifest["records_file"]["bytes_including_jsonl_header"] += 1
        manifest["region_iteration"]["records_jsonl_bytes_including_header"] += 1
    elif tamper == "sha256":
        manifest["records_file"]["sha256"] = "0" * 64
    else:
        manifest["source_bam"]["stat_after"]["mtime_ns"] += 1
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(summary.SummaryError):
        summary.summarize_case_input(records_path, manifest_path, tmp_path / "summary.json")


@pytest.mark.parametrize("raw", [b"{broken}\n", b"{}\n", b"\n", b"{}"])
def test_rejects_malformed_jsonl_instead_of_summarizing_rows(tmp_path, raw):
    records_path, manifest_path = _write_case(tmp_path / "extract", [_make_record()])
    records_path.write_bytes(raw)

    with pytest.raises(summary.SummaryError):
        summary.summarize_case_input(records_path, manifest_path, tmp_path / "summary.json")


def test_rejects_inconsistent_payload_hash_and_existing_output(tmp_path):
    row = _make_record()
    row["forward_query_sequence_sha256_uppercase"] = "0" * 64
    records_path, manifest_path = _write_case(tmp_path / "extract", [row])
    with pytest.raises(summary.SummaryError, match="does not match its stored payload"):
        summary.summarize_case_input(records_path, manifest_path, tmp_path / "summary.json")

    valid_records, valid_manifest = _write_case(tmp_path / "valid-extract", [_make_record()])
    output_path = tmp_path / "existing.json"
    output_path.write_text("preserve", encoding="utf-8")
    with pytest.raises(summary.SummaryError, match="refusing to overwrite"):
        summary.summarize_case_input(valid_records, valid_manifest, output_path)
    assert output_path.read_text(encoding="utf-8") == "preserve"


def test_hash_consistency_uses_only_non_hard_clipped_records(tmp_path):
    records = [
        _make_record("same", sequence="AACG", quality="abcd"),
        _make_record("same", sequence="AATG", quality="abcd"),
        _make_record("same", sequence="TTTT", quality="zzzz", cigar=((5, 2), (7, 4))),
    ]
    records_path, manifest_path = _write_case(tmp_path / "extract", records)

    result = summary.summarize_case_input(records_path, manifest_path, tmp_path / "summary.json")

    qname = result["qnames"][0]
    assert qname["non_hard_clipped_hash_consistency"]["sequence"] == {
        "status": "INCONSISTENT",
        "eligible_record_count": 2,
        "missing_hash_record_count": 0,
        "unique_hash_count": 2,
    }
    assert qname["non_hard_clipped_hash_consistency"]["quality"]["status"] == "CONSISTENT"
    assert result["counts"]["full_query_payload_status"] == {
        "STORED_SEQUENCE_AND_QUALITY_PRESENT": 2,
        "UNKNOWN_HARD_CLIPPED_QUERY_BASES_NOT_STORED": 1,
    }
