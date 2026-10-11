"""Synthetic ZIPs only: no released VCF body is opened by this test suite."""
import hashlib
import io
import json
import zipfile

import pytest

from analysis import stage_svpg_callsets as stage


def test_explicit_order_amendment_preserves_unsorted_records_and_multiplicity(tmp_path):
    body = row(20) + row(10) + row(10)
    path, protocol = fixture(tmp_path, body)
    protocol["input_order_policy"] = "preserve_and_report"
    report = run(tmp_path, path, protocol)
    expected = HEADER + body.replace(b";RNAMES=r1,r2", b"")
    assert (tmp_path / "staged/cutesv.vcf").read_bytes() == expected
    assert report["callers"]["cutesv"]["records"] == 3
    assert report["callers"]["cutesv"]["requires_sorting"] is True
    assert report["callers"]["cutesv"]["position_order_violations"] == 1
    assert report["input_order_policy"] == "preserve_and_report"


def test_order_amendment_reports_header_rank_regression_without_reordering():
    header = HEADER.replace(b"##contig=<ID=chr1,length=100000>\n",
                            b"##contig=<ID=chr1,length=100000>\n"
                            b"##contig=<ID=chr2,length=100000>\n"
                            b"##contig=<ID=chr10,length=100000>\n")
    body = row(1).replace(b"chr1", b"chr10") + row(1).replace(b"chr1", b"chr2")
    output = io.BytesIO()
    report = stage._stage_member(io.BytesIO(header + body), output, [0, 100000],
                                 order_policy="preserve_and_report")
    assert output.getvalue() == header + body.replace(b";RNAMES=r1,r2", b"")
    assert report["contig_order_violations"] == 1
    assert report["requires_sorting"] is True


def test_unknown_order_policy_fails_before_body_read(tmp_path):
    path, protocol = fixture(tmp_path)
    protocol["input_order_policy"] = "silently_drop_unsorted"
    with pytest.raises(ValueError, match="input-order policy"):
        run(tmp_path, path, protocol)

HEADER = (b"##fileformat=VCFv4.2\n##contig=<ID=chr1,length=100000>\n"
          b"##INFO=<ID=RNAMES,Number=.,Type=String,Description=\"Read names\">\n"
          b"#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSYNTHETIC\n")


def row(pos=10, info="SVTYPE=DEL;END=20;SVLEN=-10;RNAMES=r1,r2", gt="0/1", alt="<DEL>"):
    return f"chr1\t{pos}\tid{pos}\tA\t{alt}\t7.5\tLowQual\t{info}\tGT:PS:HP:PGT:PID:DP\t{gt}:9:1-9:0|1:id:12\n".encode()


def fixture(tmp_path, body=None, duplicate=False):
    path = tmp_path / "synthetic.zip"
    with zipfile.ZipFile(path, "w") as archive:
        for member in stage.MEMBERS:
            data = body.get(member, row()) if isinstance(body, dict) else body if body is not None else row()
            archive.writestr(member, HEADER + data)
        archive.writestr("never-execute.py", "raise RuntimeError('no execution')")
        if duplicate:
            archive.writestr(stage.MEMBERS[0], HEADER)
    payload = path.read_bytes()
    header = {"members": list(stage.MEMBERS), "expected_archive_bytes": len(payload),
              "expected_archive_md5": hashlib.md5(payload).hexdigest(),
              "verified_archive_sha256": hashlib.sha256(payload).hexdigest()}
    protocol = {"body_read_approved": True, "independent_outcome_approval": "synthetic-review",
                "header_protocol": header, "max_source_decoded_bytes": stage.DECODED_CAP,
                "charged_prior_source_decoded_bytes": 0,
                "max_line_bytes": stage.LINE_CAP, "controller_traffic_account": "synthetic-controller"}
    return path, protocol


def run(tmp_path, path, protocol, out="staged"):
    protocol_path = tmp_path / "approved.json"
    payload = json.dumps(protocol).encode()
    protocol_path.write_bytes(payload)
    return stage.stage_zip(path, tmp_path / out, protocol_path, hashlib.sha256(payload).hexdigest())


