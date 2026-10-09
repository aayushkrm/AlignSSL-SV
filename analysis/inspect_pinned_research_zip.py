"""Inventory ZIP metadata without decoding or interpreting member payloads.

Whole-file hash passes read opaque ZIP bytes, including compressed payloads.
They do not extract members or evaluate scientific outcomes.
"""

from __future__ import annotations

import hashlib
import json
import ntpath
import os
import re
import stat
import struct
import sys
from pathlib import Path


MAX_INPUT_BYTES = 47_443_427
MAX_MEMBERS = 4_096
MAX_DIRECTORY_BYTES = 256 * 1024
MAX_FILENAME_BYTES = 256 * 1024
MAX_MANIFEST_BYTES = 1024 * 1024
HASH_CHUNK_BYTES = 1024 * 1024
ZIP_METADATA_TAIL_BYTES = MAX_DIRECTORY_BYTES + 65_535 + 22 + 20 + 56

_EOCD_SIGNATURE = b"PK\x05\x06"
_ZIP64_EOCD_SIGNATURE = b"PK\x06\x06"
_ZIP64_LOCATOR_SIGNATURE = b"PK\x06\x07"
_CENTRAL_SIGNATURE = b"PK\x01\x02"
_SUPPORTED_COMPRESSION = {
    0: "stored",
    8: "deflate",
    12: "bzip2",
    14: "lzma",
}


def _absolute_path(value: os.PathLike[str] | str) -> Path:
    raw = os.fspath(value)
    if isinstance(raw, bytes):
        raw = os.fsdecode(raw)
    if not isinstance(raw, str) or not raw:
        raise ValueError("path must be a non-empty filesystem path")
    return Path(os.path.abspath(raw))


def _open_parent_without_symlinks(path: Path) -> int:
    """Open only this path's parent components, with no symlink traversal."""
    if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY"):
        raise OSError("safe directory opening is not supported on this platform")

    if sys.platform.startswith("linux"):
        if not hasattr(os, "O_PATH"):
            raise OSError("safe Linux directory references are not supported")
        access_flag = os.O_PATH
    else:
        access_flag = os.O_RDONLY
    flags = access_flag | os.O_DIRECTORY | os.O_NOFOLLOW
    flags |= getattr(os, "O_CLOEXEC", 0)
    current_fd = os.open(path.anchor, flags)
    try:
        for component in path.parent.parts[1:]:
            next_fd = os.open(component, flags, dir_fd=current_fd)
            os.close(current_fd)
            current_fd = next_fd
            if not stat.S_ISDIR(os.fstat(current_fd).st_mode):
                raise ValueError("a path parent is not a directory")
        if not stat.S_ISDIR(os.fstat(current_fd).st_mode):
            raise ValueError("a path parent is not a directory")
        return current_fd
    except OSError as exc:
        os.close(current_fd)
        raise ValueError("a path parent is missing, unsafe, or a symlink") from exc
    except BaseException:
        os.close(current_fd)
        raise


def _directory_identity(fd: int) -> tuple[int, int]:
    info = os.fstat(fd)
    return info.st_dev, info.st_ino


def _assert_parent_unchanged(path: Path, original_identity: tuple[int, int]) -> None:
    current_fd = _open_parent_without_symlinks(path)
    try:
        if _directory_identity(current_fd) != original_identity:
            raise ValueError("a path parent changed during inspection")
    finally:
        os.close(current_fd)


def _file_snapshot(info: os.stat_result) -> tuple[int, ...]:
    return (
        info.st_dev,
        info.st_ino,
        info.st_mode,
        info.st_nlink,
        info.st_size,
        info.st_mtime_ns,
        info.st_ctime_ns,
    )


def _named_file_stat(parent_fd: int, name: str) -> os.stat_result:
    return os.stat(name, dir_fd=parent_fd, follow_symlinks=False)


def _assert_source_unchanged(
    source_path: Path,
    source_parent_fd: int,
    source_parent_identity: tuple[int, int],
    source_name: str,
    source_fd: int,
    initial_snapshot: tuple[int, ...],
) -> None:
    _assert_parent_unchanged(source_path, source_parent_identity)
    descriptor_info = os.fstat(source_fd)
    named_info = _named_file_stat(source_parent_fd, source_name)
    if (
        _file_snapshot(descriptor_info) != initial_snapshot
        or _file_snapshot(named_info) != initial_snapshot
    ):
        raise ValueError("source archive changed during inspection")


