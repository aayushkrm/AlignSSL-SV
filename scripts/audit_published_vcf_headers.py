"""Verify small published VCF blobs and record input headers without scoring calls."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
import urllib.request
from pathlib import Path


CONTIG_ID = re.compile(r"(?:<|,)ID=([^,>]+)")
CONTIG_LENGTH = re.compile(r"(?:^|,)length=([0-9]+)", re.IGNORECASE)
CONTIG_M5 = re.compile(r"(?:^|,)M5=([^,>]+)", re.IGNORECASE)


def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def inspect_vcf(data: bytes, compressed: bool) -> dict:
    if compressed:
        data = gzip.decompress(data)
    references = []
    sources = []
    contigs = []
    sample_names = None
    for raw_line in data.splitlines():
        if not raw_line.startswith(b"#"):
            break
        line = raw_line.decode("utf-8", "replace")
        if line.startswith("##reference="):
            references.append(line.partition("=")[2])
        elif line.startswith("##source="):
            sources.append(line.partition("=")[2])
        elif line.startswith("##contig=<"):
            identifier = CONTIG_ID.search(line)
            length = CONTIG_LENGTH.search(line)
            m5 = CONTIG_M5.search(line)
            contigs.append({
                "id": identifier.group(1) if identifier else None,
                "length": int(length.group(1)) if length else None,
                "m5": m5.group(1) if m5 else None,
            })
        elif line.startswith("#CHROM\t"):
            fields = line.split("\t")
            sample_names = fields[9:]
            break
    if sample_names is None:
        raise ValueError("VCF lacks #CHROM header")
    return {
        "references": references,
        "sources": sources,
        "contigs": contigs,
        "sample_names": sample_names,
        "has_sequence_m5_for_all_contigs": bool(contigs) and all(c["m5"] for c in contigs),
    }


def audit(manifest: dict) -> dict:
    base_url = manifest["base_url"]
    if not base_url.startswith("https://raw.githubusercontent.com/") or not base_url.endswith("/"):
        raise ValueError("Expected pinned GitHub raw HTTPS base URL")
    results = []
    for item in manifest["files"]:
        name = item["name"]
        if "/" in name or ".." in name or not name.endswith((".vcf", ".vcf.gz")):
            raise ValueError(f"Unsafe or unexpected VCF filename: {name}")
        url = base_url + name
        expected_size = int(item["bytes"])
        if not 0 < expected_size <= 20_000_000:
            raise ValueError(f"Out-of-bounds expected size for {name}")
        with urllib.request.urlopen(url, timeout=30) as response:
            if response.status != 200 or response.geturl() != url:
                raise ValueError(f"Unexpected HTTP response for {name}")
            data = response.read(expected_size + 1)
        if len(data) != expected_size:
            raise ValueError(f"Byte length differs for {name}: {len(data)}")
        oid = git_blob_sha1(data)
        if oid != item["git_blob_sha1"]:
            raise ValueError(f"Git blob OID differs for {name}: {oid}")
        header = inspect_vcf(data, name.endswith(".gz"))
        results.append({"name": name, "url": url, "bytes": len(data),
                        "git_blob_sha1": oid, "sha256": hashlib.sha256(data).hexdigest(),
                        **header})
    return {
        "purpose": "Input provenance only; no variant records scored or raw VCFs saved",
        "files": results,
        "file_count": len(results),
        "total_bytes": sum(item["bytes"] for item in results),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error(f"Refusing to overwrite: {args.out}")
    manifest = json.loads(args.manifest.read_text())
    report = audit(manifest)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(f"Verified {report['file_count']} VCF blobs ({report['total_bytes']} bytes); "
          "headers recorded, no variants scored")


if __name__ == "__main__":
    main()
