"""Synthetic subprocesses only; the source archive is never opened."""
import json
import sys

import pytest

from scripts.run_svpg_stage_bounded import run_bounded


def test_success_records_cpu_memory_and_preserves_logs(tmp_path):
    logdir = tmp_path / "run"
    report = run_bounded([sys.executable, "-c", "print('synthetic')"], logdir)
    assert report["status"] == "complete"
    assert report["returncode"] == 0
    assert report["combined_cpu_seconds"] >= 0
    assert "not a hard" in report["memory_enforcement"]
    assert (logdir / "stdout.log").read_text().strip() == "synthetic"
    assert json.loads((logdir / "resources.json").read_text())["status"] == "complete"
    with pytest.raises(FileExistsError):
        run_bounded([sys.executable, "-c", "pass"], logdir)


@pytest.mark.parametrize("sampler,reason", [
    (lambda pid: (100, []), "sampled RSS"),
    (lambda pid: (0, [999999]), "single-process"),
])
def test_supervisor_stops_only_owned_child_and_keeps_evidence(tmp_path, sampler, reason):
    report = run_bounded([sys.executable, "-c", "import time; time.sleep(20)"],
                         tmp_path / "run", sampler=sampler, rss_stop=50)
    assert report["status"] == "incomplete"
    assert reason in report["stop_reason"]
    assert report["returncode"] != 0
    assert (tmp_path / "run/resources.json").exists()


def test_sampling_failure_fails_closed(tmp_path):
    def fail(pid):
        raise RuntimeError("synthetic unavailable sampler")
    report = run_bounded([sys.executable, "-c", "import time; time.sleep(20)"],
                         tmp_path / "run", sampler=fail)
    assert report["status"] == "incomplete"
    assert report["supervisor_error"] == "RuntimeError"


def test_nonzero_exit_is_not_a_completed_stage(tmp_path):
    report = run_bounded([sys.executable, "-c", "raise SystemExit(2)"], tmp_path / "run")
    assert report["status"] == "incomplete"
    assert report["returncode"] == 2
