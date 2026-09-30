"""Bounded VCF header and genotype-confidence availability audit tests."""

import gzip
import hashlib
import json

import pytest

from scripts.audit_vcf_confidence_fields import (
    MAX_HEADER_BYTES,
    audit_header_object,
    audit_header_lines,
    audit_vcf,
    main,
    report_bytes,
    write_new_report,
)


HEADER = [
    "##fileformat=VCFv4.2",
    "##source=caller 1.0",
    "##reference=GRCh38",
    "##contig=<ID=chr1,length=100,M5=abc>",
    "##contig=<ID=chrUn,length=20>",
    '##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype, phased or unphased">',
    '##FORMAT=<ID=GQ,Number=1,Type=Integer,Description="Sample quality, phred-scaled">',
    '##FORMAT=<ID=GP,Number=G,Type=Float,Description="joint probabilities, said \\"complete\\\\partial\\"">',
    '##FORMAT=<ID=PL,Number=G,Type=Integer,Description="Phred likelihoods">',
    '##FORMAT=<ID=GL,Number=G,Type=Float,Description="Log10 likelihoods">',
    "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tNA12878\tNA12878.bam",
]

RECORDS = [
    "1\t10\t.\tA\tC\t0\tPASS\t.\tGT:GQ:GP:PL:GL\t0/1:0:0.2,0.8:0,10,20:-0.1,-1,-2\t./.:.:0.2,0.2:0,1,2:0,-1,-2",
    "1\t20\t.\tA\tC,G\t45\tPASS\t.\tGT:GQ:GP:PL:GL\t1/2:8:0.2,0.3,0.5:0,2,4:-0.2,-1,-3",
    "1\t30\t.\tA\tC\t22\tPASS\t.\tGT:GQ:GP:PL:GL\t1:3:0.7,0.3:.:bad\t0/1/1:0:0.3,nope:0,1,2:0,-1,-2",
]


def _write_vcf(path, records=RECORDS, compressed=False):
    data = ("\n".join(HEADER + records) + "\n").encode()
    if compressed:
        path.write_bytes(gzip.compress(data))
    else:
        path.write_bytes(data)
    return path


def test_header_only_default_and_in_memory_header_object(tmp_path):
    vcf = _write_vcf(tmp_path / "calls.vcf.gz", compressed=True)
    report = audit_vcf(vcf)
    assert report["records"]["processed"] == 0
    assert report["records"]["stop_reason"] == "header_only"
    assert report["per_sample"]["NA12878"]["total_records"] == 0
    assert "sha256" not in report["source"]
    assert report["source"]["identity_status"] == "unverified"

    header = audit_header_object({
        "member": "calls/sample.vcf.gz",
        "header_lines": HEADER,
        "body_records_parsed": 0,
    })
    assert header["member"] == "calls/sample.vcf.gz"
    assert header["body_records_parsed"] == 0
    assert header["header"]["sources"] == ["caller 1.0"]
    assert header["header"]["references"] == ["GRCh38"]
    assert header["header"]["sample_ids"] == ["NA12878", "NA12878.bam"]
    assert header["header"]["formats"]["GT"][0]["Number"] == "1"
    assert header["header"]["formats"]["GT"][0]["Type"] == "String"
    gp_description = header["header"]["formats"]["GP"][0]["Description"]
    assert gp_description == 'joint probabilities, said "complete\\partial"'
    assert header["header"]["contig_m5_availability"] == {
        "contig_count": 2,
        "with_m5": 1,
        "without_m5": 1,
        "canonical_subset": [{"id": "chr1", "m5": "abc", "m5_available": True}],
    }
    assert "contigs" not in header["header"]
    assert len(header["header"]["source_header_sha256"]) == 64
    assert len(header["header"]["contig_lines_sha256"]) == 64
    assert header["header"]["source_header_sha256"] == report["header"]["source_header_sha256"]


