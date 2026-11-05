#!/usr/bin/env python3
"""Download one public count matrix; inspect its first row only."""

import csv
import datetime
import gzip
import hashlib
import io
import json
import pathlib
import shlex
import subprocess

REPO = pathlib.Path(__file__).resolve().parent.parent
RUN = REPO.parent / "runs/rna_flair_counts_20261106_run01"
OUT = REPO / "results/rna_flair_header_20261106_run01"
NAME = "Geuvadis_60EUR_Transcripts_FLAIR_COUNTS.tsv.gz"
URL = "https://zenodo.org/api/records/18763244/files/" + NAME + "/content"
SIZE = 7577751
MD5 = "3b841d33a7c7bfe4b250f700d1053b03"
MAX_BYTES = 8 * 1024 * 1024
HEADER_LIMIT = 1024 * 1024
CLUSTER = REPO.parent / "tools/cluster.sh"


def digest(path, algorithm):
    h = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    RUN.mkdir(parents=True, exist_ok=False)
    curl = ["curl", "--fail", "--silent", "--show-error", "--location",
            "--connect-timeout", "10", "--max-time", "45", "--max-filesize",
            str(MAX_BYTES), URL]
    receipt = {"url": URL, "declared_size": SIZE, "declared_md5": MD5,
               "max_download_bytes": MAX_BYTES, "max_header_bytes": HEADER_LIMIT,
               "retrieved_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
               "script_sha256": digest(pathlib.Path(__file__), "sha256"), "attempts": []}
    commands = [curl, [str(CLUSTER), shlex.join(curl)]]
    chosen = None
    for number, command in enumerate(commands, start=1):
        target = RUN / f"attempt{number:02d}.gz"
        stderr_path = OUT / f"attempt{number:02d}.stderr.txt"
        with target.open("wb") as body, stderr_path.open("wb") as stderr:
            try:
                proc = subprocess.run(command, stdout=body, stderr=stderr,
                                      timeout=75, check=False)
                code = proc.returncode
            except subprocess.TimeoutExpired:
                code = None
        entry = {"route": "local" if number == 1 else "cluster", "argv": command,
                 "exit_code": code, "bytes": target.stat().st_size,
                 "sha256": digest(target, "sha256"), "md5": digest(target, "md5"),
                 "stderr_sha256": digest(stderr_path, "sha256"),
                 "local_file": str(target)}
        receipt["attempts"].append(entry)
        (OUT / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
        if code == 0 and entry["bytes"] == SIZE and entry["md5"] == MD5:
            chosen = target
            receipt["successful_attempt"] = number
            break
    if chosen is None:
        raise SystemExit("No attempt matched the declared file size and MD5")

    with gzip.open(chosen, "rb") as stream:
        raw_header = stream.readline(HEADER_LIMIT + 1)
    if len(raw_header) > HEADER_LIMIT or not raw_header.endswith(b"\n"):
        raise ValueError("First row exceeded limit or was not newline terminated")
    header = next(csv.reader(io.StringIO(raw_header.decode("utf-8")), delimiter="\t"))
    crosswalk = json.loads((REPO / "results/paired_dna_rna_ont500_crosswalk_20261104_run01/crosswalk.json").read_text())
    rows = crosswalk["rows"]
    rna = {row["rna_sample_title"] for row in rows}
    paired = {row["rna_sample_title"] for row in rows
              if row["vienna_listed_alignment"] or row["ont500_exact_metadata_label"]}
    fields = set(header)
    summary = {"first_row_sha256": hashlib.sha256(raw_header).hexdigest(),
               "column_count": len(header), "first_row": header,
               "rna_titles_exactly_matched": sorted(rna & fields),
               "rna_titles_not_matched": sorted(rna - fields),
               "paired_titles_exactly_matched": sorted(paired & fields),
               "paired_titles_not_matched": sorted(paired - fields),
               "duplicate_matched_fields": sorted(x for x in rna & fields if header.count(x) > 1),
               "crosswalk_sha256": digest(REPO / "results/paired_dna_rna_ont500_crosswalk_20261104_run01/crosswalk.json", "sha256"),
               "interpretation": "Exact first-row fields only; no expression values or allele outcomes inspected."}
    (OUT / "header_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    receipt["header_summary_sha256"] = digest(OUT / "header_summary.json", "sha256")
    (OUT / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(f"RNA title matches: {len(rna & fields)}/{len(rna)}; paired: {len(paired & fields)}/{len(paired)}")


if __name__ == "__main__":
    main()
