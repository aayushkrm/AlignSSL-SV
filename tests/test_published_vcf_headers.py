"""Unit checks for metadata-only published VCF integrity parsing."""

import gzip
from io import BytesIO

import pytest

from scripts.audit_published_vcf_headers import audit, git_blob_sha1, inspect_vcf


VCF = (
    b"##fileformat=VCFv4.2\n"
    b"##source=caller 1.0\n"
    b"##reference=hs37d5\n"
    b"##contig=<ID=1,length=249250621,M5=abcdef>\n"
    b"#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tHG002\n"
    b"1\t100\t.\tA\t<DEL>\t.\tPASS\tSVTYPE=DEL\tGT\t0/1\n"
)


def test_inspect_plain_and_gzip_headers() -> None:
    for data, compressed in ((VCF, False), (gzip.compress(VCF), True)):
        report = inspect_vcf(data, compressed)
        assert report["references"] == ["hs37d5"]
        assert report["sources"] == ["caller 1.0"]
        assert report["sample_names"] == ["HG002"]
        assert report["contigs"] == [{"id": "1", "length": 249250621, "m5": "abcdef"}]
        assert report["has_sequence_m5_for_all_contigs"]


def test_missing_chrom_header_rejected() -> None:
    with pytest.raises(ValueError, match="lacks #CHROM"):
        inspect_vcf(VCF.split(b"#CHROM")[0], False)


def test_git_blob_oid_uses_git_header() -> None:
    assert git_blob_sha1(b"test\n") == "9daeafb9864cf43055ae93beb0afd6c7d144bfa4"


def test_audit_rejects_changed_published_blob(monkeypatch: pytest.MonkeyPatch) -> None:
    url = "https://raw.githubusercontent.com/example/pinned/file.vcf"

    class Response(BytesIO):
        status = 200

        def geturl(self) -> str:
            return url

    monkeypatch.setattr(
        "scripts.audit_published_vcf_headers.urllib.request.urlopen",
        lambda requested, timeout: Response(VCF),
    )
    manifest = {
        "base_url": "https://raw.githubusercontent.com/example/pinned/",
        "files": [{"name": "file.vcf", "bytes": len(VCF), "git_blob_sha1": "0" * 40}],
    }
    with pytest.raises(ValueError, match="Git blob OID differs"):
        audit(manifest)


def test_audit_records_verified_blob_without_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    url = "https://raw.githubusercontent.com/example/pinned/file.vcf"

    class Response(BytesIO):
        status = 200

        def geturl(self) -> str:
            return url

    monkeypatch.setattr(
        "scripts.audit_published_vcf_headers.urllib.request.urlopen",
        lambda requested, timeout: Response(VCF),
    )
    manifest = {
        "base_url": "https://raw.githubusercontent.com/example/pinned/",
        "files": [{"name": "file.vcf", "bytes": len(VCF),
                   "git_blob_sha1": git_blob_sha1(VCF)}],
    }
    report = audit(manifest)
    assert report["file_count"] == 1
    assert report["files"][0]["sample_names"] == ["HG002"]
    assert "1\t100" not in str(report)
