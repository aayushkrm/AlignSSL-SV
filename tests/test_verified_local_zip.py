import gzip
import hashlib
import io
import zipfile

import pytest

from scripts.audit_verified_local_zip import audit_zip, read_header, write_report


HEADER = b"##fileformat=VCFv4.2\n#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tTEST\n"


def fixture(tmp_path):
    path = tmp_path / "source.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("calls.vcf.gz", gzip.compress(HEADER + b"UNREAD BODY\n"))
        archive.writestr("code.py", "raise AssertionError('do not execute')")
    return path, path.stat().st_size, hashlib.md5(path.read_bytes()).hexdigest()


def test_verified_archive_inventory_and_bounded_headers(tmp_path):
    path, size, md5 = fixture(tmp_path)
    report = audit_zip(path, size, md5, "https://example.test/source.zip?token=redact",
                       ["calls.vcf.gz"])
    assert report["whole_archive_md5_verification"] == "VERIFIED"
    assert report["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert report["member_count"] == 2
    assert report["biological_records_parsed"] == 0
    assert report["vcf_headers"][0]["header_lines"] == HEADER.decode().splitlines()
    assert "redact" not in report["source_url"]
    assert not report["downloaded_code_executed"]
    out = tmp_path / "report.json"
    write_report(out, report)
    assert out.with_suffix(".json.sha256").exists()
    with pytest.raises(FileExistsError):
        write_report(out, report)


def test_size_and_md5_fail_before_inspection(tmp_path):
    path, size, md5 = fixture(tmp_path)
    with pytest.raises(ValueError, match="size differs"):
        audit_zip(path, size + 1, md5, "https://example.test/a.zip")
    with pytest.raises(ValueError, match="MD5 differs"):
        audit_zip(path, size, "0" * 32, "https://example.test/a.zip")


def test_member_selection_must_be_exact(tmp_path):
    path, size, md5 = fixture(tmp_path)
    with pytest.raises(ValueError, match="missing or unsupported"):
        audit_zip(path, size, md5, "https://example.test/a.zip", ["absent.vcf"])


@pytest.mark.parametrize("data,cap", [(HEADER, 8), (b"##fileformat=VCFv4.2\n", 1000),
                                    (b"not a header\n", 1000)])
def test_rejects_oversize_missing_or_malformed_header(data, cap):
    with pytest.raises(ValueError):
        read_header(io.BytesIO(data), cap)


def test_no_body_read_after_column_header():
    stream = io.BytesIO(HEADER + b"private body must remain unread\n")
    assert read_header(stream, 1000) == HEADER.decode().splitlines()
    assert stream.read() == b"private body must remain unread\n"


def test_dangling_checksum_symlink_prevents_partial_output(tmp_path):
    out = tmp_path / "report.json"
    out.with_suffix(".json.sha256").symlink_to(tmp_path / "absent")
    with pytest.raises(FileExistsError):
        write_report(out, {"purpose": "metadata"})
    assert not out.exists()
