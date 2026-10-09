"""Offline tests for the pinned SVUPP archive inventory launcher."""

import hashlib
import io
import json
import os
import zipfile

import pytest

import analysis.inspect_pinned_research_zip as inspector
import analysis.run_svupp_archive_inventory as launcher


OPAQUE_MEMBER = b"\xff\x00private outcome bytes\xfe\x80"
TEST_URL = "https://example.test/SVUPP_paper.zip"


def _archive_bytes():
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", allowZip64=True) as archive:
        archive.writestr("README.txt", b"metadata only")
        archive.writestr(
            "opaque.bin", OPAQUE_MEMBER, compress_type=zipfile.ZIP_DEFLATED
        )
    return stream.getvalue()


class _Response:
    def __init__(self, body):
        self.body = body
        self.offset = 0

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self, amount=-1):
        if amount < 0:
            amount = len(self.body) - self.offset
        block = self.body[self.offset:self.offset + amount]
        self.offset += len(block)
        return block


def _configure_run(monkeypatch, tmp_path, body, *, expected_bytes=None,
                   expected_md5=None):
    root = tmp_path / "experiment"
    root.mkdir()
    expected_bytes = len(body) if expected_bytes is None else expected_bytes
    expected_md5 = hashlib.md5(body).hexdigest() if expected_md5 is None else expected_md5
    monkeypatch.setattr(launcher, "ROOT", root)
    monkeypatch.setattr(launcher, "ASSET_URL", TEST_URL)
    monkeypatch.setattr(launcher, "ASSET_BYTES", expected_bytes)
    monkeypatch.setattr(launcher, "ASSET_MD5", expected_md5)
    # Keep the launcher's process-wide file-size limit local to this test.
    monkeypatch.setattr(launcher.resource, "setrlimit", lambda *_args: None)
    calls = []

    def fake_urlopen(url, timeout):
        calls.append((url, timeout))
        return _Response(body)

    monkeypatch.setattr(launcher.urllib.request, "urlopen", fake_urlopen)
    return root, calls


def test_complete_run_writes_exclusive_metadata_inventory_marker(tmp_path, monkeypatch):
    data = _archive_bytes()
    root, calls = _configure_run(monkeypatch, tmp_path, data)
    original_pread = inspector.os.pread
    source_reads = []

    def record_pread(fd, amount, offset):
        block = original_pread(fd, amount, offset)
        source_reads.append((offset, amount, block))
        return block

    monkeypatch.setattr(inspector.os, "pread", record_pread)

    launcher.run(root)

    assert calls == [(TEST_URL, 30)]
    assert (root / "SVUPP_paper.zip").read_bytes() == data
    assert [(offset, amount) for offset, amount, _ in source_reads] == [
        (0, len(data)), (0, len(data))
    ]
    assert all(isinstance(block, bytes) for _, _, block in source_reads)
    assert all(block == data for _, _, block in source_reads)

    acquisition = json.loads((root / "acquisition.json").read_text())
    assert acquisition["bytes"] == len(data)
    assert acquisition["md5"] == hashlib.md5(data).hexdigest()
    assert acquisition["sha256"] == hashlib.sha256(data).hexdigest()
    assert acquisition["member_bodies_decoded"] is False
    assert acquisition["opaque_zip_bytes_hashed"] is True

    inventory_path = root / "inventory.json"
    inventory = json.loads(inventory_path.read_text())
    assert inventory["actual_asset_sha256"] == hashlib.sha256(data).hexdigest()
    assert inventory["outcomes_not_read"] is True
    assert inventory["member_payload_integrity_not_assessed"] is True
    assert [member["name"] for member in inventory["members"]] == [
        "README.txt", "opaque.bin"
    ]
    assert OPAQUE_MEMBER.decode("latin1") not in inventory_path.read_text()

    result_path = root / "result.json"
    result = json.loads(result_path.read_text())
    assert result["status"] == "COMPLETE_METADATA_INVENTORY"
    assert result["outcomes_not_read"] is True
    assert result["publication_result"] is False
    with pytest.raises(FileExistsError):
        launcher.new_metadata(result_path, {"status": "REPLACED"})
    assert json.loads(result_path.read_text()) == result


