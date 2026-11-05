#!/usr/bin/env python3
"""Retrieve the public 1KGP ONT 500 metadata table and companion README."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import datetime
import hashlib
import json
from pathlib import Path
import urllib.request


BASE = "https://s3.amazonaws.com/1000g-ont/PROCESSED_DATA/"
SOURCES = {"ont500_metadata.tsv": BASE + "1kGP_LRSC_500_ONT_Metadata.tsv",
           "ont500_readme.txt": BASE + "READ_ME.txt"}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)

    def get(item):
        name, url = item
        try:
            with urllib.request.urlopen(url, timeout=25) as response:
                data = response.read(2 * 1024 * 1024 + 1)
                if response.status != 200 or len(data) > 2 * 1024 * 1024:
                    raise ValueError("metadata response status or size invalid")
                (out / name).write_bytes(data)
                return {"name": name, "url": url, "status": response.status, "bytes": len(data),
                        "sha256": hashlib.sha256(data).hexdigest(),
                        "last_modified": response.headers.get("Last-Modified")}
        except Exception as exc:
            return {"name": name, "url": url, "error": f"{type(exc).__name__}: {exc}"}

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
