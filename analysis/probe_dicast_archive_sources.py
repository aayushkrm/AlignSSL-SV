#!/usr/bin/env python3
"""Read only small public dicast source members using bounded HTTP ranges."""

import datetime
import hashlib
import io
import json
import pathlib
import urllib.request
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "results/dicast_archive_metadata_20261122_run01"
CACHE = ROOT.parent / "runs/dicast-source-metadata-20261122-run01"
URL = "https://zenodo.org/records/19794240/files/02_dicast.zip?download=1"
ARCHIVE_SIZE = 1_840_467_967
PUBLISHED_MD5 = "fc93ce69b8df77e28f00770e69ab9816"
MAX_TRANSFER = 2 * 1024 * 1024
MEMBERS = (
    "02_dicast/README.md",
    "02_dicast/dicast_benchmark_hg002.sh",
    "02_dicast/configs/config.yaml",
    "02_dicast/models/dicast_DEL_metadata.json",
    "02_dicast/models/dicast_INS_metadata.json",
)


class BoundedRemote(io.RawIOBase):
    def __init__(self):
        self.pos = 0
        self.total = 0
        self.ranges = []

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, offset, whence=io.SEEK_SET):
        new = offset if whence == io.SEEK_SET else self.pos + offset if whence == io.SEEK_CUR else ARCHIVE_SIZE + offset
        if new < 0:
            raise ValueError("Negative archive offset")
        self.pos = new
        return new

    def read(self, size=-1):
        if size < 0:
            size = ARCHIVE_SIZE - self.pos
        size = min(size, max(0, ARCHIVE_SIZE - self.pos))
        if not size:
            return b""
        if self.total + size > MAX_TRANSFER:
            raise ValueError("Fixed transfer cap exceeded")
        start, end = self.pos, self.pos + size - 1
        headers = {"User-Agent": "AlignSSL-research/1.0", "Range": f"bytes={start}-{end}"}
        with urllib.request.urlopen(urllib.request.Request(URL, headers=headers), timeout=30) as response:
            expected = f"bytes {start}-{end}/{ARCHIVE_SIZE}"
            if response.status != 206 or response.headers.get("Content-Range") != expected:
                raise ValueError("Server did not honor exact bounded range")
            body = response.read(size + 1)
        if len(body) != size:
            raise ValueError("Short or oversized range response")
        self.ranges.append({"start": start, "end": end, "bytes": size})
        self.total += size
        self.pos += size
        return body


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    CACHE.mkdir(parents=True, exist_ok=False)
    remote = BoundedRemote()
    receipt = {"source": URL, "archive_size": ARCHIVE_SIZE,
               "publisher_md5_unverified": PUBLISHED_MD5,
               "max_range_transfer_bytes": MAX_TRANSFER,
               "script_sha256": hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
               "checked_utc": datetime.datetime.now(datetime.timezone.utc).isoformat()}
    try:
        with zipfile.ZipFile(remote) as archive:
            names = archive.namelist()
            receipt["archive_entry_count"] = len(names)
            receipt["vcf_named_entries"] = [n for n in names if n.lower().endswith((".vcf", ".vcf.gz", ".bcf"))]
            extracted = []
            for member in MEMBERS:
                info = archive.getinfo(member)
                if info.file_size > 131072 or info.compress_size > 131072:
                    raise ValueError("Requested member exceeds the small-source limit")
                body = archive.read(info)  # zipfile validates the member CRC.
                target = CACHE / pathlib.Path(member).name
                target.write_bytes(body)
                extracted.append({"member": member, "bytes": len(body),
                                  "sha256": hashlib.sha256(body).hexdigest(),
                                  "cache_file": target.name})
            receipt["members"] = extracted
        receipt["status"] = "ok"
    except Exception as exc:
        receipt["status"] = "failed"
        receipt["error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        receipt["range_bytes"] = remote.total
        receipt["ranges"] = remote.ranges
        (OUT / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print("Archive entries", receipt["archive_entry_count"], "VCF-named entries", len(receipt["vcf_named_entries"]),
          "small sources", len(receipt["members"]), "range bytes", receipt["range_bytes"])


if __name__ == "__main__":
    main()
