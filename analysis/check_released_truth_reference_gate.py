#!/usr/bin/env python3
"""Narrow original-REF gate after a separately approved native PASS.

This checks anchored REF bytes only. It does not establish biological truth,
validate a denominator, normalize calls, or score callers. The approval flag is
protocol configuration, not evidence of independent review.
"""
from __future__ import annotations

import argparse
import gzip
import io
import json
import os
from hashlib import sha256
from pathlib import Path
import re
import sys

try:
    from . import check_released_truth_reference as reference_checker
    from . import diagnose_released_truth_metadata as census
except ImportError:
    import check_released_truth_reference as reference_checker
    import diagnose_released_truth_metadata as census

PURPOSE = "original_anchored_REF_validation_not_truth_or_scoring"
NATIVE_PURPOSE = "absolute_metadata_native_consistency_not_REF_or_scoring"
MAX_REFERENCE_COMPRESSED = 1024**3
MAX_FAI_BYTES = 1024**2
MAX_SMALL_FILE = 1024**2
MAX_PROTOCOL = 64 * 1024
MAX_NATIVE_REPORT = 64 * 1024
MAX_METADATA_BYTES = 1024**2
FAILURE_READ_AHEAD = 64 * 1024
MAX_CONTIGS = 30_000

EXPECTED = dict(
    expected_records=11_490,
    expected_input_bytes=11_853_747,
    eligible_truth_sha256="c908217f7ec8eba1efe93f51605675a8a8b9676d9c9ca443d1348ad0a00f68d2",
    identity_order_sha256="13db07d2c659f578144067d45eea85684816cce6482230e190a1b01b8d627e37",
    reference_compressed_bytes=892_326_179,
    reference_sha256="e9157e19a95e01dfc47080b5b6aa559c861de90b9934c2ea7c49cd5ec49e0285",
    fai_sha256="1eab7540d4b62ef0b43b50581d027be37c1ee57da9e9cb75957e750641c8630c",
    native_protocol_sha256="8eaf621e8ccf752417aa0286b2451298e46e17831e6bb85ca0fd4798163c630a",
    native_source_script_sha256="f97dcf0051e09f799b689be66903f88c3fceef3dd6281043ab92e8a762616214",
    reference_runtime=dict(
        python="3.10.20", implementation="cpython", buffer_size=8192,
        gzip_module_sha256="fb131d4bbe711c410f54c7f0b3c2c64292e1279199fd04c53837db03e542a907",
    ),
)
EXPECTED_KEYS = tuple(EXPECTED)
CODE_PINS = {
    "source_script_sha256": "check_released_truth_reference_gate.py",
    "reference_utility_sha256": "check_released_truth_reference.py",
    "census_helper_sha256": "diagnose_released_truth_metadata.py",
    "metadata_helper_sha256": "check_released_truth_metadata.py",
    "truth_units_helper_sha256": "released_truth_units.py",
}
RESOURCE_LIMITS = {
    "truth_bytes": census.MAX_INPUT,
    "compressed_reference_bytes": MAX_REFERENCE_COMPRESSED,
    "decoded_reference_bytes": reference_checker.MAX_FASTA_DECODED,
    "failure_read_ahead_bytes": FAILURE_READ_AHEAD,
    "contig_bytes": reference_checker.MAX_CONTIG_BYTES,
    "fasta_line_bytes": reference_checker.MAX_LINE,
    "query_records": reference_checker.MAX_QUERY_RECORDS,
    "query_ref_bytes": reference_checker.MAX_QUERY_REF_BYTES,
    "fai_bytes": MAX_FAI_BYTES,
    "native_report_bytes": MAX_NATIVE_REPORT,
    "protocol_bytes": MAX_PROTOCOL,
    "code_file_bytes": MAX_SMALL_FILE,
    "pinned_metadata_bytes": MAX_METADATA_BYTES,
    "result_report_bytes": MAX_NATIVE_REPORT,
}
NATIVE_PIN_FIELDS = {
    "native_source_script_sha256": "source_script_sha256",
    "native_truth_units_script_sha256": "truth_units_script_sha256",
    "native_bounded_reader_script_sha256": "bounded_reader_script_sha256",
    "native_sealed_buffer_script_sha256": "sealed_buffer_script_sha256",
}
NATIVE_HELPER_CODE_MAP = {
    "native_truth_units_script_sha256": "truth_units_helper_sha256",
    "native_bounded_reader_script_sha256": "census_helper_sha256",
    "native_sealed_buffer_script_sha256": "metadata_helper_sha256",
}
NATIVE_REPORT_KEYS = {
    "status", "purpose", "records", "unique_ids", "canonical_kind_counts",
    "global_sign_only_flags_retained", "identity_order_sha256", "eligible_truth_sha256",
    "input_bytes", "source_snapshot_stable", "versions", "protocol_sha256",
    "source_script_sha256", "truth_units_script_sha256", "bounded_reader_script_sha256",
    "sealed_buffer_script_sha256", "native_metadata_consistency", "normative_compliance_claim",
    "reference_validation", "denominator_validation", "scoring_performed", "input_unmodified",
    "rows_repaired_or_dropped", "parser_input_kernel_sealed", "parser_streams_share_pysam_backend",
    "serialized_rows_unchanged_by_native_calls", "input_read_reservation_bytes",
    "opaque_parser_traffic_measured",
}
PROTOCOL_KEYS = (set(EXPECTED_KEYS) | set(CODE_PINS) | set(NATIVE_PIN_FIELDS)
                 | {"reference_gate_approved", "purpose", "expected_sample",
                    "native_report_sha256", "native_protocol_sha256", "resource_limits"})
