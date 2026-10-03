"""Inventory a checksum-verified local TAR; optionally inspect one CSV header.

The complete file is hashed before streaming TAR inspection. Regular files and
zero-size directories are supported. No member is written to disk or executed, and no CSV
records are parsed, retained, or printed.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import os
import re
import tarfile
import zlib
from pathlib import Path, PurePosixPath, PureWindowsPath
from urllib.parse import urlsplit, urlunsplit


MAX_ARCHIVE_BYTES = 1_073_741_824  # 1 GiB
MAX_UNCOMPRESSED_TAR_BYTES = 250 * 1_048_576
MAX_MEMBER_BYTES = 128 * 1_048_576
MAX_MEMBERS = 1_000
MAX_HEADER_LINE_BYTES = 64 * 1_024
HASH_BLOCK_BYTES = 1_048_576
COPY_BLOCK_BYTES = 64 * 1_024
NUMERIC_FIELD_RE = re.compile(r"^[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?$")


def sanitize_source_url(source_url: str | None) -> tuple[str | None, bool]:
    if source_url is None:
        return None, False
    try:
        parts = urlsplit(source_url)
        host = parts.hostname
        port = parts.port
    except ValueError as exc:
        raise ValueError("Source URL is malformed") from exc
    if parts.scheme != "https" or not host:
        raise ValueError("Source URL must be HTTPS")
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"
    netloc = host if port is None else f"{host}:{port}"
    safe_url = urlunsplit(("https", netloc, parts.path, "", ""))
    redacted = bool(parts.username or parts.password or parts.query or parts.fragment)
    return safe_url, redacted


class DecompressionBudget:
    """One aggregate budget shared by TAR and nested CSV gzip output."""

    def __init__(self, limit: int):
        self.limit = limit
        self.bytes_read = 0
        self.by_stream = {}

    def account(self, amount: int, stream_name: str) -> None:
        if self.bytes_read + amount > self.limit:
            raise ValueError("Aggregate decompression budget exceeded")
        self.bytes_read += amount
        self.by_stream[stream_name] = self.by_stream.get(stream_name, 0) + amount


class BoundedReader:
    """Read a stream while charging every returned byte to a shared budget."""

    def __init__(self, source: io.BufferedIOBase, budget: DecompressionBudget,
                 stream_name: str):
        self.source = source
        self.budget = budget
        self.stream_name = stream_name

    def read(self, size: int = -1) -> bytes:
        remaining = self.budget.limit - self.budget.bytes_read
        if size is None or size < 0:
            size = remaining + 1
        request_size = min(size, remaining + 1)
        reader = getattr(self.source, "read1", None)
        data = reader(request_size) if callable(reader) else self.source.read(request_size)
        if len(data) > remaining:
            raise ValueError("Aggregate decompression budget exceeded")
        self.budget.account(len(data), self.stream_name)
        return data

    def readline(self, size: int = -1) -> bytes:
        if size is None or size < 0:
            size = self.budget.limit - self.budget.bytes_read + 1
        line = bytearray()
        while len(line) < size:
            byte = self.read(1)
            if not byte:
                break
            line.extend(byte)
            if byte == b"\n":
                break
        return bytes(line)

    def drain(self) -> None:
        while self.read(COPY_BLOCK_BYTES):
            pass


class TarMemberReader:
    """A non-seeking view of one TAR member, limited to its declared size."""

    def __init__(self, source: BoundedReader, size: int):
        self.source = source
        self.remaining = size

    def read(self, size: int = -1) -> bytes:
        if size is None or size < 0 or size > self.remaining:
            size = self.remaining
        if size == 0:
            return b""
        data = self.source.read(size)
        self.remaining -= len(data)
        return data

    def readline(self, size: int = -1) -> bytes:
        if size is None or size < 0:
            size = self.remaining
        line = bytearray()
        while len(line) < size and self.remaining:
            byte = self.read(1)
            if not byte:
                break
            line.extend(byte)
            if byte == b"\n":
                break
        return bytes(line)

    def drain(self) -> None:
        while self.remaining:
            if not self.read(min(COPY_BLOCK_BYTES, self.remaining)):
                raise ValueError("TAR member ended before its declared size")


def _validate_fieldnames(fields: list[str], delimiter: str | None,
                         required_columns: frozenset[str],
                         allowed_columns: frozenset[str]) -> None:
    if delimiter not in {",", "\t", ";", "|"} or len(fields) < 2:
        raise ValueError("CSV header must contain at least two fields and a supported delimiter")
    if not required_columns or not allowed_columns or not required_columns.issubset(allowed_columns):
        raise ValueError("A valid required-column and allowed-column signature is mandatory")
    seen = set()
    for index, field in enumerate(fields, start=1):
        if not field or field != field.strip():
            raise ValueError(f"CSV header has an empty or untrimmed field name at column {index}")
        if NUMERIC_FIELD_RE.fullmatch(field):
            raise ValueError(f"CSV header field name at column {index} is numeric")
        if any(ord(char) < 32 or ord(char) == 127 for char in field):
            raise ValueError(f"CSV header field name at column {index} contains a control character")
        if not any(char.isalpha() or char == "_" for char in field):
            raise ValueError(f"CSV header field name at column {index} is not a name")
        folded = field.casefold()
        if folded in seen:
            raise ValueError(f"CSV header has a duplicate field name at column {index}")
        seen.add(folded)
    if not required_columns.issubset(fields):
        raise ValueError("CSV header does not contain all required columns")
    if not set(fields).issubset(allowed_columns):
        raise ValueError("CSV header contains unrecognized field names")


def read_table_header(stream: io.BufferedIOBase,
                      required_columns: frozenset[str],
                      allowed_columns: frozenset[str],
                      max_bytes: int = MAX_HEADER_LINE_BYTES,
                      allow_leading_command_comment: bool = False) -> dict:
    if not 0 < max_bytes <= MAX_HEADER_LINE_BYTES:
        raise ValueError("CSV header-line limit must be between 1 byte and 64 KiB")
    raw = stream.readline(max_bytes + 1)
    comment_bytes = 0
    comment_sha256 = None
    if allow_leading_command_comment and raw.startswith(b"# "):
        if len(raw) >= max_bytes or not raw.endswith(b"\n"):
            raise ValueError("Leading command comment exceeds the shared header-byte limit")
        comment_bytes = len(raw)
        comment_sha256 = hashlib.sha256(raw).hexdigest()
        raw = stream.readline(max_bytes - comment_bytes + 1)
    if not raw:
        raise ValueError("Selected CSV member has no header line")
    if len(raw) + comment_bytes > max_bytes:
        raise ValueError("CSV header line exceeds its byte limit")
    try:
        line = raw.decode("utf-8", errors="strict").rstrip("\r\n")
    except UnicodeDecodeError as exc:
        raise ValueError("CSV header line is not valid UTF-8") from exc
    if not line:
        raise ValueError("Selected CSV member has an empty header line")

    try:
        dialect = csv.Sniffer().sniff(line, delimiters=",\t;|")
        delimiter = dialect.delimiter
        fields = next(csv.reader([line], delimiter=delimiter, strict=True))
    except (csv.Error, StopIteration) as exc:
        raise ValueError("CSV header line is malformed or has no detectable delimiter") from exc
    _validate_fieldnames(fields, delimiter, required_columns, allowed_columns)
    retained_header = json.dumps(
        {"fieldnames": fields, "delimiter": delimiter}, ensure_ascii=True,
        separators=(",", ":"),
    ).encode("utf-8")
    if len(retained_header) > MAX_HEADER_LINE_BYTES:
        raise ValueError("Retained CSV header metadata exceeds 64 KiB")
    return {
        "fieldnames": fields,
        "delimiter": delimiter,
        "header_line_bytes": len(raw),
        "retained_header_metadata_bytes": len(retained_header),
        "leading_command_comment_bytes": comment_bytes,
        "leading_command_comment_sha256": comment_sha256,
        "leading_command_comment_content_retained": False,
        "data_rows_parsed": 0,
    }


def _canonical_member_name(name: str) -> str:
    if not name or "\\" in name:
        raise ValueError("Unsafe TAR member path")
    if name.startswith("/") or PureWindowsPath(name).is_absolute() or PureWindowsPath(name).drive:
        raise ValueError("Unsafe TAR member path")
    if any(part == ".." for part in name.split("/")):
        raise ValueError("Unsafe TAR member path")
    return PurePosixPath(name).as_posix()


def _read_exact(stream: BoundedReader, size: int, allow_eof: bool = False) -> bytes:
    block = bytearray()
    while len(block) < size:
        part = stream.read(size - len(block))
        if not part:
            if allow_eof and not block:
                return b""
            raise ValueError("TAR stream is truncated")
        block.extend(part)
    return bytes(block)


def _parse_regular_header(block: bytes) -> tarfile.TarInfo:
    if len(block) != tarfile.BLOCKSIZE:
        raise ValueError("Malformed TAR member header")
    kind = block[156:157]
    if kind in {b"1", b"2"}:
        raise ValueError("TAR links are unsupported")
    if kind in {b"3", b"4", b"6"}:
        raise ValueError("TAR device members are unsupported")
    if kind == b"S":
        raise ValueError("Sparse TAR members are unsupported")
    if kind in {b"x", b"g", b"L", b"K"}:
        raise ValueError("TAR extension records are unsupported")
    if kind not in {b"\0", b"0", b"5"}:
        raise ValueError("Unsupported TAR member type")
    magic = block[257:263]
    if magic not in {b"\0" * 6, b"ustar\0", b"ustar "}:
        raise ValueError("Unsupported TAR format or extension")
    if ((magic == b"ustar\0" and block[263:265] != b"00")
            or (magic == b"ustar " and block[263:265] != b" \0")):
        raise ValueError("Unsupported TAR format or extension")
    if block[124] & 0x80:
        raise ValueError("Base-256 TAR member sizes are unsupported")
    try:
        return tarfile.TarInfo.frombuf(
            block, encoding="utf-8", errors="surrogateescape")
    except (tarfile.TarError, ValueError, OverflowError) as exc:
        raise ValueError("Malformed TAR member header") from exc


def _validate_limits(max_archive_bytes: int, max_uncompressed_tar_bytes: int,
                     max_member_bytes: int, max_members: int,
                     max_header_line_bytes: int) -> None:
    if not 0 < max_archive_bytes <= MAX_ARCHIVE_BYTES:
        raise ValueError("Archive-byte limit must be between 1 byte and 1 GiB")
    if not 0 < max_uncompressed_tar_bytes <= MAX_UNCOMPRESSED_TAR_BYTES:
        raise ValueError("Aggregate decompression limit must be between 1 byte and 250 MiB")
    if not 0 < max_member_bytes <= MAX_MEMBER_BYTES:
        raise ValueError("Individual-member limit must be between 1 byte and 128 MiB")
    if not 0 < max_members <= MAX_MEMBERS:
        raise ValueError("Member-count limit must be between 1 and 1,000")
    if not 0 < max_header_line_bytes <= MAX_HEADER_LINE_BYTES:
        raise ValueError("CSV header-line limit must be between 1 byte and 64 KiB")


def audit_tar(path: Path, expected_size: int, expected_md5: str,
              source_url: str | None = None, table_member: str | None = None,
              required_columns: list[str] | set[str] | None = None,
              allowed_columns: list[str] | set[str] | None = None,
              max_header_line_bytes: int = MAX_HEADER_LINE_BYTES,
              max_archive_bytes: int = MAX_ARCHIVE_BYTES,
              max_uncompressed_tar_bytes: int = MAX_UNCOMPRESSED_TAR_BYTES,
              max_member_bytes: int = MAX_MEMBER_BYTES,
              max_members: int = MAX_MEMBERS,
              allow_leading_command_comment: bool = False) -> dict:
    _validate_limits(max_archive_bytes, max_uncompressed_tar_bytes,
                     max_member_bytes, max_members, max_header_line_bytes)
    if expected_size <= 0 or expected_size > max_archive_bytes:
        raise ValueError("Positive manifest size within archive-byte limit is required")
    if not re.fullmatch(r"[0-9a-fA-F]{32}", expected_md5):
        raise ValueError("A valid expected MD5 is required")
    safe_url, source_url_redacted = sanitize_source_url(source_url)
    if table_member is not None and not table_member.endswith((".csv", ".csv.gz")):
        raise ValueError("Selected table member must end in .csv or .csv.gz")
    if table_member is None:
        if allow_leading_command_comment:
            raise ValueError("Leading-comment allowance requires a selected table")
        if required_columns or allowed_columns:
            raise ValueError("Column signatures are only valid with a selected table member")
        required_signature, allowed_vocabulary = frozenset(), frozenset()
    else:
        if not required_columns or not allowed_columns:
            raise ValueError("Header inspection requires required and allowed column signatures")
        required_signature = frozenset(required_columns)
        allowed_vocabulary = frozenset(allowed_columns)
        if (len(required_signature) != len(required_columns)
                or len(allowed_vocabulary) != len(allowed_columns)):
            raise ValueError("Column signatures must not contain duplicates")
        if (any(not field or field != field.strip() for field in required_signature | allowed_vocabulary)
                or not required_signature.issubset(allowed_vocabulary)):
            raise ValueError("Column signatures are malformed or inconsistent")

    md5, sha256 = hashlib.md5(), hashlib.sha256()
    with path.open("rb") as source:
        before = os.fstat(source.fileno())
        if before.st_size > max_archive_bytes:
            raise ValueError("Local archive exceeds archive-byte limit")
        if before.st_size != expected_size:
            raise ValueError("Local archive size differs from expected manifest size")
        hashed_bytes = 0
        while block := source.read(HASH_BLOCK_BYTES):
            hashed_bytes += len(block)
            if hashed_bytes > max_archive_bytes:
                raise ValueError("Local archive exceeds archive-byte limit")
            md5.update(block)
            sha256.update(block)
        if hashed_bytes != expected_size:
            raise ValueError("Local archive size changed while hashing")
        if md5.hexdigest() != expected_md5.lower():
            raise ValueError("Whole-archive MD5 differs from expected manifest MD5")

        source.seek(0)
        gzip_archive = source.read(2) == b"\x1f\x8b"
        source.seek(0)
        gzip_stream = gzip.GzipFile(fileobj=source, mode="rb") if gzip_archive else source
        budget = DecompressionBudget(max_uncompressed_tar_bytes)
        tar_stream = BoundedReader(gzip_stream, budget, "outer_tar_stream_bytes")
        members, seen_names = [], set()
        table_header = None
        member_data_bytes = 0
        nested_gzip_integrity = "NOT_INSPECTED"

        try:
            first = _read_exact(tar_stream, tarfile.BLOCKSIZE, allow_eof=True)
            if not first:
                raise ValueError("TAR archive contains no member headers")
            while first != b"\0" * tarfile.BLOCKSIZE:
                if len(members) >= max_members:
                    raise ValueError("TAR member count exceeds its limit")
                item = _parse_regular_header(first)
                canonical_name = _canonical_member_name(item.name)
                if canonical_name in seen_names:
                    raise ValueError("Duplicate TAR member names are ambiguous")
                seen_names.add(canonical_name)

                if item.size < 0 or item.size > max_member_bytes:
                    raise ValueError("TAR member exceeds individual-size limit")
                member_data_bytes += item.size
                if member_data_bytes > max_uncompressed_tar_bytes:
                    raise ValueError("Declared TAR member bytes exceed aggregate decompression limit")

                if item.type == tarfile.DIRTYPE:
                    if item.size != 0:
                        raise ValueError("TAR directory member has a nonzero size")
                    member_kind = "directory"
                else:
                    member_kind = "file"
                members.append({"name": item.name, "type": member_kind, "size": item.size})
                member_stream = TarMemberReader(tar_stream, item.size)
                if item.name == table_member:
                    if member_kind != "file":
                        raise ValueError("Selected CSV table is not a regular file")
                    if item.name.endswith(".gz"):
                        nested_gzip = gzip.GzipFile(fileobj=member_stream, mode="rb")
                        nested_stream = BoundedReader(
                            nested_gzip, budget, "nested_csv_gzip_output_bytes")
                        try:
                            table_header = read_table_header(
                                nested_stream, required_signature, allowed_vocabulary,
                                max_header_line_bytes, allow_leading_command_comment)
                            nested_stream.drain()
                        except (gzip.BadGzipFile, EOFError, zlib.error) as exc:
                            raise ValueError(
                                "Selected nested gzip CSV failed integrity validation") from exc
                        finally:
                            nested_gzip.close()
                        if member_stream.remaining:
                            raise ValueError("Nested gzip CSV has trailing member bytes")
                        nested_gzip_integrity = "VERIFIED"
                    else:
                        nested_gzip_integrity = "NOT_APPLICABLE"
                        table_header = read_table_header(
                            member_stream, required_signature, allowed_vocabulary,
                            max_header_line_bytes, allow_leading_command_comment)
                member_stream.drain()
                padding = (-item.size) % tarfile.BLOCKSIZE
                if padding:
                    _read_exact(tar_stream, padding)
                first = _read_exact(tar_stream, tarfile.BLOCKSIZE)

            second_end_block = _read_exact(tar_stream, tarfile.BLOCKSIZE)
            if second_end_block != b"\0" * tarfile.BLOCKSIZE:
                raise ValueError("TAR end marker is malformed")
            while trailing := tar_stream.read(COPY_BLOCK_BYTES):
                if any(trailing):
                    raise ValueError("Nonzero bytes follow the TAR end marker")
        except (gzip.BadGzipFile, EOFError, zlib.error) as exc:
            label = "Outer gzip TAR" if gzip_archive else "TAR stream"
            raise ValueError(f"{label} failed integrity validation") from exc
        finally:
            if gzip_archive:
                gzip_stream.close()

        if table_member is not None and table_header is None:
            raise ValueError("Selected CSV member was not found")
        after = os.fstat(source.fileno())
        if (before.st_size, before.st_mtime_ns, before.st_ctime_ns, before.st_ino) != (
                after.st_size, after.st_mtime_ns, after.st_ctime_ns, after.st_ino):
            raise ValueError("Source archive changed during inspection")

    return {
        "schema_version": 1,
        "scan_stage": "INVENTORY" if table_member is None else "HEADER_INSPECTION",
        "purpose": "Checksum-verified TAR inventory and optional CSV header only",
        "source_url": safe_url,
        "source_url_redacted": source_url_redacted,
        "source_archive_name": path.name,
        "archive_format": "tar.gz" if gzip_archive else "tar",
        "expected_size_bytes": expected_size,
        "actual_size_bytes": hashed_bytes,
        "expected_md5": expected_md5.lower(),
        "actual_md5": md5.hexdigest(),
        "sha256": sha256.hexdigest(),
        "whole_archive_md5_verification": "VERIFIED",
        "whole_archive_sha256_computed": True,
        "acquisition_identity_status": "VERIFIED",
        "acquisition_identity": {
            "source_archive_name": path.name,
            "expected_size_bytes": expected_size,
            "actual_size_bytes": hashed_bytes,
            "expected_md5": expected_md5.lower(),
            "actual_md5": md5.hexdigest(),
            "sha256": sha256.hexdigest(),
        },
        "tar_integrity_status": "VERIFIED",
        "outer_gzip_integrity": "VERIFIED" if gzip_archive else "NOT_APPLICABLE",
        "inspected_nested_gzip_integrity": nested_gzip_integrity,
        "aggregate_decompressed_bytes": budget.bytes_read,
        "decompression_counts": {
            "outer_tar_stream_bytes": budget.by_stream.get("outer_tar_stream_bytes", 0),
            "nested_csv_gzip_output_bytes": budget.by_stream.get(
                "nested_csv_gzip_output_bytes", 0),
            "aggregate_output_bytes": budget.bytes_read,
        },
        "member_count": len(members),
        "members": members,
        "selected_table_member": table_member,
        "allow_single_leading_command_comment": allow_leading_command_comment,
        "column_signature": None if table_member is None else {
            "required_columns": sorted(required_signature),
            "allowed_columns": sorted(allowed_vocabulary),
        },
        "table_header": table_header,
        "inspected_records": 0,
        "table_data_rows_parsed": 0,
        "member_files_written_to_disk": False,
        "archive_code_executed": False,
        "truth_or_performance_outputs_scored": False,
        "limits": {
            "archive_bytes": max_archive_bytes,
            "aggregate_decompressed_bytes": max_uncompressed_tar_bytes,
            "declared_member_data_bytes": max_uncompressed_tar_bytes,
            "individual_member_bytes": max_member_bytes,
            "member_count": max_members,
            "selected_csv_header_line_bytes": max_header_line_bytes,
            "selected_csv_headers": 1 if table_member is not None else 0,
            "retained_csv_header_metadata_bytes": MAX_HEADER_LINE_BYTES,
            "data_rows_parsed": 0,
        },
    }


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
    parser.add_argument("--expected-md5", required=True)
    parser.add_argument("--source-url")
    parser.add_argument("--table-member")
    parser.add_argument("--required-column", action="append")
    parser.add_argument("--allowed-column", action="append")
    parser.add_argument("--allow-leading-command-comment", action="store_true")
    parser.add_argument("--max-uncompressed-tar-bytes", type=int,
                        default=MAX_UNCOMPRESSED_TAR_BYTES)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists() or args.out.is_symlink():
        parser.error("Refusing to overwrite existing output")
    if args.table_member and (not args.required_column or not args.allowed_column):
        parser.error("--table-member requires --required-column and --allowed-column")
    if not args.table_member and (args.required_column or args.allowed_column):
        parser.error("Column signatures require --table-member")
    try:
        report = audit_tar(
            args.archive, args.expected_size, args.expected_md5,
            args.source_url, args.table_member, args.required_column, args.allowed_column,
            max_uncompressed_tar_bytes=args.max_uncompressed_tar_bytes,
            allow_leading_command_comment=args.allow_leading_command_comment,
        )
        write_report(args.out, report)
    except (ValueError, OSError, EOFError, tarfile.TarError, zlib.error) as exc:
        parser.error(str(exc))
    print(f"MD5 verified; {report['member_count']} members; "
          f"{report['inspected_records']} records inspected")


if __name__ == "__main__":
    main()
