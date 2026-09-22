import gzip

import pytest

from scripts.audit_hgsvc3_genotypes import summarize


def test_summarize_separates_carriers_reference_and_missing(tmp_path):
    vcf = tmp_path / "truth.vcf.gz"
    lines = [
        "##fileformat=VCFv4.2",
        "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tA\tB",
        "chr1\t100\td1\tAC\tA\t.\t.\tSVTYPE=DEL;SVLEN=-60\tGT\t0|1\t0|0",
        "chr1\t200\td2\tAC\tA\t.\t.\tSVTYPE=DEL;SVLEN=-75\tGT\t.|.\t0|1",
        "chr1\t300\td3\tAC\tA\t.\t.\tSVTYPE=DEL;SVLEN=-80\tGT\t0|.\t1|1",
        "chr1\t400\ti1\tA\tAC\t.\t.\tSVTYPE=INS;SVLEN=60\tGT\t1|0\t.|.",
    ]
    with gzip.open(vcf, "wt") as target:
        target.write("\n".join(lines) + "\n")

    result = summarize(vcf)
    assert result["total_sv_records"] == 4
    assert result["del_records_ge_50bp"] == 3
    assert result["samples"]["A"] == {
        "carrier": 1, "hom_ref": 0, "partial_missing": 1, "fully_missing": 1
    }
    assert result["samples"]["B"] == {
        "carrier": 2, "hom_ref": 1, "partial_missing": 0, "fully_missing": 0
    }


def test_summarize_rejects_bad_row_width(tmp_path):
    vcf = tmp_path / "bad.vcf.gz"
    with gzip.open(vcf, "wt") as target:
        target.write(
            "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tA\n"
            "chr1\t100\td1\tAC\tA\t.\t.\tSVTYPE=DEL;SVLEN=-60\tGT\n"
        )
    with pytest.raises(ValueError, match="row has"):
        summarize(vcf)