def _hash_source(fd: int, size: int, *, capture_tail: bool = True) -> tuple[str, str, bytes]:
    md5 = hashlib.md5()
    sha256 = hashlib.sha256()
    offset = 0
    tail = bytearray()
    while offset < size:
        amount = min(HASH_CHUNK_BYTES, size - offset)
        block = os.pread(fd, amount, offset)
        if len(block) != amount:
            raise ValueError("source archive hash read was incomplete")
        md5.update(block)
        sha256.update(block)
        if capture_tail:
            tail.extend(block)
            if len(tail) > ZIP_METADATA_TAIL_BYTES:
                del tail[:len(tail) - ZIP_METADATA_TAIL_BYTES]
        offset += amount
    return md5.hexdigest(), sha256.hexdigest(), bytes(tail)


def _tail_read(tail: bytes, tail_offset: int, offset: int, amount: int) -> bytes:
    start = offset - tail_offset
    end = start + amount
    if start < 0 or amount < 0 or end > len(tail):
        raise ValueError("ZIP metadata is outside the bounded captured tail")
    return tail[start:end]


def _end_records(tail: bytes, tail_offset: int) -> tuple[int, int, int, int]:
    """Return entry count, directory size, directory offset, and end-record offset."""
    candidate = tail.rfind(_EOCD_SIGNATURE)
    end_record = None
    while candidate >= 0:
        if candidate + 22 <= len(tail):
            comment_size = struct.unpack_from("<H", tail, candidate + 20)[0]
            if candidate + 22 + comment_size == len(tail):
                end_record = (candidate, tail[candidate:candidate + 22])
                break
        candidate = tail.rfind(_EOCD_SIGNATURE, 0, candidate)
    if end_record is None:
        raise ValueError("ZIP end-of-central-directory record is missing or malformed")

    candidate, record = end_record
    (
        _signature,
        disk_number,
        directory_disk,
        entries_on_disk,
        entry_count,
        directory_size,
        directory_offset,
        _comment_size,
    ) = struct.unpack("<4s4H2IH", record)
    end_offset = tail_offset + candidate
    if disk_number != 0 or directory_disk != 0:
        raise ValueError("multi-disk ZIP archives are not supported")

    zip64_values_needed = (
        entries_on_disk == 0xFFFF
        or entry_count == 0xFFFF
        or directory_size == 0xFFFFFFFF
        or directory_offset == 0xFFFFFFFF
    )
    if zip64_values_needed:
        locator_offset = end_offset - 20
        if locator_offset < 0:
            raise ValueError("ZIP64 locator is missing")
        locator = _tail_read(tail, tail_offset, locator_offset, 20)
        locator_signature, locator_disk, zip64_offset, disk_count = struct.unpack(
            "<4sIQI", locator
        )
        if (
            locator_signature != _ZIP64_LOCATOR_SIGNATURE
            or locator_disk != 0
            or disk_count != 1
        ):
            raise ValueError("multi-disk or malformed ZIP64 locator")
        if zip64_offset + 56 != locator_offset:
            raise ValueError("unsupported ZIP64 end-record layout")
        zip64_record = _tail_read(tail, tail_offset, zip64_offset, 56)
        (
            zip64_signature,
            zip64_record_size,
            _version_made,
            _version_needed,
            zip64_disk,
            zip64_directory_disk,
            zip64_entries_on_disk,
            zip64_entry_count,
            zip64_directory_size,
            zip64_directory_offset,
        ) = struct.unpack("<4sQ2H2I4Q", zip64_record)
        if zip64_signature != _ZIP64_EOCD_SIGNATURE or zip64_record_size != 44:
            raise ValueError("unsupported or malformed ZIP64 end record")
        if zip64_disk != 0 or zip64_directory_disk != 0:
            raise ValueError("multi-disk ZIP64 archives are not supported")
        if zip64_entries_on_disk != zip64_entry_count:
            raise ValueError("multi-disk ZIP64 entry counts are not supported")
        if entries_on_disk != 0xFFFF and entries_on_disk != zip64_entries_on_disk:
            raise ValueError("ZIP64 entry counts disagree")
        if entry_count != 0xFFFF and entry_count != zip64_entry_count:
            raise ValueError("ZIP64 entry counts disagree")
        if directory_size != 0xFFFFFFFF and directory_size != zip64_directory_size:
            raise ValueError("ZIP64 directory sizes disagree")
        if directory_offset != 0xFFFFFFFF and directory_offset != zip64_directory_offset:
            raise ValueError("ZIP64 directory offsets disagree")
        return (
            zip64_entry_count,
            zip64_directory_size,
            zip64_directory_offset,
            zip64_offset,
        )

    if entries_on_disk != entry_count:
        raise ValueError("multi-disk ZIP entry counts are not supported")
    return entry_count, directory_size, directory_offset, end_offset


