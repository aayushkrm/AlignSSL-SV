"""Summarize a complete mapped-case JSONL census without modifying its inputs."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys


CHROMOSOME = "chr2"
REGION = {
    "chromosome": CHROMOSOME,
    "start_zero_based_inclusive": 240_675_000,
    "end_zero_based_exclusive": 240_704_000,
    "length_bp": 29_000,
}
RECORDS_FILENAME = "alignments.jsonl"
MANIFEST_FILENAME = "manifest.json"
MAX_RECORDS_BYTES = 9 * 1024 * 1024
MAX_MANIFEST_BYTES = 1024 * 1024
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
PAYLOAD_STATUSES = frozenset({
    "STORED_SEQUENCE_AND_QUALITY_PRESENT",
    "UNKNOWN_HARD_CLIPPED_QUERY_BASES_NOT_STORED",
    "UNKNOWN_SEQUENCE_OR_QUALITY_MISSING",
    "UNKNOWN_SEQUENCE_QUALITY_LENGTH_MISMATCH",
    "UNKNOWN_CIGAR_QUERY_LENGTH_MISMATCH",
})
QUERY_CONSUMING_CIGAR_CODES = frozenset({0, 1, 4, 7, 8})
_COMPLEMENT = str.maketrans(
    "ACGTRYMKBDHVNacgtrymkbdhvn=",
    "TGCAYRKMVHDBNtgcayrkmvhdbn=",
)


class SummaryError(ValueError):
    """Raised when an extraction is incomplete, malformed, or unstable."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _strict_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise SummaryError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def _reject_constant(value):
    raise SummaryError(f"non-standard JSON numeric constant: {value}")


def _decode_json(raw: bytes, label: str):
    try:
        return json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
        )
    except SummaryError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SummaryError(f"{label} is not valid UTF-8 JSON") from exc


def _require(condition, message):
    if not condition:
        raise SummaryError(message)


def _is_int(value):
    return type(value) is int


def _valid_sha(value):
    return isinstance(value, str) and HEX64.fullmatch(value) is not None


def _stat_fields(info):
    return {
        "exists": True,
        "size_bytes": info.st_size,
        "mtime_ns": info.st_mtime_ns,
        "ctime_ns": info.st_ctime_ns,
        "device": info.st_dev,
        "inode": info.st_ino,
    }


def _file_snapshot(path: Path):
    if path.is_symlink():
        raise SummaryError(f"input must not be a symbolic link: {path}")
    try:
        info = path.stat()
    except OSError as exc:
        raise SummaryError(f"cannot stat input file {path}: {exc}") from exc
    _require(stat.S_ISREG(info.st_mode), f"input must be a regular file: {path}")
    return _stat_fields(info)


def _snapshot_matches(left, right):
    keys = ("exists", "size_bytes", "mtime_ns", "ctime_ns", "device", "inode")
    return all(left.get(key) == right.get(key) for key in keys)


def _read_manifest(path: Path):
    before = _file_snapshot(path)
    _require(before["size_bytes"] <= MAX_MANIFEST_BYTES, "manifest exceeds the 1 MiB input cap")
    try:
        with path.open("rb") as handle:
            opened = _stat_fields(os.fstat(handle.fileno()))
            _require(_snapshot_matches(before, opened), "manifest changed before it was read")
            raw = handle.read(MAX_MANIFEST_BYTES + 1)
            after_fd = _stat_fields(os.fstat(handle.fileno()))
    except OSError as exc:
        raise SummaryError(f"cannot read manifest {path}: {exc}") from exc
    after = _file_snapshot(path)
    _require(len(raw) <= MAX_MANIFEST_BYTES, "manifest exceeds the 1 MiB input cap")
    _require(len(raw) == before["size_bytes"], "manifest byte count differs from its initial stat")
    _require(
        _snapshot_matches(before, after) and _snapshot_matches(before, after_fd),
        "manifest changed while it was read",
    )
    document = _decode_json(raw, "manifest")
    _require(isinstance(document, dict), "manifest root must be an object")
    return document, raw, before, after


