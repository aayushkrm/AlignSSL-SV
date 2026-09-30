"""Inventory a checksum-verified local source ZIP; optionally inspect VCF headers.

This is the whole-archive alternative when strict remote Range validation is
unavailable. No member is extracted, executed, or scored. Whole-archive MD5 and
SHA-256 are computed by streaming, and VCF header decompression is bounded.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import re
import zipfile
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


def audit_zip(path: Path, expected_size: int, official_md5: str,
              source_url: str, header_members: list[str] | None = None,
              max_header_bytes: int = 1_048_576) -> dict:
    if expected_size <= 0 or not re.fullmatch(r"[0-9a-fA-F]{32}", official_md5):
        raise ValueError("Positive manifest size and official MD5 are required")
    if not 0 < max_header_bytes <= 1_048_576:
        raise ValueError("Header limit must be between 1 byte and 1 MiB")
    parts = urlsplit(source_url)
    if parts.scheme != "https" or not parts.netloc or parts.username or parts.password:
        raise ValueError("Source must be a credential-free HTTPS URL")
    safe_url = urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))
    header_members = header_members or []
    if len(header_members) != len(set(header_members)) or len(header_members) > 32:
        raise ValueError("Select at most 32 distinct VCF header members")
    md5, sha256 = hashlib.md5(), hashlib.sha256()
    with path.open("rb") as source:
        before = path.stat()
        if before.st_size != expected_size:
            raise ValueError("Local archive size differs from source manifest")
        while block := source.read(1_048_576):
            md5.update(block)
            sha256.update(block)
        if md5.hexdigest() != official_md5.lower():
            raise ValueError("Whole-archive MD5 differs from source manifest")
        source.seek(0)
        headers, members = [], []
        with zipfile.ZipFile(source) as archive:
            names = [item.filename for item in archive.infolist()]
            if len(names) != len(set(names)):
                raise ValueError("Duplicate ZIP names are ambiguous")
            for item in archive.infolist():
                if item.flag_bits & 0x41 or item.volume != 0:
                    raise ValueError("Encrypted or multi-disk members are unsupported")
                members.append({
                    "name": item.filename, "compressed_size": item.compress_size,
                    "uncompressed_size": item.file_size,
                    "compression_method": item.compress_type,
                    "crc32": f"{item.CRC:08x}", "header_offset": item.header_offset,
                })
            for name in header_members:
                if name not in names or not name.endswith((".vcf", ".vcf.gz")):
                    raise ValueError(f"Selected VCF member missing or unsupported: {name}")
                with archive.open(name) as member:
                    stream = gzip.GzipFile(fileobj=member) if name.endswith(".gz") else member
                    try:
                        header = read_header(stream, max_header_bytes)
                    finally:
                        if stream is not member:
                            stream.close()
                headers.append({"member": name, "header_lines": header,
                                "body_records_parsed": 0})
        after = path.stat()
        if (before.st_size, before.st_mtime_ns, before.st_ino) != (
                after.st_size, after.st_mtime_ns, after.st_ino):
            raise ValueError("Source archive changed during inspection")
    return {
        "schema_version": 1, "purpose": "Source inventory and header semantics only",
        "source_url": safe_url, "source_url_query_redacted": bool(parts.query),
        "source_archive_name": path.name, "source_manifest_bytes": expected_size,
        "actual_bytes": before.st_size, "official_md5": official_md5.lower(),
        "actual_md5": md5.hexdigest(), "sha256": sha256.hexdigest(),
        "whole_archive_md5_verification": "VERIFIED",
        "whole_archive_payload_downloaded": True,
        "member_count": len(members), "members": members, "vcf_headers": headers,
        "member_extraction_performed": False, "downloaded_code_executed": False,
        "biological_records_parsed": 0, "truth_or_performance_outputs_scored": False,
        "max_uncompressed_header_bytes_per_member": max_header_bytes,
        "limits": ["Names and header declarations do not establish caller stage or callability.",
                   "Header declarations do not establish score calibration or record completeness.",
                   "No internal-candidate ceiling, genotype accuracy or publication claim."],
    }


def read_header(stream: io.BufferedIOBase, max_bytes: int) -> list[str]:
    lines, used = [], 0
    while used < max_bytes:
        raw = stream.readline(max_bytes - used + 1)
        used += len(raw)
        if used > max_bytes:
            raise ValueError("VCF header exceeds decompression budget")
        if not raw or not raw.startswith(b"#") or not raw.endswith(b"\n"):
            raise ValueError("VCF header missing, malformed or truncated")
        line = raw.decode("utf-8", errors="strict").rstrip("\r\n")
        lines.append(line)
        if line.startswith("#CHROM\t"):
            if len(line.split("\t")) < 8:
                raise ValueError("Malformed #CHROM header")
            return lines
    raise ValueError("VCF header exceeds decompression budget")


def write_report(out: Path, report: dict) -> None:
    checksum = out.with_suffix(out.suffix + ".sha256")
    if out.exists() or out.is_symlink() or checksum.exists() or checksum.is_symlink():
        raise FileExistsError("Refusing to overwrite output or checksum")
    data = (json.dumps(report, indent=2, sort_keys=True) + "\n").encode()
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("xb") as handle:
        handle.write(data)
    with checksum.open("x") as handle:
        handle.write(f"{hashlib.sha256(data).hexdigest()}  {out.name}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--expected-size", type=int, required=True)
    parser.add_argument("--official-md5", required=True)
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--vcf-header-members", nargs="*", default=[])
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists() or args.out.is_symlink():
        parser.error("Refusing to overwrite existing output")
    try:
        report = audit_zip(args.archive, args.expected_size, args.official_md5,
                           args.source_url, args.vcf_header_members)
        write_report(args.out, report)
    except (ValueError, OSError, zipfile.BadZipFile) as exc:
        parser.error(str(exc))
    print(f"MD5 verified; {report['member_count']} members; "
          f"{len(report['vcf_headers'])} VCF headers; no records scored")


if __name__ == "__main__":
    main()
