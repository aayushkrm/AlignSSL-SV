#!/usr/bin/env python3
"""Uniform sign-tolerant native metadata check; not REF, truth or scoring."""
from __future__ import annotations

import argparse
from hashlib import sha256
from itertools import zip_longest
import json
from pathlib import Path
import re
import sys

try:
    from . import diagnose_released_truth_metadata as bounded
    from .check_released_truth_metadata import sealed_input
    from .released_truth_units import classify_truth_record
except ImportError:
    import diagnose_released_truth_metadata as bounded
    from check_released_truth_metadata import sealed_input
    from released_truth_units import classify_truth_record

require = bounded.require
PURPOSE = "absolute_metadata_native_consistency_not_REF_or_scoring"
RESERVATION = 65 * 1024**2
MAX_REPORT = 64 * 1024
VERSIONS = dict(python="3.10.20", pysam="0.24.0", truvari="5.4.0",
                bcftools="1.23.1", htslib="1.23.1")
EXPECTED = dict(expected_records=11_490, expected_input_bytes=11_853_747,
                eligible_truth_sha256=bounded.SOURCE_SHA256,
                identity_order_sha256="13db07d2c659f578144067d45eea85684816cce6482230e190a1b01b8d627e37")
PIN_FILES = dict(source_script_sha256="check_released_truth_native.py",
                 truth_units_script_sha256="released_truth_units.py",
                 bounded_reader_script_sha256="diagnose_released_truth_metadata.py",
                 sealed_buffer_script_sha256="check_released_truth_metadata.py")
PROTOCOL_KEYS = set(EXPECTED) | set(PIN_FILES) | {
    "native_gate_approved", "purpose", "expected_sample", "versions",
    "input_read_reservation_bytes",
}


def scalar(value):
    if isinstance(value, (tuple, list)):
        require(len(value) == 1, "INFO must be scalar")
        return value[0]
    return value


def canonical_metadata(record, native):
    """Keep raw fields; return kind and sign flag, or reject the entire gate."""
    require(len(record.alts or ()) == 1, "eligible truth is not biallelic")
    sample = record.samples[0]
    gt = sample.get("GT")
    require(gt is not None and len(gt) == 2, "missing or non-diploid truth GT")
    sep = "|" if sample.phased else "/"
    genotype = sep.join("." if a is None else str(a) for a in gt)
    unit = classify_truth_record("0" * 64, 1, record.contig, record.pos,
                                 record.ref, record.alts[0], genotype).unit
    require(unit is not None, "prepared record violates frozen eligibility")
    require(scalar(record.info.get("SVTYPE")) == unit.kind,
            "SVTYPE contradicts canonical allele")
    size = scalar(record.info.get("SVLEN"))
    require(type(size) is int and abs(size) == unit.length,
            "SVLEN magnitude contradicts canonical allele")
    before_raw, before_native = str(record), str(native)
    require(before_raw == before_native, "native/raw whole rows differ")
    native_size, native_type = native.var_size(), native.var_type().name
    require(type(native_size) is int and native_size == unit.length,
            "native size contradicts canonical allele")
    require(native_type == unit.kind, "native type contradicts canonical allele")
    require(str(record) == before_raw and str(native) == before_native,
            "native metadata calls changed serialized row")
    expected_sign = unit.length if unit.kind == "INS" else -unit.length
    return unit.kind, size != expected_sign


def _versions():
    import importlib.metadata
    import pysam
    import truvari  # noqa: F401 -- require installed native reader before data
    from pysam.version import __bcftools_version__, __htslib_version__
    return dict(python=sys.version.split()[0], pysam=pysam.__version__,
                truvari=importlib.metadata.version("truvari"),
                bcftools=__bcftools_version__, htslib=__htslib_version__)


