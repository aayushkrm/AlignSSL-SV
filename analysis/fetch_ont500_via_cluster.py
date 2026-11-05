#!/usr/bin/env python3
"""Fetch public ONT-500 metadata via cluster curl after local TLS failures."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import datetime
import hashlib
import json
from pathlib import Path
import shlex
import subprocess

from analysis.fetch_ont500_metadata import SOURCES


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--cluster-helper", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)

    def get(item):
        name, url = item
        remote = ("curl --fail --silent --show-error --location --connect-timeout 8 "
                  "--max-time 25 --max-filesize 2097152 " + shlex.quote(url))
        cmd = [str(args.cluster_helper.resolve()), remote]
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=40)
            (out / f"{name}.stderr.txt").write_bytes(result.stderr)
            if result.returncode == 0 and len(result.stdout) <= 2 * 1024 * 1024:
                (out / name).write_bytes(result.stdout)
            row = {"name": name, "url": url, "argv": cmd, "exit_code": result.returncode,
                   "bytes": len(result.stdout), "sha256": hashlib.sha256(result.stdout).hexdigest()}
            if result.returncode or len(result.stdout) > 2 * 1024 * 1024:
                row["error"] = "cluster curl failed or exceeded the metadata cap"
            return row
        except subprocess.TimeoutExpired as exc:
            (out / f"{name}.stderr.txt").write_text(str(exc) + "\n")
            return {"name": name, "url": url, "argv": cmd, "error": "cluster helper timed out"}

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(get, SOURCES.items()))
    receipt = {"retrieved_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
               "script_sha256": hashlib.sha256(Path(__file__).resolve().read_bytes()).hexdigest(),
               "sources": results}
    (out / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))
    if any("error" in x for x in results):
        raise SystemExit("one or more sources failed; partial output retained")


if __name__ == "__main__":
    main()
