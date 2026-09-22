"""Holdout-only calibration and representation provenance contracts."""

import numpy as np
from argparse import Namespace
import pytest
import torch

from scripts.finetune_eval import (
    build_result_config,
    calibrate_test_from_validation,
    fit_temperature_on_validation,
    require_checkpoint_depth_mode,
    require_checkpoint_row_pool_mode,
)


def _logits():
    val_logits = torch.tensor([[3.0, 0.0], [0.0, 3.0]])
    val_labels = torch.tensor([0, 1])
    test_logits = torch.tensor([[2.0, 0.0], [0.0, 2.0]])
    return val_logits, val_labels, test_logits


def test_temperature_is_fit_from_validation_labels_only(monkeypatch):
    val_logits, val_labels, test_logits = _logits()
    seen = {}

    from alignssl.heads import TemperatureScaler

    def fake_fit(self, logits, labels, max_iter=200, lr=0.01):
        seen["logits"] = logits.clone()
        seen["labels"] = labels.clone()
        return 2.0

    monkeypatch.setattr(TemperatureScaler, "fit", fake_fit)
    first = calibrate_test_from_validation(
        val_logits, val_labels, test_logits, torch.tensor([0, 1])
    )
    second = calibrate_test_from_validation(
        val_logits, val_labels, test_logits, torch.tensor([1, 0])
    )

    assert torch.equal(seen["logits"], val_logits)
    assert torch.equal(seen["labels"], val_labels)
    assert first["calibration_status"] == "fit_validation"
    assert first["calibration_source"] == "validation"
    assert first["temperature"] == 2.0
    assert second["temperature"] == first["temperature"]
    assert first["ece"] != second["ece"]


def test_no_validation_is_explicitly_skipped():
    _, _, test_logits = _logits()
    scaler, record = fit_temperature_on_validation(None, None)
    assert scaler is None
    assert record == {
        "calibration_status": "skipped_no_validation",
        "calibration_source": None,
        "temperature": None,
    }
    scored = calibrate_test_from_validation(
        None, None, test_logits, torch.tensor([0, 1])
    )
    assert scored["calibration_status"] == "skipped_no_validation"
    assert scored["ece"] is None


def test_single_class_validation_is_explicitly_skipped():
    val_logits = torch.tensor([[2.0, 0.0], [1.0, 0.0]])
    val_labels = torch.tensor([0, 0])
    scaler, record = fit_temperature_on_validation(val_logits, val_labels)
    assert scaler is None
    assert record["calibration_status"] == "skipped_single_class"
    assert record["calibration_source"] is None
    assert record["temperature"] is None


def test_checkpoint_depth_mode_must_match_training_shards():
    assert require_checkpoint_depth_mode(
        "mean_base_coverage", {"depth_mode": np.asarray("mean_base_coverage")}
    ) == "mean_base_coverage"
    with pytest.raises(ValueError, match="Mixed depth"):
        require_checkpoint_depth_mode(
            "mean_base_coverage", {"depth_mode": np.asarray("legacy")}
        )


def test_checkpoint_row_pool_mode_must_match_encoder():
    assert require_checkpoint_row_pool_mode(
        "mask_aware", {"row_pool_mode": np.asarray("mask_aware")}
    ) == "mask_aware"
    with pytest.raises(ValueError, match="Mixed row-pooling"):
        require_checkpoint_row_pool_mode(
            "mask_aware", {"row_pool_mode": np.asarray("legacy")}
        )
    # Released checkpoints predate this field and retain historical behavior.
    assert require_checkpoint_row_pool_mode("legacy", {}) == "legacy"


def test_result_config_records_depth_mode():
    args = Namespace(out="results.json", seed=7)
    config = build_result_config(args, "mean_base_coverage")
    assert config["depth_mode"] == "mean_base_coverage"
    assert config["out"] == "results.json"
