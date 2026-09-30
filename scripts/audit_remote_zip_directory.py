"""Create a bounded, payload-free inventory of a remote ZIP central directory.

The caller must supply the archive size from its source manifest. This helper
uses the standard-library ``zipfile`` parser over strict HTTP Range reads; it
never downloads member payloads or verifies the whole-archive MD5. ZIP64 is
handled by ``zipfile`` when it uses the supported fixed end records. Commented
archives, trailing data, and ZIP64 extensible-data records are rejected before
the parser can scan a payload-bearing tail. Every response body read is bounded
and charged to a cumulative byte budget.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import struct
import urllib.error
import urllib.request
import zipfile
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import unquote, urlsplit, urlunsplit


DEFAULT_MAX_NETWORK_BYTES = 1_048_576
CONTENT_RANGE = re.compile(r"bytes ([0-9]+)-([0-9]+)/([0-9]+)")
DECIMAL = re.compile(r"[0-9]+")
MD5 = re.compile(r"[0-9a-fA-F]{32}")
STRONG_ETAG = re.compile(r'"[\x21\x23-\x7e\x80-\xff]*"')
EOCD = struct.Struct("<4s4H2LH")
ZIP64_LOCATOR = struct.Struct("<4sLQL")
ZIP64_EOCD = struct.Struct("<4sQ2H2L4Q")
EOCD_SIGNATURE = b"PK\x05\x06"
ZIP64_LOCATOR_SIGNATURE = b"PK\x06\x07"
ZIP64_EOCD_SIGNATURE = b"PK\x06\x06"


class RemoteZipError(ValueError):
    """The remote object or ZIP metadata did not satisfy the safety contract."""


def _header(headers, name: str) -> str:
    """Read a header from either email.message.Message or a plain mapping."""
    value = headers.get(name)
    if value is not None:
        return str(value)
    wanted = name.lower()
    for key, value in headers.items():
        if str(key).lower() == wanted:
            return str(value)
    return ""


def _status(response) -> int:
    value = getattr(response, "status", None)
    if value is None:
        value = response.getcode()
    return int(value)


def _validate_url(url: str) -> None:
    parts = urlsplit(url)
    if parts.scheme.lower() not in {"http", "https"} or not parts.netloc:
        raise RemoteZipError("URL must be an absolute HTTP or HTTPS URL")
    if parts.username is not None or parts.password is not None or parts.fragment:
        raise RemoteZipError("URL credentials and fragments are not supported")


def _validate_response_url(url: str, original_url: str) -> None:
    _validate_url(url)
    if urlsplit(original_url).scheme.lower() == "https" and urlsplit(url).scheme.lower() != "https":
        raise RemoteZipError("HTTPS request redirected to an insecure URL")


def _summary_url(url: str) -> str:
    """Return a URL without query values, which may contain signed credentials."""
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


def _is_strong_etag(value: str) -> bool:
    return bool(STRONG_ETAG.fullmatch(value))


def _identity_encoding(headers) -> None:
    encoding = _header(headers, "Content-Encoding").strip().lower()
    if encoding not in {"", "identity"}:
        raise RemoteZipError(f"Encoded HTTP representation is unsupported: {encoding}")


class RemoteRangeReader:
    """Seekable file-like reader backed only by validated HTTP byte ranges.

    ``read`` rejects an oversized request before opening its HTTP request. One
    extra byte is reserved while reading each response so an oversized body
    cannot silently pass as a correctly sized range.
    """

    def __init__(
        self,
        url: str,
        expected_size: int,
        *,
        max_network_bytes: int = DEFAULT_MAX_NETWORK_BYTES,
        opener=None,
        timeout: int = 30,
    ) -> None:
        _validate_url(url)
        if isinstance(expected_size, bool) or not isinstance(expected_size, int) or expected_size <= 0:
            raise RemoteZipError("Expected archive size must be a positive manifest byte count")
        if (isinstance(max_network_bytes, bool) or not isinstance(max_network_bytes, int)
                or max_network_bytes <= 0):
            raise RemoteZipError("Network byte budget must be a positive integer")
        if timeout <= 0:
            raise RemoteZipError("HTTP timeout must be positive")

        self.url = url
        self.expected_size = expected_size
        self.max_network_bytes = max_network_bytes
        self.timeout = timeout
        self._opener = opener or urllib.request.urlopen
        self.position = 0
        self.network_bytes_read = 0
        self.range_requests: list[dict[str, object]] = []
        self.closed = False
        self.resolved_url = ""
        self.remote_size = 0
        self.etag = ""
        self.last_modified = ""
        self.validator_kind = ""
        self._range_cache: dict[tuple[int, int], bytes] = {}
        self._pin_head()

    def _open(self, request):
        try:
            return self._opener(request, timeout=self.timeout)
        except urllib.error.HTTPError as exc:
            raise RemoteZipError(f"HTTP request failed with status {exc.code}") from exc
        except urllib.error.URLError as exc:
            raise RemoteZipError("HTTP request failed due to a transport error") from exc

    def _pin_head(self) -> None:
        request = urllib.request.Request(
            self.url, headers={"Accept-Encoding": "identity"}, method="HEAD"
        )
        with self._open(request) as response:
            if _status(response) != 200:
                raise RemoteZipError(f"HEAD did not return 200: {_status(response)}")
            resolved_url = response.geturl()
            _validate_response_url(resolved_url, self.url)
            headers = response.headers
            _identity_encoding(headers)
            raw_size = _header(headers, "Content-Length")
            if not DECIMAL.fullmatch(raw_size):
                raise RemoteZipError("HEAD omitted a valid Content-Length")
            remote_size = int(raw_size)
            if remote_size != self.expected_size:
                raise RemoteZipError(
                    f"HEAD length {remote_size} differs from source-manifest size "
                    f"{self.expected_size}"
                )

            self.resolved_url = resolved_url
            self.remote_size = remote_size
            candidate_etag = _header(headers, "ETag")
            if _is_strong_etag(candidate_etag):
                self.etag = candidate_etag
                self.validator_kind = "strong_etag"
            else:
                last_modified = _header(headers, "Last-Modified")
                if not last_modified or "\r" in last_modified or "\n" in last_modified:
                    raise RemoteZipError(
                        "No strong ETag or usable Last-Modified validator is available"
                    )
                try:
                    parsed = parsedate_to_datetime(last_modified)
                except (TypeError, ValueError, OverflowError) as exc:
                    raise RemoteZipError("HEAD Last-Modified is not a valid HTTP date") from exc
                if parsed is None:
                    raise RemoteZipError("HEAD Last-Modified is not a valid HTTP date")
                self.last_modified = last_modified
                self.validator_kind = "last_modified_and_size_weaker"

    def seek(self, offset: int, whence: int = os.SEEK_SET) -> int:
        self._ensure_open()
        if isinstance(offset, bool) or not isinstance(offset, int):
            raise TypeError("seek offset must be an integer")
        if whence == os.SEEK_SET:
            position = offset
        elif whence == os.SEEK_CUR:
            position = self.position + offset
        elif whence == os.SEEK_END:
            position = self.expected_size + offset
        else:
            raise ValueError(f"invalid whence value: {whence}")
        if position < 0:
            raise OSError("negative seek position")
        self.position = position
        return position

    def tell(self) -> int:
        self._ensure_open()
        return self.position

    def read(self, size: int = -1) -> bytes:
        self._ensure_open()
        if isinstance(size, bool) or not isinstance(size, int):
            raise TypeError("read size must be an integer")
        if size == 0 or self.position >= self.expected_size:
            return b""
        requested = self.expected_size - self.position if size < 0 else size
        amount = min(requested, self.expected_size - self.position)
        if amount <= 0:
            return b""
        cache_key = (self.position, amount)
        if cache_key in self._range_cache:
            data = self._range_cache[cache_key]
            self.position += len(data)
            return data
        if amount > self.max_network_bytes:
            raise RemoteZipError(
                f"Requested read of {amount} bytes exceeds per-read network cap "
                f"{self.max_network_bytes}"
            )
        if amount + 1 > self.max_network_bytes - self.network_bytes_read:
            raise RemoteZipError(
                f"Requested read of {amount} bytes exceeds remaining network budget"
            )
        data = self._read_range(self.position, amount)
        self.position += len(data)
        return data

    def readinto(self, buffer) -> int:
        data = self.read(len(buffer))
        buffer[:len(data)] = data
        return len(data)

    def readable(self) -> bool:
        return not self.closed

    def seekable(self) -> bool:
        return not self.closed

    def close(self) -> None:
        self.closed = True

    def __enter__(self):
        self._ensure_open()
        return self

    def __exit__(self, *_):
        self.close()
        return False

    def _ensure_open(self) -> None:
        if self.closed:
            raise ValueError("I/O operation on closed remote ZIP reader")

    def _read_range(self, offset: int, amount: int) -> bytes:
        end = offset + amount - 1
        headers = {
            "Range": f"bytes={offset}-{end}",
            "Accept-Encoding": "identity",
        }
        if self.validator_kind == "strong_etag":
            headers["If-Range"] = self.etag
        else:
            headers["If-Unmodified-Since"] = self.last_modified
        request = urllib.request.Request(self.url, headers=headers, method="GET")
        with self._open(request) as response:
            status = _status(response)
            if status != 206:
                raise RemoteZipError(
                    f"Server did not honor Range at {offset}: HTTP {status}"
                )
            resolved_url = response.geturl()
            _validate_response_url(resolved_url, self.url)
            if resolved_url != self.resolved_url:
                raise RemoteZipError("Resolved archive URL changed during range scan")
            response_headers = response.headers
            _identity_encoding(response_headers)

            content_range = CONTENT_RANGE.fullmatch(
                _header(response_headers, "Content-Range")
            )
            if not content_range or tuple(map(int, content_range.groups())) != (
                offset, end, self.expected_size
            ):
                raise RemoteZipError(f"Incorrect Content-Range at offset {offset}")

            raw_length = _header(response_headers, "Content-Length")
            if not DECIMAL.fullmatch(raw_length) or int(raw_length) != amount:
                raise RemoteZipError(f"Incorrect Content-Length at offset {offset}")

            if self.validator_kind == "strong_etag":
                response_etag = _header(response_headers, "ETag")
                if response_etag != self.etag:
                    raise RemoteZipError(f"Strong ETag changed or disappeared at offset {offset}")
            elif _header(response_headers, "Last-Modified") != self.last_modified:
                raise RemoteZipError(f"Last-Modified changed or disappeared at offset {offset}")

            body = response.read(amount + 1)
            if not isinstance(body, bytes):
                raise RemoteZipError("HTTP response body was not bytes")
            if len(body) > self.max_network_bytes - self.network_bytes_read:
                self.network_bytes_read = self.max_network_bytes
                raise RemoteZipError("HTTP response exceeded the cumulative network byte budget")
            self.network_bytes_read += len(body)
            if len(body) > amount:
                raise RemoteZipError(f"Oversized Range response body at offset {offset}")
            if len(body) != amount:
                raise RemoteZipError(f"Short Range response body at offset {offset}")

            self.range_requests.append({
                "offset": offset,
                "length": amount,
                "sha256": hashlib.sha256(body).hexdigest(),
            })
            self._range_cache[(offset, amount)] = body
            return body


def _compression_name(method: int) -> str:
    names = {
        zipfile.ZIP_STORED: "stored",
        zipfile.ZIP_DEFLATED: "deflate",
        zipfile.ZIP_BZIP2: "bzip2",
        zipfile.ZIP_LZMA: "lzma",
    }
    zstandard = getattr(zipfile, "ZIP_ZSTANDARD", None)
    if zstandard is not None:
        names[zstandard] = "zstandard"
    return names.get(method, f"method_{method}")


def _precheck_eocd(reader: RemoteRangeReader) -> dict[str, object]:
    """Accept only an EOCD exactly at EOF, before invoking zipfile's tail scan.

    Python's normal ZIP parser scans up to 65,557 trailing bytes when an EOCD
    is not at EOF. That scan can overlap a member payload. This helper permits
    the common comment-free layout and rejects comments or trailing bytes after
    reading only the fixed-size terminal records.
    """
    if reader.expected_size < EOCD.size:
        raise RemoteZipError("Archive is too small to contain a ZIP end record")

    reader.seek(-EOCD.size, os.SEEK_END)
    raw_eocd = reader.read(EOCD.size)
    if len(raw_eocd) != EOCD.size or raw_eocd[:4] != EOCD_SIGNATURE:
        raise RemoteZipError(
            "Only a comment-free ZIP with EOCD exactly at EOF is supported; "
            "ZIP comments and trailing bytes are rejected"
        )

    (_signature, disk_number, directory_disk, entries_on_disk, entries_total,
     directory_size, directory_offset, comment_size) = EOCD.unpack(raw_eocd)
    if comment_size != 0:
        raise RemoteZipError("ZIP archive comments are unsupported")
    if disk_number != 0 or directory_disk != 0:
        raise RemoteZipError("Multi-disk ZIP archives are unsupported")
    if entries_on_disk != entries_total:
        raise RemoteZipError("ZIP end record has inconsistent per-disk entry counts")

    eocd_offset = reader.expected_size - EOCD.size
    zip64 = False
    zip64_offset = None
    if reader.expected_size >= EOCD.size + ZIP64_LOCATOR.size:
        reader.seek(-(EOCD.size + ZIP64_LOCATOR.size), os.SEEK_END)
        raw_locator = reader.read(ZIP64_LOCATOR.size)
    else:
        raw_locator = b""

    if raw_locator[:4] == ZIP64_LOCATOR_SIGNATURE:
        zip64 = True
        (_locator_signature, locator_disk, locator_offset, total_disks) = ZIP64_LOCATOR.unpack(
            raw_locator
        )
        if locator_disk != 0 or total_disks != 1:
            raise RemoteZipError("Multi-disk ZIP64 archives are unsupported")
        zip64_offset = reader.expected_size - EOCD.size - ZIP64_LOCATOR.size - ZIP64_EOCD.size
        if locator_offset != zip64_offset:
            raise RemoteZipError(
                "ZIP64 extensible data or prepended archive data is unsupported"
            )
        reader.seek(zip64_offset, os.SEEK_SET)
        raw_zip64 = reader.read(ZIP64_EOCD.size)
        if len(raw_zip64) != ZIP64_EOCD.size:
            raise RemoteZipError("Truncated ZIP64 end record")
        (zip64_signature, record_size, _made_by, _needed, zip64_disk,
         zip64_directory_disk, zip64_entries_on_disk, zip64_entries_total,
         directory_size, directory_offset) = ZIP64_EOCD.unpack(raw_zip64)
        if zip64_signature != ZIP64_EOCD_SIGNATURE or record_size != 44:
            raise RemoteZipError("Unsupported or malformed ZIP64 end record")
        if zip64_disk != 0 or zip64_directory_disk != 0:
            raise RemoteZipError("Multi-disk ZIP64 archives are unsupported")
        if zip64_entries_on_disk != zip64_entries_total:
            raise RemoteZipError("ZIP64 end record has inconsistent per-disk entry counts")
        entries_total = zip64_entries_total
        directory_end = zip64_offset
    else:
        has_zip64_sentinel = (
            entries_on_disk == 0xFFFF
            or entries_total == 0xFFFF
            or directory_size == 0xFFFFFFFF
            or directory_offset == 0xFFFFFFFF
        )
        if has_zip64_sentinel:
            raise RemoteZipError("ZIP64 sentinel values require a supported ZIP64 locator")
        directory_end = eocd_offset

    if directory_offset + directory_size != directory_end:
        raise RemoteZipError(
            "Central directory is not directly followed by the ZIP end records"
        )
    return {
        "central_directory_offset": directory_offset,
        "central_directory_size": directory_size,
        "member_count": entries_total,
        "zip64": zip64,
        "zip64_end_record_offset": zip64_offset,
    }


def inventory_remote_zip(
    url: str,
    expected_size: int,
    *,
    official_md5: str | None = None,
    max_network_bytes: int = DEFAULT_MAX_NETWORK_BYTES,
    opener=None,
) -> dict[str, object]:
    """Read central-directory metadata without fetching any member payload."""
    if official_md5 is not None and not MD5.fullmatch(official_md5):
        raise RemoteZipError("Official manifest MD5 must contain exactly 32 hex characters")

    reader = RemoteRangeReader(
        url,
        expected_size,
        max_network_bytes=max_network_bytes,
        opener=opener,
    )
    try:
        end_record = _precheck_eocd(reader)
        with zipfile.ZipFile(reader, mode="r") as archive:
            if archive.start_dir != end_record["central_directory_offset"]:
                raise RemoteZipError("ZIP central-directory offset changed during parsing")
            members = []
            seen_names = set()
            for info in archive.infolist():
                original_name = getattr(info, "orig_filename", info.filename)
                if "\x00" in original_name:
                    raise RemoteZipError("ZIP member name contains NUL and is ambiguous")
                if info.filename in seen_names:
                    raise RemoteZipError(f"Duplicate ZIP member name is ambiguous: {info.filename!r}")
                seen_names.add(info.filename)
                if info.flag_bits & 0x41:
                    raise RemoteZipError(f"Encrypted ZIP member is unsupported: {info.filename!r}")
                if info.volume != 0:
                    raise RemoteZipError(
                        f"Multi-disk ZIP member is unsupported: {info.filename!r}"
                    )
                members.append({
                    "name": info.filename,
                    "compressed_size": info.compress_size,
                    "uncompressed_size": info.file_size,
                    "crc32": f"{info.CRC:08x}",
                    "compression_method": info.compress_type,
                    "compression": _compression_name(info.compress_type),
                    "header_offset": info.header_offset,
                })
            central_directory_offset = archive.start_dir
            if len(members) != end_record["member_count"]:
                raise RemoteZipError("ZIP end record member count disagrees with the central directory")
    finally:
        reader.close()

    validator = {
        "kind": reader.validator_kind,
        "etag": reader.etag or None,
        "last_modified": reader.last_modified or None,
    }
    summary = {
        "inventory_type": "remote_zip_central_directory",
        "archive_url": _summary_url(url),
        "archive_url_query_redacted": bool(urlsplit(url).query),
        "resolved_archive_url": _summary_url(reader.resolved_url),
        "resolved_archive_url_query_redacted": bool(urlsplit(reader.resolved_url).query),
        "archive_name": unquote(urlsplit(url).path.rsplit("/", 1)[-1]) or "archive.zip",
        "source_manifest_size_bytes": expected_size,
        "http_head_size_bytes": reader.remote_size,
        "source_manifest_md5": official_md5.lower() if official_md5 else None,
        "whole_archive_md5_verification": "UNVERIFIED_NOT_DOWNLOADED",
        "validator": validator,
        "member_count": len(members),
        "central_directory_offset": central_directory_offset,
        "zip64": end_record["zip64"],
        "range_request_count": len(reader.range_requests),
        "range_response_body_bytes_read": reader.network_bytes_read,
        "range_requests": reader.range_requests,
        "member_payloads_requested": False,
        "member_payload_bytes_requested": 0,
        "inventory_scope": "ZIP member metadata only; no extraction or member-body reads",
        "network_byte_budget": max_network_bytes,
        "zip64_support": (
            "Python standard-library zipfile with fixed end records; "
            "extensible-data layouts are rejected"
        ),
        "eocd_policy": "Comment-free EOCD exactly at EOF; comments and trailing data rejected",
    }
    return {"members": members, "summary": summary}


def _json_lines(records: list[dict[str, object]]) -> bytes:
    return b"".join(
        (json.dumps(record, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
        for record in records
    )


def write_inventory(out_dir: Path, inventory: dict[str, object]) -> None:
    """Create a new output directory and write checksummed, non-overwriting files."""
    out_dir = Path(out_dir)
    if os.path.lexists(out_dir):
        raise FileExistsError(f"Refusing to overwrite existing output directory: {out_dir}")

    members_data = _json_lines(inventory["members"])
    ranges_data = _json_lines(inventory["summary"]["range_requests"])
    summary_data = (json.dumps(
        inventory["summary"], ensure_ascii=True, indent=2, sort_keys=True
    ) + "\n").encode("utf-8")
    named_data = {
        "members.jsonl": members_data,
        "range_requests.jsonl": ranges_data,
        "summary.json": summary_data,
    }
    sums_data = "".join(
        f"{hashlib.sha256(data).hexdigest()}  {name}\n"
        for name, data in named_data.items()
    ).encode("ascii")

    out_dir.mkdir(parents=True, exist_ok=False)
    for name, data in named_data.items():
        with (out_dir / name).open("xb") as output:
            output.write(data)
    with (out_dir / "SHA256SUMS").open("xb") as output:
        output.write(sums_data)


def _positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return parsed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True, help="HTTP(S) archive URL from the source manifest")
    parser.add_argument(
        "--expected-size", type=_positive_int, required=True,
        help="exact archive byte size from the source manifest",
    )
    parser.add_argument("--official-md5", help="official manifest MD5 label (never verified here)")
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument(
        "--max-network-bytes", type=_positive_int, default=DEFAULT_MAX_NETWORK_BYTES,
        help=f"maximum cumulative HTTP response body bytes (default {DEFAULT_MAX_NETWORK_BYTES})",
    )
    args = parser.parse_args()
    if os.path.lexists(args.out_dir):
        parser.error(f"Refusing to overwrite existing output directory: {args.out_dir}")
    try:
        inventory = inventory_remote_zip(
            args.url,
            args.expected_size,
            official_md5=args.official_md5,
            max_network_bytes=args.max_network_bytes,
        )
        write_inventory(args.out_dir, inventory)
    except (RemoteZipError, zipfile.BadZipFile, OSError) as exc:
        parser.error(str(exc))
    print(
        f"{inventory['summary']['archive_name']}: "
        f"{inventory['summary']['member_count']} members, "
        f"{inventory['summary']['range_request_count']} range requests, "
        f"{inventory['summary']['range_response_body_bytes_read']} response bytes; "
        "whole-archive MD5 UNVERIFIED"
    )


if __name__ == "__main__":
    main()
