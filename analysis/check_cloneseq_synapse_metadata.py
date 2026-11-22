#!/usr/bin/env python3
"""Record anonymous metadata and download-URL status, without downloading data."""

import datetime
import hashlib
import json
import pathlib
import urllib.error
import urllib.request

REPO = pathlib.Path(__file__).resolve().parent.parent
OUT = REPO / "results/cloneseq_synapse_metadata_20261122_run01"
BASE = "https://repo-prod.prod.sagebase.org"
CHILDREN = {"parentId": "syn66399325", "includeTypes": ["file", "folder"],
            "limit": 50, "sortBy": "NAME", "sortDirection": "ASC"}
REQUESTS = [
    ("project", "GET", "/repo/v1/entity/syn66399325", None),
    ("children", "POST", "/repo/v1/entity/children", CHILDREN),
    ("archive_entity", "GET", "/repo/v1/entity/syn68823979", None),
    ("archive_filehandles", "GET", "/repo/v1/entity/syn68823979/filehandles", None),
    ("archive_download_reference", "GET", "/file/v1/file/161011949?redirect=false&fileAssociateType=FileEntity&fileAssociateId=syn68823979", None),
]
LIMIT = 128 * 1024


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    rows = []
    for name, method, path, payload in REQUESTS:
        data = json.dumps(payload).encode() if payload is not None else None
        request = urllib.request.Request(BASE + path, data=data, method=method,
                                         headers={"Content-Type": "application/json", "Accept": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                status, body = response.status, response.read(LIMIT + 1)
        except urllib.error.HTTPError as exc:
            status, body = exc.code, exc.read(LIMIT + 1)
        if len(body) > LIMIT:
            raise ValueError("Response exceeded the fixed metadata limit")
        row = {"name": name, "method": method, "url": BASE + path,
               "request_json": payload, "status": status, "bytes": len(body),
               "sha256": hashlib.sha256(body).hexdigest()}
        if name == "archive_download_reference" and 200 <= status < 400:
            # A successful URL may contain signed credentials. Never save or print it.
            row["response"] = "successful download reference redacted; no file fetched"
        else:
            filename = name + ".json"
            (OUT / filename).write_bytes(body)
            row["saved_as"] = filename
        rows.append(row)
    result = {"checked_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "anonymous": True, "max_response_bytes": LIMIT,
              "script_sha256": hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
              "requests": rows, "limits": "Anonymous metadata and download-reference check only; no file contents or access applications."}
    (OUT / "receipt.json").write_text(json.dumps(result, indent=2) + "\n")
    print("Anonymous response statuses:", ", ".join(f"{x['name']}={x['status']}" for x in rows))


if __name__ == "__main__":
    main()
