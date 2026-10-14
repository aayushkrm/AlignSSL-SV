"""Extract a bounded, unfiltered regional census from one indexed DNA BAM."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import sys
import time
from pathlib import Path


CHROMOSOME = "chr2"
REGION_START = 240_675_000
REGION_END = 240_704_000
REGION_LENGTH = REGION_END - REGION_START
CHR2_LENGTH = 242_193_529
MAX_RECORDS = 1_000
MAX_CASE_PAYLOAD_BYTES = 9 * 1024 * 1024
MAX_MANIFEST_BYTES = 1024 * 1024
MAX_TOTAL_OUTPUT_BYTES = MAX_CASE_PAYLOAD_BYTES + MAX_MANIFEST_BYTES
MAX_REFERENCE_JSON_BYTES = 128 * 1024
MAX_HEADER_BYTES = 128 * 1024
MAX_RUNTIME_SECONDS = 120
RECORDS_FILENAME = "alignments.jsonl"
MANIFEST_FILENAME = "manifest.json"

HISTORICAL_BAM_PATH = Path(
    "/beegfs/datasets/home/igorno/alignssl_restart_20260922/experiments/"
    "hg002_dna_s1a_20261010_01/HG002_WGS.haplotagged.bam"
)
HISTORICAL_BAM_SHA256 = "b7edeb4bbc2589039c6148a912857f26924ca8fd5971cd3141337d0ce24bbde4"
HISTORICAL_BAI_SHA256 = "5106ac6339847460842a528a312471785d9348f59cc65cca02b55b15e157e546"
HISTORICAL_BAM_SIZE_BYTES = 48_727_325_910
HISTORICAL_BAI_SIZE_BYTES = 21_582_928

ESSENTIAL_TAGS = frozenset({"SA", "RG", "HP", "PS", "MD", "NM", "AS"})
CIGAR_NAMES = {
    0: "M",
    1: "I",
    2: "D",
    3: "N",
    4: "S",
    5: "H",
    6: "P",
    7: "=",
    8: "X",
}
QUERY_CONSUMING = frozenset({0, 1, 4, 7, 8})
REFERENCE_CONSUMING = frozenset({0, 2, 3, 7, 8})
_COMPLEMENT = str.maketrans(
    "ACGTRYMKBDHVNacgtrymkbdhvn=",
    "TGCAYRKMVHDBNtgcayrkmvhdbn=",
)

CLAIM_LIMITS = [
    "This output is a regional alignment census, not an inversion-read classifier.",
    "A complete region iterator does not enumerate every possible placement or every source molecule.",
    "QNAME counts describe alignment labels only; they do not establish independent molecules or replicate support.",
    "SA tags are self-reported alignment metadata; they are not independently fetched alignments.",
    "Omitted nonessential tag values remain in the unchanged source BAM; this output records their names only.",
    "HP and PS values are raw observed tags, not validated phase or genotype evidence.",
    "CIGAR '=' witnesses compare only query bases and covered positions in the supplied 29 kb reference context.",
    "M, X, D, and N operations do not provide reference-equality witnesses; uncovered positions remain unknown.",
    "Zero witness conflicts cannot certify uncovered reference positions, the caller FASTA, an alternate allele, or unique mapping.",
    "A record-count, payload, or time cap makes the census incomplete and supports no biological negative claim.",
    "This mapped DNA track is separate from the benchmark's 20-result panel and does not reproduce its outcome.",
]


class ExtractionError(ValueError):
    """Raised when an input does not meet the fixed extraction contract."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json_bytes(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def validate_reference_json(raw: bytes) -> dict:
    """Validate and return only the small frozen reference context."""
    if len(raw) > MAX_REFERENCE_JSON_BYTES:
        raise ExtractionError("reference JSON exceeds the 128 KiB input cap")
    try:
        document = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ExtractionError("reference JSON is not valid UTF-8 JSON") from exc
    if not isinstance(document, dict):
        raise ExtractionError("reference JSON root must be an object")
    if document.get("genome") != "hg38" or document.get("chrom") != CHROMOSOME:
        raise ExtractionError("reference JSON must describe hg38 chr2")
    if type(document.get("start")) is not int or document["start"] != REGION_START:
        raise ExtractionError("reference JSON start differs from the frozen region")
    if type(document.get("end")) is not int or document["end"] != REGION_END:
        raise ExtractionError("reference JSON end differs from the frozen region")
    dna = document.get("dna")
    if not isinstance(dna, str) or len(dna) != REGION_LENGTH:
        raise ExtractionError("reference JSON DNA must contain exactly 29,000 bases")
    if set(dna.upper()) - set("ACGT"):
        raise ExtractionError("reference JSON DNA contains bases outside A/C/G/T")
    return {
        "genome": "hg38",
        "chromosome": CHROMOSOME,
        "start": REGION_START,
        "end": REGION_END,
        "dna": dna.upper(),
        "dna_sha256": _sha256(dna.upper().encode("ascii")),
    }