def test_preserves_complex_fields_filters_phase_and_all_six(tmp_path):
    info = "SVTYPE=DEL;END=20;SVLEN=-10;START2=30;END2=40;SVLEN2=11;OTHER=x;RNAMES=r1,r2"
    path, protocol = fixture(tmp_path, row(info=info, gt="0|1"))
    report = run(tmp_path, path, protocol)
    frozen = json.loads((tmp_path / "staged/header_protocol.json").read_text())
    assert frozen == protocol["header_protocol"]
    assert list(report["callers"]) == list(stage.CALLERS)
    for caller in stage.CALLERS:
        data = (tmp_path / f"staged/{caller}.vcf").read_bytes()
        assert data.startswith(HEADER)  # RNAMES header is preserved.
        assert data == HEADER + row(info=info.replace(";RNAMES=r1,r2", ""), gt="0|1")
        counts = report["callers"][caller]
        assert counts["by_filter"] == {"LowQual": 1}
        assert counts["gt_phased"] == counts["omitted_RNAMES"] == 1
        assert counts["selected_member_crc_verified"] is True
        assert counts["source_sha256"] == hashlib.sha256(HEADER + row(info=info, gt="0|1")).hexdigest()
    assert report["unique_source_decoded_bytes"] == 6 * len(HEADER + row(info=info, gt="0|1"))
    assert report["staging_decoded_traffic_bytes"] == report["unique_source_decoded_bytes"]
    assert report["controller_traffic_account"] == "synthetic-controller"
    assert report["global_traffic_limit_enforced"] is False
    assert report["biological_records_parsed"] is True
    assert report["truth_comparison_performed"] is False
    assert report["scoring_performed"] is False


def test_no_size_filter_split_imputation_or_deduplication(tmp_path):
    body = row(1, "SVLEN=1", "./.", "AT") + row(2, ".", "0/0", "C,G") + row(2, ".", "0/0", "C,G")
    body += b"chr1\t3\t.\tA\tC\t.\tPASS\t.\tDP\t8\n"
    path, protocol = fixture(tmp_path, body)
    report = run(tmp_path, path, protocol)
    assert (tmp_path / "staged/cutesv.vcf").read_bytes() == HEADER + body
    counts = report["callers"]["cutesv"]
    assert counts["records"] == 4
    assert counts["gt_missing"] == 2 and counts["gt_absent"] == 1 and counts["gt_reference"] == 2
    assert counts["by_alt_representation"] == {"sequence": 2, "multiallelic": 2}


@pytest.mark.parametrize("pin", ["expected_archive_bytes", "expected_archive_md5", "verified_archive_sha256"])
def test_wrong_archive_pin_fails_before_member_open(tmp_path, monkeypatch, pin):
    path, protocol = fixture(tmp_path)
    header = protocol["header_protocol"]
    header[pin] = header[pin] + 1 if pin.endswith("bytes") else "0" * len(header[pin])
    monkeypatch.setattr(zipfile.ZipFile, "open", lambda *a, **k: pytest.fail("member opened before preflight"))
    with pytest.raises(ValueError, match="Archive"):
        run(tmp_path, path, protocol)
    assert not (tmp_path / "staged").exists()


def test_header_only_protocol_is_not_body_approval(tmp_path, monkeypatch):
    path, protocol = fixture(tmp_path)
    monkeypatch.setattr(zipfile.ZipFile, "open", lambda *a, **k: pytest.fail("body read without approval"))
    with pytest.raises(ValueError, match="approval"):
        run(tmp_path, path, protocol["header_protocol"])


def test_protocol_sha_is_required_and_checked(tmp_path):
    path, protocol = fixture(tmp_path)
    protocol_path = tmp_path / "protocol.json"
    protocol_path.write_text(json.dumps(protocol))
    with pytest.raises(ValueError, match="Protocol SHA256"):
        stage.stage_zip(path, tmp_path / "out", protocol_path, "0" * 64)


def test_source_budget_charges_headers_unstripped_input_and_prior_passes(tmp_path):
    path, protocol = fixture(tmp_path)
    protocol["charged_prior_source_decoded_bytes"] = 17
    protocol["max_source_decoded_bytes"] = 6 * len(HEADER + row()) + 16
    with pytest.raises(ValueError, match="decoded budget"):
        run(tmp_path, path, protocol)
    with pytest.raises(ValueError, match="budget"):
        stage._stage_member(io.BytesIO(HEADER + row()), io.BytesIO(), [0, len(HEADER) + 3])


