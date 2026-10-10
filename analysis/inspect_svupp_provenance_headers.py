"""Read fixed SVUPP provenance text and bounded VCF headers from a pinned ZIP.

Text members are preserved as exact UTF-8 strings and are never executed.
Nested gzip members are read as complete outer-ZIP payloads, then only their
VCF headers are interpreted. Gzip buffering can decode body bytes past the
header; genotype records are never parsed or saved and full nested-gzip CRC
integrity is not assessed.
"""
from __future__ import annotations

import gzip
import hashlib
import io
import os
import re
import stat
import zipfile
from pathlib import Path
from typing import Any

from analysis import inspect_pinned_research_zip as _source_guards


MAX_ARCHIVE_BYTES = 47_443_427
MAX_ZIP_MEMBERS = 4_096
MAX_ZIP_FILENAME_BYTES = 256 * 1024
MAX_MEMBER_BYTES = 12 * 1024 * 1024
MAX_SELECTED_MEMBER_BYTES = 32 * 1024 * 1024
EXPECTED_SELECTED_COMPRESSED_BYTES = 28_409_706
MAX_VCF_HEADER_BYTES = 256 * 1024
READ_CHUNK_BYTES = 64 * 1024

# Values are (member kind, exact ZIP-declared uncompressed size). Tests may
# replace this map with a small synthetic map; production callers use it as-is.
MEMBER_SPECS: dict[str, tuple[str, int]] = {
    "SVUPP_paper/README.md": ("text", 2_835),
    "SVUPP_paper/samplesheet/platinum-ont-ul.csv": ("text", 1_568),
    "SVUPP_paper/pipeline/bench-force-calling.nf": ("text", 6_496),
    "SVUPP_paper/reproduceplot/discordance_per_GQ_noneighbors.R": ("text", 5_329),
    "SVUPP_paper/reproduceplot/discordance_per_GQ_withneighbors.R": ("text", 5_346),
    "SVUPP_paper/reproduceplot/platinum.withdist1000.vcf.gz": ("gzip_vcf", 9_222_119),
    "SVUPP_paper/reproduceplot/kanpig.vcf.gz": ("gzip_vcf", 10_950_303),
    "SVUPP_paper/reproduceplot/svupp.vcf.gz": ("gzip_vcf", 9_250_146),
}

_FIXED_VCF_COLUMNS = (
    "#CHROM", "POS", "ID", "REF", "ALT", "QUAL", "FILTER", "INFO",
)
_ZIP_COMPRESSION_METHODS = {
    zipfile.ZIP_STORED,
    zipfile.ZIP_DEFLATED,
    zipfile.ZIP_BZIP2,
    zipfile.ZIP_LZMA,
}


def _validate_pins(
    expected_bytes: int, expected_md5: str, expected_sha256: str,
) -> tuple[str, str]:
    if type(expected_bytes) is not int or not 0 < expected_bytes <= MAX_ARCHIVE_BYTES:
        raise ValueError("expected_bytes is outside the configured archive limit")
    if not isinstance(expected_md5, str) or re.fullmatch(r"[0-9a-fA-F]{32}", expected_md5) is None:
        raise ValueError("expected_md5 must contain 32 hexadecimal digits")
    if not isinstance(expected_sha256, str) or re.fullmatch(r"[0-9a-fA-F]{64}", expected_sha256) is None:
        raise ValueError("expected_sha256 must contain 64 hexadecimal digits")
    if len(MEMBER_SPECS) != 8:
        raise ValueError("the fixed selected-member map must contain exactly eight entries")
    total = 0
    for name, spec in MEMBER_SPECS.items():
        if (not isinstance(name, str) or not name or type(spec) is not tuple
                or len(spec) != 2 or spec[0] not in {"text", "gzip_vcf"}
                or type(spec[1]) is not int or not 0 < spec[1] <= MAX_MEMBER_BYTES):
            raise ValueError("the fixed selected-member map is malformed")
        total += spec[1]
    if total > MAX_SELECTED_MEMBER_BYTES:
        raise ValueError("fixed selected members exceed the aggregate read limit")
    return expected_md5.lower(), expected_sha256.lower()


