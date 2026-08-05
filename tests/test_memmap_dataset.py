"""Guards on the memmap fast path for labelled shards.

``MemmapShardDataset`` replaces ``ShardDataset`` for training.  A silent
divergence between them does not crash -- it produces a *plausible but
wrong* number, because the model trains on mislabelled or reordered
windows and still reports an AUPRC.  These tests therefore pin
equivalence field-by-field rather than checking that the loader "works".

What each test pins:

  * ``test_memmap_matches_shards``      -- every emitted key, for every
    item, in the same order, for both splits.  This is the test that
    would have caught ``build_memmap.py`` carrying only 4 of the 6
    label fields.
  * ``test_split_filtering``            -- train/test chromosome
    partition is identical, so the memmap cannot leak test
    chromosomes into training.
  * ``test_open_shards_dispatch``       -- auto-detection picks the
    memmap when one exists and the .npz path when it does not, so
    adopting the fast path per-benchmark cannot silently change which
    data a run reads.
  * ``test_unlabeled_mode``             -- SSL path still returns a bare
    tensor.
"""
from __future__ import annotations
import os
import subprocess
import sys

import numpy as np
import pytest
import torch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from alignssl.data import ShardDataset, MemmapShardDataset, open_shards  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
C, R, W = 18, 8, 32


def _make_shards(tmp_path, n_shards=3, per=7, seed=0):
    """Write .npz shards in the exact schema extract_tensors.py writes."""
    rng = np.random.default_rng(seed)
    # chroms spanning both splits (train=1-11, test=12-22)
    chrom_pool = [1, 5, 11, 12, 17, 22]
    for si in range(n_shards):
        n = per
        X = rng.random((n, C, R, W)).astype(np.float32)
        np.savez_compressed(
            tmp_path / f"SMP_all_shard{si:04d}.npz",
            X=X,
            label=rng.integers(0, 2, n).astype(np.int64),
            geno=rng.integers(0, 3, n).astype(np.int64),
            bp=rng.random((n, 2)).astype(np.float32),
            bin_size=rng.choice([1, 4, 16], n).astype(np.int64),
            del_len=rng.integers(50, 5000, n).astype(np.int64),
            chrom=np.array([chrom_pool[(si * per + j) % len(chrom_pool)]
                            for j in range(n)], dtype=np.int64),
            start=rng.integers(0, 10 ** 6, n).astype(np.int64),
        )
    return tmp_path


def _build_memmap(shard_dir):
    out = os.path.join(str(shard_dir), "mm")
    r = subprocess.run(
        [sys.executable, os.path.join(REPO, "scripts", "build_memmap.py"),
         "--shard-dir", str(shard_dir), "--out", out],
        capture_output=True, text=True, cwd=REPO,
        env={**os.environ, "PYTHONPATH": REPO},
    )
    assert r.returncode == 0, r.stderr
    return out


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    d = _make_shards(tmp_path_factory.mktemp("shards"))
    pre = _build_memmap(d)
    return d, pre


@pytest.mark.parametrize("split", ["train", "test", "all"])
def test_memmap_matches_shards(built, split):
    d, pre = built
    a = ShardDataset(str(d), split=split, labeled=True)
    b = MemmapShardDataset(pre, split=split, labeled=True)
    assert len(a) == len(b) > 0
    for i in range(len(a)):
        ia, ib = a[i], b[i]
        assert sorted(ia.keys()) == sorted(ib.keys())
        for k in ia:
            va, vb = ia[k], ib[k]
            if k == "x":
                # memmap stores float16; compare at that precision
                assert torch.allclose(va.half().float(), vb, atol=1e-3), (i, k)
            elif k == "bp":
                assert np.allclose(va.numpy(), vb.numpy(),
                                   atol=1e-6, equal_nan=True), (i, k)
            else:
                assert int(va) == int(vb), (i, k)


def test_split_filtering(built):
    d, pre = built
    tr = MemmapShardDataset(pre, split="train")
    te = MemmapShardDataset(pre, split="test")
    al = MemmapShardDataset(pre, split="all")
    assert len(tr) + len(te) == len(al)
    assert len(tr) > 0 and len(te) > 0
    meta = np.load(pre + ".meta.npz")
    assert all(int(meta["chrom"][j]) <= 11 for j in tr.index)
    assert all(int(meta["chrom"][j]) >= 12 for j in te.index)


def test_open_shards_dispatch(built, tmp_path):
    d, pre = built
    assert isinstance(open_shards(str(d)), MemmapShardDataset)
    assert isinstance(open_shards(pre), MemmapShardDataset)
    bare = _make_shards(tmp_path / "bare" if False else tmp_path, seed=1)
    assert isinstance(open_shards(str(bare)), ShardDataset)
    with pytest.raises(FileNotFoundError):
        open_shards(str(tmp_path / "nope"))


def test_unlabeled_mode(built):
    d, pre = built
    x = MemmapShardDataset(pre, split="all", labeled=False)[0]
    assert isinstance(x, torch.Tensor) and x.shape == (C, R, W)


def test_meta_carries_full_schema(built):
    """build_memmap.py must persist every field the loader reads."""
    _, pre = built
    meta = np.load(pre + ".meta.npz")
    for k in ("chrom", "bin_size", "start", "label", "geno", "del_len", "bp"):
        assert k in meta.files, f"build_memmap dropped {k!r}"
    assert meta["bp"].ndim == 2 and meta["bp"].shape[1] == 2
