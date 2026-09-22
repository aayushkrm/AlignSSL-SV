"""Exercise depth-mode CLI propagation and shard provenance without input data."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = {
    "extract_tensors": ROOT / "scripts" / "extract_tensors.py",
    "extract_pretrain": ROOT / "scripts" / "extract_pretrain.py",
    "extract_tensors_candidates": ROOT / "scripts" / "extract_tensors_candidates.py",
    "extract_tensors_hardneg": ROOT / "scripts" / "extract_tensors_hardneg.py",
}


class _FakeFasta:
    def __init__(self, _path):
        pass

    def get_reference_length(self, _chrom):
        return 1_000_000

    def fetch(self, _chrom, start, end):
        return "A" * (int(end) - int(start))


class _FakeBam:
    def __init__(self, _path, _mode, index_filename=None):
        self.index_filename = index_filename

    def fetch(self, _chrom, _start=None, _end=None):
        return []


def _load_script(name):
    spec = importlib.util.spec_from_file_location(
        f"depth_mode_test_{name}", SCRIPTS[name]
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _configure_script(module, monkeypatch, tmp_path, seen):
    monkeypatch.setattr(
        module.pysam, "FastaFile", _FakeFasta
    )
    monkeypatch.setattr(
        module.pysam, "AlignmentFile", _FakeBam
    )
    monkeypatch.setattr(module, "CHROM_SPLIT", {
        "train": ["1"],
        "test": ["1"],
    })
    monkeypatch.setattr(
        module, "estimate_isize", lambda *args, **kwargs: (450.0, 100.0)
    )

    def fake_build_tensor(*args, **kwargs):
        seen.append(kwargs["depth_mode"])
        return np.zeros((1, 1, 1), dtype=np.float32)

    monkeypatch.setattr(module, "build_tensor", fake_build_tensor)

    name = next(name for name, path in SCRIPTS.items()
                if path == Path(module.__file__))
    common = [
        "--bam", "unused.bam",
        "--fasta", "unused.fa",
        "--sample", "SAMPLE",
        "--out-dir", str(tmp_path),
        "--split", "all",
        "--shard-size", "10",
    ]

    if name == "extract_tensors":
        monkeypatch.setattr(
            module, "load_truth_dels",
            lambda *args, **kwargs: {"1": [(100, 200, 1)]},
        )
        monkeypatch.setattr(
            module, "build_items",
            lambda *args, **kwargs: [
                ("1", 0, 256, 1, 1, 1, 0.25, 0.5, 100)
            ],
        )
        common += ["--vcf", "unused.vcf"]
        output = tmp_path / "SAMPLE_all_shard0000.npz"
        expected_keys = {
            "X", "label", "geno", "bp", "bin_size", "del_len", "chrom", "start"
        }
    elif name == "extract_pretrain":
        common += [
            "--n-windows", "1",
            "--min-reads", "0",
        ]
        output = tmp_path / "pretrain_SAMPLE_all_shard0000.npz"
        expected_keys = {"X", "bin_size", "chrom", "start", "label"}
    elif name == "extract_tensors_candidates":
        monkeypatch.setattr(
            module, "load_truth_giab",
            lambda *args, **kwargs: ({"1": []}, {"1": np.zeros((0, 2), dtype=np.int64)}),
        )
        monkeypatch.setattr(
            module, "load_bed",
            lambda *args, **kwargs: {"1": np.array([[0, 1_000_000]], dtype=np.int64)},
        )
        monkeypatch.setattr(
            module, "load_candidate_dels",
            lambda *args, **kwargs: ({"1": [(100, 200), (300, 400)]}, 2, 2),
        )
        monkeypatch.setattr(
            module, "label_candidates",
            lambda *args, **kwargs: (
                [("1", 100, 200, 1, 1), ("1", 300, 400, 0, 0)],
                {
                    "n_cand": 2,
                    "n_tp": 1,
                    "n_fp": 1,
                    "drop_unconfident": 0,
                    "drop_ambiguous": 0,
                    "drop_below_reciprocal": 0,
                },
            ),
        )
        common += [
            "--vcf", "unused.vcf",
            "--candidate-vcf", "unused-candidates.vcf",
            "--confident-bed", "unused.bed",
        ]
        output = tmp_path / "SAMPLE_all_shard0000.npz"
        expected_keys = {
            "X", "label", "geno", "bp", "bin_size", "del_len", "chrom", "start"
        }
    else:
        monkeypatch.setattr(
            module, "load_truth_dels",
            lambda *args, **kwargs: {"1": [(100, 200, 1)]},
        )
        monkeypatch.setattr(
            module, "build_items",
            lambda *args, **kwargs: (
                [("1", 0, 256, 1, 1, 1, 0.25, 0.5, 100)],
                [],
            ),
        )
        common += ["--vcf", "unused.vcf"]
        output = tmp_path / "SAMPLE_all_shard0000.npz"
        expected_keys = {
            "X", "label", "geno", "bp", "bin_size", "del_len", "chrom", "start"
        }

    return name, common, output, expected_keys


@pytest.mark.parametrize("name", list(SCRIPTS))
@pytest.mark.parametrize("with_flag", [True, False], ids=["explicit", "default"])
def test_cli_propagates_depth_mode_and_records_scalar_provenance(
    name, with_flag, monkeypatch, tmp_path
):
    """Each extractor passes the selected mode and records it without schema loss."""
    module = _load_script(name)
    seen = []
    name, argv, output, expected_keys = _configure_script(
        module, monkeypatch, tmp_path, seen
    )
    if with_flag:
        argv += ["--depth-mode", "mean_base_coverage"]
    monkeypatch.setattr(sys, "argv", [str(SCRIPTS[name]), *argv])

    module.main()

    expected_mode = "mean_base_coverage" if with_flag else "legacy"
    assert seen and all(mode == expected_mode for mode in seen)
    assert output.exists()
    with np.load(output, allow_pickle=False) as shard:
        assert expected_keys <= set(shard.files)
        assert "depth_mode" in shard.files
        assert shard["depth_mode"].shape == ()
        assert shard["depth_mode"].dtype.kind == "U"
        assert shard["depth_mode"].item() == expected_mode
