"""SHA-pinned truth header only, with all decoded read-ahead bounded.

Decode one standard gzip member prefix once, with zlib's output limit. Only
header lines through #CHROM are interpreted; no body row is parsed or saved.
First-member EOF/CRC is reported honestly, not inferred for the complete VCF.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import resource
import sys
import time
import zlib

CAP = 1024**2


def snapshot(path, handle):
    def signature(s):
        return (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    opened = signature(os.fstat(handle.fileno()))
    if signature(path.stat()) != opened:
        raise ValueError("Truth path and descriptor differ")
    return opened


def inspect_header(path, expected_bytes, expected_sha256, decoded_cap=CAP):
    if (type(expected_bytes) is not int or not 0 < expected_bytes <= 2 * 1024**3
            or not re.fullmatch(r"[0-9a-f]{64}", expected_sha256)
            or type(decoded_cap) is not int or not 0 < decoded_cap <= CAP):
        raise ValueError("Explicit source and decoded-byte pins required")
    path = Path(path)
    with path.open("rb") as source:
        before = snapshot(path, source)
        if before[2] != expected_bytes:
            raise ValueError("Truth compressed size differs")
        digest, remaining = hashlib.sha256(), expected_bytes
        while remaining:
            chunk = source.read(min(CAP, remaining))
            if not chunk:
                raise ValueError("Truth compressed source truncated")
            digest.update(chunk)
            remaining -= len(chunk)
        if digest.hexdigest() != expected_sha256 or snapshot(path, source) != before:
            raise ValueError("Truth SHA or snapshot differs")
        source.seek(0)
        prefix = source.read(min(65536, expected_bytes))
        decoder = zlib.decompressobj(wbits=31)
        decoded = decoder.decompress(prefix, max_length=decoded_cap)
        if snapshot(path, source) != before:
            raise ValueError("Truth changed during prefix read")
    header = []
    columns = None
    for line in io.BytesIO(decoded):
        if not line.endswith(b"\n"):
            raise ValueError("Header line not complete within bounded prefix")
        text = line.decode("utf-8").rstrip("\r\n")
        if text.startswith("##"):
            header.append(line)
        elif text.startswith("#CHROM\t"):
            columns = text.split("\t")
            if columns[:9] != "#CHROM POS ID REF ALT QUAL FILTER INFO FORMAT".split() or len(columns) < 10:
                raise ValueError("Truth sample column header differs")
            header.append(line)
            break
        else:
            raise ValueError("Non-header line before #CHROM")
    if columns is None:
        raise ValueError("#CHROM absent in one bounded gzip prefix; no retry")
    raw = b"".join(header)
    lines = [line.decode("utf-8").rstrip("\r\n") for line in header]
    return {"status": "complete", "source_compressed_sha256": expected_sha256,
            "source_compressed_bytes": expected_bytes, "header_sha256": hashlib.sha256(raw).hexdigest(),
            "header_bytes": len(raw), "decoded_prefix_bytes_including_read_ahead": len(decoded),
            "compressed_prefix_bytes": len(prefix), "first_gzip_member_eof_crc_verified": decoder.eof,
            "whole_gzip_crc_verified": False, "header_lines": lines, "samples": columns[9:],
            "contig_declarations": [s for s in lines if s.startswith("##contig=")],
            "gt_phase_declarations": [s for s in lines if s.startswith("##FORMAT=")],
            "body_records_parsed": 0, "body_records_saved": 0, "bed_read": False,
            "eligibility_denominator_computed": False, "scientific_scoring_performed": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--protocol-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    with args.protocol.open("rb") as handle:
        raw = handle.read(CAP + 1)
    if len(raw) > CAP or hashlib.sha256(raw).hexdigest() != args.protocol_sha256:
        raise ValueError("Protocol SHA or size differs")
    p = json.loads(raw)
    if (p.get("purpose") != "current_Q100_truth_header_only_v1"
            or p.get("header_only_approved") is not True or not p.get("independent_review")
            or p["decoded_reservation_bytes"] != CAP
            or type(p["charged_prior_global_bytes"]) is not int or p["charged_prior_global_bytes"] < 0
            or type(p["global_limit_bytes"]) is not int
            or p["charged_prior_global_bytes"] + CAP > p["global_limit_bytes"]
            or p["global_limit_bytes"] > 12 * 1024**3):
        raise ValueError("Separate review and retained traffic reservation required")
    if args.output.exists() or args.output.is_symlink():
        raise FileExistsError("Header report must be fresh")
    for ancestor in (args.output.resolve(), *args.output.resolve().parents):
        if (ancestor / ".git").exists():
            raise ValueError("Execution outputs must remain outside Git")
    resource.setrlimit(resource.RLIMIT_CPU, (30, 30))
    if sys.platform == "linux":
        resource.setrlimit(resource.RLIMIT_AS, (256 * 1024**2, 256 * 1024**2))
    start = time.monotonic()
    before_cpu = resource.getrusage(resource.RUSAGE_SELF)
    report = {"status": "incomplete", "protocol_sha256": args.protocol_sha256,
              "conservative_global_charge_bytes": p["charged_prior_global_bytes"] + CAP,
              "decoded_reservation_bytes": CAP}
    try:
        report.update(inspect_header(p["truth_path"], p["truth_compressed_bytes"], p["truth_sha256"]))
    except BaseException as exc:
        report.update(exception_type=type(exc).__name__, exception_message=str(exc)[:300])
        raise
    finally:
        after_cpu = resource.getrusage(resource.RUSAGE_SELF)
        report.update(wall_seconds=time.monotonic() - start,
                      cpu_seconds=(after_cpu.ru_utime + after_cpu.ru_stime - before_cpu.ru_utime - before_cpu.ru_stime),
                      process_peak_rss_bytes=after_cpu.ru_maxrss * (1 if sys.platform == "darwin" else 1024))
        with args.output.open("x") as handle:
            json.dump(report, handle, indent=2, sort_keys=True)
            handle.write("\n")


if __name__ == "__main__":
    main()
