"""Run the single-process SVPG stager with CPU and sampled-memory guards.

The RSS supervisor is not a hard macOS RAM limit. It stops at 3 GiB to retain
headroom below the reviewed 4 GiB ceiling. Only its own new process group can
be terminated. Logs and partial outputs are retained; no automatic retries.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
CPU_SECONDS = 1800
RSS_STOP_BYTES = 3 * 1024**3


def sample_process(pid: int) -> tuple[int, list[int]]:
    """Read RSS and verify the stager has not created child processes."""
    result = subprocess.run(["ps", "-p", str(pid), "-o", "rss="],
                            capture_output=True, text=True, timeout=3)
    rss = int(result.stdout.strip()) * 1024 if result.stdout.strip() else 0
    children = subprocess.run(["pgrep", "-P", str(pid)], capture_output=True,
                              text=True, timeout=3)
    if children.returncode not in (0, 1):
        raise RuntimeError("Cannot inspect stager child processes")
    return rss, [int(value) for value in children.stdout.split()]


def cpu_limit() -> None:
    resource.setrlimit(resource.RLIMIT_CPU, (CPU_SECONDS, CPU_SECONDS))


def stop_owned_group(process: subprocess.Popen) -> None:
    if process.poll() is None:
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=5)


def run_bounded(command: list[str], logdir: Path, *, sampler=sample_process,
                rss_stop=RSS_STOP_BYTES, wall_seconds=1800) -> dict:
    logdir = logdir.resolve()
    if logdir == ROOT or ROOT in logdir.parents:
        raise ValueError("Runtime logs must remain outside Git")
    logdir.mkdir(mode=0o700, parents=False, exist_ok=False)
    before_self = resource.getrusage(resource.RUSAGE_SELF)
    before_children = resource.getrusage(resource.RUSAGE_CHILDREN)
    start = time.monotonic()
    peak, reason, error = 0, None, None
    with (logdir / "stdout.log").open("xb") as stdout, (logdir / "stderr.log").open("xb") as stderr:
        process = subprocess.Popen(command, stdout=stdout, stderr=stderr,
                                   start_new_session=True, preexec_fn=cpu_limit)
        try:
            while process.poll() is None:
                rss, children = sampler(process.pid)
                peak = max(peak, rss)
                if children:
                    reason = "single-process invariant violated"
                elif rss == 0 and process.poll() is None:
                    reason = "live stager RSS unavailable"
                elif rss >= rss_stop:
                    reason = "sampled RSS headroom exceeded"
                elif time.monotonic() - start >= wall_seconds:
                    reason = "wall-clock cap exceeded"
                elif os.statvfs(logdir).f_bavail * os.statvfs(logdir).f_frsize < 10 * 1024**3 + 32 * 1024**2:
                    reason = "local free-space headroom exhausted"
                if reason:
                    stop_owned_group(process)
                    break
                time.sleep(0.25)
        except BaseException as exc:
            reason, error = "supervisor interrupted or failed", type(exc).__name__
            stop_owned_group(process)
        returncode = process.wait()
    after_self = resource.getrusage(resource.RUSAGE_SELF)
    after_children = resource.getrusage(resource.RUSAGE_CHILDREN)
    cpu = sum(getattr(after_self, key) - getattr(before_self, key) +
              getattr(after_children, key) - getattr(before_children, key)
              for key in ("ru_utime", "ru_stime"))
    rusage_peak = after_children.ru_maxrss * (1 if sys.platform == "darwin" else 1024)
    report = {"status": "complete" if returncode == 0 and reason is None else "incomplete",
              "command": command, "returncode": returncode, "stop_reason": reason,
              "supervisor_error": error, "wall_seconds": time.monotonic() - start,
              "combined_cpu_seconds": cpu, "sampled_peak_rss_bytes": peak,
              "children_rusage_peak_rss_bytes": rusage_peak,
              "child_cpu_limit_seconds": CPU_SECONDS, "rss_stop_bytes": rss_stop,
              "memory_enforcement": "Sampled external guard, not a hard RAM guarantee",
              "single_process_required": True, "partial_outputs_preserved": True}
    with (logdir / "resources.json").open("x") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("archive", "outdir", "protocol", "logdir"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    parser.add_argument("--protocol-sha256", required=True)
    args = parser.parse_args()
    if os.statvfs(args.outdir.parent).f_bavail * os.statvfs(args.outdir.parent).f_frsize < 10 * 1024**3 + 1_037_019_267:
        parser.error("Free space cannot retain the 10 GiB guard after staging")
    command = [sys.executable, str(ROOT / "analysis/stage_svpg_callsets.py"),
               "--archive", str(args.archive), "--outdir", str(args.outdir),
               "--protocol", str(args.protocol), "--protocol-sha256", args.protocol_sha256]
    report = run_bounded(command, args.logdir)
    print(json.dumps(report, indent=2, sort_keys=True))
    if report["status"] != "complete":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
