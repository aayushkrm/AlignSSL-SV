#!/usr/bin/env python3
"""Read-only native/canonical metadata gate; NOT REF validation or scoring.

Use only on the separately prepared, SHA-pinned eligible plaintext truth.
No repair, filtering, normalization, or derived genomic output is performed.
External CPU/wall/address-space enforcement is required for real execution.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from hashlib import sha256
from itertools import zip_longest
import json
import os
from pathlib import Path
import sys

try:
    from .released_truth_units import classify_truth_record
except ImportError:
    from released_truth_units import classify_truth_record

MAX_INPUT = 16 * 1024**2
MAX_REPORT = 1024**2
MAX_RECORDS = 30_000


def require(condition, message):
    if not condition:
        raise ValueError(message)


def file_hash(path, cap):
    digest, count = sha256(), 0
    with Path(path).open("rb") as stream:
        while True:
            block = stream.read(min(1024**2, cap - count + 1))
            if not block:
                break
            count += len(block)
            require(count <= cap, "input byte cap exceeded")
            digest.update(block)
    return digest.hexdigest(), count


def scalar(value):
    if isinstance(value, (tuple, list)):
        require(len(value) == 1, "INFO must be scalar")
        return value[0]
    return value


def frozen_bytes(path, cap):
    with Path(path).open("rb") as stream:
        payload = stream.read(cap + 1)
    require(len(payload) <= cap, "input byte cap exceeded")
    return payload


@contextmanager
def sealed_input(payload):
    """Linux UAPI via libc; the pinned Python build lacks memfd/seal bindings."""
    import ctypes
    import fcntl
    require(sys.platform == "linux", "requires Linux sealed input buffer")
    require(isinstance(payload, bytes) and len(payload) <= MAX_INPUT, "input byte cap exceeded")
    lib = ctypes.CDLL(None, use_errno=True)
    require(hasattr(lib, "memfd_create"), "libc memfd_create unavailable")
    create = lib.memfd_create
    create.argtypes, create.restype = (ctypes.c_char_p, ctypes.c_uint), ctypes.c_int
    # Verified host Linux UAPI: CLOEXEC=1, ALLOW_SEALING=2; ADD/GET=1033/1034;
    # SEAL_SEAL/SHRINK/GROW/WRITE bits=1/2/4/8. No architecture-specific syscall.
    fd = create(b"truth-metadata-input", 3)
    if fd < 0:
        errno = ctypes.get_errno()
        raise OSError(errno, os.strerror(errno))
    try:
        offset = 0
        while offset < len(payload):
            written = os.write(fd, payload[offset:])
            require(written > 0, "input-buffer write stalled")
            offset += written
        fcntl.fcntl(fd, 1033, 15)
        require(fcntl.fcntl(fd, 1034) & 15 == 15, "input-buffer seals missing")
        yield f"/proc/self/fd/{fd}"
    finally:
        os.close(fd)


def canonical_metadata(record, native):
    """Fail the whole gate on any contradiction; return no repaired record."""
    require(len(record.alts or ()) == 1, "eligible truth is not biallelic")
    sample = record.samples[0]
    gt = sample.get("GT")
    require(gt is not None and len(gt) == 2, "missing or non-diploid truth GT")
    sep = "|" if sample.phased else "/"
    genotype = sep.join("." if allele is None else str(allele) for allele in gt)
    unit = classify_truth_record("0" * 64, 1, record.contig, record.pos,
                                 record.ref, record.alts[0], genotype).unit
    require(unit is not None, "prepared record violates frozen eligibility")
    require(scalar(record.info.get("SVTYPE")) == unit.kind,
            "SVTYPE contradicts canonical allele")
    size = scalar(record.info.get("SVLEN"))
    require(type(size) is int and size == (unit.length if unit.kind == "INS" else -unit.length),
            "SVLEN contradicts canonical signed allele length")
    require(native.var_size() == unit.length, "native size contradicts canonical allele")
    require(native.var_type().name == unit.kind, "native type contradicts canonical allele")
    return unit.kind


def check_metadata(truth_path, protocol_path, protocol_sha, report_path):
    protocol_path, truth_path, report_path = map(Path, (protocol_path, truth_path, report_path))
    protocol_bytes = frozen_bytes(protocol_path, MAX_REPORT)
    require(sha256(protocol_bytes).hexdigest() == protocol_sha, "protocol hash mismatch")
    protocol = json.loads(protocol_bytes)
    require(protocol.get("metadata_gate_approved") is True, "metadata gate not approved")
    expected = protocol.get("expected_records")
    require(type(expected) is int and 0 < expected <= MAX_RECORDS, "invalid expected record count")
    require(protocol.get("expected_sample") == "HG002", "unexpected truth sample")
    require(protocol.get("purpose") == "metadata_only_not_REF_or_scoring", "incorrect scope")
    require(protocol.get("source_script_sha256") == file_hash(Path(__file__), MAX_REPORT)[0],
            "source script hash mismatch")
    helper = Path(__file__).with_name("released_truth_units.py")
    require(protocol.get("truth_units_script_sha256") == file_hash(helper, MAX_REPORT)[0],
            "truth helper hash mismatch")
    require(not truth_path.is_symlink(), "symlink input not permitted")
    before = truth_path.stat()
    require(before.st_size <= MAX_INPUT, "truth input exceeds byte cap")
    require(not report_path.exists(), "report already exists")
    real_parent = report_path.parent.resolve()
    require(not any((p / ".git").exists() for p in (real_parent, *real_parent.parents)),
            "report must be outside Git")
    require(report_path.parent.is_dir(), "report directory missing")
    payload = frozen_bytes(truth_path, MAX_INPUT)
    source_sha, source_bytes = sha256(payload).hexdigest(), len(payload)
    require(source_sha == protocol.get("eligible_truth_sha256"), "eligible truth hash mismatch")
    import importlib.metadata
    import pysam
    import truvari
    from pysam.version import __bcftools_version__, __htslib_version__
    versions = dict(python=sys.version.split()[0], pysam=pysam.__version__,
                    truvari=importlib.metadata.version("truvari"),
                    bcftools=__bcftools_version__, htslib=__htslib_version__)
    require(versions == protocol.get("versions"), "scientific stack differs from protocol")
    require(versions == dict(python="3.10.20", pysam="0.24.0", truvari="5.4.0",
                             bcftools="1.23.1", htslib="1.23.1"), "unpinned stack")
    ids, kind_counts, identity_digest = set(), {"INS": 0, "DEL": 0}, sha256()
    sentinel = object()
    # Linux anonymous immutable input buffer: both standard parsers see exactly
    # the bounded bytes hashed above, not a reopened/mutable scientific source.
    # Opening the proc paths separately provides independent file positions.
    with sealed_input(payload) as frozen_path:
        with pysam.VariantFile(frozen_path) as raw, truvari.VariantFile(frozen_path) as native:
            require(list(raw.header.samples) == ["HG002"], "truth sample mismatch")
            for rec, trv in zip_longest(raw, native, fillvalue=sentinel):
                require(rec is not sentinel and trv is not sentinel, "native/raw stream lengths differ")
                require(str(rec) == str(trv), "native/raw whole rows differ")
                require(len(ids) < MAX_RECORDS, "truth record cap exceeded")
                require(isinstance(rec.id, str) and len(rec.id) == 64
                        and all(c in "0123456789abcdef" for c in rec.id), "invalid truth identity")
                require(rec.id not in ids, "duplicate truth identity")
                ids.add(rec.id)
                identity_digest.update((rec.id + "\n").encode("ascii"))
                kind_counts[canonical_metadata(rec, trv)] += 1
    require(len(ids) == expected, "prepared truth cardinality differs from inventory")
    final_sha, final_bytes = file_hash(truth_path, MAX_INPUT)
    after = truth_path.stat()
    require((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns)
            == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns),
            "truth snapshot changed")
    require(final_sha == source_sha and final_bytes == source_bytes, "truth bytes changed")
    result = dict(status="complete", scope="canonical_INFO_native_metadata_only", records=len(ids),
                  kind_counts=kind_counts, identity_order_sha256=identity_digest.hexdigest(),
                  eligible_truth_sha256=source_sha, input_bytes=source_bytes, versions=versions,
                  protocol_sha256=protocol_sha, reference_validation_performed=False,
                  scoring_performed=False, input_unmodified=True,
                  parser_input_bounded_and_kernel_sealed=True,
                  input_read_reservation_bytes=65 * 1024**2,
                  opaque_parser_traffic_not_measured=True)
    output = (json.dumps(result, sort_keys=True, indent=2) + "\n").encode("ascii")
    require(len(output) <= MAX_REPORT, "report byte cap exceeded")
    with report_path.open("xb") as report:
        report.write(output)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("truth-path", "protocol-path", "protocol-sha256", "report-path"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args()
    try:
        result = check_metadata(args.truth_path, args.protocol_path, args.protocol_sha256, args.report_path)
    except Exception as error:
        print(json.dumps(dict(status="failed", error_type=type(error).__name__,
                              error=str(error), scope="metadata_only_not_REF_or_scoring")), file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
