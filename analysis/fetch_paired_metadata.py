#!/usr/bin/env python3
"""Retrieve small public DNA/RNA source manifests with bounded downloads."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import datetime
import hashlib
import json
from pathlib import Path
import urllib.parse
import urllib.request


BASE = "https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/1KG_ONT_VIENNA/"
ENA_PARAMS = {"accession": "PRJEB76585", "result": "read_run",
              "fields": "study_accession,run_accession,sample_accession,sample_alias,secondary_sample_accession,library_strategy",
              "format": "tsv", "limit": "0"}
SOURCES = {
    "vienna_manifest.tsv": BASE + "1KG_ONT_VIENNA_manifest.tsv",
    "vienna_manifest_20240112.tsv": BASE + "1KG_ONT_VIENNA_manifest_20240112.tsv",
    "vienna_manifest_20240215.tsv": BASE + "1KG_ONT_VIENNA_manifest_20240215.tsv",
    "vienna_reuse.md": BASE + "README_1KG_ONT_VIENNA_datareuse_statement.md",
    "ena_prjeb76585_read_runs.tsv": "https://www.ebi.ac.uk/ena/portal/api/filereport?" + urllib.parse.urlencode(ENA_PARAMS),
}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    sources = out / "sources"
    sources.mkdir()

    def get(item):
        name, url = item
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "AlignSSL-SV-metadata-audit/1.0"})
            with urllib.request.urlopen(request, timeout=45) as response:
                data = response.read(2 * 1024 * 1024 + 1)
                if len(data) > 2 * 1024 * 1024:
                    raise ValueError("response exceeded 2 MiB metadata limit")
                if response.status != 200:
                    raise ValueError(f"unexpected HTTP status {response.status}")
                (sources / name).write_bytes(data)
                return {"name": name, "url": url, "status": response.status, "bytes": len(data),
                        "sha256": hashlib.sha256(data).hexdigest(),
                        "last_modified": response.headers.get("Last-Modified"),
                        "content_type": response.headers.get("Content-Type")}
        except Exception as exc:
            return {"name": name, "url": url, "error": f"{type(exc).__name__}: {exc}"}

    with ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(get, SOURCES.items()))
    receipt = {"retrieved_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
               "script_sha256": hashlib.sha256(Path(__file__).resolve().read_bytes()).hexdigest(),
               "max_bytes_per_response": 2 * 1024 * 1024, "sources": results}
    (out / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))
    if any("error" in r for r in results):
        raise SystemExit("one or more sources failed; partial packet retained")


if __name__ == "__main__":
    main()
