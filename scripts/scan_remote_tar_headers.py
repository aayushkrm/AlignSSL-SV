"""Inventory a frozen HTTP TAR using only 512-byte Range header requests.

The HGSVC3 working archives are ~12 GB each. This scanner intentionally never
downloads member payloads. It cannot verify a whole-archive MD5 from headers;
the official manifest length and stable ETag are weaker provenance checks.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.request
from collections import Counter
from pathlib import Path


BASE = "https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/HGSVC3/working/20240307_PAV_VCF"
ARCHIVES = {
    "hg38": ("20240307_PAV_VCF_hg38_mm2.tar", 12630108160, "c4d379205f4fb3162de89a09abb12dca"),
    "hs1": ("20240307_PAV_VCF_hs1_mm2.tar", 12857282560, "167bb858385c36e64d27ab68ef4472cb"),
}
BLOCK = 512
CONTENT_RANGE = re.compile(r"bytes (\d+)-(\d+)/(\d+)")


def _head(url: str, expected_size: int) -> tuple[str, str]:
    request = urllib.request.Request(url, method="HEAD")
    with urllib.request.urlopen(request, timeout=30) as response:
        if response.status != 200 or response.geturl() != url:
            raise ValueError(f"HEAD did not return the exact archive URL: {response.status}")
        length = int(response.headers.get("Content-Length", "-1"))
        if length != expected_size:
            raise ValueError(f"Archive length {length} differs from official manifest {expected_size}")
        if response.headers.get("Accept-Ranges", "").lower() != "bytes":
            raise ValueError("Archive does not advertise byte ranges")
        etag = response.headers.get("ETag", "")
        if not etag or etag.startswith("W/"):
            raise ValueError("A stable strong ETag is required for the member walk")
        return etag, response.headers.get("Last-Modified", "")


def _range(url: str, offset: int, archive_size: int, etag: str) -> bytes:
    end = offset + BLOCK - 1
    request = urllib.request.Request(
        url, headers={"Range": f"bytes={offset}-{end}", "If-Range": etag}
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        if response.status != 206 or response.geturl() != url:
            raise ValueError(f"Server did not honor Range at {offset}: {response.status}")
        if response.headers.get("ETag") != etag:
            raise ValueError(f"ETag changed during scan at {offset}")
        match = CONTENT_RANGE.fullmatch(response.headers.get("Content-Range", ""))
        if not match or tuple(map(int, match.groups())) != (offset, end, archive_size):
            raise ValueError(f"Incorrect Content-Range at {offset}")
        if int(response.headers.get("Content-Length", "-1")) != BLOCK:
            raise ValueError(f"Incorrect response length at {offset}")
        block = response.read(BLOCK + 1)
        if len(block) != BLOCK:
            raise ValueError(f"Short or excessive header response at {offset}")
        return block


def _octal(raw: bytes, field: str) -> int:
    value = raw.strip(b"\x00 ")
    if not value or not re.fullmatch(rb"[0-7]+", value):
        raise ValueError(f"Invalid TAR {field} octal field")
    return int(value, 8)


def _name(raw: bytes) -> str:
    return raw.split(b"\x00", 1)[0].decode("utf-8", "surrogateescape")


def parse_header(block: bytes, offset: int) -> dict[str, object]:
    if len(block) != BLOCK or block == bytes(BLOCK):
        raise ValueError(f"Missing TAR header at {offset}")
    stored = _octal(block[148:156], "checksum")
    unsigned = sum(block[:148]) + 8 * ord(" ") + sum(block[156:])
    if stored != unsigned:
        raise ValueError(f"TAR checksum mismatch at {offset}: {stored} != {unsigned}")
    name = _name(block[:100])
    if block[257:262] == b"ustar":
        prefix = _name(block[345:500])
        if prefix:
            name = f"{prefix}/{name}"
    if not name:
        raise ValueError(f"Empty TAR member name at {offset}")
    size = _octal(block[124:136], "size")
    kind = chr(block[156]) if block[156] else "0"
    if kind in ("x", "g", "L", "K"):
        raise ValueError(f"Extended-name metadata at {offset}; payload-free inventory cannot resolve names")
    if kind not in ("0", "5", "1", "2"):
        raise ValueError(f"Unsupported TAR member type {kind!r} at {offset}")
    lower = name.lower()
    return {
        "header_offset": offset,
        "name": name,
        "size": size,
        "type": kind,
        "is_bed": lower.endswith((".bed", ".bed.gz", ".bed.bgz")),
        "contains_callable": "callable" in lower,
    }


def walk_headers(fetch, archive_size: int, max_members: int = 10000) -> tuple[list[dict[str, object]], int]:
    """Walk standard TAR headers; fetch must return exactly one 512-byte block."""
    members: list[dict[str, object]] = []
    offset = 0
    requests = 0
    while len(members) < max_members:
        if offset + BLOCK > archive_size:
            raise ValueError("Reached archive boundary before TAR end markers")
        block = fetch(offset)
        requests += 1
        if block == bytes(BLOCK):
            if offset + 2 * BLOCK > archive_size or fetch(offset + BLOCK) != bytes(BLOCK):
                raise ValueError("TAR has no second zero end marker")
            return members, requests + 1
        member = parse_header(block, offset)
        members.append(member)
        payload_blocks = (int(member["size"]) + BLOCK - 1) // BLOCK
        offset += (1 + payload_blocks) * BLOCK
    raise ValueError(f"Exceeded configured maximum of {max_members} TAR members")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", choices=sorted(ARCHIVES), required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.out_dir.exists():
        parser.error(f"Refusing to overwrite existing output directory: {args.out_dir}")
    filename, expected_size, official_md5 = ARCHIVES[args.archive]
    url = f"{BASE}/{filename}"
    etag, last_modified = _head(url, expected_size)
    members, requests = walk_headers(
        lambda offset: _range(url, offset, expected_size, etag), expected_size
    )
    kinds = Counter(str(member["type"]) for member in members)
    suffixes = Counter(
        ".vcf.gz" if str(member["name"]).lower().endswith(".vcf.gz")
        else ".tbi" if str(member["name"]).lower().endswith(".tbi")
        else "other" for member in members
    )
    summary = {
        "archive": filename,
        "url": url,
        "official_manifest_size": expected_size,
        "official_manifest_md5": official_md5,
        "whole_archive_md5_verified": False,
        "etag": etag,
        "last_modified": last_modified,
        "member_count": len(members),
        "member_type_counts": dict(sorted(kinds.items())),
        "suffix_counts": dict(sorted(suffixes.items())),
        "bed_members": [member["name"] for member in members if member["is_bed"]],
        "callable_name_members": [member["name"] for member in members if member["contains_callable"]],
        "range_requests": requests,
        "tar_header_bytes_requested": requests * BLOCK,
        "member_payload_bytes_requested": 0,
        "interpretation": "Header-only inventory of this archive, not a donor-callability assessment",
    }
    members_data = "".join(json.dumps(member, sort_keys=True) + "\n" for member in members).encode()
    summary_data = (json.dumps(summary, indent=2, sort_keys=True) + "\n").encode()
    args.out_dir.mkdir(parents=True, exist_ok=False)
    (args.out_dir / "members.jsonl").write_bytes(members_data)
    (args.out_dir / "summary.json").write_bytes(summary_data)
    (args.out_dir / "SHA256SUMS").write_text(
        f"{_sha256(members_data)}  members.jsonl\n{_sha256(summary_data)}  summary.json\n"
    )
    print(f"{filename}: {len(members)} members, {requests} header requests, "
          f"{len(summary['bed_members'])} BEDs, {len(summary['callable_name_members'])} callable names")


if __name__ == "__main__":
    main()