def _json_tag_value(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, bytes):
        return value.decode("ascii")
    raise ExtractionError("an essential alignment tag has a non-scalar value")


def _alignment_tags(alignment):
    try:
        tags = alignment.get_tags(with_value_type=True)
    except TypeError:
        tags = [(name, value, None) for name, value in alignment.get_tags()]
    essential, omitted = [], []
    for item in tags:
        if len(item) == 3:
            name, value, value_type = item
        elif len(item) == 2:
            name, value = item
            value_type = None
        else:
            raise ExtractionError("alignment tag has an unexpected tuple shape")
        if name in ESSENTIAL_TAGS:
            essential.append({
                "name": name,
                "type": value_type,
                "value": _json_tag_value(value),
            })
        else:
            omitted.append(name)
    return essential, omitted


def _query_quality_ascii(alignment):
    raw = getattr(alignment, "qual", None)
    if raw is not None:
        return str(raw)
    qualities = getattr(alignment, "query_qualities", None)
    if qualities is None:
        return None
    try:
        return "".join(chr(int(value) + 33) for value in qualities)
    except (TypeError, ValueError, OverflowError):
        raise ExtractionError("query qualities cannot be represented as SAM QUAL") from None


def _forward_sequence(reference_oriented_sequence, is_reverse):
    if reference_oriented_sequence is None:
        return None
    if is_reverse:
        return reference_oriented_sequence.translate(_COMPLEMENT)[::-1]
    return reference_oriented_sequence


def _forward_interval(start, end, query_length, is_reverse):
    if start is None or end is None or query_length is None:
        return None
    if start < 0 or end < start or end > query_length:
        return None
    if is_reverse:
        return [query_length - end, query_length - start]
    return [start, end]