def _validate_zip_infos(infos: list[zipfile.ZipInfo]) -> dict[str, zipfile.ZipInfo]:
    if len(infos) > MAX_ZIP_MEMBERS:
        raise ValueError("ZIP member count exceeds the configured limit")
    filename_bytes = 0
    matches: dict[str, list[zipfile.ZipInfo]] = {name: [] for name in MEMBER_SPECS}
    for info in infos:
        filename_bytes += len(info.filename.encode("utf-8", errors="strict"))
        if filename_bytes > MAX_ZIP_FILENAME_BYTES:
            raise ValueError("ZIP aggregate filename bytes exceed the configured limit")
        if info.filename in matches:
            matches[info.filename].append(info)

    selected: dict[str, zipfile.ZipInfo] = {}
    selected_compressed_bytes = 0
    for name, (kind, expected_size) in MEMBER_SPECS.items():
        found = matches[name]
        if len(found) != 1:
            raise ValueError(f"fixed ZIP member is missing or duplicated: {name}")
        info = found[0]
        if info.file_size != expected_size:
            raise ValueError(f"fixed ZIP member size differs from the declaration: {name}")
        if (info.file_size > MAX_MEMBER_BYTES or info.compress_size < 0
                or info.compress_size > MAX_MEMBER_BYTES):
            raise ValueError(f"fixed ZIP member exceeds a size guard: {name}")
        if info.is_dir() or info.flag_bits & (0x0001 | 0x0040 | 0x2000):
            raise ValueError(f"fixed ZIP member is a directory or encrypted: {name}")
        if info.compress_type not in _ZIP_COMPRESSION_METHODS:
            raise ValueError(f"fixed ZIP member uses an unsupported compression method: {name}")
        if info.create_system == 3:
            unix_type = stat.S_IFMT(info.external_attr >> 16)
            if unix_type not in (0, stat.S_IFREG):
                raise ValueError(f"fixed ZIP member is not a regular file: {name}")
        if kind == "gzip_vcf" and not name.endswith(".vcf.gz"):
            raise ValueError(f"gzip VCF member name differs from its fixed kind: {name}")
        if kind == "text" and name.endswith(".vcf.gz"):
            raise ValueError(f"text member name differs from its fixed kind: {name}")
        selected[name] = info
        selected_compressed_bytes += info.compress_size
    if selected_compressed_bytes != EXPECTED_SELECTED_COMPRESSED_BYTES:
        raise ValueError("fixed selected ZIP-compressed byte total differs from the declaration")
    return selected


def _read_complete_member(
    archive: zipfile.ZipFile, info: zipfile.ZipInfo, expected_size: int,
) -> tuple[bytes, str]:
    digest = hashlib.sha256()
    blocks: list[bytes] = []
    total = 0
    # A final one-byte read at the exact declared size reaches ZipExtFile EOF,
    # which is where zipfile verifies the outer member CRC.
    with archive.open(info, "r") as member:
        while True:
            amount = min(READ_CHUNK_BYTES, expected_size - total + 1)
            block = member.read(amount)
            if not block:
                break
            total += len(block)
            if total > expected_size or total > MAX_MEMBER_BYTES:
                raise ValueError(f"ZIP member expanded beyond its declared bound: {info.filename}")
            digest.update(block)
            blocks.append(block)
    if total != expected_size or total != info.file_size:
        raise ValueError(f"ZIP member complete-read size differs: {info.filename}")
    return b"".join(blocks), digest.hexdigest()


