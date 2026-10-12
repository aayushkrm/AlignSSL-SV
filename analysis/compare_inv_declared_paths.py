"""Bounded, conditional pure-inversion path comparison for the fixed HG002 case."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any


REPOSITORY = "jamesc99/INV-Benchmark"
PINNED_COMMIT = "ee77a2f336bf055e5234d7565389aafda56b85cd"
TREE_ENTRY_COUNT = 603
TREE_URL = (
    "https://api.github.com/repos/jamesc99/INV-Benchmark/git/trees/"
    f"{PINNED_COMMIT}?recursive=1"
)
RAW_FILE_BASE = (
    "https://raw.githubusercontent.com/jamesc99/INV-Benchmark/"
    f"{PINNED_COMMIT}/"
)

CALLER_DIRECTORY = "data_zenodo/inv_call_5samples/30x/hg002/"
TRUTH_DIRECTORY = "data_zenodo/truvari_ref_vcf/HG002/"
CALLERS = ("cutesv2", "severus", "sniffles2", "svim", "svisionpro")
PLATFORMS = ("ont", "pb")
ALIGNERS = ("minimap2", "vacmap")
CALL_GROUP = "long_read_caller_panel"
CONTROL_GROUP = "supplemental_short_read_controls"
TRUTH_GROUP = "truth_set"

CHROMOSOME = "chr2"
TARGET_POS = 240685775
TARGET_END = 240688980
TARGET_LENGTH = TARGET_END - TARGET_POS
REFERENCE_GENOME = "hg38"
REFERENCE_START = 240675000
REFERENCE_END = 240704000
REFERENCE_LENGTH = REFERENCE_END - REFERENCE_START
DECLARED_CHR2_LENGTH = 242193529
REFERENCE_JSON_MAX_BYTES = 128 * 1024

MODE_PAIRS = (("A", "A"), ("A", "B"), ("B", "A"), ("B", "B"))
MODE_PAIR_KEYS = tuple(f"truth_{truth}_call_{call}" for truth, call in MODE_PAIRS)
CLAIM_LIMITS = (
    "An exact match applies only to the declared pure-INV model, the stated UCSC hg38 reference window, and the tested coordinate-mode pair.",
    "It does not establish the original caller FASTA identity, haplotype sequence or phase, dosage, carrier genotype, copy state, or caller-input identity.",
    "These nine declarations are not independent biological events, and this fixed case is development data. A GT value, including 0/0, is retained as metadata and is not a carrier or detection conclusion.",
    "Symbolic INV may encode partial-junction evidence; reverse-complement substitution is a conditional full-context model, not an observed allele.",
    "If every eligible comparison differs, reject this exact normalization explanation only; do not infer that all original structures were missed or that a new architecture will rescue them.",
    "Any major positive conclusion needs independent review; later evidence should inspect qualified molecules, alignments, and candidate evidence.",
)


class DiagnosticError(ValueError):
    """Raised when an input falls outside the frozen diagnostic contract."""


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _reject_constant(value: str) -> None:
    raise DiagnosticError(f"non-finite JSON number is not allowed: {value}")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DiagnosticError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def _parse_json(raw: bytes, label: str) -> Any:
    try:
        return json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DiagnosticError(f"{label} is not valid UTF-8 JSON: {exc}") from exc


def _expected_source_paths() -> dict[str, set[str]]:
    caller_paths = {
        CALLER_DIRECTORY + f"inv_{caller}_{platform}_{aligner}.vcf"
        for caller in CALLERS
        for platform in PLATFORMS
        for aligner in ALIGNERS
    }
    control_paths = {
        CALLER_DIRECTORY + "gridss2_inv.vcf",
        CALLER_DIRECTORY + "manta_inv.vcf",
    }
    truth_paths = {
        TRUTH_DIRECTORY + "HG002_T2Tv1.1_asm_ref_2aligners.merged.vcf.gz",
        TRUTH_DIRECTORY + "HG002_T2Tv1.1_asm_ref_2aligners.merged.vcf_Tier1.vcf.gz",
        TRUTH_DIRECTORY + "HG002_T2Tv1.1_asm_ref_2aligners.merged.vcf_Tier2.vcf.gz",
    }
    return {
        CALL_GROUP: caller_paths,
        CONTROL_GROUP: control_paths,
        TRUTH_GROUP: truth_paths,
    }


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise DiagnosticError(message)


def _validate_source_identity(source: dict[str, Any]) -> None:
    path = source.get("path")
    _require(isinstance(path, str), "source path must be a string")
    _require(source.get("download_status") == "VALIDATED", f"source not validated: {path}")
    _require(source.get("http_status") == 200, f"source HTTP status is not 200: {path}")
    _require(_is_int(source.get("size")) and source["size"] > 0, f"invalid source size: {path}")
    _require(source.get("downloaded_bytes") == source.get("size"), f"download size mismatch: {path}")
    _require(bool(re.fullmatch(r"[0-9a-f]{64}", str(source.get("sha256", "")))), f"invalid SHA-256: {path}")
    _require(bool(re.fullmatch(r"[0-9a-f]{40}", str(source.get("git_blob_sha1", "")))), f"invalid Git blob SHA-1: {path}")
    _require(source.get("git_blob_sha1_verified") is True, f"Git blob identity is not verified: {path}")
    _require(
        source.get("git_blob_sha1_computed") == source.get("git_blob_sha1"),
        f"computed Git blob SHA-1 does not match declaration: {path}",
    )
    _require(source.get("raw_url") == RAW_FILE_BASE + path, f"source URL does not match pinned path: {path}")


def _header_chr2_length(source: dict[str, Any]) -> int:
    summary = source.get("vcf_summary")
    _require(isinstance(summary, dict), f"missing VCF summary: {source.get('path')}")
    headers = summary.get("relevant_headers")
    _require(isinstance(headers, list), f"missing VCF headers: {source.get('path')}")
    lengths: list[int] = []
    for line in headers:
        if not isinstance(line, str) or not line.startswith("##contig=<") or not line.endswith(">"):
            continue
        attrs: dict[str, str] = {}
        for item in line[len("##contig=<") : -1].split(","):
            key, sep, value = item.partition("=")
            if sep:
                attrs[key] = value
        if attrs.get("ID") == CHROMOSOME:
            raw_length = attrs.get("length", "")
            _require(raw_length.isdecimal(), f"invalid chr2 length in header: {source.get('path')}")
            lengths.append(int(raw_length))
    _require(len(lengths) == 1, f"expected one chr2 contig header: {source.get('path')}")
    _require(lengths[0] == DECLARED_CHR2_LENGTH, f"unexpected chr2 length in header: {source.get('path')}")
    return lengths[0]


def _validate_manifest_pin(manifest: Any) -> list[dict[str, Any]]:
    _require(isinstance(manifest, dict), "manifest root must be an object")
    _require(manifest.get("schema_version") == 1, "unexpected manifest schema version")
    _require(manifest.get("status") == "COMPLETE", "source manifest is not complete")

    case = manifest.get("case")
    _require(isinstance(case, dict), "manifest case metadata is missing")
    expected_case = {
        "chromosome": CHROMOSOME,
        "start": TARGET_POS,
        "end": TARGET_END,
        "reported_length_bp": TARGET_LENGTH,
        "supplement_label": "GRCh38/hg38",
    }
    for key, expected in expected_case.items():
        _require(case.get(key) == expected, f"manifest fixed-case pin mismatch: {key}")
    _require(
        case.get("coordinate_build_status") == "UNKNOWN_PENDING_INDEPENDENT_HEADER_AND_RECORD_REVIEW",
        "manifest must preserve the unknown original build identity",
    )
    _require(
        case.get("coordinate_convention_status") == "UNKNOWN; coordinates are used verbatim without conversion",
        "manifest must preserve the unknown original coordinate convention",
    )

    provenance = manifest.get("provenance")
    _require(isinstance(provenance, dict), "manifest provenance is missing")
    for key, expected in {
        "repository": REPOSITORY,
        "commit": PINNED_COMMIT,
        "tree_url": TREE_URL,
        "tree_entry_count_expected": TREE_ENTRY_COUNT,
        "raw_file_base": RAW_FILE_BASE,
    }.items():
        _require(provenance.get(key) == expected, f"manifest provenance pin mismatch: {key}")

    retrieval = manifest.get("retrieval")
    _require(isinstance(retrieval, dict), "manifest retrieval metadata is missing")
    _require(retrieval.get("tree_truncated") is False, "pinned Git tree is truncated")
    _require(retrieval.get("tree_entries") == TREE_ENTRY_COUNT, "Git tree entry count mismatch")
    _require(
        bool(re.fullmatch(r"[0-9a-f]{64}", str(retrieval.get("whole_source_set_sha256", "")))),
        "invalid whole source-set SHA-256",
    )

    sources = manifest.get("sources")
    _require(isinstance(sources, list) and len(sources) == 25, "expected exactly 25 pinned source entries")
    expected_paths = _expected_source_paths()
    observed_paths: dict[str, set[str]] = {group: set() for group in expected_paths}
    total_size = 0
    for source in sources:
        _require(isinstance(source, dict), "source entry must be an object")
        group = source.get("group")
        _require(group in observed_paths, f"unexpected source group: {group}")
        _validate_source_identity(source)
        path = source["path"]
        _require(path not in observed_paths[group], f"duplicate source path: {path}")
        observed_paths[group].add(path)
        _header_chr2_length(source)
        total_size += source["size"]
        summary = source["vcf_summary"]
        _require(isinstance(summary.get("nearby_records"), list), f"nearby record list missing: {path}")
        _require(isinstance(summary.get("spanning_records"), list), f"spanning record list missing: {path}")

    for group, expected in expected_paths.items():
        _require(observed_paths[group] == expected, f"source path set mismatch for group {group}")
    _require(total_size == retrieval.get("declared_source_bytes"), "declared source byte total mismatch")
    _require(total_size == retrieval.get("source_bytes_transferred"), "transferred source byte total mismatch")
    return sources


def _parse_record(
    record: Any,
    *,
    source: dict[str, Any],
    bucket: str,
    bucket_index: int,
) -> dict[str, Any]:
    path = source["path"]
    _require(isinstance(record, dict), f"record entry must be an object: {path}")
    fields = record.get("fields")
    _require(
        isinstance(fields, list) and len(fields) >= 10 and all(isinstance(x, str) for x in fields),
        f"record must have VCF fields and at least one sample: {path}",
    )
    chromosome, raw_pos, record_id, ref, alt, qual, filt, info = fields[:8]
    _require(chromosome == CHROMOSOME, f"selected record is not on chr2: {path}")
    _require(raw_pos.isdecimal(), f"invalid VCF POS: {path}")
    position = int(raw_pos)
    _require(position > 0, f"VCF POS must be positive: {path}")
    _require(alt == "<INV>", f"unsupported or ambiguous ALT {alt!r}: {path}")
    _require(record.get("chromosome") == chromosome, f"record chromosome summary mismatch: {path}")
    _require(record.get("position") == position, f"record POS summary mismatch: {path}")
    _require(record.get("id") == record_id, f"record ID summary mismatch: {path}")
    _require(record.get("ref") == ref, f"record REF summary mismatch: {path}")
    _require(record.get("alt") == alt, f"record ALT summary mismatch: {path}")
    _require(record.get("qual") == qual, f"record QUAL summary mismatch: {path}")
    _require(record.get("filter") == filt, f"record FILTER summary mismatch: {path}")
    _require(record.get("info") == info, f"record INFO summary mismatch: {path}")

    raw_record = record.get("raw_record")
    _require(
        isinstance(raw_record, str) and raw_record.rstrip("\r\n").split("\t") == fields,
        f"raw VCF row mismatch: {path}",
    )
    _require(record.get("format_and_samples") == fields[8:], f"FORMAT/sample summary mismatch: {path}")
    _require(_is_int(record.get("line_number")) and record["line_number"] > 0, f"invalid record line number: {path}")

    end_values: list[str] = []
    for item in info.split(";"):
        key, sep, value = item.partition("=")
        if key == "END" and sep:
            end_values.append(value)
    _require(len(end_values) == 1 and end_values[0].isdecimal(), f"symbolic INV requires one integer INFO/END: {path}")
    end = int(end_values[0])
    _require(record.get("end_positions") == [end], f"record END summary mismatch: {path}")
    _require(end > position, f"INV interval is zero-width or reversed: {path}")

    format_keys = fields[8].split(":")
    _require("GT" in format_keys, f"selected record does not retain a GT field: {path}")
    gt_index = format_keys.index("GT")
    genotypes: list[str] = []
    for sample in fields[9:]:
        sample_values = sample.split(":")
        _require(gt_index < len(sample_values), f"selected record has a truncated GT sample: {path}")
        genotypes.append(sample_values[gt_index])

    key = f"{path}#bucket={bucket}:index={bucket_index}:line={record['line_number']}"
    return {
        "record_key": key,
        "source": {
            "group": source["group"],
            "path": path,
            "size": source["size"],
            "sha256": source["sha256"],
            "git_blob_sha1": source["git_blob_sha1"],
        },
        "selection": {"bucket": bucket, "bucket_index": bucket_index, "line_number": record["line_number"]},
        "chromosome": chromosome,
        "position": position,
        "end": end,
        "id": record_id,
        "ref": ref,
        "alt": alt,
        "qual": qual,
        "filter": filt,
        "info": info,
        "format": fields[8],
        "sample_columns": fields[9:],
        "genotypes": genotypes,
        "raw_fields": fields,
        "raw_record": raw_record,
    }


def _records_for_source(source: dict[str, Any]) -> list[dict[str, Any]]:
    summary = source["vcf_summary"]
    parsed: list[dict[str, Any]] = []
    for bucket in ("nearby_records", "spanning_records"):
        for index, record in enumerate(summary[bucket]):
            parsed.append(
                _parse_record(
                    record,
                    source=source,
                    bucket=bucket,
                    bucket_index=index,
                )
            )
    return parsed


def _validate_selected_records(
    sources: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    calls: list[dict[str, Any]] = []
    near_count = 0
    span_count = 0
    tier1_record: dict[str, Any] | None = None
    merged_record: dict[str, Any] | None = None
    tier2_records: list[dict[str, Any]] = []

    for source in sources:
        records = _records_for_source(source)
        if source["group"] == CALL_GROUP:
            calls.extend(records)
            near_count += sum(record["selection"]["bucket"] == "nearby_records" for record in records)
            span_count += sum(record["selection"]["bucket"] == "spanning_records" for record in records)
        elif source["group"] == CONTROL_GROUP:
            _require(not records, f"unexpected short-read control record in fixed selection: {source['path']}")
        else:
            matches = [
                record
                for record in records
                if record["chromosome"] == CHROMOSOME
                and record["position"] == TARGET_POS
                and record["end"] == TARGET_END
                and record["alt"] == "<INV>"
            ]
            path = source["path"]
            if path.endswith("merged.vcf.gz"):
                _require(len(matches) == 1, "merged truth must contain exactly one fixed target")
                merged_record = matches[0]
            elif path.endswith("merged.vcf_Tier1.vcf.gz"):
                _require(len(matches) == 1, "Tier 1 truth must contain exactly one fixed target")
                tier1_record = matches[0]
            elif path.endswith("merged.vcf_Tier2.vcf.gz"):
                tier2_records.extend(matches)

    _require(near_count == 1 and span_count == 8 and len(calls) == 9, "expected one nearby and eight spanning caller declarations")
    _require(tier1_record is not None and merged_record is not None, "fixed truth target missing from merged or Tier 1 set")
    _require(not tier2_records, "fixed target unexpectedly appears in Tier 2 truth")
    _require(tier1_record["raw_record"] == merged_record["raw_record"], "merged and Tier 1 target records are not exact duplicates")
    _require(tier1_record["genotypes"] == ["0/1"], "Tier 1 target must retain the declared GT 0/1")
    _require(tier1_record["alt"] == "<INV>", "Tier 1 target is not a symbolic pure INV")
    return tier1_record, merged_record, calls


def validate_reference_document(document: Any) -> tuple[str, dict[str, Any]]:
    _require(isinstance(document, dict), "reference JSON root must be an object")
    for key, expected in {"genome": REFERENCE_GENOME, "chrom": CHROMOSOME}.items():
        _require(document.get(key) == expected, f"reference metadata mismatch: {key}")
    for key, expected in {"start": REFERENCE_START, "end": REFERENCE_END}.items():
        _require(_is_int(document.get(key)), f"reference metadata must be an integer: {key}")
        _require(document[key] == expected, f"reference metadata mismatch: {key}")
    dna = document.get("dna")
    _require(isinstance(dna, str), "reference JSON must contain a DNA string")
    _require(len(dna) == REFERENCE_LENGTH, "reference DNA length is not the frozen 29,000 bases")
    invalid = sorted(set(dna) - set("ACGTacgt"))
    _require(not invalid, f"reference DNA contains non-ACGT characters: {''.join(invalid)!r}")

    base_counts = Counter(dna.upper())
    case_counts = {
        "uppercase_bases": sum(character.isupper() for character in dna),
        "lowercase_bases": sum(character.islower() for character in dna),
    }
    metadata = {
        "genome": REFERENCE_GENOME,
        "chromosome": CHROMOSOME,
        "start": REFERENCE_START,
        "end": REFERENCE_END,
        "length": REFERENCE_LENGTH,
        "base_counts_casefolded": {base: base_counts.get(base, 0) for base in "ACGT"},
        "case_counts": case_counts,
        "original_caller_fasta_identity": "UNKNOWN",
    }
    return dna.upper(), metadata


def interval_for_mode(position: int, end: int, mode: str) -> tuple[int, int]:
    _require(_is_int(position) and _is_int(end), "POS and END must be integers")
    _require(position > 0 and end > position, "POS/END interval is zero-width or reversed")
    if mode == "A":
        start0, end0 = position, end
    elif mode == "B":
        start0, end0 = position - 1, end - 1
    else:
        raise DiagnosticError(f"unknown coordinate mode: {mode}")
    _require(
        REFERENCE_START <= start0 < end0 <= REFERENCE_END,
        f"interval [{start0},{end0}) is outside the fetched reference window",
    )
    return start0, end0


def invert_interval_in_context(sequence: str, window_start: int, start: int, end: int) -> str:
    _require(_is_int(window_start), "reference window start must be an integer")
    _require(_is_int(start) and _is_int(end), "inversion endpoints must be integers")
    local_start, local_end = start - window_start, end - window_start
    _require(0 <= local_start < local_end <= len(sequence), "inversion interval is outside the reference context")
    segment = sequence[local_start:local_end]
    _require(not (set(segment.upper()) - set("ACGT")), "inversion segment contains non-ACGT bases")
    reverse_complement = segment.upper().translate(str.maketrans("ACGT", "TGCA"))[::-1]
    return sequence[:local_start].upper() + reverse_complement + sequence[local_end:].upper()


def compare_full_contexts(reference: str, truth_alt: str, call_alt: str) -> dict[str, Any]:
    _require(len(reference) == len(truth_alt) == len(call_alt), "full-context strings must have equal lengths")
    exact_equal = truth_alt == call_alt
    truth_equals_reference = truth_alt == reference
    call_equals_reference = call_alt == reference
    return {
        "exact_string_equal": exact_equal,
        "mismatched_positions": sum(left != right for left, right in zip(truth_alt, call_alt)),
        "truth_alternate_equals_reference": truth_equals_reference,
        "call_alternate_equals_reference": call_equals_reference,
        "equivalence_claim_eligible": exact_equal and not truth_equals_reference and not call_equals_reference,
    }


def build_diagnostic(
    manifest: Any,
    reference_document: Any,
    *,
    manifest_sha256: str,
    reference_json_sha256: str,
) -> dict[str, Any]:
    sources = _validate_manifest_pin(manifest)
    truth_record, merged_truth_record, call_records = _validate_selected_records(sources)
    reference_sequence, reference_metadata = validate_reference_document(reference_document)

    truth_paths = {
        mode: interval_for_mode(truth_record["position"], truth_record["end"], mode)
        for mode in ("A", "B")
    }
    truth_alternates = {
        mode: invert_interval_in_context(reference_sequence, REFERENCE_START, *interval)
        for mode, interval in truth_paths.items()
    }
    truth_metadata = {
        "source": truth_record["source"],
        "record_key": truth_record["record_key"],
        "chromosome": truth_record["chromosome"],
        "position": truth_record["position"],
        "end": truth_record["end"],
        "length_bp": truth_record["end"] - truth_record["position"],
        "id": truth_record["id"],
        "ref": truth_record["ref"],
        "alt": truth_record["alt"],
        "qual": truth_record["qual"],
        "filter": truth_record["filter"],
        "info": truth_record["info"],
        "format": truth_record["format"],
        "sample_columns": truth_record["sample_columns"],
        "genotypes": truth_record["genotypes"],
        "raw_gt_values": truth_record["genotypes"],
        "raw_record": truth_record["raw_record"],
        "merged_duplicate_verified": True,
        "merged_duplicate": {
            "source": merged_truth_record["source"],
            "record_key": merged_truth_record["record_key"],
            "raw_record_sha256": _sha256(merged_truth_record["raw_record"].encode("utf-8")),
        },
    }

    output_calls: list[dict[str, Any]] = []
    comparisons: list[dict[str, Any]] = []
    for call in call_records:
        call_paths = {
            mode: interval_for_mode(call["position"], call["end"], mode)
            for mode in ("A", "B")
        }
        call_alternates = {
            mode: invert_interval_in_context(reference_sequence, REFERENCE_START, *interval)
            for mode, interval in call_paths.items()
        }
        output_calls.append(
            {
                "record_key": call["record_key"],
                "source": call["source"],
                "selection": call["selection"],
                "chromosome": call["chromosome"],
                "position": call["position"],
                "end": call["end"],
                "id": call["id"],
                "ref": call["ref"],
                "alt": call["alt"],
                "qual": call["qual"],
                "filter": call["filter"],
                "filter_raw": call["filter"],
                "info": call["info"],
                "format": call["format"],
                "sample_columns": call["sample_columns"],
                "genotypes": call["genotypes"],
                "raw_gt_values": call["genotypes"],
                "raw_fields": call["raw_fields"],
                "raw_record": call["raw_record"],
                "carrier_or_detection_interpretation": "NOT_ASSESSED",
            }
        )
        for truth_mode, call_mode in MODE_PAIRS:
            truth_alt = truth_alternates[truth_mode]
            call_alt = call_alternates[call_mode]
            metrics = compare_full_contexts(reference_sequence, truth_alt, call_alt)
            mode_pair_key = f"truth_{truth_mode}_call_{call_mode}"
            comparisons.append(
                {
                    "comparison_key": f"{call['record_key']}::{mode_pair_key}",
                    "call_record_key": call["record_key"],
                    "mode_pair_key": mode_pair_key,
                    "truth_mode": truth_mode,
                    "call_mode": call_mode,
                    "truth_interval_zero_based_half_open": list(truth_paths[truth_mode]),
                    "call_interval_zero_based_half_open": list(call_paths[call_mode]),
                    "truth_alternate_sha256": _sha256(truth_alt.encode("ascii")),
                    "call_alternate_sha256": _sha256(call_alt.encode("ascii")),
                    **metrics,
                    "conditional_claim_limit": CLAIM_LIMITS[0],
                }
            )

    source_groups = Counter(source["group"] for source in sources)
    result = {
        "diagnostic": "conditional_pure_inversion_path_equivalence",
        "schema_version": 1,
        "inputs": {
            "manifest_json_sha256": manifest_sha256,
            "reference_json_sha256": reference_json_sha256,
            "whole_source_set_sha256": manifest["retrieval"]["whole_source_set_sha256"],
        },
        "provenance_pin": {
            "repository": manifest["provenance"]["repository"],
            "commit": manifest["provenance"]["commit"],
            "tree_url": manifest["provenance"]["tree_url"],
            "tree_entry_count": manifest["retrieval"]["tree_entries"],
            "source_count": len(sources),
            "source_group_counts": dict(sorted(source_groups.items())),
            "chr2_declared_length_bp_all_sources": DECLARED_CHR2_LENGTH,
            "original_caller_fasta_identity": "UNKNOWN",
        },
        "case": {
            "chromosome": CHROMOSOME,
            "truth_position": TARGET_POS,
            "truth_end": TARGET_END,
            "truth_length_bp": TARGET_LENGTH,
            "published_coordinate_label": manifest["case"]["supplement_label"],
            "original_coordinate_build_status": manifest["case"]["coordinate_build_status"],
            "original_coordinate_convention_status": manifest["case"]["coordinate_convention_status"],
            "reference_window": {
                "genome": REFERENCE_GENOME,
                "chromosome": CHROMOSOME,
                "start": REFERENCE_START,
                "end": REFERENCE_END,
                "length": REFERENCE_LENGTH,
            },
            "reference": {
                **reference_metadata,
                "json_sha256": reference_json_sha256,
                "dna_sha256_casefolded": _sha256(reference_sequence.encode("ascii")),
            },
        },
        "model": {
            "alternate_construction": "replace interval in the same full 29,000-base reference context with its reverse complement",
            "coordinate_modes": {
                "A": "[POS, END)",
                "B": "[POS-1, END-1)",
            },
            "mode_pair_keys": list(MODE_PAIR_KEYS),
            "claim_limits": list(CLAIM_LIMITS),
        },
        "truth": truth_metadata,
        "call_record_count": len(output_calls),
        "comparison_count": len(comparisons),
        "carrier_recovery_claimed": False,
        "call_records": output_calls,
        "comparisons": comparisons,
    }
    _require(len(comparisons) == 36, "internal error: expected 36 fixed comparisons")
    return result


def build_from_json_bytes(manifest_bytes: bytes, reference_bytes: bytes) -> dict[str, Any]:
    _require(len(reference_bytes) <= REFERENCE_JSON_MAX_BYTES, "reference JSON exceeds the 128 KiB input cap")
    manifest = _parse_json(manifest_bytes, "manifest")
    reference_document = _parse_json(reference_bytes, "reference JSON")
    return build_diagnostic(
        manifest,
        reference_document,
        manifest_sha256=_sha256(manifest_bytes),
        reference_json_sha256=_sha256(reference_bytes),
    )


def read_bounded_file(path: str | Path, max_bytes: int) -> bytes:
    source_path = Path(path)
    _require(_is_int(max_bytes) and max_bytes >= 0, "maximum input size must be a nonnegative integer")
    _require(source_path.stat().st_size <= max_bytes, f"input exceeds the {max_bytes}-byte cap: {source_path}")
    data = source_path.read_bytes()
    _require(len(data) <= max_bytes, f"input exceeds the {max_bytes}-byte cap: {source_path}")
    return data


def write_json_exclusive(path: str | Path, value: Any) -> None:
    destination = Path(path)
    payload = json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
    try:
        with destination.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(payload)
    except FileExistsError as exc:
        raise DiagnosticError(f"refusing to overwrite existing output: {destination}") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--reference-json", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        manifest_bytes = args.manifest.read_bytes()
        reference_bytes = read_bounded_file(args.reference_json, REFERENCE_JSON_MAX_BYTES)
        result = build_from_json_bytes(manifest_bytes, reference_bytes)
        write_json_exclusive(args.output, result)
    except (OSError, ValueError, TypeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
