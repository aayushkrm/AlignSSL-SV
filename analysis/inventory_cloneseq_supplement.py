#!/usr/bin/env python3
"""Preserve bounded ZIP directory ranges for the CloneSeq-SV supplement."""

import datetime
import hashlib
import json
import pathlib
import sys
import zipfile

from inventory_remote_zip import RemoteZip

REPO = pathlib.Path(__file__).resolve().parent.parent
OUT = REPO / "results/cloneseq_supplement_inventory_20261106_run01"
URL = "https://pmc-oa-opendata.s3.amazonaws.com/PMC12629990.1/41586_2025_9580_MOESM1_ESM.zip?md5=053c2a18cbd1da4a250efc78e49b57e7"
MAX_BYTES = 512 * 1024


def sha(data):
    return hashlib.sha256(data).hexdigest()


class RecordingRemoteZip(RemoteZip):
    def read(self, size=-1):
        count = len(self.requests)
        data = super().read(size)
        if len(self.requests) > count:
            request = self.requests[-1]
            name = f"range{len(self.requests):02d}.bin"
            (OUT / name).write_bytes(data)
            request.update({"saved_as": name, "sha256": sha(data)})
        return data


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    result = {"source_url": URL, "retrieved_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "max_body_bytes": MAX_BYTES, "script_sha256": sha(pathlib.Path(__file__).read_bytes()),
              "reader_sha256": sha((REPO / "analysis/inventory_remote_zip.py").read_bytes()),
              "publisher_archive_md5_not_verified": "053c2a18cbd1da4a250efc78e49b57e7"}
    stream = None
    try:
        stream = RecordingRemoteZip(URL, MAX_BYTES)
        with zipfile.ZipFile(stream) as archive:
            entries = [{"name": e.filename, "directory": e.is_dir(),
                        "compressed_size": e.compress_size, "uncompressed_size": e.file_size,
                        "crc32_not_verified": f"{e.CRC:08x}", "compression_method": e.compress_type,
                        "header_offset": e.header_offset} for e in archive.infolist()]
        head_etag = stream.head.get("ETag")
        response_etags = [r.get("etag") for r in stream.requests]
        result.update({"head": stream.head, "archive_bytes": stream.size,
                       "bytes_transferred": stream.used, "requests": stream.requests,
                       "etag_consistent": bool(head_etag) and all(x == head_etag for x in response_etags),
                       "entries": entries,
                       "limits": "ZIP directory only; archive MD5 and member CRCs not verified, no members opened."})
        if not result["etag_consistent"]:
            result["error"] = "Missing or inconsistent ETags; source identity not verified"
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        if stream is not None:
            result.update({"head": stream.head, "archive_bytes": stream.size,
                           "bytes_transferred": stream.used, "requests": stream.requests})
    (OUT / "inventory.json").write_text(json.dumps(result, indent=2) + "\n")
    if "error" in result:
        raise SystemExit(result["error"])
    print("Entries", len(result["entries"]), "range bytes", result["bytes_transferred"],
          "archive bytes", result["archive_bytes"], "ETag consistent", result["etag_consistent"])


if __name__ == "__main__":
    main()
