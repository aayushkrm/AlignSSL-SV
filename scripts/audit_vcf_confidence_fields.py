"""Audit declared and observed VCF genotype-confidence fields without scoring calls.

The default scan stops after the header.  Requested record scans are bounded by
both a record count and decompressed-byte limits; neither mode computes a hash
of the complete source file or interprets confidence values as calibrated.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import re
from pathlib import Path
from typing import BinaryIO, Iterable


MAX_HEADER_BYTES = 1 * 1024 * 1024
MAX_RECORDS = 100_000
MAX_RECORD_BYTES = 1 * 1024 * 1024
MAX_TOTAL_RECORD_BYTES = 64 * 1024 * 1024
MAX_SAMPLES = 10_000
MAX_SAMPLE_RECORD_OBSERVATIONS = 2_000_000
MAX_HEADER_AUDIT_JSON_BYTES = 16 * 1024 * 1024
MAX_HEADER_OBJECTS = 1_000
CONFIDENCE_FIELDS = ("GQ", "GP", "PL", "GL")
REPORTED_FORMAT_FIELDS = ("GT", *CONFIDENCE_FIELDS)
GT_PATTERN = re.compile(r"(?:\.|[0-9]+)(?:[/|](?:\.|[0-9]+))*\Z")
NUMBER_PATTERN = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?\Z")
CANONICAL_CONTIG_IDS = {
    *(str(index) for index in range(1, 23)),
    *(f"chr{index}" for index in range(1, 23)),
    "X", "Y", "M", "MT", "chrX", "chrY", "chrM", "chrMT",
}


def _decode_quoted(value: str) -> str:
    if not value.startswith('"'):
        if '"' in value:
            raise ValueError("quote inside an unquoted structured-header value")
        return value
    if len(value) < 2 or not value.endswith('"'):
        raise ValueError("unterminated quoted structured-header value")
    decoded: list[str] = []
    index = 1
    while index < len(value) - 1:
        char = value[index]
        if char == "\\" and index + 1 < len(value) - 1:
            following = value[index + 1]
            if following in ('"', "\\"):
                decoded.append(following)
                index += 2
                continue
            decoded.extend((char, following))
            index += 2
            continue
        if char == '"':
            raise ValueError("unescaped quote inside structured-header value")
        decoded.append(char)
        index += 1
    return "".join(decoded)


def parse_structured_attributes(value: str) -> dict[str, str]:
    """Parse VCF angle-bracket attributes, splitting commas outside quotes."""
    if not value.startswith("<") or not value.endswith(">"):
        raise ValueError("expected an angle-bracket structured header")
    body = value[1:-1]
    parts: list[str] = []
    start = 0
    quoted = False
    escaped = False
    for index, char in enumerate(body):
        if escaped:
            escaped = False
        elif quoted and char == "\\":
            escaped = True
        elif char == '"':
            quoted = not quoted
        elif char == "," and not quoted:
            parts.append(body[start:index])
            start = index + 1
    if quoted or escaped:
        raise ValueError("unterminated escape or quote in structured header")
    parts.append(body[start:])

    attributes: dict[str, str] = {}
    for part in parts:
        key, separator, raw_value = part.partition("=")
        if not separator or not key or key in attributes:
            raise ValueError("malformed or duplicate structured-header attribute")
        attributes[key] = _decode_quoted(raw_value)
    return attributes


def _new_sample_stats() -> dict:
    return dict(total_records=0, completeGT=0, missingGT=0, missingrecord=0,
                malformedGT=0, invalidGT=0, out_of_scope_non_diploid_GT=0)


def _new_field_stats() -> dict:
    return dict(numeric_entries=0, numeric_values=0, missing=0, malformed=0)


def _parse_numbers(tag: str, value: str) -> list[float] | None:
    tokens = value.split(",")
    if tag == "GQ" and len(tokens) != 1:
        return None
    if not all(NUMBER_PATTERN.fullmatch(token) for token in tokens):
        return None
    try:
        numbers = [float(token) for token in tokens]
    except ValueError:
        return None
    if not numbers or not all(math.isfinite(number) for number in numbers):
        return None
    return numbers


def _allele_index_exceeds_alt(allele: str, alt_count: int) -> bool:
    index = allele.lstrip("0") or "0"
    limit = str(alt_count)
    return len(index) > len(limit) or len(index) == len(limit) and index > limit


def _observe_gt(value: str, alt_count: int) -> tuple[str, int | None]:
    if not GT_PATTERN.fullmatch(value):
        return "malformed", None
    if value == ".":
        return "missing", None
    alleles = re.split(r"[/|]", value)
    ploidy = len(alleles)
    if any(allele != "." and _allele_index_exceeds_alt(allele, alt_count)
           for allele in alleles):
        return "invalid_allele_index", ploidy
    if any(allele == "." for allele in alleles):
        return "missing", ploidy
    return "complete", ploidy


def _parse_header_lines(
    header_lines: Iterable[str], add_missing_line_ending: bool = True
) -> tuple[dict, list[str], int, int]:
    header = {"sources": [], "references": [],
              "formats": {field: [] for field in REPORTED_FORMAT_FIELDS}}
    consumed = 0
    line_number = 0
    samples: list[str] | None = None
    header_hash = hashlib.sha256()
    contig_hash = hashlib.sha256()
    contig_count = contigs_with_m5 = 0
    canonical_contigs: list[dict] = []
    for supplied_line in header_lines:
        if not isinstance(supplied_line, str):
            raise ValueError("in-memory header_lines entries must be strings")
        encoded = supplied_line.encode("utf-8")
        if add_missing_line_ending and not supplied_line.endswith(("\n", "\r")):
            encoded += b"\n"
        if consumed + len(encoded) > MAX_HEADER_BYTES:
            raise ValueError(f"VCF header exceeds {MAX_HEADER_BYTES} bytes")
        consumed += len(encoded)
        header_hash.update(encoded)
        line_number += 1
        line = supplied_line.rstrip("\r\n")
        if "\n" in line or "\r" in line:
            raise ValueError("in-memory header_lines entry contains multiple lines")

        if line.startswith("#CHROM"):
            if samples is not None:
                raise ValueError("duplicate #CHROM header")
            columns = line.split("\t")
            required = ["#CHROM", "POS", "ID", "REF", "ALT", "QUAL", "FILTER", "INFO"]
            if columns[:8] != required or len(columns) >= 9 and columns[8] != "FORMAT":
                raise ValueError("malformed #CHROM header columns")
            samples = columns[9:] if len(columns) >= 10 else []
            if len(samples) > MAX_SAMPLES:
                raise ValueError(f"sample count exceeds safety limit ({MAX_SAMPLES})")
            if len(set(samples)) != len(samples):
                raise ValueError("duplicate sample IDs in #CHROM header")
            continue

        if samples is not None:
            raise ValueError("in-memory header_lines contains data after #CHROM")

        if not line.startswith("#"):
            raise ValueError("VCF data appears before the #CHROM header")
        if line.startswith("##source="):
            header["sources"].append(line.partition("=")[2])
        elif line.startswith("##reference="):
            header["references"].append(line.partition("=")[2])
        elif line.startswith("##FORMAT="):
            raw_definition = line.partition("=")[2]
            attributes = parse_structured_attributes(raw_definition)
            identifier = attributes.get("ID")
            if not identifier:
                raise ValueError("FORMAT declaration lacks ID")
            if identifier in REPORTED_FORMAT_FIELDS:
                header["formats"][identifier].append(dict(
                    Number=attributes.get("Number"), Type=attributes.get("Type"),
                    Description=attributes.get("Description"), attributes=attributes,
                    raw_header_line=line))
        elif line.startswith("##contig="):
            attributes = parse_structured_attributes(line.partition("=")[2])
            folded = {key.casefold(): value for key, value in attributes.items()}
            m5 = folded.get("m5", folded.get("md5"))
            identifier = attributes.get("ID")
            contig_hash.update(encoded)
            contig_count += 1
            contigs_with_m5 += bool(m5)
            if identifier in CANONICAL_CONTIG_IDS:
                canonical_contigs.append(dict(id=identifier, m5=m5, m5_available=bool(m5)))
    if samples is None:
        raise ValueError("VCF lacks #CHROM header within the header byte limit")
    header["source_header_sha256"] = header_hash.hexdigest()
    header["source_header_sha256_scope"] = (
        "UTF-8 header lines through #CHROM; LF added to in-memory lines lacking a line ending"
        if add_missing_line_ending else "Exact UTF-8 source header bytes through #CHROM"
    )
    header["contig_lines_sha256"] = contig_hash.hexdigest()
    header["contig_lines_sha256_scope"] = header["source_header_sha256_scope"]
    header["contig_m5_availability"] = dict(
        contig_count=contig_count, with_m5=contigs_with_m5,
        without_m5=contig_count - contigs_with_m5, canonical_subset=canonical_contigs)
    return header, samples, consumed, line_number


def _read_header(stream: BinaryIO) -> tuple[dict, list[str], int, int]:
    lines: list[str] = []
    consumed = 0
    while consumed <= MAX_HEADER_BYTES:
        raw_line = stream.readline(MAX_HEADER_BYTES - consumed + 1)
        if not raw_line:
            break
        if len(raw_line) > MAX_HEADER_BYTES - consumed:
            raise ValueError(f"VCF header exceeds {MAX_HEADER_BYTES} bytes")
        try:
            line = raw_line.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError("VCF header is not UTF-8") from exc
        lines.append(line)
        consumed += len(raw_line)
        if line.startswith("#CHROM"):
            break
    parsed = _parse_header_lines(lines, add_missing_line_ending=False)
    return parsed[0], parsed[1], consumed, parsed[3]


def audit_header_lines(header_lines: Iterable[str]) -> dict:
    """Audit an in-memory VCF header, including its final ``#CHROM`` line.

    This accepts header lines captured from an archive without requiring the
    VCF body or extracting the member.  No records are read or interpreted.
    """
    parsed, samples, header_bytes, line_count = _parse_header_lines(header_lines)
    return {"header": {**parsed, "sample_ids": samples}, "header_bytes": header_bytes,
            "header_line_count": line_count, "body_records_parsed": 0,
            "interpretation_limits": _interpretation_limits()}


def audit_header_object(header_object: dict) -> dict:
    """Audit ``{member, header_lines, body_records_parsed: 0}`` in-memory input."""
    if not isinstance(header_object, dict):
        raise ValueError("header object must be a JSON object")
    if type(header_object.get("body_records_parsed")) is not int or header_object["body_records_parsed"] != 0:
        raise ValueError("header object must attest body_records_parsed: 0")
    member = header_object.get("member")
    lines = header_object.get("header_lines")
    if not isinstance(member, str) or not isinstance(lines, list):
        raise ValueError("header object requires string member and list header_lines")
    return {"member": member, **audit_header_lines(lines)}


def audit_header_document(document: dict, input_artifact: str | None = None) -> dict:
    """Audit an in-memory ``{"vcf_headers": [header objects...]}`` document."""
    headers = document.get("vcf_headers") if isinstance(document, dict) else None
    if not isinstance(headers, list):
        raise ValueError("header audit JSON requires a vcf_headers list")
    if len(headers) > MAX_HEADER_OBJECTS:
        raise ValueError(f"header count exceeds safety limit ({MAX_HEADER_OBJECTS})")
    result = {"headers": [audit_header_object(item) for item in headers],
              "header_count": len(headers)}
    if input_artifact is not None:
        result["input_artifact"] = input_artifact
    return result


def _read_header_audit_json(path: Path) -> dict:
    with path.open("rb") as source:
        payload = source.read(MAX_HEADER_AUDIT_JSON_BYTES + 1)
    if len(payload) > MAX_HEADER_AUDIT_JSON_BYTES:
        raise ValueError(f"header-audit JSON exceeds {MAX_HEADER_AUDIT_JSON_BYTES} bytes")
    try:
        document = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid header-audit JSON: {path}") from exc
    return audit_header_document(document, str(path))


def _interpretation_limits() -> list[str]:
    return ["QUAL is fixed-column site quality, distinct from sample FORMAT/GQ.",
            "Field names and header declarations do not validate population probabilities or sample-level calibration.",
            "GP sum/nonnegative checks describe numeric shape only.",
            "Number=G cardinality uses ALT count and parseable GT ploidy; unknown ploidy is not inferred.",
            "PL and GL are likelihood encodings, not posterior probabilities.",
            "No posterior is calculated; multiallelic ALT and non-diploid GT are out of scope.",
            "invalidGT counts allele indexes above the ALT count; this is a structural check, not a truth comparison.",
            "missingrecord counts a row without that sample column; it does not mean an absent catalog site.",
            "Missing GT is explicit; no genotype such as 0/0 is inferred."]


def audit_vcf(vcf_path: str | Path, max_records: int = 0) -> dict:
    """Read header and at most ``max_records`` records from a local VCF."""
    if type(max_records) is not int or not 0 <= max_records <= MAX_RECORDS:
        raise ValueError(f"--max-records must be between 0 and {MAX_RECORDS}")
    path = Path(vcf_path)
    with path.open("rb") as raw_source:
        magic = raw_source.read(2)
        raw_source.seek(0)
        compressed = magic == b"\x1f\x8b"
        if compressed:
            stream_context = gzip.GzipFile(fileobj=raw_source, mode="rb")
        else:
            stream_context = raw_source

        try:
            with stream_context as stream:
                header, samples, header_bytes, header_lines = _read_header(stream)
                sample_stats = {sample: _new_sample_stats() for sample in samples}
                field_stats = {tag: _new_field_stats() for tag in CONFIDENCE_FIELDS}
                gp_shape = dict(numeric_entries=0, sum_near_one=0, sum_not_near_one=0,
                                all_values_nonnegative=0, contains_negative=0,
                                sum_absolute_tolerance=1e-3)
                number_g = {}
                for tag in ("GP", "PL", "GL"):
                    declarations = header["formats"][tag]
                    number_g[tag] = dict(
                        declared_number_g=bool(declarations) and all(
                            item["Number"] == "G" for item in declarations),
                        declaration_count=len(declarations), checked=0, matches=0,
                        mismatches=0, unknown_ploidy=0, not_checked_declaration=0)
                record_stats = dict(requested_max=max_records, processed=0,
                                    stop_reason="header_only" if max_records == 0 else None,
                                    record_bytes_read=0, records_with_nonmissing_QUAL=0,
                                    records_with_missing_QUAL=0, records_with_multiallelic_ALT=0)

                while record_stats["processed"] < max_records:
                    if (samples and
                            (record_stats["processed"] + 1) * len(samples) > MAX_SAMPLE_RECORD_OBSERVATIONS):
                        record_stats["stop_reason"] = "sample_observation_limit"
                        break
                    remaining = MAX_TOTAL_RECORD_BYTES - record_stats["record_bytes_read"]
                    line_limit = min(MAX_RECORD_BYTES, remaining)
                    raw_line = stream.readline(line_limit + 1)
                    if not raw_line:
                        record_stats["stop_reason"] = "eof"
                        break
                    if len(raw_line) > line_limit:
                        if remaining < MAX_RECORD_BYTES:
                            record_stats["stop_reason"] = "record_byte_limit"
                            break
                        raise ValueError(
                            f"VCF record exceeds per-record byte limit ({MAX_RECORD_BYTES})"
                        )
                    record_stats["record_bytes_read"] += len(raw_line)
                    try:
                        row = raw_line.decode("utf-8").rstrip("\r\n")
                    except UnicodeDecodeError as exc:
                        raise ValueError("record is not UTF-8") from exc
                    if row.startswith("#"):
                        raise ValueError("unexpected header line after #CHROM")
                    columns = row.split("\t")
                    if len(columns) < 8:
                        raise ValueError("VCF record has fewer than 8 fixed columns")
                    if len(columns) > 9 + len(samples):
                        raise ValueError("VCF record has more sample columns than the header")

                    record_stats["processed"] += 1
                    if columns[5] == ".":
                        record_stats["records_with_missing_QUAL"] += 1
                    else:
                        record_stats["records_with_nonmissing_QUAL"] += 1
                    if columns[4] != "." and len(columns[4].split(",")) > 1:
                        record_stats["records_with_multiallelic_ALT"] += 1
                    alt_count = 0 if columns[4] == "." else len(columns[4].split(","))

                    format_keys: list[str] = []
                    if len(columns) >= 9 and columns[8] not in ("", "."):
                        format_keys = columns[8].split(":")
                        if any(not key for key in format_keys) or len(set(format_keys)) != len(format_keys):
                            raise ValueError("record has empty or duplicate FORMAT keys")
                    format_index = {key: index for index, key in enumerate(format_keys)}

                    for sample_index, sample in enumerate(samples, start=9):
                        stats = sample_stats[sample]
                        stats["total_records"] += 1
                        if sample_index >= len(columns):
                            stats["missingrecord"] += 1
                            continue
                        values = columns[sample_index].split(":")
                        gt_index = format_index.get("GT")
                        gt_ploidy = None
                        if gt_index is None or gt_index >= len(values):
                            stats["missingGT"] += 1
                        elif values[gt_index] == "":
                            stats["malformedGT"] += 1
                        else:
                            gt_state, gt_ploidy = _observe_gt(values[gt_index], alt_count)
                            if gt_state == "complete":
                                stats["completeGT"] += 1
                            elif gt_state == "missing":
                                stats["missingGT"] += 1
                            elif gt_state == "invalid_allele_index":
                                stats["invalidGT"] += 1
                            else:
                                stats["malformedGT"] += 1
                            if gt_state in ("complete", "missing") and gt_ploidy not in (None, 2):
                                stats["out_of_scope_non_diploid_GT"] += 1

                        for tag in CONFIDENCE_FIELDS:
                            tag_stats = field_stats[tag]
                            tag_index = format_index.get(tag)
                            if tag_index is None or tag_index >= len(values):
                                tag_stats["missing"] += 1
                                continue
                            value = values[tag_index]
                            if value == ".":
                                tag_stats["missing"] += 1
                                continue
                            numbers = _parse_numbers(tag, value)
                            if numbers is None:
                                tag_stats["malformed"] += 1
                                continue
                            tag_stats["numeric_entries"] += 1
                            tag_stats["numeric_values"] += len(numbers)
                            if tag == "GP":
                                gp_shape["numeric_entries"] += 1
                                if math.isclose(sum(numbers), 1.0, rel_tol=0.0, abs_tol=1e-3):
                                    gp_shape["sum_near_one"] += 1
                                else:
                                    gp_shape["sum_not_near_one"] += 1
                                if all(number >= 0 for number in numbers):
                                    gp_shape["all_values_nonnegative"] += 1
                                else:
                                    gp_shape["contains_negative"] += 1
                            if tag in number_g:
                                cardinality = number_g[tag]
                                if not cardinality["declared_number_g"]:
                                    cardinality["not_checked_declaration"] += 1
                                elif gt_ploidy is None:
                                    cardinality["unknown_ploidy"] += 1
                                else:
                                    expected = math.comb(alt_count + gt_ploidy, gt_ploidy)
                                    cardinality["checked"] += 1
                                    cardinality["matches" if len(numbers) == expected else "mismatches"] += 1

                if record_stats["stop_reason"] is None:
                    record_stats["stop_reason"] = "record_limit_reached"
                return {
                    "purpose": "Local VCF FORMAT availability and numeric parse audit; no scoring",
                    "source": {"path": str(path), "identity_status": "unverified",
                               "identity_note": "Only the requested prefix was streamed; no full-file SHA-256 was computed."},
                    "container": {"compression": "gzip" if compressed else "plain",
                                  "stream_eof_reached": record_stats["stop_reason"] == "eof",
                                  "header_bytes_read": header_bytes, "header_line_count": header_lines},
                    "header": {**header, "sample_ids": samples}, "records": record_stats,
                    "per_sample": sample_stats, "confidence_field_parse": field_stats,
                    "GP_numeric_shape": gp_shape, "Number_G_cardinality": number_g,
                    "interpretation_limits": _interpretation_limits(),
                    "limits": dict(max_header_bytes=MAX_HEADER_BYTES, max_record_bytes=MAX_RECORD_BYTES,
                                   max_total_record_bytes=MAX_TOTAL_RECORD_BYTES,
                                   max_records=MAX_RECORDS, max_samples=MAX_SAMPLES,
                                   max_sample_record_observations=MAX_SAMPLE_RECORD_OBSERVATIONS),
                }
        finally:
            if compressed:
                stream_context.close()


def report_bytes(report: dict) -> bytes:
    canonical = json.dumps(
        report, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    complete = {
        **report,
        "report_checksum": {
            "algorithm": "sha256",
            "scope": "canonical report object before adding report_checksum",
            "value": hashlib.sha256(canonical).hexdigest(),
        },
    }
    return (json.dumps(complete, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def write_new_report(path: str | Path, report: dict) -> None:
    """Create a new JSON report; exclusive creation refuses existing paths and symlinks."""
    with Path(path).open("x", encoding="utf-8", newline="\n") as destination:
        destination.write(report_bytes(report).decode("utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--vcf", type=Path, help="local .vcf or .vcf.gz input")
    mode.add_argument("--header-audit-json", type=Path, action="append",
                      help="header-only JSON input with vcf_headers; repeat to combine inputs")
    parser.add_argument("--out", type=Path, required=True, help="new JSON output path; existing paths are refused")
    parser.add_argument("--max-records", type=int, default=0,
                        help=f"records to inspect (default 0/header only; maximum {MAX_RECORDS})")
    args = parser.parse_args()
    try:
        if args.vcf:
            report = audit_vcf(args.vcf, args.max_records)
        else:
            if args.max_records != 0:
                raise ValueError("--max-records applies only to --vcf; header JSON mode never reads records")
            inputs = [_read_header_audit_json(path) for path in args.header_audit_json]
            count = sum(item["header_count"] for item in inputs)
            if count > MAX_HEADER_OBJECTS:
                raise ValueError(f"combined header count exceeds safety limit ({MAX_HEADER_OBJECTS})")
            report = {"purpose": "In-memory VCF header semantics audit; no records scored or read",
                      "mode": "header_only", "input_count": len(inputs),
                      "header_count": count, "inputs": inputs,
                      "interpretation_limits": _interpretation_limits(),
                      "limits": {"max_header_bytes": MAX_HEADER_BYTES,
                                 "max_header_json_bytes": MAX_HEADER_AUDIT_JSON_BYTES,
                                 "max_header_objects": MAX_HEADER_OBJECTS}}
        write_new_report(args.out, report)
    except (OSError, ValueError, EOFError) as exc:
        parser.error(str(exc))
    count = report.get("records", {}).get("processed", report.get("header_count", 0))
    print(f"Audited {count} VCF record(s)/header(s); report written to {args.out}")


if __name__ == "__main__":
    main()
