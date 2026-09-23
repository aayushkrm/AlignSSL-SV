import hashlib
import json

import pytest

from scripts import verify_frozen_reference_replay as replay


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fixture_dirs(tmp_path, monkeypatch):
    monkeypatch.setattr(replay, "CONTIGS", ("chr1",))
    monkeypatch.setattr(replay, "verify_original", lambda _: {
        "n_contigs": 1, "n_compared_bases": 10,
    })
    old, new = tmp_path / "old", tmp_path / "new"
    old.mkdir()
    new.mkdir()
    bed_name = "chr1_base_differences.bed"
    json_name = "chr1_base_differences_full.json"
    bed = b"chr1\t2\t4\n"
    (old / bed_name).write_bytes(bed)
    (new / bed_name).write_bytes(bed)
    common = {
        "contig": "chr1", "length": 10, "n_different_bases": 2,
        "n_difference_intervals": 1, "difference_types": {"A>N": 2},
        "first_differences": [{"position_1based": 3, "left": "A", "right": "N"}],
        "difference_bed_sha256": hashlib.sha256(bed).hexdigest(),
    }
    (old / json_name).write_text(json.dumps({**common, "left_fasta": "old-left",
                                              "right_fasta": "old-right"}))
    (new / json_name).write_text(json.dumps({
        **common, "left_fasta": replay.HGSVC_FASTA,
        "right_fasta": replay.IGSR_FASTA,
        "difference_bed_path": f"/scratch/output/{bed_name}",
    }))
    (new / "SOURCE.txt").write_text(
        f"purpose=frozen-reference-provenance-rerun\n"
        f"hgsvc_sha256={replay.HGSVC_SHA256}\n"
        f"igsr_sha256={replay.IGSR_SHA256}\njob_id=123\n"
    )
    (new / "SHA256SUMS").write_text(
        f"{digest(new / bed_name)}  {bed_name}\n"
        f"{digest(new / json_name)}  {json_name}\n"
    )
    return old, new


def test_exact_frozen_replay_passes(tmp_path, monkeypatch):
    old, new = fixture_dirs(tmp_path, monkeypatch)
    result = replay.verify(old, new)
    assert result["n_contigs"] == 1
    assert result["n_different_bases"] == 2
    assert result["job_id"] == "123"


def test_frozen_replay_rejects_changed_scientific_summary(tmp_path, monkeypatch):
    old, new = fixture_dirs(tmp_path, monkeypatch)
    json_name = "chr1_base_differences_full.json"
    record = json.loads((new / json_name).read_text())
    record["difference_types"] = {"A>C": 2}
    (new / json_name).write_text(json.dumps(record))
    bed_name = "chr1_base_differences.bed"
    (new / "SHA256SUMS").write_text(
        f"{digest(new / bed_name)}  {bed_name}\n"
        f"{digest(new / json_name)}  {json_name}\n"
    )
    with pytest.raises(ValueError, match="scientific summary differs"):
        replay.verify(old, new)
