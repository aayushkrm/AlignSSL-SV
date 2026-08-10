"""ShardDataset must not re-inflate a shard on every shuffled access.

Regression test for a performance defect that cost ~4 h of GPU time before it
was noticed. ShardDataset cached exactly ONE decompressed shard. A shard of
1024 windows at 18x64x256 float16 is ~604 MB decompressed from ~8 MB on disk,
so under a shuffled sampler over S shards roughly (1 - 1/S) of items paid a
full 604 MB zlib inflate to serve one 1.18 MB window. Symptom on the cluster:
training main process at 1.4% CPU, dataloader workers at 99%, GPU utilisation
sampled at 0% for minutes on end -- the GPU was starved, not stalled.

The fix is an LRU cache with a byte budget. These tests pin the two properties
that matter: bounded inflates under shuffle, and graceful degradation when a
single shard exceeds the budget (must not thrash, must not crash).
"""
from __future__ import annotations

import os

import numpy as np
import pytest

from alignssl.data import ShardDataset


def _write_shards(d, n_shards, n_win, shape=(18, 8, 16), chrom=1):
    rng = np.random.default_rng(0)
    for k in range(n_shards):
        np.savez_compressed(
            os.path.join(d, f"s{k:04d}.npz"),
            X=rng.random((n_win, *shape)).astype(np.float16),
            label=rng.integers(0, 2, n_win),
            geno=rng.integers(0, 3, n_win),
            bp=rng.random((n_win, 2)).astype(np.float32),
            bin_size=np.ones(n_win, np.int32),
            del_len=np.full(n_win, 300, np.int32),
            chrom=np.full(n_win, chrom, np.int32),
            start=np.arange(n_win),
        )


def test_shuffled_epoch_inflates_each_shard_at_most_once(tmp_path, monkeypatch):
    n_shards, n_win = 4, 40
    _write_shards(str(tmp_path), n_shards, n_win)
    ds = ShardDataset(str(tmp_path), split="train")
    assert len(ds) == n_shards * n_win

    calls = {"n": 0}
    real_load = np.load

    def counting(*a, **k):
        calls["n"] += 1
        return real_load(*a, **k)

    monkeypatch.setattr(np, "load", counting)
    rng = np.random.default_rng(1)
    order = rng.permutation(len(ds))
    for i in order:
        ds[int(i)]
    first = calls["n"]
    # Second pass over the same shuffled order must be fully cached.
    for i in order:
        ds[int(i)]

    assert first <= n_shards, (
        f"{first} inflates for one shuffled epoch over {n_shards} shards -- "
        "the shard cache is not holding shards across accesses"
    )
    assert calls["n"] == first, (
        "a warm second epoch re-inflated shards; cache is being evicted "
        "when it should fit"
    )


def test_tiny_budget_degrades_without_thrashing(tmp_path):
    """A budget smaller than one shard must still work, holding one slot.

    The eviction loop must never evict the shard it just inserted, or every
    access would insert-then-drop and `_cache` would be empty.
    """
    _write_shards(str(tmp_path), 3, 20)
    ds = ShardDataset(str(tmp_path), split="train", cache_bytes=1)
    rng = np.random.default_rng(2)
    for i in rng.permutation(len(ds))[:15]:
        item = ds[int(i)]
        assert item["x"].shape == (18, 8, 16)
    assert len(ds._cache) == 1, (
        f"tiny budget left {len(ds._cache)} cached shards; expected exactly 1"
    )


def test_cache_respects_byte_budget(tmp_path):
    """With a budget of ~2 shards, the cache must not grow past it."""
    n_shards, n_win = 5, 16
    _write_shards(str(tmp_path), n_shards, n_win)
    probe = ShardDataset(str(tmp_path), split="train")
    probe[0]
    one = probe._cache_bytes
    assert one > 0

    ds = ShardDataset(str(tmp_path), split="train", cache_bytes=int(2.5 * one))
    rng = np.random.default_rng(3)
    for i in rng.permutation(len(ds)):
        ds[int(i)]
    assert len(ds._cache) <= 3, f"cache grew to {len(ds._cache)} shards"
    assert ds._cache_bytes <= int(2.5 * one) + one, "byte accounting drifted"


def test_env_var_sets_default_budget(monkeypatch):
    """The budget is tunable without touching call sites (cluster --mem)."""
    import importlib

    import alignssl.data as m

    monkeypatch.setenv("ALIGNSSL_SHARD_CACHE_BYTES", str(123 << 20))
    importlib.reload(m)
    try:
        assert m.ShardDataset.CACHE_BYTES == 123 << 20
    finally:
        monkeypatch.delenv("ALIGNSSL_SHARD_CACHE_BYTES", raising=False)
        importlib.reload(m)


@pytest.mark.parametrize("split", ["train", "test"])
def test_values_unchanged_by_caching(tmp_path, split):
    """Caching must not alter what is served: compare against a cold read."""
    _write_shards(str(tmp_path), 3, 12, chrom=1 if split == "train" else 12)
    cold = ShardDataset(str(tmp_path), split=split, cache_bytes=1)
    warm = ShardDataset(str(tmp_path), split=split)
    assert len(cold) == len(warm) > 0
    for i in range(len(cold)):
        a, b = cold[i], warm[i]
        assert set(a) == set(b)
        for k in a:
            assert np.array_equal(a[k].numpy(), b[k].numpy()), f"{k} differs at {i}"
