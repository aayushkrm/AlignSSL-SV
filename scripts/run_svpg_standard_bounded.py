"""Use the existing own-group guard with a sampled combined-CPU stop."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import resource
import re
import subprocess
import sys

if __package__:
    from . import run_svpg_stage_bounded as bounded
else:
    import run_svpg_stage_bounded as bounded


def parse_cpu_time(text):
    days, clock = text.strip().split("-", 1) if "-" in text else ("0", text.strip())
    fields = clock.split(":")
    if (len(fields) not in (2, 3) or not days.isdigit()
            or any(not f.isdigit() for f in fields[:-1])
            or not re.fullmatch(r"\d+(?:\.\d+)?", fields[-1])
            or float(fields[-1]) >= 60
            or (len(fields) == 3 and int(fields[-2]) >= 60)):
        raise ValueError("Cannot interpret owned child CPU time")
    total = int(days) * 86400 + float(fields[-1]) + int(fields[-2]) * 60
    return total + (int(fields[0]) * 3600 if len(fields) == 3 else 0)


def run_with_guard(command, logdir):
    baseline = sum(r.ru_utime + r.ru_stime for r in
                   (resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)))
    latest_cpu = [0.0]
    def sampler(pid):
        rss, children = bounded.sample_process(pid)
        result = subprocess.run(["ps", "-p", str(pid), "-o", "time="],
                                capture_output=True, text=True, timeout=3)
        if not result.stdout.strip():
            # Exit can race ps. The existing guard rejects zero RSS for a
            # still-live child; an exited child is reaped for final CPU totals.
            return 0, children
        child_cpu = parse_cpu_time(result.stdout)
        overhead = sum(r.ru_utime + r.ru_stime for r in
                       (resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN))) - baseline
        latest_cpu[0] = child_cpu + overhead
        if latest_cpu[0] >= 580:
            raise RuntimeError("Combined CPU headroom exhausted")
        return rss, children
    bounded.CPU_SECONDS = 550
    # Do not lower the parent's hard CPU limit: the child inherits it and
    # could not then set its reviewed 550-second limit. Parent/helper CPU
    # remains counted in the runtime combined sampler and final check.
    report = bounded.run_bounded(command, logdir, sampler=sampler, wall_seconds=900)
    guard = {"sampled_combined_cpu_stop_seconds": 580, "combined_cpu_ceiling_seconds": 600,
             "latest_sampled_combined_cpu_seconds": latest_cpu[0], "child_hard_cpu_limit_seconds": 550,
             "enforcement": "runtime sampled child plus launcher and reaped helper CPU; final combined check",
             "measured_combined_cpu_seconds": report["combined_cpu_seconds"],
             "budget_pass": report["status"] == "complete" and report["combined_cpu_seconds"] <= 600}
    with (logdir / "cpu_guard.json").open("x") as handle:
        json.dump(guard, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return {"resources": report, "cpu_guard": guard}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("archive", "outdir", "protocol", "logdir"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    parser.add_argument("--protocol-sha256", required=True)
    args = parser.parse_args()
    command = [sys.executable, str(bounded.ROOT / "analysis/transport_svpg_standard.py"),
               "--archive", str(args.archive), "--outdir", str(args.outdir),
               "--protocol", str(args.protocol), "--protocol-sha256", args.protocol_sha256]
    result = run_with_guard(command, args.logdir)
    print(json.dumps(result, indent=2, sort_keys=True))
    if not result["cpu_guard"]["budget_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