def _parse_vcf_header(member_bytes: bytes) -> dict[str, Any]:
    header = bytearray()
    pending = bytearray()
    decoded_prefix_bytes = 0
    header_columns: list[str] | None = None
    header_cap_reached = False

    with gzip.GzipFile(fileobj=io.BytesIO(member_bytes), mode="rb") as nested:
        while True:
            remaining = MAX_VCF_HEADER_BYTES - decoded_prefix_bytes
            if remaining <= 0:
                header_cap_reached = True
                break
            # read1 bounds decompressed output from each decoder call. It can
            # still return body bytes after #CHROM; those bytes are discarded.
            block = nested.read1(min(READ_CHUNK_BYTES, remaining))
            if not block:
                break
            decoded_prefix_bytes += len(block)
            pending.extend(block)

            while True:
                newline = pending.find(b"\n")
                if newline < 0:
                    break
                raw_line = bytes(pending[:newline + 1])
                del pending[:newline + 1]
                header.extend(raw_line)
                if len(header) > MAX_VCF_HEADER_BYTES:
                    header_cap_reached = True
                    break
                if not raw_line.endswith(b"\n"):
                    raise ValueError("VCF header line is incomplete")
                text_line = raw_line.decode("utf-8", errors="strict")
                parse_line = text_line[:-1]
                if parse_line.endswith("\r"):
                    parse_line = parse_line[:-1]

                if parse_line.startswith("##"):
                    continue
                if parse_line.startswith("#CHROM"):
                    columns = parse_line.split("\t")
                    if columns[:8] != list(_FIXED_VCF_COLUMNS):
                        raise ValueError("VCF #CHROM fixed-column prefix is invalid")
                    if len(columns) == 8:
                        header_columns = columns
                    elif len(columns) == 9:
                        if columns[8] != "FORMAT":
                            raise ValueError("VCF #CHROM ninth column must be FORMAT")
                        raise ValueError("VCF FORMAT column has no sample columns")
                    else:
                        if columns[8] != "FORMAT":
                            raise ValueError("VCF #CHROM ninth column must be FORMAT")
                        samples = columns[9:]
                        if any(not sample for sample in samples):
                            raise ValueError("VCF sample names must be non-empty")
                        if len(set(samples)) != len(samples):
                            raise ValueError("VCF sample names must be unique")
                        header_columns = columns
                    break
                raise ValueError("non-header VCF record or line appears before #CHROM")

            if header_columns is not None:
                break
            if header_cap_reached:
                break
            if decoded_prefix_bytes >= MAX_VCF_HEADER_BYTES:
                header_cap_reached = True
                break

    if header_columns is None:
        if header_cap_reached:
            raise ValueError("VCF #CHROM header exceeds the 256 KiB decoded-prefix limit")
        if pending:
            pending.decode("utf-8", errors="strict")
            raise ValueError("VCF header line is incomplete before #CHROM")
        raise ValueError("VCF #CHROM header is absent before gzip EOF")

    samples = header_columns[9:] if len(header_columns) >= 10 else []
    format_present = len(header_columns) >= 9 and header_columns[8] == "FORMAT"
    return {
        "vcf_header_text": bytes(header).decode("utf-8", errors="strict"),
        "vcf_header_bytes": len(header),
        "vcf_header_sha256": hashlib.sha256(header).hexdigest(),
        "vcf_columns": header_columns,
        "sample_names": samples,
        "sample_count": len(samples),
        "format_column_present": format_present,
        "genotyping_input_status": (
            "missing_sample_columns" if not samples
            else "sample_columns_present_gt_content_unassessed"
        ),
        "decoded_prefix_bytes_observed": decoded_prefix_bytes,
        "body_bytes_may_be_included_by_gzip_read_ahead": True,
        "bodies_decoded": True,
        "genotype_records_not_interpreted": True,
        "nested_gzip_full_crc_not_assessed": True,
        "nested_gzip_body_integrity_not_assessed": True,
    }


def _assert_source_unchanged(
    source_path: Path,
    source_parent_fd: int,
    source_parent_identity: tuple[int, int],
    source_name: str,
    source_fd: int,
    initial_snapshot: tuple[int, ...],
) -> None:
    _source_guards._assert_source_unchanged(
        source_path,
        source_parent_fd,
        source_parent_identity,
        source_name,
        source_fd,
        initial_snapshot,
    )