def _read_records(path: Path):
    before = _file_snapshot(path)
    _require(before["size_bytes"] <= MAX_RECORDS_BYTES, "JSONL exceeds the 9 MiB input cap")
    digest = hashlib.sha256()
    rows = []
    header = None
    header_line = None
    total_bytes = 0
    try:
        with path.open("rb") as handle:
            opened = _stat_fields(os.fstat(handle.fileno()))
            _require(_snapshot_matches(before, opened), "JSONL changed before it was read")
            for line_number, raw_line in enumerate(handle, start=1):
                total_bytes += len(raw_line)
                _require(total_bytes <= MAX_RECORDS_BYTES, "JSONL exceeds the 9 MiB input cap")
                _require(raw_line.endswith(b"\n"), f"JSONL line {line_number} is not newline terminated")
                _require(not raw_line.endswith(b"\r\n"), "JSONL must use LF line endings")
                _require(len(raw_line) > 1, f"JSONL line {line_number} is empty")
                digest.update(raw_line)
                value = _decode_json(raw_line[:-1], f"JSONL line {line_number}")
                _require(isinstance(value, dict), f"JSONL line {line_number} must be an object")
                if line_number == 1:
                    header, header_line = value, raw_line
                else:
                    _require(value.get("record_type") == "alignment", f"JSONL line {line_number} is not an alignment row")
                    rows.append(value)
            after_fd = _stat_fields(os.fstat(handle.fileno()))
    except OSError as exc:
        raise SummaryError(f"cannot read JSONL {path}: {exc}") from exc
    after = _file_snapshot(path)
    _require(header is not None, "JSONL is empty; required header is missing")
    _require(total_bytes == before["size_bytes"], "JSONL byte count differs from its initial stat")
    _require(
        _snapshot_matches(before, after) and _snapshot_matches(before, after_fd),
        "JSONL changed while it was read",
    )
    return header, header_line, rows, digest.hexdigest(), total_bytes, before, after


def _check_stat_pair(source, label):
    _require(isinstance(source, dict), f"manifest {label} metadata is missing")
    path = source.get("path")
    before, after = source.get("stat_before"), source.get("stat_after")
    _require(isinstance(path, str) and path, f"manifest {label} path is missing")
    _require(isinstance(before, dict) and isinstance(after, dict), f"manifest {label} stats are missing")
    for snapshot in (before, after):
        _require(snapshot.get("exists") is True, f"manifest {label} stat does not report an existing file")
        _require(snapshot.get("path") == path, f"manifest {label} stat path differs from its source path")
        for key in ("size_bytes", "mtime_ns", "ctime_ns", "device", "inode"):
            _require(_is_int(snapshot.get(key)), f"manifest {label} stat field {key} is invalid")
    _require(_snapshot_matches(before, after), f"manifest reports that the {label} changed during extraction")
    return {
        "path": path,
        "stable_during_extraction": True,
        "stat_before": {key: before[key] for key in ("size_bytes", "mtime_ns", "ctime_ns", "device", "inode")},
        "stat_after": {key: after[key] for key in ("size_bytes", "mtime_ns", "ctime_ns", "device", "inode")},
    }