def _check_native(truth_path, protocol_path, protocol_sha256, report_path, expected):
    require(re.fullmatch(r"[0-9a-f]{64}", protocol_sha256 or "") is not None,
            "invalid protocol SHA-256")
    protocol_bytes = bounded._read_pinned(protocol_path, MAX_REPORT)
    require(sha256(protocol_bytes).hexdigest() == protocol_sha256, "protocol hash mismatch")
    try:
        protocol = json.loads(protocol_bytes.decode("utf-8"),
                              object_pairs_hook=bounded._pairs_no_duplicates)
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise bounded.CensusError("invalid protocol JSON") from None
    require(isinstance(protocol, dict) and set(protocol) == PROTOCOL_KEYS,
            "protocol schema mismatch")
    require(protocol["native_gate_approved"] is True, "native gate flag is not true")
    require(protocol["purpose"] == PURPOSE and protocol["expected_sample"] == "HG002",
            "incorrect scope or sample")
    require(all(protocol[k] == v and type(protocol[k]) is type(v) for k, v in expected.items()),
            "protocol input contract mismatch")
    require(type(expected["expected_records"]) is int
            and 0 < expected["expected_records"] <= bounded.MAX_ROWS,
            "invalid expected record count")
    require(type(expected["expected_input_bytes"]) is int
            and 0 < expected["expected_input_bytes"] <= bounded.MAX_INPUT,
            "invalid expected input size")
    require(type(protocol["input_read_reservation_bytes"]) is int
            and protocol["input_read_reservation_bytes"] == RESERVATION,
            "reservation mismatch")
    metadata_bytes = len(protocol_bytes)
    code_pins = {}
    for key, filename in PIN_FILES.items():
        content = bounded._read_pinned(Path(__file__).with_name(filename), MAX_REPORT)
        metadata_bytes += len(content)
        require(metadata_bytes <= bounded.MAX_REPORT, "pinned metadata exceeds byte cap")
        code_pins[key] = sha256(content).hexdigest()
        require(protocol[key] == code_pins[key], "local code pin mismatch")
    require(protocol["versions"] == VERSIONS and _versions() == VERSIONS,
            "scientific stack differs from protocol")
    require(sys.platform == "linux", "requires Linux sealed input buffer")
    report_path = bounded._check_report_path(report_path)
    payload, snapshot = bounded._read_source(truth_path)
    source_sha, source_bytes = sha256(payload).hexdigest(), len(payload)
    require(source_sha == expected["eligible_truth_sha256"]
            and source_bytes == expected["expected_input_bytes"], "truth source pin mismatch")
    fileformat, declarations, lexical_rows = bounded._header_and_rows(payload)
    require(fileformat == "##fileformat=VCFv4.2", "unexpected declared VCF version")
    schema = {d["id"]: (d["number"], d["type"]) for d in declarations}
    require(schema == {"SVLEN": ("1", "Integer"), "SVTYPE": ("1", "String")},
            "unexpected INFO declaration")
    require(len(lexical_rows) == expected["expected_records"], "lexical count mismatch")
    import pysam
    import truvari
    ids, order, kinds, sign_flags = set(), sha256(), {"INS": 0, "DEL": 0}, 0
    sentinel = object()
    with sealed_input(payload) as frozen_path:
        with pysam.VariantFile(frozen_path) as raw, truvari.VariantFile(frozen_path) as native:
            require(list(raw.header.samples) == list(native.header.samples) == ["HG002"],
                    "truth sample mismatch")
            for literal, rec, trv in zip_longest(lexical_rows, raw, native, fillvalue=sentinel):
                require(all(x is not sentinel for x in (literal, rec, trv)),
                        "lexical/native/raw stream lengths differ")
                fields = literal.split("\t")
                require(len(fields) == 10, "record column count mismatch")
                require(rec.id == trv.id == fields[2]
                        and re.fullmatch(r"[0-9a-f]{64}", rec.id or "") is not None,
                        "invalid or noncorresponding truth identity")
                require(rec.id not in ids, "duplicate truth identity")
                require(len(ids) < bounded.MAX_ROWS, "truth record cap exceeded")
                # Do not let HTSlib collapse duplicate INFO tags or convert bad
                # scalar text without detecting that lexical incompatibility.
                info = bounded._info_values(fields[7])
                for tag in ("SVTYPE", "SVLEN"):
                    state, value, duplicate, multiple = bounded._field_view(info.get(tag, []))
                    require(state == "value" and not duplicate and not multiple,
                            "literal INFO must be present and scalar")
                    if tag == "SVLEN":
                        require(re.fullmatch(r"[+-]?[0-9]+", value or "") is not None
                                and len(value) <= 4300, "literal SVLEN must be integer")
                        value = int(value)
                    require(value == scalar(rec.info.get(tag)) == scalar(trv.info.get(tag)),
                            "literal/native INFO values differ")
                kind, wrong_sign = canonical_metadata(rec, trv)
                ids.add(rec.id)
                order.update((rec.id + "\n").encode("ascii"))
                kinds[kind] += 1
                sign_flags += wrong_sign
    require(len(ids) == expected["expected_records"], "native count mismatch")
    require(order.hexdigest() == expected["identity_order_sha256"], "identity order mismatch")
    bounded._posthash(truth_path, snapshot, source_sha, source_bytes)
    result = dict(status="complete", purpose=PURPOSE, records=len(ids), unique_ids=len(ids),
                  canonical_kind_counts=kinds, global_sign_only_flags_retained=sign_flags,
                  identity_order_sha256=order.hexdigest(), eligible_truth_sha256=source_sha,
                  input_bytes=source_bytes, source_snapshot_stable=True, versions=VERSIONS,
                  protocol_sha256=protocol_sha256, **code_pins,
                  native_metadata_consistency="PASS", normative_compliance_claim=False,
                  reference_validation="UNASSESSED", denominator_validation="NOT_VALIDATED",
                  scoring_performed=False, input_unmodified=True, rows_repaired_or_dropped=0,
                  parser_input_kernel_sealed=True, parser_streams_share_pysam_backend=True,
                  serialized_rows_unchanged_by_native_calls=True,
                  input_read_reservation_bytes=RESERVATION,
                  opaque_parser_traffic_measured=False)
    output = (json.dumps(result, sort_keys=True, indent=2) + "\n").encode("ascii")
    require(len(output) <= MAX_REPORT and metadata_bytes + len(output) <= bounded.MAX_REPORT,
            "report and metadata exceed byte cap")
    with report_path.open("xb") as stream:
        stream.write(output)
    return result


def check_native(truth_path, protocol_path, protocol_sha256, report_path):
    return _check_native(truth_path, protocol_path, protocol_sha256, report_path, EXPECTED)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("truth-path", "protocol-path", "protocol-sha256", "report-path"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args()
    try:
        result = check_native(args.truth_path, args.protocol_path, args.protocol_sha256, args.report_path)
    except Exception as error:
        message = str(error) if isinstance(error, bounded.CensusError) else "native check operation failed"
        print(json.dumps(dict(status="incomplete", error_type=type(error).__name__, error=message)),
              file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