def _zip64_member_values(extra: bytes, uncompressed: int, compressed: int,
                         local_offset: int, disk_start: int) -> tuple[int, int, int, int]:
    cursor = 0
    zip64_payload = None
    while cursor < len(extra):
        if cursor + 4 > len(extra):
            raise ValueError("malformed ZIP member extra metadata")
        tag, length = struct.unpack_from("<HH", extra, cursor)
        cursor += 4
        end = cursor + length
        if end > len(extra):
            raise ValueError("malformed ZIP member extra metadata")
        if tag == 0x0001:
            if zip64_payload is not None:
                raise ValueError("duplicate ZIP64 member metadata")
            zip64_payload = extra[cursor:end]
        cursor = end

    needs_values = (
        uncompressed == 0xFFFFFFFF
        or compressed == 0xFFFFFFFF
        or local_offset == 0xFFFFFFFF
        or disk_start == 0xFFFF
    )
    if not needs_values:
        return uncompressed, compressed, local_offset, disk_start
    if zip64_payload is None:
        raise ValueError("required ZIP64 member metadata is missing")

    cursor = 0

    def take(fmt: str) -> int:
        nonlocal cursor
        width = struct.calcsize(fmt)
        if cursor + width > len(zip64_payload):
            raise ValueError("required ZIP64 member metadata is incomplete")
        value = struct.unpack_from(fmt, zip64_payload, cursor)[0]
        cursor += width
        return value

    if uncompressed == 0xFFFFFFFF:
        uncompressed = take("<Q")
    if compressed == 0xFFFFFFFF:
        compressed = take("<Q")
    if local_offset == 0xFFFFFFFF:
        local_offset = take("<Q")
    if disk_start == 0xFFFF:
        disk_start = take("<I")
    return uncompressed, compressed, local_offset, disk_start


def _validate_member_name(name: str) -> None:
    if not name or "\x00" in name:
        raise ValueError("ZIP member has an empty or NUL-containing name")
    drive, _tail = ntpath.splitdrive(name)
    if name.startswith(("/", "\\")) or ntpath.isabs(name) or drive:
        raise ValueError("ZIP member has an absolute or drive-qualified name")
    if ".." in name.replace("\\", "/").split("/"):
        raise ValueError("ZIP member name contains a parent traversal component")