HEX64 = re.compile(r"[0-9a-f]{64}\Z")


def _path_snapshot(path):
    fd, before = census._open_regular(path)
    try:
        census.require(before == census._snapshot(os.fstat(fd)) == census._snapshot(os.lstat(path)),
                       "input snapshot is unstable")
        return before
    finally:
        os.close(fd)


def _read_small(path, cap, label):
    before = _path_snapshot(path)
    payload = census._read_pinned(path, cap)
    census.require(before == _path_snapshot(path), f"{label} snapshot changed while read")
    return payload, before


def _reference_runtime():
    """Bind the inspected standard decoder; not executed-bytecode attestation."""
    path = Path(gzip.__file__)
    raw, snapshot = _read_small(path, MAX_SMALL_FILE, "gzip runtime source")
    digest = sha256(raw).hexdigest()
    return (dict(python=sys.version.split()[0], implementation=sys.implementation.name,
                 buffer_size=io.DEFAULT_BUFFER_SIZE, gzip_module_sha256=digest),
            (path, snapshot, digest, len(raw)))


def _posthash(path, snapshot, digest, size, cap, label):
    fd, opened = census._open_regular(path)
    try:
        census.require(opened == snapshot and size <= cap and opened[2] == size,
                       f"{label} snapshot or size changed")
        check, count = sha256(), 0
        while count < cap:
            block = os.read(fd, min(1024**2, cap - count))
            if not block:
                break
            count += len(block)
            check.update(block)
        census.require(count == size and check.hexdigest() == digest
                       and opened == census._snapshot(os.fstat(fd))
                       == census._snapshot(os.lstat(path)), f"{label} posthash or snapshot failed")
    finally:
        os.close(fd)


def _same_snapshot(path, snapshot, label):
    census.require(_path_snapshot(path) == snapshot, f"{label} snapshot changed")


def _snapshot_record(snapshot):
    return dict(device=snapshot[0], inode=snapshot[1], size_bytes=snapshot[2],
                mtime_ns=snapshot[3], ctime_ns=snapshot[4])


def _require_outside_git(path):
    parent = Path(path).parent.resolve()
    census.require(not any((item / ".git").exists() for item in (parent, *parent.parents)),
                   "native report must be outside Git")


