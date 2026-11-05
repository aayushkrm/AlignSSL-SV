#!/usr/bin/env python3
"""Fetch four bounded HGSVC2 text metadata files with a cluster fallback."""

import concurrent.futures
import datetime
import hashlib
import json
import pathlib
import shlex
import subprocess

REPO = pathlib.Path(__file__).resolve().parent.parent
OUT = REPO / "results/hgsvc2_sample_lists_20261106_run01"
BASE = "https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/HGSVC2/release/v1.0/PanGenie_results/"
FILES = ["20200902_HHU_genotyping_pangenie-results-freeze3_MANIFEST.txt",
         "20200902_HHU_genotyping_pangenie-results-freeze3_README.txt",
         "pangenie-genotyping.PRJEB31736.2504.sample-list.txt",
         "pangenie-genotyping.PRJEB36890.698.sample-list.txt"]
CLUSTER = REPO.parent / "tools/cluster.sh"
MAX_BYTES = 256 * 1024


def sha(data):
    return hashlib.sha256(data).hexdigest()


def fetch(name):
    curl = ["curl", "--fail", "--silent", "--show-error", "--location",
            "--connect-timeout", "8", "--max-time", "25", "--max-filesize",
            str(MAX_BYTES), BASE + name]
    attempts = []
    for number, command in enumerate([curl, [str(CLUSTER), shlex.join(curl)]], 1):
        try:
            result = subprocess.run(command, capture_output=True, timeout=60, check=False)
            body, stderr, code = result.stdout, result.stderr, result.returncode
        except subprocess.TimeoutExpired as exc:
            body, stderr, code = exc.stdout or b"", exc.stderr or b"", None
        stem = f"{name}.attempt{number:02d}"
        (OUT / f"{stem}.stdout").write_bytes(body)
        (OUT / f"{stem}.stderr").write_bytes(stderr)
        attempts.append({"route": "local" if number == 1 else "cluster",
                         "argv": command, "exit_code": code, "bytes": len(body),
                         "stdout_sha256": sha(body), "stderr_sha256": sha(stderr)})
        if code == 0 and 0 < len(body) <= MAX_BYTES:
            return {"name": name, "url": BASE + name,
                    "successful_attempt": number, "attempts": attempts}
    return {"name": name, "url": BASE + name, "attempts": attempts}


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        sources = list(pool.map(fetch, FILES))
    receipt = {"retrieved_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
               "max_bytes_per_response": MAX_BYTES,
               "script_sha256": sha(pathlib.Path(__file__).read_bytes()), "sources": sources}
    (OUT / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print("Retrieved", sum("successful_attempt" in source for source in sources),
          "of", len(sources), "metadata files")
    if any("successful_attempt" not in source for source in sources):
        raise SystemExit("At least one source failed; see receipt")


if __name__ == "__main__":
    main()
