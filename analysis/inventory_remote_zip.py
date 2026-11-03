#!/usr/bin/env python3
"""Inventory a remote ZIP central directory using bounded HTTP range reads."""

import argparse
from collections import Counter
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import urllib.request
import zipfile


class RemoteZip(io.RawIOBase):
    def __init__(self, url, max_bytes):
        super().__init__()
        self.url = url
        self.max_bytes = max_bytes
        self.used = 0
        self.pos = 0
        self.requests = []
        request = urllib.request.Request(url, method="HEAD", headers={"Accept-Encoding": "identity"})
        with urllib.request.urlopen(request, timeout=30) as response:
            self.size = int(response.headers["Content-Length"])
            self.head = {k: response.headers.get(k) for k in ("Content-Length", "ETag", "Last-Modified")}

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, offset, whence=io.SEEK_SET):
        new = offset if whence == io.SEEK_SET else self.pos + offset if whence == io.SEEK_CUR else self.size + offset
        if new < 0:
            raise ValueError("negative seek")
        self.pos = new
        return new

    def read(self, size=-1):
        if size is None or size < 0:
            size = max(0, self.size - self.pos)
        size = min(size, max(0, self.size - self.pos))
        if not size:
            return b""
        if size > self.max_bytes - self.used:
            raise ValueError("range request would exceed the transfer budget")
        start, end = self.pos, self.pos + size - 1
        request = urllib.request.Request(self.url, headers={"Range": f"bytes={start}-{end}",
                                                             "Accept-Encoding": "identity"})
        with urllib.request.urlopen(request, timeout=45) as response:
            content_range = response.headers.get("Content-Range", "")
            expected = f"bytes {start}-{end}/{self.size}"
            if response.status != 206 or content_range != expected:
                raise ValueError(f"server did not return expected partial range: {response.status}, {content_range}")
            data = response.read(size + 1)
            if len(data) != size:
                raise ValueError("partial response length mismatch")
            self.requests.append({"start": start, "end": end, "bytes": len(data),
                                  "etag": response.headers.get("ETag"),
                                  "last_modified": response.headers.get("Last-Modified")})
        self.used += size
        self.pos += size
        return data


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--url", required=True)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--max-bytes", type=int, default=8 * 1024 * 1024)
    args = p.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    stream = RemoteZip(args.url, args.max_bytes)
    with zipfile.ZipFile(stream) as archive:
        entries = []
        for entry in archive.infolist():
            entries.append({"name": entry.filename, "directory": entry.is_dir(),
                            "compressed_size": entry.compress_size, "uncompressed_size": entry.file_size,
                            "crc32": f"{entry.CRC:08x}", "compression_method": entry.compress_type,
                            "header_offset": entry.header_offset})
    data = {"url": args.url, "head": stream.head, "archive_bytes": stream.size,
            "transfer_budget": args.max_bytes, "bytes_transferred": stream.used,
            "range_requests": stream.requests, "entry_count": len(entries),
            "directory_count": sum(e["directory"] for e in entries),
            "suffix_counts": dict(Counter(Path(e["name"]).suffix.lower() for e in entries if not e["directory"])),
            "entries": entries,
            "limits": "Central-directory metadata only; no whole-archive checksum or member content was verified."}
    result = output / "inventory.json"
    result.write_text(json.dumps(data, indent=2) + "\n")
    receipt = {"python": sys.version, "script_sha256": hashlib.sha256(Path(__file__).resolve().read_bytes()).hexdigest(),
               "inventory_sha256": hashlib.sha256(result.read_bytes()).hexdigest()}
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({k: v for k, v in data.items() if k != "entries"}, indent=2))


if __name__ == "__main__":
    main()
