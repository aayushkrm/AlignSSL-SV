"""Offline guard/output tests; these do not emulate the native estimator."""
import io
import json
from pathlib import Path

import pytest

from analysis import check_aeons_observability as checker


@pytest.mark.parametrize("payload,message", [
    (b"raise RuntimeError('must not execute')", "size differs"),
    (b"x" * 3898, "blob differs"),
    (b"x" * 65537, "size differs"),
])
def test_source_guard_fails_before_execution(monkeypatch, payload, message):
    class Response(io.BytesIO):
        def read(self, size=-1):
            assert size == 65537
            return super().read(size)

    def fake_open(url, timeout):
        assert url == checker.URL
        assert timeout == 25
        return Response(payload)

    monkeypatch.setattr(checker.urllib.request, "urlopen", fake_open)
    with pytest.raises(ValueError, match=message):
        checker.load_reviewed_class()


def test_saved_control_preserves_scope_and_matched_observations():
    path = Path(__file__).resolve().parents[1] / (
        "results/analytic_controls/2026-10-07/aeons_observability.json")
    result = json.loads(path.read_text())
    observed = result["observable_lengths_in_both_cases"]
    native = result["native_all_sampled_length_states"]
    for full, state in zip(result["hidden_full_lengths"], native):
        assert full["kept"] == observed["kept"]
        assert observed["rejected"] == 400 < full["rejected"]
        assert state["mean_length"] == sum(full.values()) / len(full)
    assert native[0]["approx_ccl"] != native[1]["approx_ccl"]
    guards = result["observed_only_guard_states"]
    assert guards[0] == guards[1]
    assert guards[0]["mean_length"] == 4000
    assert result["guard_is_not_selection_bias_correction"]
    assert not result["full_simulator_or_live_instrument_executed"]
    assert not result["strategy_mask_or_SV_performance_effect_measured"]
    assert not result["genomic_input_read"]
    assert result["source"]["commit"] == checker.COMMIT
    assert result["source"]["git_blob"] == checker.BLOB