def test_long_rnames_line_fails_and_reports_failed_traffic(tmp_path):
    path, protocol = fixture(tmp_path, row(info="RNAMES=" + "r" * 1024))
    protocol["max_line_bytes"] = 512
    with pytest.raises(ValueError, match="line exceeds") as failure:
        run(tmp_path, path, protocol)
    assert failure.value.staging_decoded_bytes_read > len(HEADER)
    evidence = json.loads((tmp_path / "staged/failure.json").read_text())
    assert evidence["status"] == "incomplete" and evidence["failed_caller"] == "cutesv"
    assert evidence["staging_decoded_bytes_read"] == len(HEADER) + 513
    assert evidence["source_decoded_budget_used_including_prior"] == len(HEADER) + 513
    assert evidence["max_line_bytes"] == 512
    assert (tmp_path / "staged/cutesv.vcf").read_bytes() == HEADER
    assert not (tmp_path / "staged/caller_inventory.json").exists()


def test_duplicate_zip_and_frozen_selection_fail(tmp_path):
    with pytest.warns(UserWarning, match="Duplicate"):
        path, protocol = fixture(tmp_path, duplicate=True)
    with pytest.raises(ValueError, match="Duplicate ZIP"):
        run(tmp_path, path, protocol)
    protocol["header_protocol"]["members"][-1] = stage.MEMBERS[0]
    with pytest.raises(ValueError, match="selection"):
        run(tmp_path, path, protocol)


@pytest.mark.parametrize("body", [row(20) + row(10), b"chr1\t1\t.\tA\tC\t.\tPASS\tEND=2;END=3\tGT\t0/1\n",
                                  b"chr1\t1\t.\tA\tC\t.\tPASS\t.\tGT:GT\t0/1:0/1\n"])
def test_unsorted_and_duplicate_fields_preserve_incomplete_evidence(tmp_path, body):
    path, protocol = fixture(tmp_path, body)
    with pytest.raises(ValueError):
        run(tmp_path, path, protocol)
    assert (tmp_path / "staged/cutesv.vcf").exists()
    assert (tmp_path / "staged/failure.json").exists()
    assert not (tmp_path / "staged/caller_inventory.json").exists()


def test_no_overwrite_and_outside_git(tmp_path):
    path, protocol = fixture(tmp_path)
    existing = tmp_path / "existing"
    existing.mkdir()
    sentinel = existing / "keep"
    sentinel.write_text("unchanged")
    with pytest.raises(FileExistsError):
        run(tmp_path, path, protocol, "existing")
    assert sentinel.read_text() == "unchanged"
    with pytest.raises(ValueError, match="outside Git"):
        run(tmp_path, path, protocol, str(stage.REPO / "forbidden-stage"))


def test_selected_crc_failure_is_fatal_even_with_matching_archive_hashes(tmp_path):
    path, protocol = fixture(tmp_path)
    payload = path.read_bytes().replace(b"SVTYPE=DEL", b"SVTYPE=DUP", 1)
    path.write_bytes(payload)  # Synthetic stored member changed; old ZIP CRC remains.
    protocol["header_protocol"]["expected_archive_md5"] = hashlib.md5(payload).hexdigest()
    protocol["header_protocol"]["verified_archive_sha256"] = hashlib.sha256(payload).hexdigest()
    with pytest.raises(zipfile.BadZipFile, match="CRC"):
        run(tmp_path, path, protocol)
    failure = json.loads((tmp_path / "staged/failure.json").read_text())
    assert failure["exception_type"] == "BadZipFile"
    assert failure["conservative_staging_traffic_charge_bytes"] == 6 * len(HEADER + row())
    assert (tmp_path / "staged/cutesv.vcf").exists()
    assert not (tmp_path / "staged/caller_inventory.json").exists()


def test_only_selected_members_are_opened_and_rnames_key_is_exact(tmp_path, monkeypatch):
    info = "RNAMES=r1;MYRNAMES=keep;FLAG;END2=40"
    path, protocol = fixture(tmp_path, row(info=info))
    original, opened = zipfile.ZipFile.open, []
    def selected_only(self, member, *args, **kwargs):
        name = member.filename if isinstance(member, zipfile.ZipInfo) else member
        opened.append(name)
        assert name in stage.MEMBERS
        return original(self, member, *args, **kwargs)
    monkeypatch.setattr(zipfile.ZipFile, "open", selected_only)
    run(tmp_path, path, protocol)
    assert opened == list(stage.MEMBERS)
    assert (tmp_path / "staged/cutesv.vcf").read_bytes() == HEADER + row(info="MYRNAMES=keep;FLAG;END2=40")


