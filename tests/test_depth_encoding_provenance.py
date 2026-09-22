"""Prevent a representation ablation from silently mixing incompatible inputs."""
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from alignssl.data import MemmapDataset, ShardDataset, open_shards
from alignssl.encoding import read_depth_mode


def shard(path, mode=None):
    fields = dict(X=np.zeros((2, 18, 2, 4), np.float16),
                  chrom=np.array([1, 20]), bin_size=np.array([4, 4]),
                  start=np.array([100, 200]), label=np.array([0, 1]))
    if mode is not None:
        fields["depth_mode"] = np.asarray(mode)
    np.savez(path, **fields)


def test_old_shards_remain_legacy(tmp_path):
    shard(tmp_path / "old.npz")
    assert ShardDataset(tmp_path, labeled=False).depth_mode == "legacy"


def test_mixed_shards_rejected_even_across_chrom_splits(tmp_path):
    shard(tmp_path / "a.npz")
    shard(tmp_path / "b.npz", "mean_base_coverage")
    with pytest.raises(ValueError, match="Mixed depth"):
        ShardDataset(tmp_path, split="train", labeled=False)


@pytest.mark.parametrize("invalid", ["other", ["legacy"], b"legacy", 1])
def test_bad_provenance_rejected(invalid):
    with pytest.raises(ValueError, match="depth_mode"):
        read_depth_mode({"depth_mode": invalid})


def run_conversion(directory, output):
    return subprocess.run([sys.executable, "-m", "scripts.build_memmap",
                           "--shard-dir", str(directory), "--out", str(output)],
                          cwd=Path(__file__).resolve().parents[1],
                          capture_output=True, text=True)


def test_memmap_preserves_corrected_encoding(tmp_path):
    source = tmp_path / "shards"
    source.mkdir()
    shard(source / "a.npz", "mean_base_coverage")
    prefix = tmp_path / "tensor"
    result = run_conversion(source, prefix)
    assert result.returncode == 0, result.stderr
    dataset = MemmapDataset(str(prefix), split="train")
    assert dataset.depth_mode == "mean_base_coverage"
    assert len(dataset) == 1
    assert open_shards(str(prefix), labeled=False).depth_mode == "mean_base_coverage"


def test_mixed_conversion_fails_before_writing_tensor(tmp_path):
    source = tmp_path / "shards"
    source.mkdir()
    shard(source / "a.npz")
    shard(source / "b.npz", "mean_base_coverage")
    prefix = tmp_path / "tensor"
    result = run_conversion(source, prefix)
    assert result.returncode != 0
    assert "Mixed depth" in result.stderr
    assert not prefix.with_suffix(".f16").exists()
