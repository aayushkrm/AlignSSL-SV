import hashlib
import json
import os
import stat
import struct
import warnings
import zipfile

import pytest

import analysis.inspect_pinned_research_zip as inventory_module
from analysis.inspect_pinned_research_zip import MAX_INPUT_BYTES, inspect_zip


def make_archive(path, entries=(("data/readme.txt", b"PAYLOAD MUST NOT BE READ"),)):
    with zipfile.ZipFile(path, "w", allowZip64=True) as archive:
        for name, body in entries:
            archive.writestr(name, body, compress_type=zipfile.ZIP_DEFLATED)
    return path


def call_inspect(source, output, *, expected_bytes=None, expected_md5=None):
    source_bytes = source.stat().st_size
    return inspect_zip(
        source,
        expected_bytes=source_bytes if expected_bytes is None else expected_bytes,
        expected_md5=(hashlib.md5(source.read_bytes()).hexdigest()
                      if expected_md5 is None else expected_md5),
        output_manifest=output,
    )


def test_valid_inventory_verifies_hashes_and_writes_bounded_manifest(tmp_path, monkeypatch):
    source = make_archive(
        tmp_path / "candidate.zip",
        (("data/readme.txt", b"member bytes remain unread"), ("docs/", b"")),
    )
    output = tmp_path / "inventory.json"
    source_read_sizes = []
    original_pread = inventory_module.os.pread

    def count_source_reads(fd, amount, offset):
        source_read_sizes.append(amount)
        return original_pread(fd, amount, offset)

    monkeypatch.setattr(inventory_module.os, "pread", count_source_reads)

    report = call_inspect(source, output)

    data = source.read_bytes()
    assert report["actual_asset_bytes"] == len(data)
    assert report["actual_asset_md5"] == hashlib.md5(data).hexdigest()
    assert report["actual_asset_sha256"] == hashlib.sha256(data).hexdigest()
    assert report["member_count"] == 2
    with zipfile.ZipFile(source) as archive:
        expected_compressed_sizes = [info.compress_size for info in archive.infolist()]
        expected_uncompressed_sizes = [info.file_size for info in archive.infolist()]
    assert report["members"] == [
        {
            "name": "data/readme.txt",
            "compressed_bytes": expected_compressed_sizes[0],
            "uncompressed_bytes": len(b"member bytes remain unread"),
            "crc32": f"{zipfile.crc32(b'member bytes remain unread'):08x}",
            "type": "file",
            "compression": "deflate",
        },
        {
            "name": "docs/",
            "compressed_bytes": expected_compressed_sizes[1],
            "uncompressed_bytes": 0,
            "crc32": "00000000",
            "type": "directory",
            "compression": "deflate",
        },
    ]
    assert report["total_declared_compressed_bytes"] == sum(
        expected_compressed_sizes
    )
    assert report["total_declared_uncompressed_bytes"] == sum(expected_uncompressed_sizes)
    assert report["member_payload_integrity_not_assessed"] is True
    assert report["outcomes_not_read"] is True
    assert report["genomic_scoring_performed"] is False
    assert report["campaign_approval"] is False
    assert json.loads(output.read_text()) == report
    assert output.stat().st_size <= 1024 * 1024
    assert sum(source_read_sizes) == 2 * len(data)


@pytest.mark.parametrize("wrong_size,wrong_md5", [(True, False), (False, True)])
def test_expected_size_and_md5_are_required_before_inventory(tmp_path, wrong_size, wrong_md5):
    source = make_archive(tmp_path / "candidate.zip")
    output = tmp_path / "inventory.json"
    source_size = source.stat().st_size
    expected_md5 = hashlib.md5(source.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="size differs|MD5 differs"):
        inspect_zip(
            source,
            expected_bytes=source_size + int(wrong_size),
            expected_md5=("0" * 32 if wrong_md5 else expected_md5),
            output_manifest=output,
        )
    assert not output.exists()


def test_expected_input_size_cannot_exceed_candidate_cap(tmp_path):
    source = make_archive(tmp_path / "candidate.zip")
    with pytest.raises(ValueError, match="configured archive size limit"):
        inspect_zip(
            source,
            expected_bytes=MAX_INPUT_BYTES + 1,
            expected_md5=hashlib.md5(source.read_bytes()).hexdigest(),
            output_manifest=tmp_path / "inventory.json",
        )


def test_source_change_during_directory_inspection_leaves_no_manifest(tmp_path, monkeypatch):
    source = make_archive(tmp_path / "candidate.zip")
    output = tmp_path / "inventory.json"
    original = inventory_module._inventory_directory

    def inspect_then_change(file_size, tail, tail_offset):
        result = original(file_size, tail, tail_offset)
        with source.open("r+b") as handle:
            handle.seek(0)
            handle.write(b"X")
            handle.flush()
            os.fsync(handle.fileno())
        return result

    monkeypatch.setattr(inventory_module, "_inventory_directory", inspect_then_change)
    with pytest.raises(ValueError, match="changed during inspection"):
        call_inspect(source, output)
    assert not output.exists()