def _validate_manifest(manifest):
    _require(_is_int(manifest.get("schema_version")) and manifest["schema_version"] == 1,
             "unsupported extractor manifest schema")
    _require(manifest.get("status") == "COMPLETE", "extractor manifest status is not COMPLETE")
    _require(manifest.get("case_region_eof_reached") is True, "extractor manifest does not confirm region EOF")
    _require(manifest.get("region_fetch_started") is True, "extractor manifest does not confirm a region fetch")
    _require(manifest.get("region") == REGION, "extractor manifest region differs from the fixed 29 kb region")
    _require(manifest.get("failure") is None, "extractor manifest contains a failure")
    _require(manifest.get("failures") == [], "extractor manifest contains one or more failures")
    _require(manifest.get("biological_inv_classification_emitted") is False,
             "extractor manifest reports a biological inversion classification")
    _require(manifest.get("biological_negative_claimed") is False,
             "extractor manifest reports a biological negative claim")

    iteration = manifest.get("region_iteration")
    _require(isinstance(iteration, dict), "extractor region iteration metadata is missing")
    _require(iteration.get("status") == "COMPLETE", "region iteration status is not COMPLETE")
    _require(iteration.get("region_iterator_eof_reached") is True, "region iterator did not reach EOF")
    _require(iteration.get("stop_reason") is None, "complete region iteration has a stop reason")
    _require(iteration.get("failure") is None, "region iteration contains a failure")
    row_count = iteration.get("records_written")
    _require(_is_int(row_count) and row_count >= 0, "retained alignment row count is invalid")

    records_file = manifest.get("records_file")
    _require(isinstance(records_file, dict), "manifest records_file metadata is missing")
    _require(records_file.get("name") == RECORDS_FILENAME, "manifest JSONL filename is not alignments.jsonl")
    _require(_valid_sha(records_file.get("sha256")), "manifest JSONL SHA-256 is invalid")
    _require(_is_int(records_file.get("bytes_including_jsonl_header")), "manifest JSONL byte count is invalid")
    _require(records_file["bytes_including_jsonl_header"] > 0, "manifest JSONL byte count must be positive")
    _require(
        iteration.get("records_jsonl_bytes_including_header") == records_file["bytes_including_jsonl_header"],
        "manifest JSONL byte counts disagree",
    )

    bam = manifest.get("source_bam")
    index = manifest.get("source_index")
    _require(isinstance(bam, dict) and bam.get("opened_successfully") is True,
             "manifest does not confirm that the source BAM opened successfully")
    _require(bam.get("whole_file_sha256_computed_this_run") is False,
             "unexpected whole-file BAM hash declaration")
    _require(isinstance(index, dict) and index.get("has_index_at_open") is True,
             "manifest does not confirm an indexed source BAM")
    bam_stats = _check_stat_pair(bam, "source BAM")
    index_stats = _check_stat_pair(index, "source index")

    reference = manifest.get("reference_json")
    _require(isinstance(reference, dict), "manifest reference JSON metadata is missing")
    _require(_valid_sha(reference.get("json_sha256")), "manifest reference JSON SHA-256 is invalid")
    _require(_valid_sha(reference.get("dna_sha256")), "manifest reference DNA SHA-256 is invalid")
    reference_path = reference.get("path")
    reference_stat = reference.get("stat_before")
    _require(isinstance(reference_path, str) and reference_path, "manifest reference JSON path is missing")
    _require(isinstance(reference_stat, dict) and reference_stat.get("exists") is True,
             "manifest reference JSON initial stat is missing")
    _require(reference_stat.get("path") == reference_path, "manifest reference stat path differs")
    _require(
        all(_is_int(reference_stat.get(key)) for key in ("size_bytes", "mtime_ns", "ctime_ns", "device", "inode")),
        "manifest reference JSON stat fields are invalid",
    )

    return {
        "retained_alignment_records": row_count,
        "records_file": records_file,
        "region_iteration": iteration,
        "bam_stats": bam_stats,
        "index_stats": index_stats,
        "reference": {
            "path": reference_path,
            "json_sha256": reference["json_sha256"],
            "dna_sha256": reference["dna_sha256"],
            "stat_before": {
                key: reference_stat[key]
                for key in ("size_bytes", "mtime_ns", "ctime_ns", "device", "inode")
            },
            "stability_basis": "COMPLETE manifest with no extraction failures; reference post-read stat is not retained by schema v1",
        },
    }


