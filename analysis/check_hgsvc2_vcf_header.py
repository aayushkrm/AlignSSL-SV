#!/usr/bin/env python3
"""Decode only a bounded HGSVC2 VCF header, retaining no records in Git."""

import collections
import datetime
import gzip
import hashlib
import io
import json
import pathlib
import shlex
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
OUT = REPO / "results/hgsvc2_vcf_header_20261106_run01"
RUN = REPO.parent / "runs/hgsvc2_vcf_header_20261106_run01"
CROSSWALK = REPO / "results/hgsvc2_sample_lists_20261106_run01/crosswalk.json"
CLUSTER = REPO.parent / "tools/cluster.sh"
URL = "https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/HGSVC2/release/v1.0/PanGenie_results/pangenie_merged_bi_nosnvs.vcf.gz"
TOTAL = 1753712867
LIMITS = (262144, 1048576)
HEADER_LIMIT = 8 * 1024 * 1024

# This runs locally or through SSH. It never reads a body for an HTTP 200.
FETCH = r'''
import json, re, sys, urllib.request
url, limit, expected_total = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
req = urllib.request.Request(url, headers={"Range": f"bytes=0-{limit-1}", "Accept-Encoding": "identity", "User-Agent": "AlignSSL-SV-metadata-check/1"})
with urllib.request.urlopen(req, timeout=25) as response:
    info = {"status": response.status, "content_range": response.headers.get("Content-Range"), "content_length": response.headers.get("Content-Length"), "etag": response.headers.get("ETag"), "last_modified": response.headers.get("Last-Modified")}
    print(json.dumps(info), file=sys.stderr, flush=True)
    m = re.fullmatch(r"bytes 0-(\d+)/(\d+)", info["content_range"] or "")
    if response.status != 206 or not m or int(m.group(1)) != limit-1 or int(m.group(2)) != expected_total:
        raise ValueError("HTTP range or source length mismatch; no response body read")
    body = response.read(limit + 1)
    if len(body) != limit:
        raise ValueError(f"Unexpected prefix byte count: {len(body)}")
    sys.stdout.buffer.write(body)
'''


def sha(data):
    return hashlib.sha256(data).hexdigest()


def extract_header(prefix):
    total = 0
    try:
        with gzip.GzipFile(fileobj=io.BytesIO(prefix), mode="rb") as stream:
            while total <= HEADER_LIMIT:
                line = stream.readline(HEADER_LIMIT + 1)
                total += len(line)
                if not line:
                    return None
                if line.startswith(b"#CHROM\t"):
                    if not line.endswith(b"\n") or total > HEADER_LIMIT:
                        return None
                    return line.decode("utf-8").rstrip("\r\n").split("\t")
                if not line.startswith(b"#"):
                    raise ValueError("VCF header ended before #CHROM")
    except (EOFError, gzip.BadGzipFile):
        return None
    return None


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    RUN.mkdir(parents=True, exist_ok=False)
    old = json.loads(CROSSWALK.read_text())
    receipt = {"url": URL, "declared_size": TOTAL,
               "declared_md5_not_verified": "003c94d1249b946f2276787dfad93e99",
               "crosswalk_sha256": sha(CROSSWALK.read_bytes()),
               "script_sha256": sha(pathlib.Path(__file__).read_bytes()),
               "attempts": []}
    columns = None
    for limit in LIMITS:
        for route in ("local", "cluster"):
            fetch_args = ["python3", "-c", FETCH, URL, str(limit), str(TOTAL)]
            command = ([sys.executable] + fetch_args[1:] if route == "local"
                       else [str(CLUSTER), shlex.join(fetch_args)])
            number = len(receipt["attempts"]) + 1
            try:
                proc = subprocess.run(command, capture_output=True, timeout=60, check=False)
                body, stderr, code = proc.stdout, proc.stderr, proc.returncode
            except subprocess.TimeoutExpired as exc:
                body, stderr, code = exc.stdout or b"", exc.stderr or b"", None
            prefix_path = RUN / f"attempt{number:02d}.prefix"
            prefix_path.write_bytes(body)
            (OUT / f"attempt{number:02d}.stderr.txt").write_bytes(stderr)
            attempt = {"route": route, "limit_bytes": limit, "exit_code": code,
                       "retrieved_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                       "prefix_bytes": len(body), "prefix_sha256": sha(body),
                       "prefix_path": str(prefix_path), "stderr_sha256": sha(stderr)}
            receipt["attempts"].append(attempt)
            if code == 0 and len(body) == limit:
                try:
                    columns = extract_header(body)
                except (ValueError, UnicodeError) as exc:
                    attempt["header_error"] = str(exc)
                if columns is not None:
                    attempt["header_decoded"] = True
                    break
                attempt["header_decoded"] = False
                # More bytes, not a duplicate request through another route.
                break
        if columns is not None:
            break
    (OUT / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    if columns is None:
        raise SystemExit("VCF header unavailable within the fixed range limits")
    if len(columns) < 9 or columns[:9] != ["#CHROM", "POS", "ID", "REF", "ALT", "QUAL", "FILTER", "INFO", "FORMAT"]:
        raise ValueError("Unexpected VCF header columns")
    samples = columns[9:]
    counts = collections.Counter(samples)
    rows = []
    for row in old["rows"]:
        title = row["rna_title"]
        exact = [title] if title in counts else []
        mapped = sorted({x["full_row"] for x in row["pangenie_list_rows"] if x["full_row"] in counts})
        hits = sorted(set(exact + mapped))
        rows.append({"rna_title": title, "exact_column": exact, "full_list_row_column": mapped,
                     "matched_columns": hits, "unambiguous": len(hits) == 1 and counts[hits[0]] == 1 if hits else False,
                     "prior_long_read_metadata_match": row["prior_long_read_metadata_match"]})
    result = {"vcf_sample_column_count": len(samples), "vcf_sample_columns": samples,
              "duplicate_columns": {k: v for k, v in counts.items() if v > 1},
              "rna_title_count": len(rows),
              "unambiguous_rna_title_matches": sum(r["unambiguous"] for r in rows),
              "ambiguous_or_unmatched_rna_titles": [r["rna_title"] for r in rows if not r["unambiguous"]],
              "rows": rows, "limit": "Header membership only; no VCF records or genotypes inspected."}
    data = (json.dumps(result, indent=2) + "\n").encode()
    (OUT / "header_summary.json").write_bytes(data)
    receipt["header_summary_sha256"] = sha(data)
    (OUT / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print("VCF samples", len(samples), "unambiguous RNA matches", result["unambiguous_rna_title_matches"])


if __name__ == "__main__":
    main()