def test_record_prefix_confidence_parsing_and_genotype_counts(tmp_path):
    report = audit_vcf(_write_vcf(tmp_path / "calls.vcf"), max_records=3)
    assert report["records"]["processed"] == 3
    assert report["records"]["stop_reason"] == "record_limit_reached"
    assert report["records"]["records_with_nonmissing_QUAL"] == 3
    assert report["records"]["records_with_multiallelic_ALT"] == 1

    first = report["per_sample"]["NA12878"]
    assert first["total_records"] == 3
    assert first["completeGT"] == 3  # Includes the explicit haploid call.
    assert first["missingGT"] == 0
    assert first["missingrecord"] == 0
    assert first["out_of_scope_non_diploid_GT"] == 1

    second = report["per_sample"]["NA12878.bam"]
    assert second["total_records"] == 3
    assert second["completeGT"] == 1  # Explicit triploid call; never coerced to diploid.
    assert second["missingGT"] == 1
    assert second["missingrecord"] == 1
    assert second["out_of_scope_non_diploid_GT"] == 1

    fields = report["confidence_field_parse"]
    assert fields["GQ"] == {"numeric_entries": 4, "numeric_values": 4, "missing": 1, "malformed": 0}
    assert fields["GP"]["numeric_entries"] == 4
    assert fields["GP"]["missing"] == 0
    assert fields["GP"]["malformed"] == 1
    assert fields["PL"]["numeric_entries"] == 4
    assert fields["PL"]["missing"] == 1
    assert fields["GL"]["numeric_entries"] == 4
    assert fields["GL"]["malformed"] == 1

    gp = report["GP_numeric_shape"]
    assert gp["numeric_entries"] == 4
    assert gp["sum_near_one"] == 3
    assert gp["sum_not_near_one"] == 1
    assert gp["all_values_nonnegative"] == 4
    assert gp["contains_negative"] == 0
    cardinality = report["Number_G_cardinality"]
    assert cardinality["GP"]["declared_number_g"] is True
    assert cardinality["GP"]["checked"] == 4
    assert cardinality["GP"]["matches"] == 1
    assert cardinality["GP"]["mismatches"] == 3
    assert cardinality["PL"]["matches"] == 2
    assert cardinality["PL"]["mismatches"] == 2
    limits = " ".join(report["interpretation_limits"])
    assert "PL and GL are likelihood encodings, not posterior probabilities" in limits
    assert "do not validate population probabilities" in limits
    assert "QUAL is fixed-column site quality" in limits


def test_sample_truncation_is_missing_record_not_missing_gt(tmp_path):
    report = audit_vcf(_write_vcf(tmp_path / "truncated.vcf", records=RECORDS[:2]), 2)
    assert report["per_sample"]["NA12878.bam"]["missingrecord"] == 1
    assert report["per_sample"]["NA12878.bam"]["missingGT"] == 1


def test_wide_sample_scan_has_an_observation_cap(tmp_path, monkeypatch):
    monkeypatch.setattr("scripts.audit_vcf_confidence_fields.MAX_SAMPLE_RECORD_OBSERVATIONS", 2)
    report = audit_vcf(_write_vcf(tmp_path / "wide.vcf"), max_records=3)
    assert report["records"]["processed"] == 1
    assert report["records"]["stop_reason"] == "sample_observation_limit"


def test_decompressed_record_byte_limit_and_record_argument_cap(tmp_path, monkeypatch):
    monkeypatch.setattr("scripts.audit_vcf_confidence_fields.MAX_TOTAL_RECORD_BYTES", 32)
    huge_row = "1\t10\t.\tA\tC\t0\tPASS\t.\tGT\t0/1" + "x" * 256
    report = audit_vcf(_write_vcf(tmp_path / "large.vcf.gz", [huge_row], compressed=True), 1)
    assert report["records"]["processed"] == 0
    assert report["records"]["stop_reason"] == "record_byte_limit"
    assert not report["container"]["stream_eof_reached"]
    with pytest.raises(ValueError, match="between 0 and"):
        audit_vcf(tmp_path / "large.vcf.gz", 100_001)


def test_malformed_header_and_header_cap_are_rejected(tmp_path):
    malformed = [
        '##FORMAT=<ID=GP,Number=G,Type=Float,Description="unfinished>',
        HEADER[-1],
    ]
    with pytest.raises(ValueError, match="quote"):
        audit_header_lines(malformed)

    oversized = tmp_path / "oversized.vcf"
    oversized.write_text("##source=" + "x" * MAX_HEADER_BYTES + "\n" + HEADER[-1] + "\n")
    with pytest.raises(ValueError, match="header exceeds"):
        audit_vcf(oversized)