@pytest.mark.parametrize("bad_body,wrong_digest", [
    ("truncated", False),
    ("oversized", False),
    ("complete", True),
])
def test_invalid_acquisition_never_writes_completion_marker(
    tmp_path, monkeypatch, bad_body, wrong_digest
):
    data = _archive_bytes()
    if bad_body == "truncated":
        response_body = data[:-1]
    elif bad_body == "oversized":
        response_body = data + b"x"
    else:
        response_body = data
    md5 = "0" * 32 if wrong_digest else hashlib.md5(data).hexdigest()
    root, _calls = _configure_run(
        monkeypatch,
        tmp_path,
        response_body,
        expected_bytes=len(data),
        expected_md5=md5,
    )

    with pytest.raises(ValueError):
        launcher.run(root)

    assert not (root / "result.json").exists()
    assert not (root / "acquisition.json").exists()


def test_stored_sha_mismatch_never_writes_completion_marker(tmp_path, monkeypatch):
    data = _archive_bytes()
    root, _calls = _configure_run(monkeypatch, tmp_path, data)
    original_inspect = inspector.inspect_zip

    def report_wrong_stored_sha(*args, **kwargs):
        report = original_inspect(*args, **kwargs)
        report["actual_asset_sha256"] = "0" * 64
        return report

    monkeypatch.setattr(inspector, "inspect_zip", report_wrong_stored_sha)

    with pytest.raises(ValueError, match="stored archive differs"):
        launcher.run(root)

    assert (root / "inventory.json").exists()
    assert not (root / "result.json").exists()


def test_duplicate_payload_claim_prevents_network_replay(tmp_path, monkeypatch):
    data = _archive_bytes()
    root, calls = _configure_run(monkeypatch, tmp_path, data[:-1])

    with pytest.raises(ValueError):
        launcher.run(root)
    claim_path = root / "payload.claim.json"
    original_claim = claim_path.read_bytes()

    with pytest.raises(FileExistsError):
        launcher.run(root)

    assert calls == [(TEST_URL, 30)]
    assert claim_path.read_bytes() == original_claim
    assert not (root / "result.json").exists()


@pytest.mark.parametrize("root_kind", ["different", "symlink"])
def test_untrusted_root_is_rejected_before_network(tmp_path, monkeypatch, root_kind):
    data = _archive_bytes()
    trusted_root, calls = _configure_run(monkeypatch, tmp_path, data)
    if root_kind == "different":
        supplied_root = tmp_path / "other"
        supplied_root.mkdir()
    else:
        supplied_root = tmp_path / "linked-experiment"
        supplied_root.symlink_to(trusted_root, target_is_directory=True)

    with pytest.raises(ValueError, match="unexpected or linked"):
        launcher.run(supplied_root)

    assert calls == []
    assert not (trusted_root / "payload.claim.json").exists()


def test_control_tree_size_counts_hardlinks_and_does_not_follow_symlinks(tmp_path):
    tree = tmp_path / "tree"
    tree.mkdir()
    first = tree / "first.bin"
    first.write_bytes(b"1234")
    os.link(first, tree / "hardlink.bin")

    outside = tmp_path / "outside"
    outside.mkdir()
    outside_file = outside / "large.bin"
    outside_file.write_bytes(b"outside data must not be counted" * 100)
    (tree / "file-link").symlink_to(outside_file)
    (tree / "directory-link").symlink_to(outside, target_is_directory=True)

    assert launcher.control_tree_size(tree) == 8


def test_control_tree_size_enforces_byte_and_entry_caps(tmp_path):
    oversized = tmp_path / "oversized"
    oversized.mkdir()
    with (oversized / "sparse.bin").open("wb") as output:
        output.truncate(32 * 1024**2 + 1)
    with pytest.raises(ValueError, match="exceeds its cap"):
        launcher.control_tree_size(oversized)
    # Remove only the synthetic sparse cap witness after the assertion. The
    # enclosing actual-stack control tree must satisfy the production cap.
    (oversized / "sparse.bin").unlink()

    too_many = tmp_path / "too-many"
    too_many.mkdir()
    for index in range(4097):
        (too_many / str(index)).touch()
    with pytest.raises(ValueError, match="exceeds its cap"):
        launcher.control_tree_size(too_many)
    for index in range(4097):
        (too_many / str(index)).unlink()


def test_control_tree_size_rejects_special_files(tmp_path):
    tree = tmp_path / "special"
    tree.mkdir()
    os.mkfifo(tree / "pipe")

    with pytest.raises(ValueError, match="unexpected special"):
        launcher.control_tree_size(tree)
    (tree / "pipe").unlink()


def test_new_metadata_never_overwrites_existing_file(tmp_path):
    path = tmp_path / "metadata.json"
    path.write_bytes(b"existing metadata\n")

    with pytest.raises(FileExistsError):
        launcher.new_metadata(path, {"status": "REPLACED"})

    assert path.read_bytes() == b"existing metadata\n"
