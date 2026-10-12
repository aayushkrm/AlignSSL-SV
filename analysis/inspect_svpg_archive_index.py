"""Bounded, read-only ZIP directory access; no whole archive checksum claim."""

import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import urllib.request
import zipfile


class RangeReader(io.RawIOBase):
    def __init__(self, url, total_bytes, request_cap=4 * 1024**2, transfer_cap=16 * 1024**2):
        self.url, self.total = url, total_bytes
        self.request_cap, self.transfer_cap = request_cap, transfer_cap
        self.position, self.transferred = 0, 0
        self.receipts = []
        self.last_modified = None

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.position

    def seek(self, offset, whence=0):
        base = {0: 0, 1: self.position, 2: self.total}[whence]
        position = base + offset
        if position < 0 or position > self.total:
            raise ValueError("Seek outside declared archive")
        self.position = position
        return position

    def read(self, size=-1):
        size = self.total - self.position if size < 0 else min(size, self.total - self.position)
        if size == 0:
            return b""
        # Reserve the extra byte used to detect a malformed overlong response.
        # Never read that probe beyond the cumulative body-byte budget.
        if size > self.request_cap or self.transferred + size + 1 > self.transfer_cap:
            raise ValueError("Range request or cumulative transfer/probe exceeds cap")
        start, end = self.position, self.position + size - 1
        request = urllib.request.Request(self.url, headers={
            "Range": f"bytes={start}-{end}", "Accept-Encoding": "identity"
        })
        with urllib.request.urlopen(request, timeout=25) as response:
            expected = f"bytes {start}-{end}/{self.total}"
            if response.status != 206 or response.headers.get("Content-Range") != expected:
                raise ValueError("Server did not honor exact bounded range; body not read")
            if response.headers.get("Content-Encoding", "identity") != "identity":
                raise ValueError("Unexpected response content encoding")
            modified = response.headers.get("Last-Modified")
            if self.receipts and modified != self.last_modified:
                raise ValueError("Remote Last-Modified changed between ranges")
            if not self.receipts:
                self.last_modified = modified
            body = response.read(size + 1)
            self.transferred += len(body)
            if len(body) != size:
                raise ValueError("Wrong response body size")
        self.position += size
        self.receipts.append({"start": start, "end": end, "bytes": len(body),
                              "sha256": hashlib.sha256(body).hexdigest()})
        return body


def inspect_index(url, size):
    reader = RangeReader(url, size)
    with zipfile.ZipFile(reader) as archive:
        entries = [{"name": entry.filename, "uncompressed_bytes": entry.file_size,
                    "compressed_bytes": entry.compress_size, "local_header_offset": entry.header_offset,
                    "compression_method": entry.compress_type, "crc32": f"{entry.CRC:08x}"}
                   for entry in archive.infolist() if not entry.is_dir()]
    return {"schema": 1, "scope": "ZIP_DIRECTORY_ONLY", "url": url,
            "declared_archive_bytes": size, "transferred_range_bytes": reader.transferred,
            "last_modified": reader.last_modified, "range_receipts": reader.receipts,
            "file_entries": len(entries), "entries": entries,
            "whole_archive_checksum_verified": False, "member_bodies_read": 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    parser.add_argument("--total-bytes", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.total_bytes <= 0:
        raise ValueError("Positive declared archive size required")
    result = inspect_index(args.url, args.total_bytes)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, allow_nan=False)
        handle.write("\n")
    selected = [entry for entry in result["entries"]
                if re.search(r"HG008|COLO829|somatic|cancer", entry["name"], re.IGNORECASE)]
    print(json.dumps({"file_entries": result["file_entries"],
                      "transferred_range_bytes": result["transferred_range_bytes"],
                      "selected_name_metadata": selected}, indent=2))


if __name__ == "__main__":
    main()
