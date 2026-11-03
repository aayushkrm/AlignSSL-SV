from pathlib import Path

import pytest

from analysis.verify_colo829_case_diff import inspect


HEADER = b"##contig=<ID=chrB,length=100>\n#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n"
OLD = b"chrA\t10\ta\tA\tA[CHRB:20[\t.\tPASS\tSVTYPE=BND\n"
NEW = b"chrA\t10\ta\tA\tA[chrB:20[\t.\tPASS\tSVTYPE=BND\n"


def test_case_only_is_accepted(tmp_path):
    left, right = tmp_path / "old.vcf", tmp_path / "new.vcf"
    left.write_bytes(HEADER + OLD)
    right.write_bytes(HEADER + NEW)
    report = inspect(left, right)
    assert (report["changed_lines"], report["unchanged_lines"]) == (1, 2)
    assert report["changes"][0]["old_remote"] == "CHRB"
    assert report["changes"][0]["new_remote"] == "chrB"


@pytest.mark.parametrize(
    ("header", "output"),
    [
        (HEADER, NEW.replace(b"\ta\t", b"\tb\t")),
        (HEADER, NEW.replace(b":20[", b":21[")),
        (HEADER, NEW.replace(b"chrB", b"chrC")),
        (HEADER.replace(b"#CHROM", b"##contig=<ID=CHRB,length=100>\n#CHROM"), NEW),
    ],
)
def test_other_changes_are_rejected(tmp_path: Path, header: bytes, output: bytes):
    left, right = tmp_path / "old.vcf", tmp_path / "new.vcf"
    left.write_bytes(header + OLD)
    right.write_bytes(header + output)
    with pytest.raises(ValueError):
        inspect(left, right)