def _inventory_directory(file_size: int, tail: bytes,
                         tail_offset: int) -> tuple[list[dict[str, object]], int, int]:
    entry_count, directory_size, directory_offset, directory_end = _end_records(
        tail, tail_offset
    )
    if entry_count > MAX_MEMBERS:
        raise ValueError("ZIP member count exceeds the configured limit")
    if directory_size > MAX_DIRECTORY_BYTES:
        raise ValueError("ZIP central-directory metadata exceeds the configured limit")
    if directory_offset > file_size or directory_size > file_size - directory_offset:
        raise ValueError("ZIP central-directory range is outside the source archive")

    # ZIP self-extracting prefixes shift stored offsets by this amount. The
    # directory must still end exactly at the ZIP64 or classic end record.
    offset_adjustment = directory_end - directory_size - directory_offset
    if offset_adjustment < 0:
        raise ValueError("ZIP central-directory offsets are inconsistent")
    actual_directory_offset = directory_offset + offset_adjustment
    if actual_directory_offset + directory_size != directory_end:
        raise ValueError("ZIP central-directory range is inconsistent")
    directory = _tail_read(tail, tail_offset, actual_directory_offset, directory_size)

    members: list[dict[str, object]] = []
    names: set[str] = set()
    aggregate_filename_bytes = 0
    cursor = 0
    for _ in range(entry_count):
        if cursor + 46 > len(directory):
            raise ValueError("ZIP central-directory entry is truncated")
        fields = struct.unpack_from("<4s6H3I5H2I", directory, cursor)
        (
            signature,
            version_made,
            _version_needed,
            flags,
            compression_method,
            _modified_time,
            _modified_date,
            crc32,
            compressed_size,
            uncompressed_size,
            filename_size,
            extra_size,
            comment_size,
            disk_start,
            _internal_attributes,
            external_attributes,
            local_header_offset,
        ) = fields
        if signature != _CENTRAL_SIGNATURE:
            raise ValueError("ZIP central-directory entry signature is invalid")
        record_end = cursor + 46 + filename_size + extra_size + comment_size
        if record_end > len(directory):
            raise ValueError("ZIP central-directory member metadata is truncated")
        filename_start = cursor + 46
        filename_bytes = directory[filename_start:filename_start + filename_size]
        extra_start = filename_start + filename_size
        extra = directory[extra_start:extra_start + extra_size]
        cursor = record_end

        aggregate_filename_bytes += filename_size
        if aggregate_filename_bytes > MAX_FILENAME_BYTES:
            raise ValueError("ZIP aggregate filename bytes exceed the configured limit")
        if flags & (0x0001 | 0x0040 | 0x2000):
            raise ValueError("encrypted ZIP members are not supported")
        if compression_method not in _SUPPORTED_COMPRESSION:
            raise ValueError("ZIP member uses an unsupported compression method")
        if flags & 0x0800:
            name = filename_bytes.decode("utf-8", errors="strict")
        else:
            name = filename_bytes.decode("cp437", errors="strict")
        _validate_member_name(name)
        if name in names:
            raise ValueError("ZIP central directory contains duplicate member names")
        names.add(name)

        (
            uncompressed_size,
            compressed_size,
            local_header_offset,
            disk_start,
        ) = _zip64_member_values(
            extra,
            uncompressed_size,
            compressed_size,
            local_header_offset,
            disk_start,
        )
        if disk_start != 0:
            raise ValueError("multi-disk ZIP members are not supported")
        local_header_offset += offset_adjustment
        if local_header_offset >= actual_directory_offset:
            raise ValueError("ZIP local-header offset is outside the member-data area")

        member_type = "directory" if name.endswith("/") else "file"
        if version_made >> 8 == 3:
            unix_mode = external_attributes >> 16
            unix_type = stat.S_IFMT(unix_mode)
            if unix_type not in (0, stat.S_IFREG, stat.S_IFDIR):
                raise ValueError("ZIP contains a symlink or special Unix member")
            if unix_type == stat.S_IFDIR and member_type != "directory":
                raise ValueError("ZIP Unix directory metadata conflicts with its name")
            if unix_type == stat.S_IFREG and member_type != "file":
                raise ValueError("ZIP Unix file metadata conflicts with its name")

        members.append(
            {
                "name": name,
                "compressed_bytes": compressed_size,
                "uncompressed_bytes": uncompressed_size,
                "crc32": f"{crc32:08x}",
                "type": member_type,
                "compression": _SUPPORTED_COMPRESSION[compression_method],
            }
        )

    if cursor != len(directory):
        raise ValueError("ZIP central directory has unparsed or trailing metadata")
    total_compressed = sum(int(member["compressed_bytes"]) for member in members)
    total_uncompressed = sum(int(member["uncompressed_bytes"]) for member in members)
    return members, total_compressed, total_uncompressed