def _normalized_hash(value, is_reverse, *, quality=False):
    if value is None:
        return None
    try:
        normalized = value[::-1] if quality and is_reverse else value
        if not quality and is_reverse:
            normalized = normalized.translate(_COMPLEMENT)[::-1]
        if not quality:
            normalized = normalized.upper()
        return _sha256(normalized.encode("ascii"))
    except (UnicodeEncodeError, AttributeError) as exc:
        label = "quality" if quality else "sequence"
        raise SummaryError(f"stored query {label} payload is not ASCII text") from exc


def _check_hash_field(value, expected, label):
    _require(value is None or _valid_sha(value), f"alignment {label} is not a SHA-256 digest")
    _require(value == expected, f"alignment {label} does not match its stored payload")


def _validate_alignment(row, record_index):
    required = {
        "record_type", "qname", "flag", "is_reverse_strand_flag", "is_primary_by_flags",
        "is_secondary_flag", "is_supplementary_flag", "reference_name",
        "reference_start_zero_based", "reference_end_zero_based_exclusive", "mapping_quality",
        "query_length", "query_alignment_interval_forward", "cigar_tuples_code_length",
        "sequence_reference_oriented_bam", "quality_ascii_reference_oriented_bam",
        "forward_query_sequence_sha256_uppercase", "forward_query_quality_sha256",
        "full_query_payload_status", "sequence_present", "quality_present",
        "sequence_quality_lengths_match", "hard_clipped", "essential_tags_typed",
    }
    _require(required.issubset(row), f"alignment row {record_index} is missing extractor fields")
    _require(row.get("record_type") == "alignment", f"alignment row {record_index} has the wrong record type")
    qname = row.get("qname")
    _require(qname is None or (isinstance(qname, str) and bool(qname)),
             f"alignment row {record_index} has an invalid QNAME")

    flag = row.get("flag")
    _require(_is_int(flag) and 0 <= flag <= 0xFFFF, f"alignment row {record_index} has an invalid flag")
    reverse = bool(flag & 0x10)
    secondary = bool(flag & 0x100)
    supplementary = bool(flag & 0x800)
    flag_expectations = {
        "is_reverse_strand_flag": reverse,
        "is_primary_by_flags": not secondary and not supplementary,
        "is_secondary_flag": secondary,
        "is_supplementary_flag": supplementary,
    }
    for key, expected in flag_expectations.items():
        _require(type(row.get(key)) is bool and row[key] is expected,
                 f"alignment row {record_index} has inconsistent {key}")

    reference_name = row.get("reference_name")
    _require(reference_name == CHROMOSOME, f"alignment row {record_index} is outside the fetched chromosome")
    start = row.get("reference_start_zero_based")
    end = row.get("reference_end_zero_based_exclusive")
    _require((start is None and end is None) or (_is_int(start) and _is_int(end)),
             f"alignment row {record_index} has incomplete reference bounds")
    if start is not None:
        _require(start >= 0 and end >= start, f"alignment row {record_index} has invalid reference bounds")

    mapq = row.get("mapping_quality")
    _require(_is_int(mapq) and 0 <= mapq <= 255, f"alignment row {record_index} has invalid MAPQ")
    query_length = row.get("query_length")
    _require(query_length is None or (_is_int(query_length) and query_length >= 0),
             f"alignment row {record_index} has invalid query length")
    interval = row.get("query_alignment_interval_forward")
    _require(
        interval is None or (
            isinstance(interval, list) and len(interval) == 2
            and all(_is_int(item) for item in interval)
            and 0 <= interval[0] <= interval[1]
            and (query_length is None or interval[1] <= query_length)
        ),
        f"alignment row {record_index} has an invalid forward-query interval",
    )

    cigar = row.get("cigar_tuples_code_length")
    _require(isinstance(cigar, list), f"alignment row {record_index} has invalid CIGAR tuples")
    for item in cigar:
        _require(
            isinstance(item, list) and len(item) == 2
            and _is_int(item[0]) and 0 <= item[0] <= 8
            and _is_int(item[1]) and item[1] > 0,
            f"alignment row {record_index} has an invalid CIGAR operation",
        )
    hard_clipped = any(code == 5 for code, _length in cigar)
    _require(type(row.get("hard_clipped")) is bool and row["hard_clipped"] is hard_clipped,
             f"alignment row {record_index} has inconsistent hard-clip metadata")

    sequence = row.get("sequence_reference_oriented_bam")
    quality = row.get("quality_ascii_reference_oriented_bam")
    _require(sequence is None or isinstance(sequence, str), f"alignment row {record_index} sequence is malformed")
    _require(quality is None or isinstance(quality, str), f"alignment row {record_index} quality is malformed")
    _require(type(row.get("sequence_present")) is bool and row["sequence_present"] is (sequence is not None),
             f"alignment row {record_index} has inconsistent sequence-presence metadata")
    _require(type(row.get("quality_present")) is bool and row["quality_present"] is (quality is not None),
             f"alignment row {record_index} has inconsistent quality-presence metadata")

    lengths_match = None if sequence is None or quality is None else len(sequence) == len(quality)
    _require(row.get("sequence_quality_lengths_match") is lengths_match,
             f"alignment row {record_index} has inconsistent sequence/quality lengths")
    sequence_hash = _normalized_hash(sequence, reverse)
    quality_hash = _normalized_hash(quality, reverse, quality=True)
    _check_hash_field(row.get("forward_query_sequence_sha256_uppercase"), sequence_hash, "sequence hash")
    _check_hash_field(row.get("forward_query_quality_sha256"), quality_hash, "quality hash")

    payload_status = row.get("full_query_payload_status")
    _require(payload_status in PAYLOAD_STATUSES, f"alignment row {record_index} has an unknown payload status")
    if hard_clipped:
        expected_status = "UNKNOWN_HARD_CLIPPED_QUERY_BASES_NOT_STORED"
    elif sequence is None or quality is None:
        expected_status = "UNKNOWN_SEQUENCE_OR_QUALITY_MISSING"
    elif lengths_match is False:
        expected_status = "UNKNOWN_SEQUENCE_QUALITY_LENGTH_MISMATCH"
    elif sum(length for code, length in cigar if code in QUERY_CONSUMING_CIGAR_CODES) != len(sequence):
        expected_status = "UNKNOWN_CIGAR_QUERY_LENGTH_MISMATCH"
    else:
        expected_status = "STORED_SEQUENCE_AND_QUALITY_PRESENT"
    _require(payload_status == expected_status, f"alignment row {record_index} has inconsistent payload status")

    tags = row.get("essential_tags_typed")
    _require(isinstance(tags, list), f"alignment row {record_index} has malformed essential tags")
    sa_values = []
    for tag in tags:
        _require(isinstance(tag, dict), f"alignment row {record_index} has malformed essential tag")
        _require(isinstance(tag.get("name"), str), f"alignment row {record_index} has malformed tag name")
        if tag["name"] == "SA":
            _require(isinstance(tag.get("value"), str), f"alignment row {record_index} has malformed SA metadata")
            sa_values.append({"type": tag.get("type"), "value": tag["value"]})

    return {
        "record_index": record_index,
        "qname": qname,
        "flag": flag,
        "primary": not secondary and not supplementary,
        "secondary": secondary,
        "supplementary": supplementary,
        "strand": "-" if reverse else "+",
        "reference_name": reference_name,
        "reference_start": start,
        "reference_end": end,
        "mapping_quality": mapq,
        "query_length": query_length,
        "query_interval": interval,
        "payload_status": payload_status,
        "hard_clipped": hard_clipped,
        "sequence_hash": sequence_hash,
        "quality_hash": quality_hash,
        "sa_values": sa_values,
    }


