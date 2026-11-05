#!/usr/bin/env python3
"""Retrieve ENA sample titles needed to join the public PRJEB76585 runs."""

import argparse
import datetime
import hashlib
import json
from pathlib import Path
import urllib.parse
import urllib.request


PARAMS = {"accession": "PRJEB76585", "result": "read_run",
          "fields": "study_accession,run_accession,sample_accession,sample_alias,sample_title,sample_description,secondary_sample_accession,library_strategy",
          "format": "tsv", "limit": "0"}
URL = "https://www.ebi.ac.uk/ena/portal/api/filereport?" + urllib.parse.urlencode(PARAMS)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    request = urllib.request.Request(URL, headers={"User-Agent": "AlignSSL-SV-metadata-audit/1.0"})
    with urllib.request.urlopen(request, timeout=45) as response:
        data = response.read(2 * 1024 * 1024 + 1)
        if response.status != 200 or len(data) > 2 * 1024 * 1024:
            raise ValueError("ENA response status or metadata size invalid")
        (out / "ena_titles.tsv").write_bytes(data)
        receipt = {"url": URL, "retrieved_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                   "status": response.status, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                   "script_sha256": hashlib.sha256(Path(__file__).resolve().read_bytes()).hexdigest(),
                   "max_bytes": 2 * 1024 * 1024}
    (out / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