def test_in_memory_header_object_requires_zero_body_records():
    item = {"member": "x.vcf.gz", "header_lines": HEADER, "body_records_parsed": 2}
    with pytest.raises(ValueError, match="body_records_parsed: 0"):
        audit_header_object(item)


def test_cli_combines_guo_and_svupp_header_documents(tmp_path, monkeypatch):
    def document(prefix, count):
        return {"vcf_headers": [
            {"member": f"{prefix}/{index}.vcf.gz", "header_lines": HEADER,
             "body_records_parsed": 0}
            for index in range(count)
        ]}

    guo = tmp_path / "guo.json"
    svupp = tmp_path / "svupp.json"
    guo.write_text(json.dumps(document("guo", 14)))
    svupp.write_text(json.dumps(document("svupp", 5)))
    output = tmp_path / "combined.json"
    monkeypatch.setattr("sys.argv", ["audit_vcf_confidence_fields.py",
        "--header-audit-json", str(guo), "--header-audit-json", str(svupp),
        "--out", str(output)])
    main()

    report = json.loads(output.read_text())
    assert report["mode"] == "header_only"
    assert report["header_count"] == 19
    assert [item["header_count"] for item in report["inputs"]] == [14, 5]
    assert report["inputs"][0]["headers"][0]["member"] == "guo/0.vcf.gz"
    assert "records" not in report
    assert "contigs" not in report["inputs"][0]["headers"][0]["header"]


def test_duplicate_chrom_line_triploid_missing_ploidy_and_invalid_allele(tmp_path):
    with pytest.raises(ValueError, match="duplicate #CHROM"):
        audit_header_lines(HEADER + [HEADER[-1]])

    one_sample_header = HEADER[:-1] + [HEADER[-1].split("\t")[0] + "\t" +
                                       "\t".join(HEADER[-1].split("\t")[1:9]) + "\tS"]
    row = "1\t40\t.\tA\tC\t.\tPASS\t.\tGT:GP\t././.:0.1,0.2,0.3,0.4"
    one_sample = tmp_path / "ploidy.vcf"
    one_sample.write_text("\n".join(one_sample_header + [row]) + "\n")
    report = audit_vcf(one_sample, 1)
    sample = report["per_sample"]["S"]
    assert sample["missingGT"] == 1
    assert sample["completeGT"] == 0
    assert sample["out_of_scope_non_diploid_GT"] == 1
    assert report["Number_G_cardinality"]["GP"]["matches"] == 1

    bad_index_row = "1\t41\t.\tA\tC\t.\tPASS\t.\tGT:GP\t0/2:0.2,0.3,0.5"
    one_sample.write_text("\n".join(one_sample_header + [bad_index_row]) + "\n")
    invalid = audit_vcf(one_sample, 1)["per_sample"]["S"]
    assert invalid["invalidGT"] == 1
    assert invalid["completeGT"] == 0

    no_gt_row = "1\t42\t.\tA\tC\t.\tPASS\t.\tGP\t0.2,0.3,0.5"
    one_sample.write_text("\n".join(one_sample_header + [no_gt_row]) + "\n")
    no_ploidy = audit_vcf(one_sample, 1)
    assert no_ploidy["Number_G_cardinality"]["GP"]["unknown_ploidy"] == 1
    assert no_ploidy["Number_G_cardinality"]["GP"]["checked"] == 0


def test_report_checksum_and_exclusive_output(tmp_path):
    source = {"purpose": "metadata only"}
    serialized = json.loads(report_bytes(source))
    canonical = json.dumps(source, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    assert serialized["report_checksum"]["value"] == hashlib.sha256(canonical).hexdigest()

    output = tmp_path / "audit.json"
    write_new_report(output, source)
    original = output.read_bytes()
    with pytest.raises(FileExistsError):
        write_new_report(output, {"changed": True})
    assert output.read_bytes() == original

    dangling = tmp_path / "dangling.json"
    dangling.symlink_to(tmp_path / "not-created.json")
    with pytest.raises(FileExistsError):
        write_new_report(dangling, source)