def alignment_record_and_witness(alignment, reference_dna: str):
    """Build one lossless sequence/tag record plus internal '=' observations."""
    qname = getattr(alignment, "query_name", None)
    flag = int(getattr(alignment, "flag"))
    is_reverse = bool(flag & 0x10)
    flag_classes = _flag_classes(flag)
    sequence = getattr(alignment, "query_sequence", None)
    qualities = _query_quality_ascii(alignment)
    sequence_length = len(sequence) if sequence is not None else None
    query_length = getattr(alignment, "query_length", sequence_length)
    if query_length is None:
        query_length = sequence_length
    query_length = int(query_length) if query_length is not None else None
    qalign_start = getattr(alignment, "query_alignment_start", None)
    qalign_end = getattr(alignment, "query_alignment_end", None)
    qalign_start = int(qalign_start) if qalign_start is not None else None
    qalign_end = int(qalign_end) if qalign_end is not None else None
    cigar = getattr(alignment, "cigartuples", None) or []
    cigar = [[int(code), int(length)] for code, length in cigar]
    reference_start = getattr(alignment, "reference_start", None)
    reference_start = int(reference_start) if reference_start is not None else None
    reference_end = getattr(alignment, "reference_end", None)
    reference_end = int(reference_end) if reference_end is not None else None
    mapq = int(getattr(alignment, "mapping_quality"))

    hard_clipped = any(code == 5 and length > 0 for code, length in cigar)
    quality_length_matches = (
        None if sequence is None or qualities is None else len(sequence) == len(qualities)
    )
    if hard_clipped:
        payload_status = "UNKNOWN_HARD_CLIPPED_QUERY_BASES_NOT_STORED"
    elif sequence is None or qualities is None:
        payload_status = "UNKNOWN_SEQUENCE_OR_QUALITY_MISSING"
    elif not quality_length_matches:
        payload_status = "UNKNOWN_SEQUENCE_QUALITY_LENGTH_MISMATCH"
    else:
        payload_status = "STORED_SEQUENCE_AND_QUALITY_PRESENT"

    forward_sequence = _forward_sequence(sequence, is_reverse)
    forward_qualities = qualities[::-1] if qualities is not None and is_reverse else qualities
    seq_hash = None if forward_sequence is None else _sha256(forward_sequence.upper().encode("ascii"))
    qual_hash = None if forward_qualities is None else _sha256(forward_qualities.encode("ascii"))
    essential_tags, omitted_tag_names = _alignment_tags(alignment)

    qpos = 0
    rpos = reference_start
    cigar_walk = []
    observations = []
    witness = {
        "equals_reference_bases_compared": 0,
        "equals_reference_base_conflicts": 0,
        "equals_query_bases_unknown": 0,
        "equals_positions_outside_reference_context": 0,
    }
    operation_base_counts = Counter()
    for code, length in cigar:
        if length < 1 or code not in CIGAR_NAMES:
            raise ExtractionError("CIGAR contains an invalid operation or nonpositive length")
        operation_base_counts[str(code)] += length
        query_start = qpos if code in QUERY_CONSUMING else None
        query_end = qpos + length if code in QUERY_CONSUMING else None
        reference_op_start = rpos if code in REFERENCE_CONSUMING else None
        reference_op_end = rpos + length if code in REFERENCE_CONSUMING and rpos is not None else None
        forward_coords = _forward_interval(query_start, query_end, query_length, is_reverse)
        within_stored_sequence = (
            None if sequence_length is None or query_start is None
            else query_end <= sequence_length
        )
        cigar_walk.append({
            "operation_code": code,
            "operation": CIGAR_NAMES[code],
            "length": length,
            "reference_interval_zero_based_half_open": (
                [reference_op_start, reference_op_end]
                if reference_op_start is not None and reference_op_end is not None else None
            ),
            "query_interval_reference_oriented_cigar": (
                [query_start, query_end] if query_start is not None else None
            ),
            "query_interval_forward_cigar": forward_coords,
            "query_interval_within_stored_sequence": within_stored_sequence,
            "query_coordinate_scope": (
                "stored_sequence_payload; full molecule coordinates unknown with hard clips"
                if hard_clipped else "stored query sequence"
            ),
        })

        if code == 7:
            for offset in range(length):
                pos = None if rpos is None else rpos + offset
                qindex = qpos + offset
                if pos is not None and not REGION_START <= pos < REGION_END:
                    witness["equals_positions_outside_reference_context"] += 1
                    continue
                if sequence is None or qindex >= len(sequence) or qindex < 0:
                    witness["equals_query_bases_unknown"] += 1
                    continue
                query_base = sequence[qindex].upper()
                if query_base not in "ACGT":
                    witness["equals_query_bases_unknown"] += 1
                    continue
                if pos is None:
                    witness["equals_positions_outside_reference_context"] += 1
                    continue
                ref_base = reference_dna[pos - REGION_START]
                observations.append((pos, ref_base, query_base))
                witness["equals_reference_bases_compared"] += 1
                if query_base != ref_base:
                    witness["equals_reference_base_conflicts"] += 1

        if code in QUERY_CONSUMING:
            qpos += length
        if code in REFERENCE_CONSUMING and rpos is not None:
            rpos += length

    if reference_start is not None and reference_end is not None and rpos is not None and rpos != reference_end:
        raise ExtractionError("CIGAR-derived reference end differs from alignment reference_end")

    cigar_query_length_matches = None if sequence_length is None else qpos == sequence_length
    if not hard_clipped and sequence is not None and qualities is not None and cigar_query_length_matches is False:
        payload_status = "UNKNOWN_CIGAR_QUERY_LENGTH_MISMATCH"

    record = {
        "qname": qname,
        "flag": flag,
        "is_reverse_strand_flag": is_reverse,
        "is_primary_by_flags": flag_classes["primary"],
        "is_secondary_flag": flag_classes["secondary"],
        "is_supplementary_flag": flag_classes["supplementary"],
        "reference_name": getattr(alignment, "reference_name", None),
        "reference_start_zero_based": reference_start,
        "reference_end_zero_based_exclusive": reference_end,
        "mapping_quality": mapq,
        "cigar_string": getattr(alignment, "cigarstring", None),
        "cigar_tuples_code_length": cigar,
        "query_length": query_length,
        "query_alignment_start_reference_oriented": qalign_start,
        "query_alignment_end_reference_oriented": qalign_end,
        "query_alignment_interval_forward": _forward_interval(
            qalign_start, qalign_end, query_length, is_reverse
        ),
        "query_coordinate_order": "CIGAR/reference progression; forward intervals are normalized to original query orientation",
        "sequence_reference_oriented_bam": sequence,
        "quality_ascii_reference_oriented_bam": qualities,
        "forward_query_sequence_sha256_uppercase": seq_hash,
        "forward_query_quality_sha256": qual_hash,
        "forward_query_hash_scope": (
            "available stored query payload only; hard-clipped bases are absent"
            if hard_clipped else "stored query payload"
        ),
        "full_query_payload_status": payload_status,
        "sequence_present": sequence is not None,
        "quality_present": qualities is not None,
        "sequence_quality_lengths_match": quality_length_matches,
        "cigar_query_consumed_bases": qpos,
        "cigar_query_length_matches_stored_sequence": cigar_query_length_matches,
        "hard_clipped": hard_clipped,
        "essential_tags_typed": essential_tags,
        "omitted_tag_names_only": omitted_tag_names,
        "cigar_walk_genomic_order": cigar_walk,
        "equals_reference_witness": witness,
        "cigar_operation_base_counts": dict(operation_base_counts),
    }
    return record, observations