def _write_manifest_exclusive(path: Path, parent_fd: int,
                              parent_identity: tuple[int, int], payload: dict[str, object]) -> None:
    encoded = (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    if len(encoded) > MAX_MANIFEST_BYTES:
        raise ValueError("JSON manifest exceeds the configured size limit")
    _assert_parent_unchanged(path, parent_identity)
    name = path.name
    try:
        os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    except FileNotFoundError:
        pass
    else:
        raise FileExistsError(os.fspath(path))

    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
    flags |= getattr(os, "O_CLOEXEC", 0)
    output_fd = os.open(name, flags, 0o600, dir_fd=parent_fd)
    output_identity = None
    try:
        created = os.fstat(output_fd)
        output_identity = (created.st_dev, created.st_ino)
        if not stat.S_ISREG(created.st_mode) or created.st_nlink != 1:
            raise OSError("exclusive manifest is not a single-link regular file")
        view = memoryview(encoded)
        written = 0
        while written < len(view):
            count = os.write(output_fd, view[written:])
            if count <= 0:
                raise OSError("manifest write was incomplete")
            written += count
        os.fsync(output_fd)
        completed = os.fstat(output_fd)
        named = _named_file_stat(parent_fd, name)
        if (
            completed.st_size != len(encoded)
            or (completed.st_dev, completed.st_ino) != output_identity
            or _file_snapshot(named) != _file_snapshot(completed)
        ):
            raise OSError("exclusive manifest changed during write")
        _assert_parent_unchanged(path, parent_identity)
    except BaseException:
        if output_identity is not None:
            try:
                named = _named_file_stat(parent_fd, name)
                if (named.st_dev, named.st_ino) == output_identity:
                    os.unlink(name, dir_fd=parent_fd)
            except OSError:
                pass
        raise
    finally:
        os.close(output_fd)


def inspect_zip(
    path: os.PathLike[str] | str,
    *,
    expected_bytes: int,
    expected_md5: str,
    output_manifest: os.PathLike[str] | str,
) -> dict[str, object]:
    """Verify stored bytes and inventory metadata without decoding members."""
    if isinstance(expected_bytes, bool) or not isinstance(expected_bytes, int):
        raise ValueError("expected_bytes must be an integer")
    if expected_bytes < 0 or expected_bytes > MAX_INPUT_BYTES:
        raise ValueError("expected_bytes exceeds the configured archive size limit")
    if not isinstance(expected_md5, str) or re.fullmatch(r"[0-9a-fA-F]{32}", expected_md5) is None:
        raise ValueError("expected_md5 must contain 32 hexadecimal digits")

    source_path = _absolute_path(path)
    manifest_path = _absolute_path(output_manifest)
    if not source_path.name or not manifest_path.name:
        raise ValueError("source and manifest paths must name files")

    source_parent_fd = _open_parent_without_symlinks(source_path)
    manifest_parent_fd = None
    source_fd = None
    try:
        source_parent_identity = _directory_identity(source_parent_fd)
        source_name = source_path.name
        named_before_open = _named_file_stat(source_parent_fd, source_name)
        if not stat.S_ISREG(named_before_open.st_mode) or named_before_open.st_nlink != 1:
            raise ValueError("source archive must be a regular, non-link, single-link file")
        if named_before_open.st_size > MAX_INPUT_BYTES:
            raise ValueError("source archive exceeds the configured byte limit")
        if named_before_open.st_size != expected_bytes:
            raise ValueError("source archive size differs from expected_bytes")

        open_flags = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
        open_flags |= getattr(os, "O_NONBLOCK", 0)
        source_fd = os.open(source_name, open_flags, dir_fd=source_parent_fd)
        initial_info = os.fstat(source_fd)
        initial_snapshot = _file_snapshot(initial_info)
        if (
            not stat.S_ISREG(initial_info.st_mode)
            or initial_info.st_nlink != 1
            or initial_snapshot != _file_snapshot(named_before_open)
        ):
            raise ValueError("source archive changed while it was opened")
        _assert_parent_unchanged(source_path, source_parent_identity)
        _assert_source_unchanged(
            source_path,
            source_parent_fd,
            source_parent_identity,
            source_name,
            source_fd,
            initial_snapshot,
        )

        actual_md5, actual_sha256, captured_tail = _hash_source(source_fd, expected_bytes)
        if actual_md5.lower() != expected_md5.lower():
            raise ValueError("source archive MD5 differs from expected_md5")
        _assert_source_unchanged(
            source_path,
            source_parent_fd,
            source_parent_identity,
            source_name,
            source_fd,
            initial_snapshot,
        )

        manifest_parent_fd = _open_parent_without_symlinks(manifest_path)
        manifest_parent_identity = _directory_identity(manifest_parent_fd)
        try:
            os.stat(manifest_path.name, dir_fd=manifest_parent_fd, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            raise FileExistsError(os.fspath(manifest_path))

        members, total_compressed, total_uncompressed = _inventory_directory(
            expected_bytes, captured_tail, expected_bytes - len(captured_tail)
        )
        _assert_source_unchanged(
            source_path,
            source_parent_fd,
            source_parent_identity,
            source_name,
            source_fd,
            initial_snapshot,
        )
        post_md5, post_sha256, _unused_tail = _hash_source(
            source_fd, expected_bytes, capture_tail=False
        )
        _assert_source_unchanged(
            source_path,
            source_parent_fd,
            source_parent_identity,
            source_name,
            source_fd,
            initial_snapshot,
        )
        if (post_md5, post_sha256) != (actual_md5, actual_sha256):
            raise ValueError("source archive digest changed during inspection")

        payload: dict[str, object] = {
            "inventory_scope": "candidate_archive_metadata_only",
            "actual_asset_bytes": expected_bytes,
            "actual_asset_md5": actual_md5,
            "actual_asset_sha256": actual_sha256,
            "member_count": len(members),
            "members": members,
            "total_declared_compressed_bytes": total_compressed,
            "total_declared_uncompressed_bytes": total_uncompressed,
            "member_payload_integrity_not_assessed": True,
            "outcomes_not_read": True,
            "genomic_scoring_performed": False,
            "campaign_approval": False,
        }
        _write_manifest_exclusive(
            manifest_path,
            manifest_parent_fd,
            manifest_parent_identity,
            payload,
        )
        return payload
    finally:
        if source_fd is not None:
            os.close(source_fd)
        if manifest_parent_fd is not None:
            os.close(manifest_parent_fd)
        os.close(source_parent_fd)
