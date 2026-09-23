import hashlib
import json

import pytest

from scripts import analyze_reference_ambiguity as analysis
from scripts.analyze_reference_ambiguity import (
    intersection_length,
    read_mask,
    union_intervals,
)


def test_interval_union_and_intersection_keep_shared_ambiguity():
    left = [(2, 7), (9, 10)]
    right = [(3, 8), (10, 12)]
    union = union_intervals(left, right)
    assert union == [(2, 8), (9, 12)]
    assert intersection_length(left, right) == 4
    assert intersection_length([(5, 11)], union) == 5


def test_read_mask_checks_json_counts_and_hash(tmp_path):
    bed = tmp_path / "mask.bed"
    bed.write_text("chr1\t2\t7\nchr1\t9\t10\n")
    meta = tmp_path / "mask.json"
    meta.write_text(json.dumps({
        "bed_sha256": hashlib.sha256(bed.read_bytes()).hexdigest(),
        "contigs": {"chr1": {"length": 10, "n_ambiguous_bases": 6,
                              "n_ambiguous_intervals": 2}},
        "n_ambiguous_bases": 6, "n_ambiguous_intervals": 2,
    }))
    _, intervals = read_mask(bed, meta, {"chr1"})
    assert intervals["chr1"] == [(2, 7), (9, 10)]
    bed.write_text("chr1\t2\t8\nchr1\t9\t10\n")
    with pytest.raises(ValueError, match="SHA-256"):
        read_mask(bed, meta, {"chr1"})


def test_analyze_counts_differences_outside_joint_ambiguity(tmp_path, monkeypatch):
    def write_mask(stem, interval, m5):
        bed = tmp_path / f"{stem}.bed"
        bed.write_text(f"chr1\t{interval[0]}\t{interval[1]}\n")
        meta = tmp_path / f"{stem}.json"
        meta.write_text(json.dumps({
            "bed_sha256": hashlib.sha256(bed.read_bytes()).hexdigest(),
            "fasta_sha256": stem,
            "contigs": {"chr1": {
                "length": 10, "canonical_m5": m5,
                "n_ambiguous_bases": interval[1] - interval[0],
                "n_ambiguous_intervals": 1,
            }},
            "n_ambiguous_bases": interval[1] - interval[0],
            "n_ambiguous_intervals": 1,
        }))
        return bed, meta

    hgsvc_bed, hgsvc_json = write_mask("hgsvc", (2, 4), "a")
    igsr_bed, igsr_json = write_mask("igsr", (3, 5), "b")
    audit = tmp_path / "audit.json"
    audit.write_text(json.dumps({"contigs": {"chr1": {
        "length": 10, "canonical_m5": "a", "dict_length": 10,
        "dict_m5": "b",
    }}}))
    differences = tmp_path / "differences"
    differences.mkdir()
    (differences / "chr1_base_differences.bed").write_text(
        "chr1\t2\t4\nchr1\t8\t9\n"
    )
    monkeypatch.setattr(analysis, "verify_differences", lambda _: None)
    out_bed = tmp_path / "joint.bed"
    result = analysis.analyze(hgsvc_bed, hgsvc_json, igsr_bed, igsr_json,
                              audit, differences, out_bed)
    assert out_bed.read_text() == "chr1\t2\t5\n"
    assert result["n_joint_non_acgt_bases"] == 3
    assert result["n_shared_non_acgt_bases"] == 1
    assert result["n_unequal_bases_outside_joint_non_acgt"] == 1
    assert result["contigs"]["chr1"]["unequal_bases"] == 3
    assert result["joint_bed_sha256"] == hashlib.sha256(out_bed.read_bytes()).hexdigest()