def _flag_classes(flag):
    secondary = bool(flag & 0x100)
    supplementary = bool(flag & 0x800)
    return {
        "primary": not secondary and not supplementary,
        "secondary": secondary,
        "supplementary": supplementary,
    }


def _witness_summary(position_counts, conflict_counts, totals):
    conflict_positions = {position for position, _ref, _query in conflict_counts}
    conflict_base_counts = Counter()
    for (_position, reference_base, query_base), count in conflict_counts.items():
        conflict_base_counts[(reference_base, query_base)] += count
    return {
        **totals,
        "unique_reference_positions_observed": len(position_counts),
        "observed_reference_position_offsets_zero_based": [
            position - REGION_START for position in sorted(position_counts)
        ],
        "conflict_position_offsets_zero_based": [
            position - REGION_START for position in sorted(conflict_positions)
        ],
        "conflict_reference_query_base_counts": [
            [reference_base, query_base, conflict_base_counts[(reference_base, query_base)]]
            for reference_base, query_base in sorted(conflict_base_counts)
        ],
    }


def collect_region_records(
    records,
    reference_dna: str,
    *,
    header_line: bytes,
    write_line,
    clock=time.monotonic,
    started_at=None,
    record_limit=MAX_RECORDS,
    payload_limit_bytes=MAX_CASE_PAYLOAD_BYTES,
    time_limit_seconds=MAX_RUNTIME_SECONDS,
    header_already_written=False,
):
    """Stream records until region EOF or a fixed cap; never infer beyond a stop."""
    if record_limit < 1 or payload_limit_bytes < 1 or time_limit_seconds <= 0:
        raise ValueError("collection caps must be positive")
    if len(header_line) > payload_limit_bytes:
        raise ValueError("JSONL header exceeds the case-payload cap")
    start_time = clock() if started_at is None else started_at
    if not header_already_written:
        write_line(header_line)
    payload_bytes = len(header_line)
    record_count = 0
    qnames = Counter()
    unnamed_qname_records = 0
    flag_counts = Counter()
    class_counts = Counter()
    mapq_counts = Counter()
    cigar_counts = Counter()
    cigar_operation_counts = Counter()
    omitted_tag_occurrences = 0
    witness_position_counts = Counter()
    witness_conflict_counts = Counter()
    witness_totals = Counter({
        "equals_reference_bases_compared": 0,
        "equals_reference_base_conflicts": 0,
        "equals_query_bases_unknown": 0,
        "equals_positions_outside_reference_context": 0,
    })
    eof_reached = False
    status = "COMPLETE"
    stop_reason = None
    failure = None
    iterator = iter(records)

    if payload_bytes >= payload_limit_bytes:
        status, stop_reason = "INCOMPLETE", "case_payload_cap_reached"
    while stop_reason is None:
        if clock() - start_time >= time_limit_seconds:
            status, stop_reason = "INCOMPLETE", "time_cap_reached"
            break
        try:
            alignment = next(iterator)
        except StopIteration:
            eof_reached = True
            break
        except Exception as exc:
            status, stop_reason = "FAILED", "region_iteration_error"
            failure = {"type": type(exc).__name__, "message": str(exc)[:500]}
            break
        if clock() - start_time >= time_limit_seconds:
            status, stop_reason = "INCOMPLETE", "time_cap_reached"
            break
        try:
            if getattr(alignment, "reference_name", None) != CHROMOSOME:
                raise ExtractionError("indexed chr2 fetch yielded a record on another reference")
            record, observations = alignment_record_and_witness(alignment, reference_dna)
            line = _json_bytes({"record_type": "alignment", **record})
        except Exception as exc:
            status, stop_reason = "FAILED", "alignment_record_error"
            failure = {"type": type(exc).__name__, "message": str(exc)[:500]}
            break
        if clock() - start_time >= time_limit_seconds:
            status, stop_reason = "INCOMPLETE", "time_cap_reached"
            break
        if payload_bytes + len(line) > payload_limit_bytes:
            status, stop_reason = "INCOMPLETE", "case_payload_cap_reached"
            break

        try:
            write_line(line)
        except Exception as exc:
            status, stop_reason = "FAILED", "records_output_error"
            failure = {"type": type(exc).__name__, "message": str(exc)[:500]}
            break
        record_count += 1
        payload_bytes += len(line)
        qname = record["qname"]
        if qname is not None:
            qnames[qname] += 1
        else:
            unnamed_qname_records += 1
        flag_counts[str(record["flag"])] += 1
        for flag_class, present in _flag_classes(record["flag"]).items():
            if present:
                class_counts[flag_class] += 1
        mapq_counts[str(record["mapping_quality"])] += 1
        cigar_counts[record["cigar_string"] or "*"] += 1
        cigar_operation_counts.update(record["cigar_operation_base_counts"])
        omitted_tag_occurrences += len(record["omitted_tag_names_only"])
        witness_totals.update(record["equals_reference_witness"])
        for position, reference_base, query_base in observations:
            witness_position_counts[position] += 1
            if reference_base != query_base:
                witness_conflict_counts[(position, reference_base, query_base)] += 1

        if record_count >= record_limit:
            status, stop_reason = "INCOMPLETE", "record_cap_reached"
            break
        if payload_bytes >= payload_limit_bytes:
            status, stop_reason = "INCOMPLETE", "case_payload_cap_reached"
            break

    return {
        "status": status,
        "stop_reason": stop_reason,
        "failure": failure,
        "region_iterator_eof_reached": eof_reached,
        "records_written": record_count,
        "unique_qnames": len(qnames),
        "duplicate_qname_alignment_records": sum(count - 1 for count in qnames.values()),
        "unnamed_qname_records": unnamed_qname_records,
        "flag_counts": dict(flag_counts),
        "alignment_class_counts": dict(class_counts),
        "mapping_quality_counts_including_zero": dict(mapq_counts),
        "cigar_string_counts": dict(cigar_counts),
        "cigar_operation_base_counts": dict(cigar_operation_counts),
        "omitted_tag_name_occurrences": omitted_tag_occurrences,
        "records_jsonl_bytes_including_header": payload_bytes,
        "equals_reference_witness": _witness_summary(
            witness_position_counts, witness_conflict_counts, dict(witness_totals)
        ),
    }


