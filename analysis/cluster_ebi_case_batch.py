#!/usr/bin/env python3
"""Run the pinned EBI validator on five synthetic inputs in parallel."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile


EXPECTED = "7326fc83425f5367f9974aaa223f2b48b1854bf9ecd5e9e5eae3899b3107fc87"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--binary", type=Path, required=True)
    p.add_argument("--inputs", type=Path, required=True)
    p.add_argument("--manifest", type=Path, required=True)
    args = p.parse_args()
    if sha(args.binary) != EXPECTED:
        raise ValueError("validator binary hash differs from pinned release")
    manifest = json.loads(args.manifest.read_text())
    for name, digest in manifest["inputs"].items():
        if sha(args.inputs / name) != digest:
            raise ValueError(f"input hash mismatch: {name}")

    def execute(name):
        with tempfile.TemporaryDirectory(prefix="alignssl-validator-case-") as temp:
            cmd = [str(args.binary), "-i", str(args.inputs / name), "-l", "warning", "-r", "summary", "-o", temp]
            run = subprocess.run(cmd, text=True, capture_output=True)
            reports = {p.name: p.read_text() for p in sorted(Path(temp).iterdir()) if p.is_file()}
            return {"input": name, "input_sha256": sha(args.inputs / name), "command": cmd,
                    "exit_code": run.returncode, "stdout": run.stdout, "stderr": run.stderr, "reports": reports}

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(execute, sorted(manifest["inputs"])))
    print(json.dumps({"validator_sha256": EXPECTED, "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
                      "allocated_cpus": os.environ.get("SLURM_CPUS_PER_TASK"), "node": socket.gethostname(),
                      "results": results}, indent=2))


if __name__ == "__main__":
    main()
