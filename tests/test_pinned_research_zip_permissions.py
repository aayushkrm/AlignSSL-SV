import errno
import hashlib
import json
import os
import stat
import sys
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest

import analysis.inspect_pinned_research_zip as inventory_module
from analysis.inspect_pinned_research_zip import inspect_zip


def _make_archive(path):
    with zipfile.ZipFile(path, "w", allowZip64=True) as archive:
        archive.writestr("data/readme.txt", b"member payload stays opaque")
    contents = path.read_bytes()
    return len(contents), hashlib.md5(contents).hexdigest()


def _require_unprivileged_owner(path):
    effective_uid = os.geteuid()
    assert effective_uid != 0, "permission controls must run as a non-root user"
    assert path.stat().st_uid == effective_uid
    return effective_uid


def _assert_access(path, mode, expected):
    assert os.access(path, mode, effective_ids=True) is expected


def _assert_readonly_open_denied(path, *, directory=False):
    flags = os.O_RDONLY
    if directory:
        flags |= os.O_DIRECTORY
    with pytest.raises(PermissionError) as raised:
        descriptor = os.open(path, flags)
        os.close(descriptor)
    assert raised.value.errno == errno.EACCES


def _record_preads(monkeypatch):
    calls = []
    original_pread = inventory_module.os.pread

    def record_pread(descriptor, amount, offset):
        calls.append((descriptor, amount, offset))
        return original_pread(descriptor, amount, offset)

    monkeypatch.setattr(inventory_module.os, "pread", record_pread)
    return calls


def _record_component_open_failures(monkeypatch, component):
    failures = []
    original_open = inventory_module.os.open

    def record_open(path, *args, **kwargs):
        try:
            return original_open(path, *args, **kwargs)
        except OSError as exc:
            if path == component:
                failures.append(exc)
            raise

    monkeypatch.setattr(inventory_module.os, "open", record_open)
    return failures


@pytest.mark.skipif(
    not sys.platform.startswith("linux"),
    reason="requires Linux directory permission semantics",
)
def test_searchable_unreadable_owned_directory_allows_inspection_and_manifest(tmp_path):
    directory = tmp_path / "searchable-unreadable"
    directory.mkdir()
    source = directory / "candidate.zip"
    output = directory / "inventory.json"
    expected_bytes, expected_md5 = _make_archive(source)
    effective_uid = _require_unprivileged_owner(directory)
    original_mode = stat.S_IMODE(directory.stat().st_mode)

    try:
        os.chmod(directory, 0o300)
        assert directory.stat().st_uid == effective_uid
        _assert_access(directory, os.R_OK, False)
        _assert_access(directory, os.X_OK, True)
        _assert_readonly_open_denied(directory, directory=True)
        _assert_access(source, os.R_OK, True)

        report = inspect_zip(
            source,
            expected_bytes=expected_bytes,
            expected_md5=expected_md5,
            output_manifest=output,
        )

        assert report["member_count"] == 1
        assert json.loads(output.read_text()) == report
    finally:
        os.chmod(directory, original_mode)


@pytest.mark.skipif(
    not sys.platform.startswith("linux"),
    reason="requires Linux directory permission semantics",
)
def test_unsearchable_intermediate_fails_before_archive_read_or_manifest(
    tmp_path, monkeypatch
):
    first = tmp_path / "first"
    intermediate = first / "intermediate"
    source_directory = intermediate / "source-parent"
    source_directory.mkdir(parents=True)
    source = source_directory / "candidate.zip"
    expected_bytes, expected_md5 = _make_archive(source)
    effective_uid = _require_unprivileged_owner(intermediate)
    output = tmp_path / "inventory.json"
    original_mode = stat.S_IMODE(intermediate.stat().st_mode)

    try:
        os.chmod(intermediate, 0o600)
        assert intermediate.stat().st_uid == effective_uid
        _assert_access(intermediate, os.X_OK, False)
        _assert_readonly_open_denied(source_directory, directory=True)
        pread_calls = _record_preads(monkeypatch)
        failed_component_opens = _record_component_open_failures(
            monkeypatch, source_directory.name
        )

        with pytest.raises(ValueError, match="parent.*missing, unsafe, or a symlink") as raised:
            inspect_zip(
                source,
                expected_bytes=expected_bytes,
                expected_md5=expected_md5,
                output_manifest=output,
            )

        cause = raised.value.__cause__
        assert isinstance(cause, PermissionError)
        assert failed_component_opens == [cause]
        assert cause.filename == source_directory.name
        assert cause.errno == errno.EACCES
        assert pread_calls == []
        assert not output.exists()
    finally:
        os.chmod(intermediate, original_mode)