def stat_snapshot(path):
    """Return identity/size/time metadata only; never hash or read the file."""
    path = Path(path)
    try:
        info = path.stat()
    except OSError as exc:
        return {"path": str(path), "exists": False, "stat_error": str(exc)[:300]}
    return {
        "path": str(path),
        "exists": True,
        "size_bytes": info.st_size,
        "mtime_ns": info.st_mtime_ns,
        "ctime_ns": info.st_ctime_ns,
        "device": info.st_dev,
        "inode": info.st_ino,
    }


def _same_file_stat(before, after):
    keys = ("exists", "size_bytes", "mtime_ns", "ctime_ns", "device", "inode")
    return all(before.get(key) == after.get(key) for key in keys)


def validate_output_directory(output_dir):
    output_dir = Path(output_dir)
    if output_dir.is_symlink() or not output_dir.is_dir():
        raise ExtractionError("output directory must be an existing, non-symlink directory")
    if any(output_dir.iterdir()):
        raise FileExistsError("output directory must be empty; existing contents are preserved")
    return output_dir


def validate_bam_header(header):
    if not isinstance(header, dict):
        raise ExtractionError("BAM header is not a dictionary")
    if header.get("HD", {}).get("SO") != "coordinate":
        raise ExtractionError("BAM header must declare SO=coordinate")
    references = [item for item in header.get("SQ", []) if item.get("SN") == CHROMOSOME]
    if len(references) != 1 or references[0].get("LN") != CHR2_LENGTH:
        raise ExtractionError("BAM header chr2 length differs from the required 242,193,529")
    read_groups = header.get("RG", [])
    return {
        "sort_order": header["HD"]["SO"],
        "reference_count": len(header.get("SQ", [])),
        "chr2_length": references[0]["LN"],
        "read_groups": read_groups,
    }


