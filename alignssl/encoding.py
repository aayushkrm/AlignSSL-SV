"""Representation provenance for historical and corrected depth tensors."""
import numpy as np

DEPTH_MODES = frozenset({"legacy", "mean_base_coverage"})
ROW_POOL_MODES = frozenset({"legacy", "mask_aware"})


def read_depth_mode(metadata):
    """Old shards/checkpoints without a declaration use the historical encoding."""
    value = np.asarray(metadata.get("depth_mode", "legacy"))
    if value.ndim != 0 or value.dtype.kind != "U":
        raise ValueError("depth_mode must be a scalar Unicode string")
    mode = str(value.item())
    if mode not in DEPTH_MODES:
        raise ValueError(f"Unknown depth_mode: {mode}")
    return mode


def require_same_depth_mode(expected, actual):
    if expected != actual:
        raise ValueError(f"Mixed depth encodings: {expected} versus {actual}; "
                         "re-extract and retrain instead of mixing representations")


def read_row_pool_mode(metadata):
    """Released checkpoints predate row-pooling provenance and are legacy."""
    value = np.asarray(metadata.get("row_pool_mode", "legacy"))
    if value.ndim != 0 or value.dtype.kind != "U":
        raise ValueError("row_pool_mode must be a scalar Unicode string")
    mode = str(value.item())
    if mode not in ROW_POOL_MODES:
        raise ValueError(f"Unknown row_pool_mode: {mode}")
    return mode


def require_same_row_pool_mode(expected, actual):
    if expected != actual:
        raise ValueError(f"Mixed row-pooling modes: {expected} versus {actual}; "
                         "instantiate and fine-tune the checkpoint with its "
                         "recorded encoder semantics")
