"""Offline tests for the fixed SVUPP provenance launcher."""

import json
from pathlib import Path
import sys

import pytest

import analysis.inspect_svupp_provenance_headers as reader_module
import analysis.run_svupp_provenance_headers as launcher


METADATA_LIMIT = 64 * 1024


def _valid_report():
    return {
        "inspection_status": "COMPLETE_BOUNDED_PROVENANCE_HEADERS",
        "source_archive_sha256": launcher.SOURCE_SHA256,
        "fixed_member_count": 8,
        "all_selected_outer_zip_members_read_to_crc_eof": True,
        "author_text_executed": False,
        "bodies_decoded": True,
        "genotype_records_not_interpreted": True,
        "nested_gzip_full_crc_not_assessed": True,
        "nested_gzip_body_integrity_not_assessed": True,
        "gzip_read_ahead_may_include_body_bytes": True,
        "usable_data_readiness_assessed": False,
    }


def _make_root(monkeypatch, path):
    path.mkdir(parents=True)
    monkeypatch.setattr(launcher, "ROOT", path)
    return path


def _install_reader_mock(monkeypatch, *, report=None, error=None):
    report = _valid_report() if report is None else dict(report)
    calls = []

    def fake_reader(path, *, expected_bytes, expected_md5, expected_sha256,
                    output_manifest):
        manifest_path = Path(output_manifest)
        root = manifest_path.parent
        claim_path = root / "payload.claim.json"
        assert claim_path.is_file(), "launcher must claim the payload before reading"
        calls.append({
            "path": path,
            "expected_bytes": expected_bytes,
            "expected_md5": expected_md5,
            "expected_sha256": expected_sha256,
            "output_manifest": manifest_path,
        })
        if error is not None:
            raise error
        with manifest_path.open("x", encoding="utf-8") as output:
            output.write(json.dumps(report, sort_keys=True, indent=2) + "\n")
        return report

    # The reader worker may rename this entry point while its API settles.
    monkeypatch.setattr(
        reader_module, "inspect_provenance_headers", fake_reader, raising=False,
    )
    monkeypatch.setattr(reader_module, "inspect_archive", fake_reader, raising=False)
    return calls, report


def _invoke_main(monkeypatch, root, *extra_args):
    monkeypatch.setattr(
        sys, "argv",
        ["run_svupp_provenance_headers", "--root", str(root), *extra_args],
    )
    return launcher.main()


def test_valid_run_writes_claim_manifest_and_completion_exclusively(
    tmp_path, monkeypatch,
):
    root = _make_root(monkeypatch, tmp_path / "experiment")
    calls, report = _install_reader_mock(monkeypatch)

    _invoke_main(monkeypatch, root)

    claim_path = root / "payload.claim.json"
    claim = json.loads(claim_path.read_text(encoding="utf-8"))
    assert claim == {
        "experiment": launcher.EXPERIMENT,
        "root": str(root),
        "source": str(launcher.SOURCE),
        "genotype_records_not_interpreted": True,
        "author_code_not_executed": True,
    }
    assert calls == [{
        "path": launcher.SOURCE,
        "expected_bytes": launcher.SOURCE_BYTES,
        "expected_md5": launcher.SOURCE_MD5,
        "expected_sha256": launcher.SOURCE_SHA256,
        "output_manifest": root / "provenance_headers.json",
    }]

    manifest_path = root / "provenance_headers.json"
    assert json.loads(manifest_path.read_text(encoding="utf-8")) == report
    result_path = root / "result.json"
    result_bytes = result_path.read_bytes()
    assert json.loads(result_bytes) == {
        "status": "COMPLETE_PROVENANCE_HEADERS",
        "experiment": launcher.EXPERIMENT,
        "source_sha256": launcher.SOURCE_SHA256,
        "fixed_member_count": 8,
        "member_bodies_decoded": True,
        "genotype_records_not_interpreted": True,
        "nested_gzip_full_crc_not_assessed": True,
        "author_code_not_executed": True,
        "scientific_data_readiness": "UNRESOLVED_PROVENANCE_ONLY",
        "publication_result": False,
        "campaign_approval": False,
    }

    with pytest.raises(FileExistsError):
        launcher.new_metadata(result_path, {"status": "REPLACED"})
    assert result_path.read_bytes() == result_bytes
    assert all(path.stat().st_size < 2 * 1024 * 1024 for path in root.iterdir())
    assert sum(path.stat().st_size for path in root.iterdir()) < 8 * 1024 * 1024
    assert len(list(root.iterdir())) <= 4096