def _ordered_interval(record):
    interval = record["query_interval"]
    if interval is None:
        return (1, 0, 0, record["record_index"])
    return (0, interval[0], interval[1], record["record_index"])


def _hash_consistency(records, key):
    values = [record[key] for record in records if not record["hard_clipped"]]
    known = sorted(set(value for value in values if value is not None))
    missing = sum(value is None for value in values)
    if len(known) > 1:
        status = "INCONSISTENT"
    elif not values:
        status = "UNKNOWN_NO_NON_HARD_CLIPPED_RECORDS"
    elif missing:
        status = "UNKNOWN_MISSING_HASH"
    else:
        status = "CONSISTENT"
    return {
        "status": status,
        "eligible_record_count": len(values),
        "missing_hash_record_count": missing,
        "unique_hash_count": len(known),
    }


def _public_alignment(record):
    start, end = record["reference_start"], record["reference_end"]
    return {
        "source_record_index": record["record_index"],
        "forward_query_interval": record["query_interval"],
        "query_length": record["query_length"],
        "flag": record["flag"],
        "primary": record["primary"],
        "secondary": record["secondary"],
        "supplementary": record["supplementary"],
        "strand": record["strand"],
        "reference": record["reference_name"],
        "reference_interval": None if start is None else [start, end],
        "reference_span_bp": None if start is None else end - start,
        "mapping_quality": record["mapping_quality"],
        "full_query_payload_status": record["payload_status"],
        "hard_clipped": record["hard_clipped"],
        "sa_raw_metadata": record["sa_values"],
    }