def inspect_provenance_headers(
    path: os.PathLike[str] | str,
    *,
    expected_bytes: int,
    expected_md5: str,
    expected_sha256: str,
    output_manifest: os.PathLike[str] | str,
) -> dict[str, Any]:
    """Read the fixed eight members from one stable, SHA-pinned ZIP."""
    expected_md5, expected_sha256 = _validate_pins(
        expected_bytes, expected_md5, expected_sha256,
    )
    source_path = _source_guards._absolute_path(path)
    manifest_path = _source_guards._absolute_path(output_manifest)
    if not source_path.name or not manifest_path.name:
        raise ValueError("source and manifest paths must name files")

    source_parent_fd = _source_guards._open_parent_without_symlinks(source_path)
    manifest_parent_fd = None
    source_fd = None
    try:
        source_parent_identity = _source_guards._directory_identity(source_parent_fd)
        source_name = source_path.name
        named_before_open = _source_guards._named_file_stat(source_parent_fd, source_name)
        if not stat.S_ISREG(named_before_open.st_mode) or named_before_open.st_nlink != 1:
            raise ValueError("source archive must be a regular, non-link, single-link file")
        if named_before_open.st_size != expected_bytes:
            raise ValueError("source archive size differs from expected_bytes")
        if named_before_open.st_size > MAX_ARCHIVE_BYTES:
            raise ValueError("source archive exceeds the configured byte limit")

        flags = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
        flags |= getattr(os, "O_NONBLOCK", 0)
        source_fd = os.open(source_name, flags, dir_fd=source_parent_fd)
        opened = os.fstat(source_fd)
        initial_snapshot = _source_guards._file_snapshot(opened)
        if (not stat.S_ISREG(opened.st_mode) or opened.st_nlink != 1
                or initial_snapshot != _source_guards._file_snapshot(named_before_open)):
            raise ValueError("source archive changed while it was opened")
        _source_guards._assert_parent_unchanged(source_path, source_parent_identity)
        _assert_source_unchanged(
            source_path, source_parent_fd, source_parent_identity,
            source_name, source_fd, initial_snapshot,
        )

        pre_md5, pre_sha256, _unused_tail = _source_guards._hash_source(
            source_fd, expected_bytes, capture_tail=False,
        )
        if pre_md5.lower() != expected_md5 or pre_sha256.lower() != expected_sha256:
            raise ValueError("source archive MD5 or SHA256 differs from its pins")
        _assert_source_unchanged(
            source_path, source_parent_fd, source_parent_identity,
            source_name, source_fd, initial_snapshot,
        )

        manifest_parent_fd = _source_guards._open_parent_without_symlinks(manifest_path)
        manifest_parent_identity = _source_guards._directory_identity(manifest_parent_fd)
        try:
            os.stat(manifest_path.name, dir_fd=manifest_parent_fd, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            raise FileExistsError(os.fspath(manifest_path))

        members: list[dict[str, Any]] = []
        with os.fdopen(os.dup(source_fd), "rb") as pinned_stream:
            with zipfile.ZipFile(pinned_stream, "r") as archive:
                selected_infos = _validate_zip_infos(archive.infolist())
                for name, (kind, expected_size) in MEMBER_SPECS.items():
                    info = selected_infos[name]
                    _assert_source_unchanged(
                        source_path, source_parent_fd, source_parent_identity,
                        source_name, source_fd, initial_snapshot,
                    )
                    try:
                        member_bytes, member_sha256 = _read_complete_member(
                            archive, info, expected_size,
                        )
                        item: dict[str, Any] = {
                            "name": name,
                            "kind": kind,
                            "member_bytes": len(member_bytes),
                            "member_sha256": member_sha256,
                            "outer_zip_declared_uncompressed_bytes": info.file_size,
                            "outer_zip_compressed_bytes": info.compress_size,
                            "outer_zip_crc32": f"{info.CRC:08x}",
                            "outer_zip_compression": info.compress_type,
                            "outer_zip_crc_verified_by_complete_read": True,
                        }
                        if kind == "text":
                            item["text_utf8"] = member_bytes.decode("utf-8", errors="strict")
                            item["author_text_executed"] = False
                        else:
                            item.update(_parse_vcf_header(member_bytes))
                        members.append(item)
                    finally:
                        _assert_source_unchanged(
                            source_path, source_parent_fd, source_parent_identity,
                            source_name, source_fd, initial_snapshot,
                        )

        post_md5, post_sha256, _unused_tail = _source_guards._hash_source(
            source_fd, expected_bytes, capture_tail=False,
        )
        _assert_source_unchanged(
            source_path, source_parent_fd, source_parent_identity,
            source_name, source_fd, initial_snapshot,
        )
        if (post_md5.lower(), post_sha256.lower()) != (pre_md5.lower(), pre_sha256.lower()):
            raise ValueError("source archive digest changed during inspection")
        if post_md5.lower() != expected_md5 or post_sha256.lower() != expected_sha256:
            raise ValueError("post-inspection source archive digest differs from its pins")

        payload: dict[str, Any] = {
            "inspection_status": "COMPLETE_BOUNDED_PROVENANCE_HEADERS",
            "source_archive_bytes": expected_bytes,
            "source_archive_md5": pre_md5,
            "source_archive_sha256": pre_sha256,
            "source_archive_full_opaque_hash_passes": 2,
            "fixed_member_count": len(members),
            "selected_outer_zip_compressed_bytes": sum(
                item["outer_zip_compressed_bytes"] for item in members
            ),
            "members": members,
            "all_selected_outer_zip_members_read_to_crc_eof": True,
            "author_text_executed": False,
            "bodies_decoded": True,
            "genotype_records_not_interpreted": True,
            "nested_gzip_full_crc_not_assessed": True,
            "nested_gzip_body_integrity_not_assessed": True,
            "gzip_read_ahead_may_include_body_bytes": True,
            "usable_data_readiness_assessed": False,
        }
        _source_guards._write_manifest_exclusive(
            manifest_path, manifest_parent_fd, manifest_parent_identity, payload,
        )
        return payload
    finally:
        if source_fd is not None:
            os.close(source_fd)
        if manifest_parent_fd is not None:
            os.close(manifest_parent_fd)
        os.close(source_parent_fd)