def test_long_sequence_alt_below_32_mib_is_preserved_without_dropping():
    assert stage.LINE_CAP == 32 * 1024**2
    data = HEADER + row(info=".", alt="A" * (17 * 1024**2))
    output = io.BytesIO()
    report = stage._stage_member(io.BytesIO(data), output, [0, stage.DECODED_CAP])
    assert output.getvalue() == data
    assert report["records"] == 1 and report["by_type"] == {"INS": 1}


@pytest.mark.parametrize("change,expected", [
    ({"body_read_approved": False}, "approval"),
    ({"controller_traffic_account": ""}, "controller"),
    ({"max_line_bytes": 32 * 1024**2 + 1}, "line budget"),
    ({"max_source_decoded_bytes": 2 * 1024**3 + 1}, "2 GiB"),
    ({"charged_prior_source_decoded_bytes": -1}, "2 GiB"),
])
def test_unreviewed_or_out_of_bounds_protocol_fails_before_body(tmp_path, monkeypatch, change, expected):
    path, protocol = fixture(tmp_path)
    protocol.update(change)
    monkeypatch.setattr(zipfile.ZipFile, "open", lambda *a, **k: pytest.fail("unapproved body open"))
    with pytest.raises(ValueError, match=expected):
        run(tmp_path, path, protocol)
    assert not (tmp_path / "staged").exists()


def test_failure_preserves_completed_callers_partial_file_and_prior_charge(tmp_path):
    path, protocol = fixture(tmp_path, {stage.MEMBERS[1]: row(20) + row(10)})
    original_sha = hashlib.sha256(path.read_bytes()).hexdigest()
    protocol["charged_prior_source_decoded_bytes"] = 19
    with pytest.raises(ValueError, match="Unsorted"):
        run(tmp_path, path, protocol)
    failure = json.loads((tmp_path / "staged/failure.json").read_text())
    assert list(failure["completed_callers"]) == ["cutesv"]
    assert failure["failed_caller"] == "debreak"
    expected_read = len(HEADER + row()) + len(HEADER + row(20) + row(10))
    assert failure["staging_decoded_bytes_read"] == expected_read
    assert failure["source_decoded_budget_used_including_prior"] == 19 + expected_read
    assert (tmp_path / "staged/debreak.vcf").read_bytes() == HEADER + row(20).replace(b";RNAMES=r1,r2", b"")
    assert not (tmp_path / "staged/caller_inventory.json").exists()
    with pytest.raises(FileExistsError):
        run(tmp_path, path, protocol)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == original_sha


def test_undeclared_body_contig_fails_without_copying_its_record(tmp_path):
    path, protocol = fixture(tmp_path, row().replace(b"chr1\t", b"chr2\t", 1))
    with pytest.raises(ValueError, match="not declared"):
        run(tmp_path, path, protocol)
    assert (tmp_path / "staged/cutesv.vcf").read_bytes() == HEADER
    failure = json.loads((tmp_path / "staged/failure.json").read_text())
    assert failure["exception_message"] == "VCF body contig is not declared in its header"


def test_protocol_read_is_bounded_even_before_hash_validation(tmp_path):
    protocol_path = tmp_path / "oversize.json"
    data = b" " * (1024**2 + 2)
    protocol_path.write_bytes(data)
    with pytest.raises(ValueError, match="Protocol exceeds"):
        stage.stage_zip(tmp_path / "must-not-open.zip", tmp_path / "out", protocol_path,
                        hashlib.sha256(data).hexdigest())
    assert not (tmp_path / "out").exists()


def test_utf8_info_and_all_format_are_preserved(tmp_path):
    body = row(info="SVTYPE=DEL;LABEL=\u03bc;END2=40;RNAMES=r1", gt="0|1").replace(b"\n", b"\r\n")
    path, protocol = fixture(tmp_path, body)
    run(tmp_path, path, protocol)
    assert (tmp_path / "staged/cutesv.vcf").read_bytes() == HEADER + body.replace(b";RNAMES=r1", b"")


def test_declared_contig_id_need_not_be_first_header_attribute():
    header = HEADER.replace(b"ID=chr1,length=100000", b"length=100000,ID=chr1")
    data = header + row(info=".")
    output = io.BytesIO()
    stage._stage_member(io.BytesIO(data), output, [0, stage.DECODED_CAP])
    assert output.getvalue() == data