def _qname_summary(qname, records):
    ordered = sorted(records, key=_ordered_interval)
    record_count = len(ordered)
    strands = {record["strand"] for record in ordered}
    cross_strand = len(strands) > 1
    if record_count == 1:
        label = "single_observed_record"
    elif cross_strand:
        label = "multiple_records_cross_strand"
    else:
        label = "multiple_records_one_strand"
    return {
        "qname": qname,
        "observed_record_count": record_count,
        "observed_strand_count": len(strands),
        "cross_strand_observed": cross_strand,
        "record_pattern_label": label,
        "non_hard_clipped_hash_consistency": {
            "sequence": _hash_consistency(ordered, "sequence_hash"),
            "quality": _hash_consistency(ordered, "quality_hash"),
        },
        "observed_alignment_records": [_public_alignment(record) for record in ordered],
    }


def summarize_case_input(records_path, manifest_path, output_path):
    """Validate one complete extraction and write a compact, exclusive summary."""
    records_path = Path(records_path)
    manifest_path = Path(manifest_path)
    output_path = Path(output_path)
    _require(output_path.parent.is_dir(), f"output parent directory does not exist: {output_path.parent}")
    _require(not output_path.exists() and not output_path.is_symlink(),
             f"refusing to overwrite summary output: {output_path}")

    manifest, manifest_raw, manifest_before, manifest_after = _read_manifest(manifest_path)
    manifest_info = _validate_manifest(manifest)
    header, header_line, rows, records_sha, records_bytes, records_before, records_after = _read_records(records_path)

    _require(header.get("record_type") == "header", "first JSONL row is not the required header")
    _require(_is_int(header.get("schema_version")) and header["schema_version"] == 1,
             "unsupported JSONL header schema")
    _require(
        set(header) == {"record_type", "schema_version", "region", "coordinate_system"},
        "JSONL header fields differ from extractor schema v1",
    )
    _require(header.get("region") == REGION, "JSONL header region differs from the fixed 29 kb region")
    _require(header.get("coordinate_system") == "zero-based half-open", "JSONL coordinate system is unsupported")
    _require(len(rows) == manifest_info["retained_alignment_records"],
             "JSONL alignment row count differs from manifest retained row count")
    _require(records_bytes == manifest_info["records_file"]["bytes_including_jsonl_header"],
             "JSONL byte count differs from manifest")
    _require(records_sha == manifest_info["records_file"]["sha256"], "JSONL SHA-256 differs from manifest")

    aligned = [_validate_alignment(row, index) for index, row in enumerate(rows)]
    by_qname = defaultdict(list)
    unnamed = []
    payload_counts = Counter()
    for record in aligned:
        payload_counts[record["payload_status"]] += 1
        if record["qname"] is None:
            unnamed.append(record)
        else:
            by_qname[record["qname"]].append(record)

    qname_summaries = [
        _qname_summary(qname, by_qname[qname])
        for qname in sorted(by_qname)
    ]
    pattern_counts = Counter(item["record_pattern_label"] for item in qname_summaries)
    multi_record_count = sum(item["observed_record_count"] > 1 for item in qname_summaries)
    cross_strand_count = sum(item["cross_strand_observed"] for item in qname_summaries)

    try:
        summarizer_bytes = Path(__file__).read_bytes()
    except OSError as exc:
        raise SummaryError(f"cannot hash summarizer source: {exc}") from exc

    result = {
        "schema_version": 1,
        "summary_type": "observed_mapped_case_input_descriptive_summary",
        "region": REGION,
        "jsonl_header": header,
        "provenance": {
            "records_jsonl_path": str(records_path),
            "records_jsonl_sha256": records_sha,
            "records_jsonl_bytes": records_bytes,
            "records_jsonl_header_line_sha256": _sha256(header_line),
            "records_jsonl_stat_stable_during_summary": _snapshot_matches(records_before, records_after),
            "extractor_manifest_path": str(manifest_path),
            "extractor_manifest_sha256": _sha256(manifest_raw),
            "extractor_manifest_stat_stable_during_summary": _snapshot_matches(manifest_before, manifest_after),
            "summarizer_sha256": _sha256(summarizer_bytes),
            "retained_alignment_records": len(aligned),
            "source_bam": manifest_info["bam_stats"],
            "source_index": manifest_info["index_stats"],
            "reference_json": manifest_info["reference"],
        },
        "counts": {
            "observed_alignment_records": len(aligned),
            "unique_named_qnames": len(by_qname),
            "unnamed_qname_alignment_records": len(unnamed),
            "qnames_with_multiple_records": multi_record_count,
            "qnames_with_cross_strand_records": cross_strand_count,
            "record_pattern_labels": dict(sorted(pattern_counts.items())),
            "full_query_payload_status": dict(sorted(payload_counts.items())),
        },
        "qnames": qname_summaries,
        "unnamed_alignment_records": [
            _public_alignment(record) for record in sorted(unnamed, key=_ordered_interval)
        ],
        "interpretation_limits": [
            "Rows describe alignments retained by the regional iterator and grouped by QNAME.",
            "QNAME labels do not establish independent molecules or replicate support.",
            "SA values are raw alignment metadata; SA-described records were not independently fetched or counted.",
            "Cross-strand and multiple-record labels are descriptive and do not measure inversion support.",
            "No sequence or quality strings, genotype claims, or phase claims are emitted.",
            "No thresholds or biological classifications are applied.",
        ],
    }
    encoded = (json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")
    created = False
    try:
        with output_path.open("xb") as handle:
            created = True
            written = handle.write(encoded)
            _require(written == len(encoded), "short write to summary output")
    except Exception:
        if created:
            try:
                output_path.unlink()
            except OSError:
                pass
        raise
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True,
                        help="directory containing alignments.jsonl and manifest.json")
    parser.add_argument("--output", type=Path, required=True,
                        help="new JSON summary path; existing files are never overwritten")
    args = parser.parse_args(argv)
    try:
        summary = summarize_case_input(
            args.input_dir / RECORDS_FILENAME,
            args.input_dir / MANIFEST_FILENAME,
            args.output,
        )
    except (OSError, SummaryError, TypeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({
        "status": "COMPLETE",
        "observed_alignment_records": summary["counts"]["observed_alignment_records"],
        "unique_named_qnames": summary["counts"]["unique_named_qnames"],
        "output": str(args.output),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