def _header_text(alignment_file):
    text = getattr(alignment_file, "text", None)
    if text is None:
        text = str(alignment_file.header)
    if isinstance(text, bytes):
        raw = text
        decoded = text.decode("utf-8")
    else:
        decoded = str(text)
        raw = decoded.encode("utf-8")
    if len(raw) > MAX_HEADER_BYTES:
        raise ExtractionError("BAM header text exceeds the 128 KiB metadata cap")
    return decoded


def _candidate_index_path(bam_path):
    bam_path = Path(bam_path)
    candidates = (Path(str(bam_path) + ".bai"), bam_path.with_suffix(".bai"))
    return next((candidate for candidate in candidates if candidate.is_file()), candidates[0])


def _load_reference_json(path):
    path = Path(path)
    before = stat_snapshot(path)
    if not before.get("exists"):
        raise FileNotFoundError(f"reference JSON not found: {path}")
    if before["size_bytes"] > MAX_REFERENCE_JSON_BYTES:
        raise ExtractionError("reference JSON exceeds the 128 KiB input cap")
    raw = path.read_bytes()
    after = stat_snapshot(path)
    if len(raw) != before["size_bytes"] or not _same_file_stat(before, after):
        raise ExtractionError("reference JSON changed while it was read")
    reference = validate_reference_json(raw)
    reference["json_sha256"] = _sha256(raw)
    reference["path"] = str(path)
    reference["stat_before"] = before
    reference["stat_after"] = after
    return reference


