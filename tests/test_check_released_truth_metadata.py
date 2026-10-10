from types import SimpleNamespace
import importlib.metadata
import json
from pathlib import Path

import pytest
import pysam

from analysis.check_released_truth_metadata import canonical_metadata, check_metadata, file_hash, scalar, sealed_input

HEADER = ("##fileformat=VCFv4.2\n##contig=<ID=1,length=10000>\n"
          '##INFO=<ID=SVTYPE,Number=1,Type=String,Description="type">\n'
          '##INFO=<ID=SVLEN,Number=1,Type=Integer,Description="length">\n'
          '##FORMAT=<ID=GT,Number=1,Type=String,Description="genotype">\n'
          "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tHG002\n")


def record(tmp_path, *, kind="DEL", length=-60, gt="0/1", alt=None):
    path = tmp_path / "fixture.vcf"
    path.write_text(HEADER + f"1\t100\t{'a' * 64}\t{'A' * 61}\t{alt or 'A'}"
                    f"\t.\tPASS\tSVTYPE={kind};SVLEN={length}\tGT\t{gt}\n")
    with pysam.VariantFile(str(path)) as source:
        return next(source).copy()


def native(kind="DEL", length=60):
    return SimpleNamespace(var_size=lambda: length, var_type=lambda: SimpleNamespace(name=kind))


def test_metadata_checks_do_not_rewrite_source(tmp_path):
    rec = record(tmp_path)
    before = str(rec)
    assert canonical_metadata(rec, native()) == "DEL"
    assert str(rec) == before


@pytest.mark.parametrize("kind,length,gt,alt,message", [
    ("INS", -60, "0/1", None, "SVTYPE"),
    ("DEL", -59, "0/1", None, "SVLEN"),
    ("DEL", 60, "0/1", None, "SVLEN"),
    ("DEL", -60, "./1", None, "eligibility"),
    ("DEL", -60, "0/0", None, "eligibility"),
    ("DEL", -60, "0/1", "A,AA", "biallelic"),
])
def test_contradictions_fail_whole_gate(tmp_path, kind, length, gt, alt, message):
    with pytest.raises(ValueError, match=message):
        canonical_metadata(record(tmp_path, kind=kind, length=length, gt=gt, alt=alt), native())


@pytest.mark.parametrize("trv,message", [(native(length=59), "native size"),
                                        (native(kind="INS"), "native type")])
def test_native_disagreements_fail(tmp_path, trv, message):
    with pytest.raises(ValueError, match=message):
        canonical_metadata(record(tmp_path), trv)


def test_insertion_and_phased_gt(tmp_path):
    rec = record(tmp_path, kind="INS", length=60, gt="1|1", alt="A" * 121)
    assert canonical_metadata(rec, native(kind="INS")) == "INS"


def test_file_hash_cap_does_not_accept_a_prefix(tmp_path):
    path = tmp_path / "bytes"
    path.write_bytes(b"abc")
    assert file_hash(path, 3)[1] == 3
    with pytest.raises(ValueError, match="byte cap"):
        file_hash(path, 2)


def test_scalar_cardinality():
    assert scalar((-60,)) == -60
    with pytest.raises(ValueError, match="scalar"):
        scalar((-60, 60))


def test_protocol_hash_precedes_truth_reads_and_report_writes(tmp_path):
    protocol = tmp_path / "protocol.json"
    protocol.write_text("{}")
    report = tmp_path / "report.json"
    with pytest.raises(ValueError, match="protocol hash"):
        check_metadata(tmp_path / "does-not-exist.vcf", protocol, "0" * 64, report)
    assert not report.exists()


def test_protocol_is_not_reopened_after_hashing(tmp_path, monkeypatch):
    protocol = tmp_path / "protocol.json"
    protocol.write_text('{"metadata_gate_approved": false}')
    protocol_sha = file_hash(protocol, 1024**2)[0]
    def unexpected_reopen(*args, **kwargs):
        raise AssertionError("hashed protocol was reopened")
    monkeypatch.setattr(Path, "read_text", unexpected_reopen)
    with pytest.raises(ValueError, match="not approved"):
        check_metadata(tmp_path / "absent.vcf", protocol, protocol_sha, tmp_path / "report.json")


@pytest.mark.skipif(__import__("sys").platform != "linux", reason="requires Linux kernel seals")
def test_actual_kernel_blocks_writes_and_keeps_independent_positions():
    with sealed_input(b"abc") as path:
        with open(path, "rb") as first, open(path, "rb") as second:
            assert first.read(1) == second.read(1) == b"a"
        with open(path, "r+b", buffering=0) as writer:
            with pytest.raises(PermissionError):
                writer.write(b"!")
        assert Path(path).read_bytes() == b"abc"


@pytest.mark.parametrize("signed_length,passes", [(-60, True), (-59, False)])
def test_pinned_full_native_endpoint(tmp_path, signed_length, passes):
    pytest.importorskip("truvari")
    from pysam.version import __bcftools_version__, __htslib_version__
    import sys
    import analysis.check_released_truth_metadata as checker
    versions = dict(python=sys.version.split()[0], pysam=pysam.__version__,
                    truvari=importlib.metadata.version("truvari"),
                    bcftools=__bcftools_version__, htslib=__htslib_version__)
    pinned = dict(python="3.10.20", pysam="0.24.0", truvari="5.4.0",
                  bcftools="1.23.1", htslib="1.23.1")
    if versions != pinned:
        pytest.skip("requires exact cluster stack")
    record(tmp_path, length=signed_length)
    truth = tmp_path / "fixture.vcf"
    source = Path(checker.__file__)
    protocol = tmp_path / "synthetic_protocol.json"
    protocol.write_text(json.dumps(dict(
        metadata_gate_approved=True, purpose="metadata_only_not_REF_or_scoring",
        expected_records=1, expected_sample="HG002", versions=pinned,
        eligible_truth_sha256=file_hash(truth, 1024**2)[0],
        source_script_sha256=file_hash(source, 1024**2)[0],
        truth_units_script_sha256=file_hash(source.with_name("released_truth_units.py"), 1024**2)[0])))
    report = tmp_path / "synthetic_report.json"
    before = truth.read_bytes()
    if passes:
        result = check_metadata(truth, protocol, file_hash(protocol, 1024**2)[0], report)
        assert result["kind_counts"] == {"DEL": 1, "INS": 0}
        assert result["input_unmodified"]
        assert not result["reference_validation_performed"]
    else:
        with pytest.raises(ValueError, match="SVLEN"):
            check_metadata(truth, protocol, file_hash(protocol, 1024**2)[0], report)
        assert not report.exists()
    assert truth.read_bytes() == before