def test_existing_manifest_is_never_overwritten(tmp_path):
    source = make_archive(tmp_path / "candidate.zip")
    output = tmp_path / "inventory.json"
    output.write_bytes(b"existing")
    with pytest.raises(FileExistsError):
        call_inspect(source, output)
    assert output.read_bytes() == b"existing"


@pytest.mark.parametrize("flag", [0x0001, 0x0040, 0x2000])
def test_encrypted_or_masked_metadata_flags_are_rejected(tmp_path, flag):
    source = make_archive(tmp_path / "candidate.zip")
    data = bytearray(source.read_bytes())
    central = data.index(b"PK\x01\x02")
    flags = struct.unpack_from("<H", data, central + 8)[0]
    struct.pack_into("<H", data, central + 8, flags | flag)
    source.write_bytes(data)
    with pytest.raises(ValueError, match="encrypted"):
        call_inspect(source, tmp_path / "inventory.json")


def test_unsupported_compression_metadata_is_rejected(tmp_path):
    source = make_archive(tmp_path / "candidate.zip")
    data = bytearray(source.read_bytes())
    central = data.index(b"PK\x01\x02")
    struct.pack_into("<H", data, central + 10, 99)
    source.write_bytes(data)
    with pytest.raises(ValueError, match="unsupported compression"):
        call_inspect(source, tmp_path / "inventory.json")


def test_duplicate_and_traversal_names_are_rejected(tmp_path):
    duplicate = tmp_path / "duplicate.zip"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        make_archive(duplicate, (("same.txt", b"a"), ("same.txt", b"b")))
    with pytest.raises(ValueError, match="duplicate member names"):
        call_inspect(duplicate, tmp_path / "duplicate.json")

    for index, name in enumerate(("../outside.txt", "/absolute.txt", r"C:\\outside.txt")):
        source = make_archive(tmp_path / f"traversal-{index}.zip", ((name, b"x"),))
        with pytest.raises(ValueError, match="absolute|traversal"):
            call_inspect(source, tmp_path / f"traversal-{index}.json")


def test_symlink_special_member_and_linked_source_are_rejected(tmp_path):
    source = tmp_path / "symlink-member.zip"
    info = zipfile.ZipInfo("link")
    info.create_system = 3
    info.external_attr = (stat.S_IFLNK | 0o777) << 16
    with zipfile.ZipFile(source, "w") as archive:
        archive.writestr(info, "target")
    with pytest.raises(ValueError, match="symlink or special"):
        call_inspect(source, tmp_path / "symlink-member.json")

    regular = make_archive(tmp_path / "regular.zip")
    symbolic = tmp_path / "symbolic.zip"
    symbolic.symlink_to(regular)
    with pytest.raises(ValueError, match="regular, non-link, single-link"):
        call_inspect(symbolic, tmp_path / "symbolic.json")

    hardlinked = tmp_path / "hardlinked.zip"
    os.link(regular, hardlinked)
    with pytest.raises(ValueError, match="regular, non-link, single-link"):
        call_inspect(hardlinked, tmp_path / "hardlinked.json")


def test_symlink_parent_is_rejected(tmp_path):
    real_dir = tmp_path / "real"
    real_dir.mkdir()
    source = make_archive(real_dir / "candidate.zip")
    linked_dir = tmp_path / "linked"
    linked_dir.symlink_to(real_dir, target_is_directory=True)
    with pytest.raises(ValueError, match="parent.*symlink"):
        call_inspect(linked_dir / source.name, tmp_path / "inventory.json")


def test_member_count_and_filename_caps_are_enforced(tmp_path, monkeypatch):
    source = tmp_path / "too-many.zip"
    # A small synthetic end record proves the count limit is checked before
    # the utility reads or allocates a member directory.
    source.write_bytes(struct.pack("<4s4H2IH", b"PK\x05\x06", 0, 0, 4097, 4097, 0, 0, 0))
    with pytest.raises(ValueError, match="member count"):
        call_inspect(source, tmp_path / "too-many.json")

    source = make_archive(tmp_path / "long-name.zip", (("long-name.txt", b"x"),))
    monkeypatch.setattr(inventory_module, "MAX_FILENAME_BYTES", 3)
    with pytest.raises(ValueError, match="filename bytes"):
        call_inspect(source, tmp_path / "long-name.json")


def test_central_directory_byte_cap_is_enforced(tmp_path, monkeypatch):
    source = make_archive(tmp_path / "directory-cap.zip")
    monkeypatch.setattr(inventory_module, "MAX_DIRECTORY_BYTES", 32)
    with pytest.raises(ValueError, match="central-directory metadata"):
        call_inspect(source, tmp_path / "directory-cap.json")


def test_manifest_byte_cap_is_enforced_before_exclusive_create(tmp_path, monkeypatch):
    source = make_archive(tmp_path / "manifest-cap.zip")
    output = tmp_path / "manifest-cap.json"
    monkeypatch.setattr(inventory_module, "MAX_MANIFEST_BYTES", 16)
    with pytest.raises(ValueError, match="manifest exceeds"):
        call_inspect(source, output)
    assert not output.exists()