def _manifest_template(bam_path, reference_json_path, bam_before, index_path, index_before):
    same_historical_bam = Path(bam_path).resolve() == HISTORICAL_BAM_PATH
    same_historical_index = same_historical_bam and Path(index_path).resolve() == Path(str(HISTORICAL_BAM_PATH) + ".bai")
    return {
        "schema_version": 1,
        "status": "FAILED",
        "region": {
            "chromosome": CHROMOSOME,
            "start_zero_based_inclusive": REGION_START,
            "end_zero_based_exclusive": REGION_END,
            "length_bp": REGION_LENGTH,
        },
        "source_bam": {
            "path": str(Path(bam_path)),
            "stat_before": bam_before,
            "stat_after": None,
            "opened_successfully": False,
            "whole_file_sha256_computed_this_run": False,
            "historical_sha256": HISTORICAL_BAM_SHA256 if same_historical_bam else None,
            "historical_size_bytes": HISTORICAL_BAM_SIZE_BYTES if same_historical_bam else None,
            "historical_size_matches_current_stat": (
                bam_before.get("size_bytes") == HISTORICAL_BAM_SIZE_BYTES if same_historical_bam else None
            ),
            "historical_sha256_note": (
                "Previously accepted whole-file custody hash; not recomputed in this regional extraction."
                if same_historical_bam else "No historical whole-file hash attached to this input path."
            ),
        },
        "source_index": {
            "path": str(Path(index_path)),
            "stat_before": index_before,
            "stat_after": None,
            "has_index_at_open": False,
            "historical_sha256": HISTORICAL_BAI_SHA256 if same_historical_index else None,
            "historical_size_bytes": HISTORICAL_BAI_SIZE_BYTES if same_historical_index else None,
            "historical_size_matches_current_stat": (
                index_before.get("size_bytes") == HISTORICAL_BAI_SIZE_BYTES if same_historical_index else None
            ),
            "historical_sha256_note": "Historical index hash only; not recomputed." if same_historical_index else None,
        },
        "reference_json": None,
        "source_header": None,
        "runtime": None,
        "region_fetch_started": False,
        "region_iteration": None,
        "records_file": {
            "name": RECORDS_FILENAME,
            "sha256": None,
            "bytes_including_jsonl_header": 0,
            "case_payload_cap_bytes": MAX_CASE_PAYLOAD_BYTES,
            "case_payload_definition": (
                "UTF-8 bytes in alignments.jsonl, including its header line and every retained alignment row. "
                "The JSONL is capped at 9 MiB; manifest.json is capped at 1 MiB, "
                "so combined retained output is at most 10 MiB."
            ),
        },
        "process_limits": {
            "threads": 1,
            "max_records": MAX_RECORDS,
            "max_case_payload_bytes": MAX_CASE_PAYLOAD_BYTES,
            "max_runtime_seconds": MAX_RUNTIME_SECONDS,
            "max_manifest_bytes": MAX_MANIFEST_BYTES,
            "max_total_retained_output_bytes": MAX_TOTAL_OUTPUT_BYTES,
        },
        "elapsed_seconds": None,
        "failure": None,
        "failures": [],
        "biological_inv_classification_emitted": False,
        "biological_negative_claimed": False,
        "claim_limits": CLAIM_LIMITS,
    }


def write_json_exclusive(path, value):
    path = Path(path)
    data = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    encoded = data.encode("utf-8")
    if len(encoded) > MAX_MANIFEST_BYTES:
        raise ExtractionError("manifest exceeds its separate 1 MiB metadata cap")
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(data)
    return len(encoded)


