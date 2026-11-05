#!/usr/bin/env python3
"""Save bounded public Zenodo record metadata; never fetch deposited files."""

import datetime
import hashlib
import json
import pathlib
import subprocess


REPO = pathlib.Path(__file__).resolve().parent.parent
OUT = REPO / "results/rna_zenodo_record_20261106_run01"
URL = "https://zenodo.org/api/records/18763244"
MAX_BYTES = 2 * 1024 * 1024
CLUSTER = REPO.parent / "tools/cluster.sh"
CURL = [
    "curl", "--fail", "--silent", "--show-error", "--location",
    "--connect-timeout", "10", "--max-time", "30", "--max-filesize",
    str(MAX_BYTES), URL,
]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    receipt = {
        "url": URL,
        "retrieved_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "script_sha256": sha(pathlib.Path(__file__).read_bytes()),
        "max_bytes": MAX_BYTES,
        "attempts": [],
    }
    commands = [CURL, [str(CLUSTER), " ".join(CURL)]]
    for number, command in enumerate(commands, start=1):
        try:
            result = subprocess.run(command, capture_output=True, timeout=60, check=False)
            stdout, stderr, returncode = result.stdout, result.stderr, result.returncode
        except subprocess.TimeoutExpired as exc:
            stdout, stderr, returncode = exc.stdout or b"", exc.stderr or b"", None
        stem = f"attempt{number:02d}"
        (OUT / f"{stem}.stderr.txt").write_bytes(stderr)
        entry = {
            "route": "local" if number == 1 else "cluster",
            "argv": command,
            "exit_code": returncode,
            "stderr_sha256": sha(stderr),
            "bytes": len(stdout),
            "stdout_sha256": sha(stdout),
        }
        receipt["attempts"].append(entry)
        (OUT / f"{stem}.stdout").write_bytes(stdout)
        if returncode == 0 and len(stdout) <= MAX_BYTES:
            try:
                payload = json.loads(stdout)
                if str(payload.get("id")) != "18763244":
                    raise ValueError("Unexpected record ID")
                receipt["successful_attempt"] = number
                receipt["files_listed"] = len(payload.get("files", []))
            except (ValueError, TypeError, AttributeError) as exc:
                entry["error"] = str(exc)
        (OUT / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
        if "successful_attempt" in receipt:
            break
    (OUT / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    if "successful_attempt" not in receipt:
        raise SystemExit("Both bounded metadata retrieval routes failed")


if __name__ == "__main__":
    main()