@pytest.mark.skipif(
    not sys.platform.startswith("linux"),
    reason="requires Linux file permission semantics",
)
def test_unreadable_archive_leaf_fails_before_read_or_manifest(tmp_path, monkeypatch):
    source = tmp_path / "candidate.zip"
    expected_bytes, expected_md5 = _make_archive(source)
    effective_uid = _require_unprivileged_owner(source)
    output = tmp_path / "inventory.json"
    original_mode = stat.S_IMODE(source.stat().st_mode)

    try:
        os.chmod(source, 0o000)
        assert source.stat().st_uid == effective_uid
        _assert_access(source, os.R_OK, False)
        _assert_readonly_open_denied(source)
        pread_calls = _record_preads(monkeypatch)
        failed_leaf_opens = _record_component_open_failures(
            monkeypatch, source.name
        )

        with pytest.raises(PermissionError) as raised:
            inspect_zip(
                source,
                expected_bytes=expected_bytes,
                expected_md5=expected_md5,
                output_manifest=output,
            )

        assert failed_leaf_opens == [raised.value]
        assert raised.value.filename == source.name
        assert raised.value.errno == errno.EACCES
        assert pread_calls == []
        assert not output.exists()
    finally:
        os.chmod(source, original_mode)


def test_linux_without_opath_fails_closed_before_any_open(monkeypatch):
    monkeypatch.setattr(inventory_module, "sys", SimpleNamespace(platform="linux"))
    monkeypatch.delattr(inventory_module.os, "O_PATH", raising=False)
    open_calls = []
    def trace_open(*args, **kwargs):
        open_calls.append((args, kwargs))
        raise AssertionError("os.open must not run without Linux O_PATH")

    monkeypatch.setattr(inventory_module.os, "open", trace_open)
    with pytest.raises(
        OSError, match="safe Linux directory references are not supported"
    ):
        inventory_module._open_parent_without_symlinks(
            Path("/synthetic/parent/candidate.zip")
        )
    assert open_calls == []


def test_nonlinux_parent_open_uses_readonly_and_closes_directory_descriptors(
    monkeypatch,
):
    monkeypatch.setattr(inventory_module, "sys", SimpleNamespace(platform="darwin"))
    open_calls = []
    close_calls = []

    def trace_open(path, flags, *args, **kwargs):
        descriptor = 100 + len(open_calls)
        open_calls.append((path, flags, kwargs.get("dir_fd"), descriptor))
        return descriptor

    def fake_fstat(_descriptor):
        return SimpleNamespace(st_mode=stat.S_IFDIR | 0o755)

    def trace_close(descriptor):
        assert descriptor not in close_calls
        close_calls.append(descriptor)

    monkeypatch.setattr(inventory_module.os, "open", trace_open)
    monkeypatch.setattr(inventory_module.os, "fstat", fake_fstat)
    monkeypatch.setattr(inventory_module.os, "close", trace_close)
    parent_fd = inventory_module._open_parent_without_symlinks(
        Path("/synthetic/parent/candidate.zip")
    )
    try:
        assert stat.S_ISDIR(os.fstat(parent_fd).st_mode)
        assert [
            (path, dir_fd) for path, _flags, dir_fd, _descriptor in open_calls
        ] == [
            ("/", None), ("synthetic", 100), ("parent", 101)
        ]
        for _path, flags, _dir_fd, _descriptor in open_calls:
            assert (flags & os.O_ACCMODE) == os.O_RDONLY
            assert flags & os.O_DIRECTORY
            assert flags & os.O_NOFOLLOW
            assert (flags & getattr(os, "O_PATH", 0)) == 0
        assert len(close_calls) == len(open_calls) - 1
    finally:
        os.close(parent_fd)

    assert len(close_calls) == len(set(close_calls)) == len(open_calls)
    assert sorted(close_calls) == sorted(
        descriptor for _path, _flags, _dir_fd, descriptor in open_calls
    )
