#!/usr/bin/env python3
"""Retry the public ONT 500 metadata via curl after urllib TLS timeouts."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import datetime
import hashlib
import json
from pathlib import Path
import subprocess

from analysis.fetch_ont500_metadata import SOURCES


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", required=True, type=Path)
    a = p.parse_args()
    out = a.output.resolve()
    out.mkdir(parents=True, exist_ok=False)

    def get(item):
        name, url = item
        dest = out / name
        cmd = ["curl", "--fail", "--silent", "--show-error", "--location", "--connect-timeout", "10",
               "--max-time", "35", "--retry", "1", "--max-filesize", str(2 * 1024 * 1024),
               "--output", str(dest), "--write-out", "%{http_code}", url]
        run = subprocess.run(cmd, text=True, capture_output=True)
        (out / f"{name}.curl.stderr.txt").write_text(run.stderr)
        data = dest.read_bytes() if dest.exists() else b""
        result = {"name": name, "url": url, "argv": cmd, "exit_code": run.returncode,
                  "http_status": run.stdout, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest() if dest.exists() else None}
        if run.returncode or run.stdout != "200" or len(data) > 2 * 1024 * 1024:
            result["error"] = "curl failed or returned an unexpected status/size"
        return result

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