def run_extraction(
    bam_path,
    reference_json_path,
    output_dir,
    *,
    pysam_module,
    clock=time.monotonic,
    process_started_at=None,
):
    """Run the fixed regional fetch. Tests inject a tiny fake pysam-compatible reader."""
    output_dir = validate_output_directory(output_dir)
    bam_path = Path(bam_path)
    reference_json_path = Path(reference_json_path)
    records_path = output_dir / RECORDS_FILENAME
    manifest_path = output_dir / MANIFEST_FILENAME
    if records_path.exists() or manifest_path.exists():
        raise FileExistsError("refusing to overwrite an extraction output")

    started_at = clock() if process_started_at is None else process_started_at
    bam_before = stat_snapshot(bam_path)
    index_path = _candidate_index_path(bam_path)
    index_before = stat_snapshot(index_path)
    manifest = _manifest_template(bam_path, reference_json_path, bam_before, index_path, index_before)
    manifest["runtime"] = {
        "python_version": sys.version.split()[0],
        "pysam_version": getattr(pysam_module, "__version__", None),
    }
    header_line = _json_bytes({
        "record_type": "header",
        "schema_version": 1,
        "region": manifest["region"],
        "coordinate_system": "zero-based half-open",
    })
    records_digest = hashlib.sha256()
    collection = None
    source_header = None
    reference = None
    failures = []
    with records_path.open("xb") as handle:
        def write_line(line):
            written = handle.write(line)
            if written != len(line):
                raise OSError("short write to alignment JSONL")
            records_digest.update(line)

        write_line(header_line)
        try:
            reference = _load_reference_json(reference_json_path)
            if not index_before.get("exists"):
                raise ExtractionError("an existing BAI index is required; index creation is disabled")
            with pysam_module.AlignmentFile(
                str(bam_path), "rb", index_filename=str(index_path), require_index=True, threads=1
            ) as alignment_file:
                manifest["source_bam"]["opened_successfully"] = True
                if not alignment_file.has_index():
                    raise ExtractionError("indexed BAM is required; index creation is disabled")
                manifest["source_index"]["has_index_at_open"] = True
                header_dict = alignment_file.header.to_dict()
                header_summary = validate_bam_header(header_dict)
                header_text = _header_text(alignment_file)
                source_header = {**header_summary, "text": header_text}
                fetch_records = alignment_file.fetch(CHROMOSOME, REGION_START, REGION_END)
                manifest["region_fetch_started"] = True
                collection = collect_region_records(
                    fetch_records,
                    reference["dna"],
                    header_line=header_line,
                    write_line=write_line,
                    clock=clock,
                    started_at=started_at,
                    header_already_written=True,
                )
        except Exception as exc:
            failures.append({"type": type(exc).__name__, "message": str(exc)[:500]})

    bam_after = stat_snapshot(bam_path)
    index_after = stat_snapshot(index_path)
    reference_after = stat_snapshot(reference_json_path)
    if not _same_file_stat(bam_before, bam_after):
        failures.append({"type": "InputChanged", "message": "BAM stat changed during extraction"})
    if not _same_file_stat(index_before, index_after):
        failures.append({"type": "InputChanged", "message": "BAI stat changed during extraction"})
    if reference is not None and not _same_file_stat(reference["stat_before"], reference_after):
        failures.append({"type": "InputChanged", "message": "reference JSON stat changed during extraction"})

    records_file_stat = stat_snapshot(records_path)
    if records_file_stat.get("exists") and records_file_stat.get("size_bytes", 0) > MAX_CASE_PAYLOAD_BYTES:
        failures.append({"type": "OutputCapExceeded", "message": "JSONL output exceeded the 9 MiB case-payload cap"})
    if (
        collection is not None
        and records_file_stat.get("size_bytes") != collection["records_jsonl_bytes_including_header"]
    ):
        failures.append({"type": "OutputSizeMismatch", "message": "JSONL file size differs from streamed byte accounting"})
    manifest["source_bam"]["stat_after"] = bam_after
    manifest["source_index"]["stat_after"] = index_after
    if reference is not None:
        manifest["reference_json"] = {
            key: value for key, value in reference.items() if key != "dna"
        }
    manifest["source_header"] = source_header
    manifest["records_file"]["sha256"] = records_digest.hexdigest()
    manifest["records_file"]["bytes_including_jsonl_header"] = records_file_stat.get("size_bytes", 0)
    manifest["elapsed_seconds"] = max(0.0, clock() - started_at)
    if (
        manifest["elapsed_seconds"] >= MAX_RUNTIME_SECONDS
        and collection is not None
        and collection["status"] == "COMPLETE"
    ):
        collection["status"] = "INCOMPLETE"
        collection["stop_reason"] = "time_cap_reached_during_finalization"
    if collection is not None:
        manifest["region_iteration"] = collection
        manifest["status"] = collection["status"]
        if collection["failure"] is not None:
            failures.append(collection["failure"])
        if collection["status"] != "COMPLETE":
            manifest["biological_negative_claimed"] = False
    if failures:
        manifest["status"] = "FAILED"
        manifest["failure"] = failures[0]
        manifest["failures"] = failures
    if manifest["status"] == "COMPLETE" and collection is not None:
        manifest["case_region_eof_reached"] = collection["region_iterator_eof_reached"]
    else:
        manifest["case_region_eof_reached"] = bool(
            collection and collection["region_iterator_eof_reached"]
        )
    write_json_exclusive(manifest_path, manifest)
    return manifest, (0 if manifest["status"] == "COMPLETE" else 2)


def main(argv=None):
    process_started_at = time.monotonic()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bam", type=Path, required=True)
    parser.add_argument("--reference-json", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        import pysam
    except ImportError as exc:
        print(f"error: pysam is unavailable in this runtime: {exc}", file=sys.stderr)
        return 2
    try:
        manifest, exit_code = run_extraction(
            args.bam,
            args.reference_json,
            args.output_dir,
            pysam_module=pysam,
            process_started_at=process_started_at,
        )
    except (OSError, ValueError, TypeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({
        "status": manifest["status"],
        "records_written": (
            manifest["region_iteration"]["records_written"]
            if manifest["region_iteration"] is not None else 0
        ),
        "region_eof_reached": manifest["case_region_eof_reached"],
        "output_dir": str(args.output_dir),
    }, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