def _decode_json(payload, label):
    try:
        return json.loads(payload.decode("utf-8"), object_pairs_hook=census._pairs_no_duplicates,
                          parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
    except census.CensusError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        raise ValueError(f"{label} is not strict UTF-8 JSON") from None


def _protocol(path, protocol_sha256, expected):
    census.require(HEX64.fullmatch(protocol_sha256 or "") is not None, "invalid protocol SHA-256")
    raw, snapshot = _read_small(path, MAX_PROTOCOL, "protocol")
    census.require(sha256(raw).hexdigest() == protocol_sha256, "protocol hash mismatch")
    protocol = _decode_json(raw, "protocol")
    census.require(isinstance(protocol, dict) and set(protocol) == PROTOCOL_KEYS,
                   "protocol schema mismatch")
    census.require(protocol["reference_gate_approved"] is True and protocol["purpose"] == PURPOSE
                   and protocol["expected_sample"] == "HG002", "protocol approval or scope mismatch")
    census.require(isinstance(protocol["resource_limits"], dict)
                   and set(protocol["resource_limits"]) == set(RESOURCE_LIMITS)
                   and all(type(protocol["resource_limits"][key]) is int
                           and protocol["resource_limits"][key] == value
                           for key, value in RESOURCE_LIMITS.items()),
                   "protocol resource limits mismatch")
    for key in EXPECTED_KEYS:
        value = expected[key]
        census.require(type(protocol[key]) is type(value) and protocol[key] == value,
                       f"protocol input pin mismatch: {key}")
    for key in ("native_report_sha256", "native_protocol_sha256", *CODE_PINS,
                *NATIVE_PIN_FIELDS):
        census.require(HEX64.fullmatch(protocol[key] or "") is not None,
                       f"invalid protocol hash field: {key}")
    pinned_bytes, snapshots = len(raw), {"protocol": snapshot}
    for field, filename in CODE_PINS.items():
        local = Path(__file__).with_name(filename)
        content, code_snapshot = _read_small(local, MAX_SMALL_FILE, filename)
        pinned_bytes += len(content)
        census.require(pinned_bytes <= MAX_METADATA_BYTES, "pinned metadata exceeds byte cap")
        census.require(sha256(content).hexdigest() == protocol[field], f"local code pin mismatch: {field}")
        snapshots[field] = (local, code_snapshot, protocol[field], len(content))
    for native_key, local_key in NATIVE_HELPER_CODE_MAP.items():
        census.require(protocol[native_key] == protocol[local_key],
                       f"native report helper pin differs from local code: {native_key}")
    runtime, runtime_source = _reference_runtime()
    census.require(runtime == protocol["reference_runtime"], "reference decoder runtime mismatch")
    pinned_bytes += runtime_source[3]
    census.require(pinned_bytes <= MAX_METADATA_BYTES, "pinned metadata exceeds byte cap")
    snapshots["runtime_gzip_module_sha256"] = runtime_source
    return protocol, sha256(raw).hexdigest(), snapshots


def _native_report(path, protocol, expected):
    raw, snapshot = _read_small(path, MAX_NATIVE_REPORT, "native report")
    digest = sha256(raw).hexdigest()
    census.require(digest == protocol["native_report_sha256"], "native report hash mismatch")
    report = _decode_json(raw, "native report")
    census.require(isinstance(report, dict) and set(report) == NATIVE_REPORT_KEYS,
                   "native report schema mismatch")
    census.require(report["status"] == "complete" and report["purpose"] == NATIVE_PURPOSE
                   and report["native_metadata_consistency"] == "PASS", "native report is not PASS")
    for key, value in (("records", expected["expected_records"]),
                       ("unique_ids", expected["expected_records"]),
                       ("input_bytes", expected["expected_input_bytes"])):
        census.require(type(report[key]) is int and report[key] == value,
                       f"native report {key} mismatch")
    census.require(report["identity_order_sha256"] == expected["identity_order_sha256"]
                   and report["eligible_truth_sha256"] == expected["eligible_truth_sha256"],
                   "native report truth pin mismatch")
    kinds = report["canonical_kind_counts"]
    census.require(isinstance(kinds, dict) and set(kinds) == {"INS", "DEL"}
                   and all(type(value) is int and value >= 0 for value in kinds.values())
                   and sum(kinds.values()) == expected["expected_records"],
                   "native report kind counts mismatch")
    census.require(type(report["global_sign_only_flags_retained"]) is int
                   and 0 <= report["global_sign_only_flags_retained"] <= expected["expected_records"],
                   "native report sign-flag count mismatch")
    census.require(isinstance(report["versions"], dict)
                   and set(report["versions"]) == {"python", "pysam", "truvari", "bcftools", "htslib"}
                   and all(isinstance(value, str) for value in report["versions"].values()),
                   "native report version fields mismatch")
    census.require(report["protocol_sha256"] == protocol["native_protocol_sha256"],
                   "native protocol hash mismatch")
    for protocol_key, report_key in NATIVE_PIN_FIELDS.items():
        census.require(report[report_key] == protocol[protocol_key],
                       f"native report source pin mismatch: {report_key}")
    census.require(report["source_snapshot_stable"] is True and report["input_unmodified"] is True
                   and type(report["rows_repaired_or_dropped"]) is int
                   and report["rows_repaired_or_dropped"] == 0
                   and report["reference_validation"] == "UNASSESSED"
                   and report["denominator_validation"] == "NOT_VALIDATED"
                   and report["scoring_performed"] is False
                   and report["normative_compliance_claim"] is False
                   and report["parser_input_kernel_sealed"] is True
                   and report["parser_streams_share_pysam_backend"] is True
                   and report["serialized_rows_unchanged_by_native_calls"] is True
                   and type(report["input_read_reservation_bytes"]) is int
                   and report["input_read_reservation_bytes"] > 0
                   and report["opaque_parser_traffic_measured"] is False,
                   "native report precondition fields mismatch")
    return report, digest, snapshot, len(raw)


def _fai_dictionary(payload):
    try:
        text = payload.decode("ascii")
    except UnicodeDecodeError:
        raise ValueError("FAI is not ASCII") from None
    lines, lengths = text.splitlines(), {}
    census.require(bool(lines) and len(lines) <= MAX_CONTIGS, "invalid FAI line count")
    for line in lines:
        fields = line.split("\t")
        census.require(len(fields) == 5 and fields[0] and not any(c.isspace() for c in fields[0]),
                       "invalid FAI format")
        census.require(fields[0] not in lengths, "duplicate FAI contig")
        census.require(all(len(value) <= 20 and re.fullmatch(r"[0-9]+", value)
                           for value in fields[1:]),
                       "invalid FAI numeric field")
        length, offset, line_bases, line_width = map(int, fields[1:])
        census.require(0 < length <= reference_checker.MAX_CONTIG_BYTES
                       and offset >= 0 and 0 < line_bases <= length
                       and line_width in {line_bases + 1, line_bases + 2},
                       "invalid FAI length or layout")
        lengths[fields[0]] = length
    return lengths


def _truth_queries(payload, lengths, expected):
    _, _, rows = census._header_and_rows(payload)
    census.require(len(rows) == expected["expected_records"], "truth record count mismatch")
    identities, order, queries, ref_bytes = set(), sha256(), {}, 0
    for row in rows:
        fields = row.split("\t")
        census.require(len(fields) == 10 and HEX64.fullmatch(fields[2]) is not None,
                       "invalid truth row or identity")
        identity, contig = fields[2], fields[0]
        census.require(identity not in identities, "duplicate truth identity")
        census.require(contig.isascii() and contig and not any(c.isspace() for c in contig),
                       "invalid truth contig")
        census.require(re.fullmatch(r"[0-9]+", fields[1]) is not None and int(fields[1]) > 0,
                       "invalid truth position")
        try:
            ref = fields[3].encode("ascii")
        except UnicodeEncodeError:
            raise ValueError("non-ASCII truth REF") from None
        census.require(bool(ref) and all(base in b"ACGTacgt" for base in ref),
                       "ambiguous or empty truth REF")
        identities.add(identity)
        order.update((identity + "\n").encode("ascii"))
        ref_bytes += len(ref)
        census.require(len(identities) <= reference_checker.MAX_QUERY_RECORDS
                       and ref_bytes <= reference_checker.MAX_QUERY_REF_BYTES,
                       "query count or REF-byte budget exceeded")
        queries.setdefault(contig, []).append((identity, int(fields[1]) - 1, ref))
    census.require(order.hexdigest() == expected["identity_order_sha256"],
                   "truth identity order mismatch")
    census.require(set(queries) <= set(lengths), "truth contig absent from FAI")
    return queries, order.hexdigest(), ref_bytes


def _check_reference_bytes(compressed, lengths, queries):
    require = reference_checker.require
    max_decoded, max_contig, max_line = (reference_checker.MAX_FASTA_DECODED,
                                         reference_checker.MAX_CONTIG_BYTES,
                                         reference_checker.MAX_LINE)
    require(type(max_decoded) is int and 0 < max_decoded <= reference_checker.MAX_FASTA_DECODED,
            "invalid decoded-byte limit")
    require(isinstance(lengths, dict) and bool(lengths), "reference dictionary empty")
    require(all(type(v) is int and 0 < v <= max_contig for v in lengths.values()),
            "invalid reference dictionary")
    require(set(queries) <= set(lengths), "query contig absent from reference")
    seen_ids, ref_bytes = set(), 0
    for name, rows in queries.items():
        for identity, start, ref in rows:
            require(identity not in seen_ids, "duplicate query identity")
            require(len(seen_ids) < reference_checker.MAX_QUERY_RECORDS,
                    "query count limit exceeded")
            seen_ids.add(identity)
            require(type(start) is int and start >= 0 and isinstance(ref, bytes) and bool(ref)
                    and start + len(ref) <= lengths[name], "invalid REF query bounds")
            require(all(c in b"ACGTacgt" for c in ref), "ambiguous query REF")
            ref_bytes += len(ref)
            require(ref_bytes <= reference_checker.MAX_QUERY_REF_BYTES, "query REF-byte limit exceeded")
    seen, name, sequence, decoded, checked = set(), None, bytearray(), 0, 0

    def finish_contig():
        nonlocal checked
        require(name is not None, "FASTA sequence precedes first header")
        require(len(sequence) == lengths[name], "reference contig length mismatch")
        for identity, start, ref in queries.get(name, ()):
            require(sequence[start:start + len(ref)].upper() == ref.upper(),
                    f"original anchored REF mismatch for truth identity {identity}")
            checked += 1

    with gzip.GzipFile(fileobj=io.BytesIO(compressed), mode="rb") as stream:
        while True:
            raw = stream.readline(min(max_line + 1, max_decoded - decoded + 1))
            if not raw:
                break
            decoded += len(raw)
            require(decoded <= max_decoded, "FASTA decoded-byte cap exceeded")
            require(len(raw) <= max_line, "FASTA line cap exceeded")
            line = raw.rstrip(b"\r\n")
            if line.startswith(b">"):
                if name is not None:
                    finish_contig()
                parts = line[1:].split()
                require(bool(parts), "empty FASTA header")
                name = parts[0].decode("ascii")
                require(name in lengths and name not in seen, "unknown or duplicate FASTA contig")
                seen.add(name)
                sequence = bytearray()
            else:
                require(name is not None and bool(line)
                        and not line.translate(None, b"ACGTRYSWKMBDHVNacgtryswkmbdhvn"),
                        "invalid FASTA sequence line")
                require(len(sequence) + len(line) <= lengths[name],
                        "reference exceeds declared length")
                sequence.extend(line)
    require(name is not None, "empty FASTA")
    finish_contig()
    require(seen == set(lengths), "missing reference contig")
    require(checked == len(seen_ids), "REF query cardinality mismatch")
    return dict(reference_contigs=len(seen), checked_REF_records=checked,
                reference_delivered_decoded_bytes=decoded, query_REF_bytes=ref_bytes,
                whole_gzip_eof_crc_verified=True)


def _check_reference_gate(truth_path, reference_path, fai_path, native_report_path,
                          protocol_path, protocol_sha256, report_path, *, expected=EXPECTED):
    protocol, protocol_hash, snapshots = _protocol(protocol_path, protocol_sha256, expected)
    output = census._check_report_path(report_path)
    native_path = Path(native_report_path)
    _require_outside_git(native_path)
    native, native_hash, native_snapshot, native_size = _native_report(native_path, protocol, expected)
    truth, truth_snapshot = census._read_source(truth_path)
    truth_hash = sha256(truth).hexdigest()
    census.require(len(truth) == expected["expected_input_bytes"]
                   and truth_hash == expected["eligible_truth_sha256"], "truth source pin mismatch")
    fai, fai_snapshot = _read_small(fai_path, MAX_FAI_BYTES, "FAI")
    fai_hash = sha256(fai).hexdigest()
    census.require(fai_hash == expected["fai_sha256"], "FAI hash mismatch")
    lengths = _fai_dictionary(fai)
    queries, order_hash, query_ref_bytes = _truth_queries(truth, lengths, expected)
    reference, reference_snapshot = _read_small(reference_path, MAX_REFERENCE_COMPRESSED,
                                               "compressed reference")
    reference_hash = sha256(reference).hexdigest()
    census.require(len(reference) == expected["reference_compressed_bytes"]
                   and reference_hash == expected["reference_sha256"],
                   "compressed reference source pin mismatch")
    stream_result = _check_reference_bytes(reference, lengths, queries)
    census._posthash(truth_path, truth_snapshot, truth_hash, len(truth))
    _posthash(fai_path, fai_snapshot, fai_hash, len(fai), MAX_FAI_BYTES, "FAI")
    _posthash(reference_path, reference_snapshot, reference_hash, len(reference),
              MAX_REFERENCE_COMPRESSED, "compressed reference")
    _posthash(native_path, native_snapshot, native_hash, native_size, MAX_NATIVE_REPORT,
              "native report")
    protocol_snapshot = snapshots.pop("protocol")
    _same_snapshot(protocol_path, protocol_snapshot, "protocol")
    code_bytes = 0
    for field, (path, snapshot, digest, size) in snapshots.items():
        _posthash(path, snapshot, digest, size, MAX_SMALL_FILE, field)
        code_bytes += size
    result = dict(
        status="complete", purpose=PURPOSE, native_precondition="PASS",
        native_report_sha256=native_hash, native_protocol_sha256=native["protocol_sha256"],
        native_source_pins={key: protocol[key] for key in NATIVE_PIN_FIELDS},
        native_records=native["records"], records=expected["expected_records"],
        unique_ids=expected["expected_records"],
        checked_REF_records=stream_result["checked_REF_records"],
        eligible_truth_sha256=truth_hash, input_bytes=len(truth),
        identity_order_sha256=order_hash, reference_sha256=reference_hash,
        reference_compressed_bytes=len(reference), fai_sha256=fai_hash,
        reference_contigs=stream_result["reference_contigs"],
        reference_delivered_decoded_bytes=stream_result["reference_delivered_decoded_bytes"],
        query_REF_bytes=query_ref_bytes, whole_gzip_eof_crc_verified=True,
        truth_snapshot_stable=True, reference_snapshot_stable=True, fai_snapshot_stable=True,
        native_report_snapshot_stable=True, protocol_snapshot_stable=True,
        original_anchored_REF_validation="PASS", denominator_validation="NOT_VALIDATED",
        scoring_performed=False, normalization_performed=False, genomic_output_written=False,
        protocol_sha256=protocol_hash,
        reference_runtime=protocol["reference_runtime"],
        local_code_pins={key: protocol[key] for key in CODE_PINS},
        code_bytes_pinned_and_postchecked=code_bytes,
        truth_source_snapshot=_snapshot_record(truth_snapshot),
        reference_source_snapshot=_snapshot_record(reference_snapshot),
        fai_source_snapshot=_snapshot_record(fai_snapshot),
        native_report_source_snapshot=_snapshot_record(native_snapshot),
        protocol_source_snapshot=_snapshot_record(protocol_snapshot),
        failure_read_ahead_allowance_bytes=FAILURE_READ_AHEAD,
        resource_limits=RESOURCE_LIMITS,
        decoded_reference_cap_bytes=reference_checker.MAX_FASTA_DECODED,
        compressed_reference_cap_bytes=MAX_REFERENCE_COMPRESSED,
        contig_cap_bytes=reference_checker.MAX_CONTIG_BYTES,
        fasta_line_cap_bytes=reference_checker.MAX_LINE,
    )
    encoded = (json.dumps(result, sort_keys=True, indent=2) + "\n").encode("ascii")
    census.require(len(encoded) <= MAX_NATIVE_REPORT, "REF report byte cap exceeded")
    with output.open("xb") as stream:
        stream.write(encoded)
    return result


def check_reference_gate(truth_path, reference_path, fai_path, native_report_path,
                         protocol_path, protocol_sha256, report_path):
    return _check_reference_gate(truth_path, reference_path, fai_path, native_report_path,
                                 protocol_path, protocol_sha256, report_path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("truth-path", "reference-path", "fai-path", "native-report-path",
                 "protocol-path", "protocol-sha256", "report-path"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args()
    try:
        result = check_reference_gate(args.truth_path, args.reference_path, args.fai_path,
                                      args.native_report_path, args.protocol_path,
                                      args.protocol_sha256, args.report_path)
    except Exception as error:
        print(json.dumps(dict(status="incomplete", error_type=type(error).__name__,
                              error=str(error), scope="original_anchored_REF_only")), file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
