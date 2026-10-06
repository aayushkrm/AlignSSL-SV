"""Bounded, protocol-gated preparation of released truth VCFs.

This module does not read caller files, normalize variants, match calls, or make
biological claims. It accepts only the exact sample label and input hashes in
the SHA-pinned protocol. Its parser is deliberately sequential and preserves
the source header, row order, fields, and duplicate-row multiplicity.

Protocol JSON fields required by :func:`prepare_released_truth`:

``truth_preparation_approved`` (true), ``independent_approval_ref``,
``truth_sha256``, ``current_bed_sha256``, ``tier1_bed_sha256``,
``expected_truth_sample_label``, ``max_truth_decoded_bytes``,
``max_truth_compressed_bytes``, ``max_line_bytes``,
``charged_prior_global_decoded_bytes``,
``truth_preparation_reservation_bytes``, ``max_bed_bytes``,
``max_bed_rows``, and ``max_mapping_bytes``.

The reservation must cover the truth decoded-byte cap, one byte used to detect
budget overflow, and each BED byte cap plus its one-byte overflow probe. It
must also fit under the six-GiB global ceiling after the prior global charge.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from typing import Any, BinaryIO, Iterable

if __package__:
    from .released_truth_units import (
        FLANK_BP,
        TerritoryIndex,
        classify_truth_record,
        is_autosome,
        territory_sets,
    )
else:  # Support `python analysis/prepare_released_truth.py ...` from the repo.
    from released_truth_units import (
        FLANK_BP,
        TerritoryIndex,
        classify_truth_record,
        is_autosome,
        territory_sets,
    )

GIB = 1024**3
MIB = 1024**2
MAX_TRUTH_DECODED_BYTES = GIB
MAX_TRUTH_COMPRESSED_BYTES = 2 * GIB
MAX_LINE_BYTES = 32 * MIB
MAX_BED_BYTES = 4 * MIB
MAX_BED_ROWS = 1_000_000
MAX_MAPPING_BYTES = 64 * MIB
MAX_PROTOCOL_BYTES = 1 * MIB
MAX_INVENTORY_BYTES = 4 * MIB
MAX_GLOBAL_DECODED_BYTES = 6 * GIB
_SHA256_RE = re.compile(r"[0-9a-fA-F]{64}\Z")
_FILEFORMAT_RE = re.compile(r"##fileformat=VCFv4\.[0-9]+\Z")
_META_HEADER_RE = re.compile(r"##[A-Za-z][A-Za-z0-9_.-]*=.+\Z")
_FORMAT_KEY_RE = re.compile(r"[A-Za-z][A-Za-z0-9_.]*\Z")
_GT_RE = re.compile(r"(?:\.|[0-9]+)(?:[/|](?:\.|[0-9]+))*\Z")


class TruthPreparationError(ValueError):
    """A fail-closed preparation error, with a report path when available."""

    def __init__(self, message: str, report_path: Path | None = None):
        super().__init__(message)
        self.report_path = report_path


def _sha256_text(value: object, name: str) -> str:
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
        raise ValueError(f"{name} must be a 64-character SHA-256 hex string")
    return value.lower()


def _bounded_int(
    protocol: dict[str, object], name: str, *, minimum: int, maximum: int,
) -> int:
    value = protocol.get(name)
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"{name} must be an integer from {minimum} through {maximum}")
    return value


def _read_protocol(path: Path, expected_sha256: str) -> tuple[dict[str, object], str]:
    expected = _sha256_text(expected_sha256, "protocol_sha256")
    with path.open("rb") as source:
        raw = source.read(MAX_PROTOCOL_BYTES + 1)
    if len(raw) > MAX_PROTOCOL_BYTES:
        raise ValueError("protocol exceeds the 1-MiB byte limit")
    actual = hashlib.sha256(raw).hexdigest()
    if actual != expected:
        raise ValueError("protocol SHA-256 mismatch")
    try:
        protocol = json.loads(raw.decode("utf-8", errors="strict"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("protocol must be valid UTF-8 JSON") from exc
    if not isinstance(protocol, dict):
        raise ValueError("protocol root must be a JSON object")
    return protocol, actual


def _validate_protocol(protocol: dict[str, object]) -> dict[str, object]:
    if protocol.get("truth_preparation_approved") is not True:
        raise ValueError("truth_preparation_approved must be explicitly true")
    approval_ref = protocol.get("independent_approval_ref")
    if (not isinstance(approval_ref, str) or not approval_ref.strip()
            or len(approval_ref) > 512 or any(ch in approval_ref for ch in "\r\n\x00")):
        raise ValueError("independent_approval_ref must be a nonempty reference string")

    pins = {
        name: _sha256_text(protocol.get(name), name)
        for name in ("truth_sha256", "current_bed_sha256", "tier1_bed_sha256")
    }
    sample = protocol.get("expected_truth_sample_label")
    if (not isinstance(sample, str) or not sample or len(sample) > 255
            or any(ch.isspace() or ord(ch) < 32 for ch in sample)):
        raise ValueError("expected_truth_sample_label must be one exact, nonempty sample label")

    max_truth = _bounded_int(
        protocol, "max_truth_decoded_bytes", minimum=1,
        maximum=MAX_TRUTH_DECODED_BYTES,
    )
    max_compressed = _bounded_int(
        protocol, "max_truth_compressed_bytes", minimum=1,
        maximum=MAX_TRUTH_COMPRESSED_BYTES,
    )
    max_line = _bounded_int(
        protocol, "max_line_bytes", minimum=1, maximum=MAX_LINE_BYTES,
    )
    if max_line > max_truth:
        raise ValueError("max_line_bytes cannot exceed max_truth_decoded_bytes")
    max_bed_bytes = _bounded_int(
        protocol, "max_bed_bytes", minimum=1, maximum=MAX_BED_BYTES,
    )
    max_bed_rows = _bounded_int(
        protocol, "max_bed_rows", minimum=1, maximum=MAX_BED_ROWS,
    )
    max_mapping_bytes = _bounded_int(
        protocol, "max_mapping_bytes", minimum=1, maximum=MAX_MAPPING_BYTES,
    )
    prior = _bounded_int(
        protocol, "charged_prior_global_decoded_bytes", minimum=0,
        maximum=MAX_GLOBAL_DECODED_BYTES,
    )
    reservation = _bounded_int(
        protocol, "truth_preparation_reservation_bytes", minimum=1,
        maximum=MAX_GLOBAL_DECODED_BYTES,
    )
    required_reservation = max_truth + 1 + 2 * (max_bed_bytes + 1)
    if reservation < required_reservation:
        raise ValueError(
            "truth_preparation_reservation_bytes must cover the truth cap, "
            "overflow byte, and both BED caps plus overflow probes"
        )
    if prior + reservation > MAX_GLOBAL_DECODED_BYTES:
        raise ValueError("prior global charge plus reservation exceeds 6 GiB")

    return {
        **pins,
        "approval_ref": approval_ref,
        "sample_label": sample,
        "max_truth_decoded_bytes": max_truth,
        "max_truth_compressed_bytes": max_compressed,
        "max_line_bytes": max_line,
        "max_bed_bytes": max_bed_bytes,
        "max_bed_rows": max_bed_rows,
        "max_mapping_bytes": max_mapping_bytes,
        "prior_global_decoded_bytes": prior,
        "reservation_bytes": reservation,
    }


def _outside_git_fresh_outdir(path: Path) -> Path:
    if os.path.lexists(path):
        raise FileExistsError(f"outdir must be fresh and not already exist: {path}")
    resolved = path.resolve(strict=False)
    parent = resolved.parent
    if not parent.is_dir():
        raise FileNotFoundError(f"outdir parent must already exist: {parent}")
    for ancestor in (resolved, *resolved.parents):
        if (ancestor / ".git").exists():
            raise ValueError(f"outdir must be outside Git: {resolved}")
    resolved.mkdir()
    return resolved


def _hash_stream(source: BinaryIO, *, max_bytes: int) -> tuple[str, int]:
    digest = hashlib.sha256()
    total = 0
    source.seek(0)
    while True:
        chunk = source.read(1024 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise ValueError(f"truth compressed source exceeds its {max_bytes}-byte limit")
        digest.update(chunk)
    return digest.hexdigest(), total


def _source_signature(stat_result: os.stat_result) -> tuple[int, int, int, int, int]:
    return (
        stat_result.st_dev,
        stat_result.st_ino,
        stat_result.st_size,
        stat_result.st_mtime_ns,
        stat_result.st_ctime_ns,
    )


def _verify_source_snapshot(
    path: Path, source: BinaryIO, expected: tuple[int, int, int, int, int],
) -> None:
    descriptor = _source_signature(os.fstat(source.fileno()))
    pathname = _source_signature(path.stat())
    if descriptor != expected or pathname != expected:
        raise ValueError("truth source changed after its pinned snapshot was opened")


def _load_bed(
    path: Path, expected_sha256: str, *, max_bytes: int, max_rows: int,
    counters: dict[str, object],
) -> tuple[list[tuple[str, int, int]], dict[str, int], int]:
    digest = hashlib.sha256()
    chunks: list[bytes] = []
    total = 0
    with path.open("rb") as source:
        while True:
            chunk = source.read(min(64 * 1024, max_bytes + 1 - total))
            if not chunk:
                break
            total += len(chunk)
            counters["bed_decoded_bytes"] = int(counters["bed_decoded_bytes"]) + len(chunk)
            if total > max_bytes:
                raise ValueError(f"{path.name} exceeds its {max_bytes}-byte BED limit")
            digest.update(chunk)
            chunks.append(chunk)
    actual = digest.hexdigest()
    if actual != expected_sha256:
        raise ValueError(f"{path.name} SHA-256 mismatch")
    try:
        text = b"".join(chunks).decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ValueError(f"{path.name} is not valid UTF-8") from exc

    intervals: list[tuple[str, int, int]] = []
    counts = {"rows": 0, "autosomal_rows": 0, "non_autosomal_rows": 0}
    for line_number, line in enumerate(text.splitlines(), 1):
        if not line or line.startswith("#") or line.startswith(("track ", "browser ")):
            continue
        fields = line.split("\t")
        if len(fields) < 3 or not fields[0] or not fields[1] or not fields[2]:
            raise ValueError(f"{path.name}:{line_number}: malformed BED row")
        counts["rows"] += 1
        if counts["rows"] > max_rows:
            raise ValueError(f"{path.name} exceeds its {max_rows}-row BED limit")
        if not fields[1].isascii() or not fields[1].isdigit() \
                or not fields[2].isascii() or not fields[2].isdigit():
            raise ValueError(f"{path.name}:{line_number}: BED coordinates must be decimal integers")
        start, end = int(fields[1]), int(fields[2])
        if start < 0 or end <= start:
            raise ValueError(f"{path.name}:{line_number}: invalid BED interval")
        if is_autosome(fields[0]):
            intervals.append((fields[0], start, end))
            counts["autosomal_rows"] += 1
        else:
            counts["non_autosomal_rows"] += 1
    return intervals, counts, total


def _line_content(raw: bytes, *, label: str) -> bytes:
    if raw.endswith(b"\n"):
        content = raw[:-1]
        if content.endswith(b"\r"):
            content = content[:-1]
    else:
        content = raw
    if b"\r" in content or b"\n" in content:
        raise ValueError(f"{label}: embedded line-ending byte")
    content.decode("utf-8", errors="strict")
    return content


def _validate_header_line(content: bytes, *, expected_sample: str) -> bool:
    text = content.decode("utf-8", errors="strict")
    if text.startswith("##"):
        if not _META_HEADER_RE.fullmatch(text):
            raise ValueError("malformed VCF metadata header")
        return False
    if not text.startswith("#CHROM\t"):
        raise ValueError("malformed VCF header line")
    columns = text.split("\t")
    fixed = ["#CHROM", "POS", "ID", "REF", "ALT", "QUAL", "FILTER", "INFO", "FORMAT"]
    if columns[:9] != fixed or len(columns) != 10:
        raise ValueError("#CHROM header must have one FORMAT and one sample column")
    if columns[9] != expected_sample:
        raise ValueError("VCF sample label does not match expected_truth_sample_label")
    return True


def _parse_body_line(
    content: bytes, *, expected_columns: int = 10,
) -> tuple[str, int, str, str, str, str | None, bool, bool]:
    text = content.decode("utf-8", errors="strict")
    fields = text.split("\t")
    if len(fields) != expected_columns:
        raise ValueError("malformed VCF body line: expected ten columns")
    chrom, pos_text, original_id, ref, alt, _qual, _filter, _info, fmt, sample = fields
    if not chrom or any(ch.isspace() or ord(ch) < 32 or ord(ch) == 127 for ch in chrom):
        raise ValueError("malformed VCF CHROM value")
    if any(field == "" for field in fields[1:]):
        raise ValueError("malformed VCF body line: empty field")
    if not pos_text.isascii() or not pos_text.isdigit() or len(pos_text) > 19:
        raise ValueError("malformed VCF POS value")
    pos = int(pos_text)
    if pos < 1 or pos > 9_223_372_036_854_775_807:
        raise ValueError("malformed VCF POS value")

    if fmt == ".":
        if sample != ".":
            raise ValueError("FORMAT='.' requires sample='.'")
        return chrom, pos, original_id, ref, alt, None, True, False

    keys = fmt.split(":")
    if any(not _FORMAT_KEY_RE.fullmatch(key) for key in keys):
        raise ValueError("malformed VCF FORMAT key")
    gt_count = keys.count("GT")
    if gt_count > 1:
        return chrom, pos, original_id, ref, alt, None, False, True
    if len(set(keys)) != len(keys):
        raise ValueError("duplicate VCF FORMAT key")
    if gt_count == 1 and keys[0] != "GT":
        raise ValueError("VCF GT must be the first FORMAT key")
    values = sample.split(":")
    if len(values) > len(keys) or any(value == "" for value in values):
        raise ValueError("sample has extra or empty values for FORMAT")
    if gt_count == 0:
        return chrom, pos, original_id, ref, alt, None, True, False

    gt = values[0]
    if not _GT_RE.fullmatch(gt):
        raise ValueError("malformed VCF GT value")
    if "/" in gt and "|" in gt:
        raise ValueError("malformed VCF GT value: mixed separators")
    alleles = re.split(r"[/|]", gt)
    alt_count = 0 if alt == "." else len(alt.split(","))
    for allele in alleles:
        if allele != "." and int(allele) > alt_count:
            raise ValueError("VCF GT allele index exceeds the ALT allele count")
    return chrom, pos, original_id, ref, alt, gt, False, False


def _json_line(value: dict[str, object]) -> bytes:
    return (json.dumps(value, ensure_ascii=True, separators=(",", ":")) + "\n").encode("ascii")


def _write_all(target: BinaryIO, digest: Any, content: bytes) -> None:
    target.write(content)
    digest.update(content)


def _fsync_file(target: BinaryIO) -> None:
    target.flush()
    os.fsync(target.fileno())


def _write_json_exclusive(path: Path, value: dict[str, object], *, limit: int) -> bytes:
    raw = (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True) + "\n").encode("ascii")
    if len(raw) > limit:
        raise ValueError(f"inventory exceeds its {limit}-byte metadata limit")
    with path.open("xb") as target:
        target.write(raw)
        _fsync_file(target)
    return raw


def _write_failure_report(
    outdir: Path, *, error: Exception, protocol_sha256: str,
    config: dict[str, object], counters: dict[str, object],
) -> Path:
    path = outdir / "truth_preparation_failure.json"
    payload = {
        "status": "incomplete",
        "failure_type": type(error).__name__,
        "failure": str(error)[:2_000],
        "protocol_sha256": protocol_sha256,
        "truth_sha256": config["truth_sha256"],
        "charged_prior_global_decoded_bytes": config["prior_global_decoded_bytes"],
        "truth_preparation_reservation_bytes": config["reservation_bytes"],
        "global_charge_plus_reservation_bytes": (
            config["prior_global_decoded_bytes"] + config["reservation_bytes"]
        ),
        "truth_decoded_bytes_delivered": counters.get("truth_decoded_bytes", 0),
        "bed_decoded_bytes_read": counters.get("bed_decoded_bytes", 0),
        "body_records_seen": counters.get("body_records", 0),
        "gt_absent_records": counters.get("gt_absent_records", 0),
        "gt_duplicate_records": counters.get("gt_duplicate_records", 0),
        "exclusion_counts": counters.get("exclusion_counts", {}),
        "boundary_counts": counters.get("boundary_counts", {}),
        "eligible_counts": counters.get("eligible_counts", {}),
        "record_map_bytes_written": counters.get("mapping_bytes", 0),
        "partial_files_preserved": sorted(
            p.name for p in outdir.iterdir()
            if p.is_file() and p.name in {
                "eligible_truth.vcf.partial", "truth_record_map.jsonl.partial",
                "truth_preparation_inventory.json.partial", "eligible_truth.vcf",
                "truth_record_map.jsonl", "truth_preparation_inventory.json",
            }
        ),
    }
    try:
        _write_json_exclusive(path, payload, limit=MAX_INVENTORY_BYTES)
    except FileExistsError:
        # Keep the first failure report immutable if a caller retries in place.
        return path
    return path


def prepare_released_truth(
    truth_path: str | os.PathLike[str],
    current_bed: str | os.PathLike[str],
    tier1_bed: str | os.PathLike[str],
    outdir: str | os.PathLike[str],
    protocol_path: str | os.PathLike[str],
    protocol_sha256: str,
) -> dict[str, object]:
    """Prepare a SHA-pinned eligible truth VCF under a reviewed protocol.

    The BEDs are plain UTF-8 BED files. The truth input is a gzip/BGZF byte
    stream and is decoded once, sequentially. All files written by this
    function are inside a new directory outside Git.
    """
    truth = Path(truth_path)
    current = Path(current_bed)
    tier1 = Path(tier1_bed)
    protocol_file = Path(protocol_path)
    raw_outdir = Path(outdir)
    protocol, protocol_hash = _read_protocol(protocol_file, protocol_sha256)
    config = _validate_protocol(protocol)

    # Approval, protocol pin, output location, and bounds are checked before
    # any truth body is opened or decoded.
    output = _outside_git_fresh_outdir(raw_outdir)
    counters: dict[str, object] = {
        "truth_decoded_bytes": 0,
        "bed_decoded_bytes": 0,
        "body_records": 0,
        "gt_absent_records": 0,
        "gt_duplicate_records": 0,
        "exclusion_counts": {},
        "boundary_counts": {"boundary_or_mixed_territory": 0},
        "eligible_counts": {"current_minus_tier1": 0, "intersection": 0},
        "mapping_bytes": 0,
    }
    vcf_partial = output / "eligible_truth.vcf.partial"
    map_partial = output / "truth_record_map.jsonl.partial"
    inventory_partial = output / "truth_preparation_inventory.json.partial"
    truth_stream: BinaryIO | None = None

    try:
        truth_stream = truth.open("rb")
        source_snapshot = _source_signature(os.fstat(truth_stream.fileno()))
        _verify_source_snapshot(truth, truth_stream, source_snapshot)
        if source_snapshot[2] > config["max_truth_compressed_bytes"]:
            raise ValueError("truth compressed source exceeds its pinned byte-size limit")
        compressed_sha, compressed_size = _hash_stream(
            truth_stream, max_bytes=config["max_truth_compressed_bytes"],
        )
        _verify_source_snapshot(truth, truth_stream, source_snapshot)
        if compressed_sha != config["truth_sha256"]:
            raise ValueError("truth compressed-byte SHA-256 mismatch")

        current_intervals, current_bed_counts, current_bed_bytes = _load_bed(
            current, config["current_bed_sha256"],
            max_bytes=config["max_bed_bytes"], max_rows=config["max_bed_rows"],
            counters=counters,
        )
        tier1_intervals, tier1_bed_counts, tier1_bed_bytes = _load_bed(
            tier1, config["tier1_bed_sha256"],
            max_bytes=config["max_bed_bytes"], max_rows=config["max_bed_rows"],
            counters=counters,
        )

        hard_intervals, ordinary_intervals = territory_sets(current_intervals, tier1_intervals)
        hard_index = TerritoryIndex(hard_intervals)
        ordinary_index = TerritoryIndex(ordinary_intervals)
        _verify_source_snapshot(truth, truth_stream, source_snapshot)

        source_hash = config["truth_sha256"]
        expected_sample = config["sample_label"]
        max_decoded = config["max_truth_decoded_bytes"]
        max_line = config["max_line_bytes"]
        max_map = config["max_mapping_bytes"]
        decoded = 0
        ordinal = 0
        header_seen = False
        fileformat_seen = False
        header_line_number = 0
        exclusion_counts: dict[str, int] = {}
        boundary_counts = {"boundary_or_mixed_territory": 0}
        eligible_counts = {"current_minus_tier1": 0, "intersection": 0}
        vcf_digest, map_digest = hashlib.sha256(), hashlib.sha256()
        mapping_bytes = 0

        truth_stream.seek(0)
        with gzip.GzipFile(fileobj=truth_stream, mode="rb") as source, \
                vcf_partial.open("xb") as vcf_out, map_partial.open("xb") as map_out:
            while True:
                remaining = max_decoded - decoded
                read_limit = min(max_line + 1, remaining + 1)
                raw = source.readline(read_limit)
                if not raw:
                    break
                decoded += len(raw)
                counters["truth_decoded_bytes"] = decoded
                if header_seen:
                    ordinal += 1
                    counters["body_records"] = ordinal
                if decoded > max_decoded:
                    raise ValueError("truth decoded-byte budget exceeded")
                if len(raw) > max_line:
                    raise ValueError(f"VCF line exceeds {max_line} bytes")
                content = _line_content(raw, label=f"VCF line {header_line_number + 1}")

                if not header_seen:
                    header_line_number += 1
                    if header_line_number == 1:
                        if not _FILEFORMAT_RE.fullmatch(content.decode("utf-8", errors="strict")):
                            raise ValueError("first VCF header line must declare ##fileformat=VCFv4.x")
                        fileformat_seen = True
                    elif content.startswith(b"##fileformat="):
                        if fileformat_seen or not _FILEFORMAT_RE.fullmatch(
                            content.decode("utf-8", errors="strict")
                        ):
                            raise ValueError("duplicate or malformed VCF fileformat header")
                        fileformat_seen = True
                    if content.startswith(b"#CHROM\t"):
                        header_seen = _validate_header_line(
                            content, expected_sample=expected_sample,
                        )
                    else:
                        text = content.decode("utf-8", errors="strict")
                        if not _META_HEADER_RE.fullmatch(text):
                            raise ValueError("malformed VCF header or missing #CHROM line")
                    _write_all(vcf_out, vcf_digest, raw)
                    continue

                if content.startswith(b"#"):
                    raise ValueError(f"header or comment line after VCF data at ordinal {ordinal}")
                (
                    chrom, pos, original_id, ref, alt, gt,
                    gt_absent, gt_duplicate,
                ) = _parse_body_line(content)
                if gt_duplicate:
                    counters["gt_duplicate_records"] += 1
                    raise ValueError(f"duplicate GT FORMAT key at ordinal {ordinal}")
                if gt_absent:
                    counters["gt_absent_records"] += 1

                classification = classify_truth_record(
                    source_hash, ordinal, chrom, pos, ref, alt, gt,
                )
                identity = classification.identity
                territory: str | None = None
                reason = classification.exclusion_reason
                if reason is None:
                    unit = classification.unit
                    if unit is None:
                        raise AssertionError("classifier returned neither a unit nor an exclusion")
                    span_chrom, span_start, span_end = unit.full_span(FLANK_BP)
                    in_hard = hard_index.contains_interval(span_chrom, span_start, span_end)
                    in_ordinary = ordinary_index.contains_interval(span_chrom, span_start, span_end)
                    if in_hard and in_ordinary:
                        raise AssertionError("disjoint territory indexes overlap")
                    if in_hard:
                        territory = "current_minus_tier1"
                        eligible_counts[territory] += 1
                        fields = content.split(b"\t")
                        fields[2] = identity.encode("ascii")
                        emitted = b"\t".join(fields) + (b"\n" if raw.endswith(b"\n") else b"")
                        if raw.endswith(b"\r\n"):
                            emitted = b"\t".join(fields) + b"\r\n"
                        _write_all(vcf_out, vcf_digest, emitted)
                    elif in_ordinary:
                        territory = "intersection"
                        eligible_counts[territory] += 1
                        fields = content.split(b"\t")
                        fields[2] = identity.encode("ascii")
                        emitted = b"\t".join(fields)
                        if raw.endswith(b"\r\n"):
                            emitted += b"\r\n"
                        elif raw.endswith(b"\n"):
                            emitted += b"\n"
                        _write_all(vcf_out, vcf_digest, emitted)
                    else:
                        territory = "boundary_or_mixed_territory"
                        boundary_counts[territory] += 1
                else:
                    exclusion_counts[reason] = exclusion_counts.get(reason, 0) + 1

                counters["exclusion_counts"] = dict(exclusion_counts)
                counters["boundary_counts"] = dict(boundary_counts)
                counters["eligible_counts"] = dict(eligible_counts)

                mapping: dict[str, object] = {
                    "ordinal": ordinal,
                    "identity": identity,
                    "original_id": original_id,
                    "territory": territory if territory is not None else "excluded",
                }
                if reason is not None:
                    mapping["exclusion_reason"] = reason
                map_line = _json_line(mapping)
                if mapping_bytes + len(map_line) > max_map:
                    raise ValueError(f"record map exceeds its {max_map}-byte limit")
                map_out.write(map_line)
                map_digest.update(map_line)
                mapping_bytes += len(map_line)
                counters["mapping_bytes"] = mapping_bytes

            _fsync_file(vcf_out)
            _fsync_file(map_out)

        _verify_source_snapshot(truth, truth_stream, source_snapshot)
        final_source_sha, final_compressed_size = _hash_stream(
            truth_stream, max_bytes=config["max_truth_compressed_bytes"],
        )
        _verify_source_snapshot(truth, truth_stream, source_snapshot)
        if final_source_sha != compressed_sha or final_compressed_size != compressed_size:
            raise ValueError("truth compressed bytes changed during body preparation")

        if not header_seen or not fileformat_seen:
            raise ValueError("VCF lacks one valid #CHROM header")

        actual_decoded_traffic = decoded + int(counters["bed_decoded_bytes"])
        if actual_decoded_traffic > config["reservation_bytes"]:
            raise ValueError("decoded input traffic exceeds its reservation")

        inventory: dict[str, object] = {
            "status": "complete",
            "protocol_sha256": protocol_hash,
            "independent_approval_ref": config["approval_ref"],
            "truth_sha256": source_hash,
            "truth_compressed_bytes": compressed_size,
            "truth_source_snapshot_verified": True,
            "current_bed_sha256": config["current_bed_sha256"],
            "tier1_bed_sha256": config["tier1_bed_sha256"],
            "current_bed_bytes": current_bed_bytes,
            "tier1_bed_bytes": tier1_bed_bytes,
            "current_bed_counts": current_bed_counts,
            "tier1_bed_counts": tier1_bed_counts,
            "expected_truth_sample_label": expected_sample,
            "sample_label_validation": "exact_protocol_string_match_only",
            "contig_dictionary_validation": "not_performed_separate_reference_gate_required",
            "truth_decoded_bytes": decoded,
            "bed_decoded_bytes": int(counters["bed_decoded_bytes"]),
            "decoded_input_traffic_bytes": actual_decoded_traffic,
            "charged_prior_global_decoded_bytes": config["prior_global_decoded_bytes"],
            "truth_preparation_reservation_bytes": config["reservation_bytes"],
            "global_charge_plus_reservation_bytes": (
                config["prior_global_decoded_bytes"] + config["reservation_bytes"]
            ),
            "limits": {
                "max_truth_decoded_bytes": max_decoded,
                "max_truth_compressed_bytes": config["max_truth_compressed_bytes"],
                "max_line_bytes": max_line,
                "max_bed_bytes": config["max_bed_bytes"],
                "max_bed_rows": config["max_bed_rows"],
                "max_mapping_bytes": max_map,
            },
            "body_records": ordinal,
            "gt_absent_records": counters["gt_absent_records"],
            "gt_duplicate_records": counters["gt_duplicate_records"],
            "eligible_counts": eligible_counts,
            "boundary_counts": boundary_counts,
            "exclusion_counts": exclusion_counts,
            "eligible_truth_vcf_sha256": vcf_digest.hexdigest(),
            "truth_record_map_sha256": map_digest.hexdigest(),
            "truth_record_map_bytes": mapping_bytes,
        }
        inventory_raw = (
            json.dumps(inventory, sort_keys=True, indent=2, ensure_ascii=True) + "\n"
        ).encode("ascii")
        if len(inventory_raw) > MAX_INVENTORY_BYTES:
            raise ValueError("inventory exceeds the 4-MiB metadata limit")
        with inventory_partial.open("xb") as target:
            target.write(inventory_raw)
            _fsync_file(target)

        vcf_final = output / "eligible_truth.vcf"
        map_final = output / "truth_record_map.jsonl"
        inventory_final = output / "truth_preparation_inventory.json"
        vcf_partial.replace(vcf_final)
        map_partial.replace(map_final)
        inventory_partial.replace(inventory_final)
        return inventory
    except Exception as exc:
        counters["exclusion_counts"] = counters.get("exclusion_counts", {})
        report_path = _write_failure_report(
            output,
            error=exc,
            protocol_sha256=protocol_hash,
            config=config,
            counters=counters,
        )
        if isinstance(exc, TruthPreparationError):
            raise
        raise TruthPreparationError(str(exc), report_path) from exc
    finally:
        if truth_stream is not None:
            truth_stream.close()


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--truth-path", required=True)
    parser.add_argument("--current-bed", required=True)
    parser.add_argument("--tier1-bed", required=True)
    parser.add_argument("--outdir", required=True)
    parser.add_argument("--protocol-path", required=True)
    parser.add_argument("--protocol-sha256", required=True)
    args = parser.parse_args(argv)
    try:
        inventory = prepare_released_truth(
            args.truth_path,
            args.current_bed,
            args.tier1_bed,
            args.outdir,
            args.protocol_path,
            args.protocol_sha256,
        )
    except (OSError, ValueError) as exc:
        report = getattr(exc, "report_path", None)
        detail = f"; failure report: {report}" if report else ""
        print(f"truth preparation failed: {exc}{detail}", file=sys.stderr)
        return 2
    print(json.dumps(inventory, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
