"""One byte-preserving ZIP transport and standard HTSlib compatibility gate.

No custom VCF parser, repair, transformation, sorting, truth or scoring.
Genomic reads are length bounded, including the pipe into HTSlib. Failure
preserves outputs and full reservations. This does not reopen the old stager.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import threading
import zipfile

import pysam

if __package__:
    from .stage_svpg_callsets import CALLERS, MEMBERS, REPO, _snapshot
else:
    from stage_svpg_callsets import CALLERS, MEMBERS, REPO, _snapshot


def pinned_json(path, digest):
    with Path(path).open("rb") as handle:
        raw = handle.read(1024**2 + 1)
    if len(raw) > 1024**2 or hashlib.sha256(raw).hexdigest() != digest:
        raise ValueError("Metadata size or SHA256 mismatch")
    return json.loads(raw)


def copy_member(stream, output, expected_bytes):
    digest, consumed, newlines, last = hashlib.sha256(), 0, 0, b""
    while consumed < expected_bytes:
        block = stream.read(min(65536, expected_bytes - consumed))
        if not block:
            raise ValueError("ZIP member truncated")
        consumed += len(block)
        digest.update(block)
        newlines += block.count(b"\n")
        last = block[-1:]
        output.write(block)
    # This bounded EOF probe completes ZIP CRC validation and detects surplus.
    if stream.read(1):
        raise ValueError("ZIP member exceeds reservation")
    return {"decoded_bytes": consumed, "source_sha256": digest.hexdigest(),
            "newlines": newlines, "last_byte_lf": last == b"\n"}


def check_htslib(path, expected_bytes, digest, expected_sample, contigs):
    """Feed exactly the pinned length to the standard text parser, hashing once.

    A pipe prevents file growth from extending an HTSlib read past its budget.
    No record is rewritten. The feeder is one thread in the guarded process.
    """
    path = Path(path)
    counters = {"records": 0, "pos_zero": 0, "pos_length_plus_one": 0}
    result = {}
    with path.open("rb") as source:
        before = _snapshot(path, source)
        if before[2] != expected_bytes:
            raise ValueError("Compatibility input size differs")
        read_fd, write_fd = os.pipe()
        def feed():
            consumed, sha = 0, hashlib.sha256()
            try:
                with os.fdopen(write_fd, "wb") as pipe:
                    while consumed < expected_bytes:
                        block = source.read(min(65536, expected_bytes - consumed))
                        if not block:
                            raise ValueError("Compatibility input truncated")
                        consumed += len(block)
                        sha.update(block)
                        pipe.write(block)
                if _snapshot(path, source) != before or sha.hexdigest() != digest:
                    raise ValueError("Compatibility source changed or SHA256 differs")
                result.update(bytes_read=consumed, sha256=sha.hexdigest())
            except BaseException as exc:
                result["error"] = exc
        worker = threading.Thread(target=feed, daemon=True)
        worker.start()
        try:
            with os.fdopen(read_fd, "rb") as pipe, pysam.VariantFile(pipe, "r") as vcf:
                if list(vcf.header.samples) != [expected_sample]:
                    raise ValueError("Released sample column differs")
                observed = [(name, vcf.header.contigs[name].length) for name in vcf.header.contigs]
                if observed != [(row["name"], row["length"]) for row in contigs]:
                    raise ValueError("Released contig dictionary differs")
                lengths = dict(observed)
                for record in vcf:
                    if record.contig not in lengths:
                        raise ValueError("Record contig outside frozen dictionary")
                    counters["records"] += 1
                    counters["pos_zero"] += record.pos == 0
                    counters["pos_length_plus_one"] += record.pos == lengths[record.contig] + 1
        finally:
            worker.join(timeout=5)
            if worker.is_alive():
                raise RuntimeError("HTSlib feeder did not stop")
        if "error" in result:
            raise result["error"]
        return {**counters, "compatibility_bytes_read": result["bytes_read"],
                "verified_sha256": result["sha256"], "positions_repaired": 0,
                "records_rewritten": 0, "records_filtered": 0}


def run_transport(archive_path, outdir, protocol_path, protocol_sha256):
    protocol = pinned_json(protocol_path, protocol_sha256)
    if (protocol.get("purpose") != "transport_two_unfinished_v1"
            or protocol.get("body_read_approved") is not True
            or not protocol.get("independent_review")
            or protocol.get("members") != list(MEMBERS)
            or protocol.get("execution_callers") != list(CALLERS[-2:])
            or set(protocol.get("reused_completed_callers", {})) != set(CALLERS[:4])):
        raise ValueError("Separate review and fixed six-caller roster required")
    if (pysam.__version__ != protocol["pysam_version"]
            or pysam.__samtools_version__ != protocol["local_samtools_version"]):
        raise ValueError("pysam or bundled library version differs")
    for key in ("charged_prior_source_bytes", "charged_prior_global_bytes",
                "transport_reservation_bytes", "compatibility_reservation_bytes"):
        if type(protocol[key]) is not int or protocol[key] < 0:
            raise ValueError("Nonnegative integer traffic reservations required")
    if protocol["charged_prior_global_bytes"] < protocol["charged_prior_source_bytes"]:
        raise ValueError("Aggregate prior charge below source charge")
    archive_path, outdir = Path(archive_path), Path(outdir)
    if outdir.exists() or outdir.is_symlink():
        raise FileExistsError("Transport directory already exists")
    outdir = outdir.resolve()
    if outdir == REPO or REPO in outdir.parents or any((p / ".git").exists() for p in outdir.parents):
        raise ValueError("Raw outputs must remain outside Git")
    for name, maximum in (("source_limit_bytes", 4 * 1024**3),
                           ("global_limit_bytes", 12 * 1024**3)):
        if type(protocol[name]) is not int or not 0 < protocol[name] <= maximum:
            raise ValueError("Unchanged source/global limit required")
    ledger = {"status": "incomplete", "protocol_sha256": protocol_sha256,
              "transported_callers": {}, "compatibility": {},
              "scientific_scoring_performed": False, "pysam_version": pysam.__version__,
              "local_samtools_version": pysam.__samtools_version__}
    with archive_path.open("rb") as source:
        before = _snapshot(archive_path, source)
        if before[2] != protocol["archive_bytes"]:
            raise ValueError("Archive size differs")
        md5, sha = hashlib.md5(), hashlib.sha256()
        remaining = before[2]
        while remaining:
            block = source.read(min(1024**2, remaining))
            if not block:
                raise ValueError("Archive truncated")
            md5.update(block)
            sha.update(block)
            remaining -= len(block)
        if (md5.hexdigest() != protocol["archive_md5"] or sha.hexdigest() != protocol["archive_sha256"]
                or _snapshot(archive_path, source) != before):
            raise ValueError("Archive integrity or snapshot differs")
        source.seek(0)
        with zipfile.ZipFile(source) as archive:
            names = archive.namelist()
            if len(names) != len(set(names)):
                raise ValueError("Duplicate ZIP members")
            selected = {c: archive.getinfo(m) for c, m in zip(CALLERS, MEMBERS)}
            transport_bytes = sum(selected[c].file_size for c in CALLERS[-2:])
            inputs = {}
            for caller, spec in protocol["reused_completed_callers"].items():
                path = Path(spec["staged_path"]).resolve()
                if (path == REPO or REPO in path.parents
                        or type(spec["staged_bytes"]) is not int or spec["staged_bytes"] <= 0):
                    raise ValueError("Positive-size reused input must remain outside Git")
                record = pinned_json(spec["report_path"], spec["report_sha256"])["completed_callers"][caller]
                item = selected[caller]
                if (record["member"] != item.filename or record["decoded_bytes"] != item.file_size
                        or not record["selected_member_crc_verified"] or record["crc32"] != f"{item.CRC:08x}"
                        or record["staged_sha256"] != spec["staged_sha256"]
                        or record["source_sha256"] != spec["source_sha256"]):
                    raise ValueError("Completed member evidence differs")
                inputs[caller] = {**spec, "expected_records": record["records"]}
            compatibility_bytes = transport_bytes + sum(s["staged_bytes"] for s in inputs.values())
            source_charge = protocol["charged_prior_source_bytes"] + transport_bytes
            global_charge = protocol["charged_prior_global_bytes"] + transport_bytes + compatibility_bytes
            if (transport_bytes + 2 != protocol["transport_reservation_bytes"]
                    or compatibility_bytes != protocol["compatibility_reservation_bytes"]
                    or source_charge + 2 > protocol["source_limit_bytes"]
                    or global_charge + 2 > protocol["global_limit_bytes"]):
                raise ValueError("Transport/compatibility reservation or ceiling differs")
            ledger.update(conservative_source_charge_bytes=source_charge + 2,
                          conservative_global_charge_bytes=global_charge + 2,
                          transport_reservation_bytes=transport_bytes + 2,
                          compatibility_reservation_bytes=compatibility_bytes)
            if os.statvfs(outdir.parent).f_bavail * os.statvfs(outdir.parent).f_frsize < 10 * 1024**3 + transport_bytes + 32 * 1024**2:
                raise ValueError("Insufficient free-space headroom")
            outdir.mkdir(mode=0o700)
            try:
                for caller in CALLERS[-2:]:
                    item = selected[caller]
                    if item.flag_bits & 0x41 or item.volume != 0:
                        raise ValueError("Encrypted or multi-disk member")
                    path = outdir / f"{caller}.vcf"
                    with archive.open(item) as member, path.open("xb") as output:
                        record = copy_member(member, output, item.file_size)
                    ledger["transported_callers"][caller] = {**record, "member": item.filename,
                        "crc32": f"{item.CRC:08x}", "selected_member_crc_verified": True, "path": str(path)}
                    rows = record["newlines"] + int(not record["last_byte_lf"]) - protocol["header_line_counts"][caller]
                    inputs[caller] = {"staged_path": str(path), "staged_bytes": item.file_size,
                                      "staged_sha256": record["source_sha256"], "expected_records": rows}
                if _snapshot(archive_path, source) != before:
                    raise ValueError("Archive changed during transport")
                for caller in CALLERS:
                    spec = inputs[caller]
                    ledger["compatibility"][caller] = check_htslib(
                        spec["staged_path"], spec["staged_bytes"], spec["staged_sha256"],
                        protocol["samples"][caller], protocol["contigs"])
                    if ledger["compatibility"][caller]["records"] != spec["expected_records"]:
                        raise ValueError("Standard-parser count differs from source row census")
                ledger["status"] = "complete"
            except BaseException as exc:
                ledger.update(exception_type=type(exc).__name__, exception_message=str(exc)[:500])
                raise
            finally:
                with (outdir / "transport_report.json").open("x") as output:
                    json.dump(ledger, output, indent=2, sort_keys=True)
                    output.write("\n")
    return ledger


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("archive", "outdir", "protocol"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    parser.add_argument("--protocol-sha256", required=True)
    args = parser.parse_args()
    run_transport(args.archive, args.outdir, args.protocol, args.protocol_sha256)