def test_reader_exception_writes_failure_metadata_but_no_completion(
    tmp_path, monkeypatch,
):
    root = _make_root(monkeypatch, tmp_path / "experiment")
    calls, _report = _install_reader_mock(
        monkeypatch, error=RuntimeError("synthetic reader failure"),
    )

    with pytest.raises(RuntimeError, match="synthetic reader failure"):
        _invoke_main(monkeypatch, root)

    assert len(calls) == 1
    assert (root / "payload.claim.json").is_file()
    assert not (root / "provenance_headers.json").exists()
    assert not (root / "result.json").exists()
    failure = json.loads((root / "failure.json").read_text(encoding="utf-8"))
    assert failure["status"] == "INCOMPLETE"
    assert failure["error_type"] == "RuntimeError"
    assert failure["genotype_records_not_interpreted"] is True
    assert failure["publication_result"] is False


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("inspection_status", "INCOMPLETE"),
        ("source_archive_sha256", "0" * 64),
        ("fixed_member_count", 7),
        ("all_selected_outer_zip_members_read_to_crc_eof", False),
        ("author_text_executed", True),
        ("bodies_decoded", False),
        ("genotype_records_not_interpreted", False),
        ("nested_gzip_full_crc_not_assessed", False),
        ("nested_gzip_body_integrity_not_assessed", False),
        ("gzip_read_ahead_may_include_body_bytes", False),
        ("usable_data_readiness_assessed", True),
    ],
)
def test_report_outside_frozen_scope_never_writes_completion(
    tmp_path, monkeypatch, field, bad_value,
):
    root = _make_root(monkeypatch, tmp_path / "experiment")
    report = _valid_report()
    report[field] = bad_value
    calls, _report = _install_reader_mock(monkeypatch, report=report)

    with pytest.raises(ValueError, match="did not satisfy the frozen scope"):
        _invoke_main(monkeypatch, root)

    assert len(calls) == 1
    assert not (root / "result.json").exists()
    failure = json.loads((root / "failure.json").read_text(encoding="utf-8"))
    assert failure["status"] == "INCOMPLETE"
    assert failure["error_type"] == "ValueError"


def test_consumed_payload_claim_prevents_reader_replay(tmp_path, monkeypatch):
    root = _make_root(monkeypatch, tmp_path / "experiment")
    calls, _report = _install_reader_mock(monkeypatch)
    launcher.run(root)
    original_claim = (root / "payload.claim.json").read_bytes()
    original_manifest = (root / "provenance_headers.json").read_bytes()
    original_result = (root / "result.json").read_bytes()

    with pytest.raises(FileExistsError):
        launcher.run(root)

    assert len(calls) == 1
    assert (root / "payload.claim.json").read_bytes() == original_claim
    assert (root / "provenance_headers.json").read_bytes() == original_manifest
    assert (root / "result.json").read_bytes() == original_result


@pytest.mark.parametrize("root_kind", ["different", "symlink", "ancestor-symlink"])
def test_untrusted_root_is_rejected_before_claim_reader_or_failure_metadata(
    tmp_path, monkeypatch, root_kind,
):
    if root_kind == "ancestor-symlink":
        physical_parent = tmp_path / "physical-parent"
        physical_parent.mkdir()
        physical_root = physical_parent / "experiment"
        physical_root.mkdir()
        alias_parent = tmp_path / "alias-parent"
        alias_parent.symlink_to(physical_parent, target_is_directory=True)
        root = alias_parent / "experiment"
        monkeypatch.setattr(launcher, "ROOT", root)
        roots_to_check = (root, physical_root)
    else:
        trusted_root = _make_root(monkeypatch, tmp_path / "trusted")
        if root_kind == "different":
            root = tmp_path / "other"
            root.mkdir()
        else:
            root = tmp_path / "trusted-link"
            root.symlink_to(trusted_root, target_is_directory=True)
        roots_to_check = (root, trusted_root)

    calls, _report = _install_reader_mock(monkeypatch)
    with pytest.raises(ValueError, match="unexpected or linked physical provenance root"):
        _invoke_main(monkeypatch, root)

    assert calls == []
    for candidate in roots_to_check:
        assert not (candidate / "payload.claim.json").exists()
        assert not (candidate / "failure.json").exists()


@pytest.mark.parametrize(
    ("option", "value"),
    [
        ("--source", "/tmp/alternate-archive.zip"),
        ("--source-url", "https://example.invalid/archive.zip"),
        ("--url", "https://example.invalid/archive.zip"),
    ],
)
def test_cli_cannot_override_fixed_source_or_source_url(
    tmp_path, monkeypatch, option, value,
):
    root = _make_root(monkeypatch, tmp_path / "experiment")
    calls, _report = _install_reader_mock(monkeypatch)

    with pytest.raises(SystemExit) as raised:
        _invoke_main(monkeypatch, root, option, value)

    assert raised.value.code == 2
    assert calls == []
    assert list(root.iterdir()) == []


def test_failure_metadata_does_not_replace_existing_failure(
    tmp_path, monkeypatch,
):
    root = _make_root(monkeypatch, tmp_path / "experiment")
    calls, _report = _install_reader_mock(
        monkeypatch, error=RuntimeError("synthetic reader failure"),
    )
    failure_path = root / "failure.json"
    original = b"preserve prior failure metadata\n"
    failure_path.write_bytes(original)

    with pytest.raises(FileExistsError):
        _invoke_main(monkeypatch, root)

    assert len(calls) == 1
    assert failure_path.read_bytes() == original
    assert not (root / "result.json").exists()


def test_new_metadata_accepts_exact_64_kib_and_rejects_larger_payload(tmp_path):
    empty_payload = (json.dumps({"padding": ""}, sort_keys=True, indent=2) + "\n").encode()
    padding_length = METADATA_LIMIT - len(empty_payload)
    exact_value = {"padding": "x" * padding_length}
    exact_path = tmp_path / "exact.json"

    launcher.new_metadata(exact_path, exact_value)

    assert exact_path.stat().st_size == METADATA_LIMIT
    oversized_path = tmp_path / "oversized.json"
    with pytest.raises(ValueError, match="metadata exceeds 64 KiB"):
        launcher.new_metadata(oversized_path, {"padding": "x" * (padding_length + 1)})
    assert not oversized_path.exists()
