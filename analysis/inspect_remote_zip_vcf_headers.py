#!/usr/bin/env python3
"""Read only selected VCF headers from stored gzip members of a remote ZIP."""

import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import struct
import sys

from analysis.inventory_remote_zip import RemoteZip


SELECTED = [
    "1100VCF/ONT_HG00096_minimap2_sniffles2_HG00096.vcf.gz",
    "1100VCF/CCS_HG00512_minimap2_sniffles2_HG00512.vcf.gz",
    "1100VCF/CCS_NA12878_minimap2_delly_NA12878.vcf.gz",
    "1100VCF/ONT_HG002_minimap2_svision_HG002.vcf.gz",
]


def inspect(stream, entry, prefix_limit):
    if entry["compression_method"] != 0:
        raise ValueError("outer ZIP member is not stored")
    stream.seek(entry["header_offset"])
    local = stream.read(30)
    values = struct.unpack("<IHHHHHIIIHH", local)
    signature, flags, method = values[0], values[2], values[3]
    name_len, extra_len = values[-2:]
    if signature != 0x04034B50 or flags & 1 or method != 0:
        raise ValueError("unexpected ZIP local header")
    name_and_extra = stream.read(name_len + extra_len)
    name = name_and_extra[:name_len].decode("utf-8")
    if name != entry["name"]:
        raise ValueError("local and central ZIP names differ")
    offset = entry["header_offset"] + 30 + name_len + extra_len
    stream.seek(offset)
    prefix = stream.read(min(prefix_limit, entry["compressed_size"]))
    selected = []
    header_bytes = 0
    header_hash = hashlib.sha256()
    contigs = 0
    complete = False
    with gzip.GzipFile(fileobj=io.BytesIO(prefix)) as gz:
        while header_bytes < 8 * 1024 * 1024:
            line = gz.readline(1024 * 1024 + 1)
            if not line or len(line) > 1024 * 1024 or not line.startswith(b"#"):
                break
            header_bytes += len(line)
            header_hash.update(line)
            if line.startswith(b"##contig=<"):
                contigs += 1
            if line.startswith((b"##fileformat=", b"##source=", b"##reference=", b"##SnpEff",
                                b"##INFO=<ID=ANN,", b"##ALT=<ID=BND", b"#CHROM\t")):
                selected.append(line.decode("utf-8", errors="replace").rstrip("\r\n"))
            if line.startswith(b"#CHROM\t"):
                complete = True
                break
    return {"name": name, "member_offset": offset, "prefix_bytes": len(prefix),
            "prefix_sha256": hashlib.sha256(prefix).hexdigest(), "header_complete": complete,
            "header_bytes": header_bytes, "header_sha256": header_hash.hexdigest(),
            "contig_declarations": contigs, "selected_header_lines": selected,
            "has_snpeff_header": any(line.startswith("##SnpEff") for line in selected),
            "has_ann_info_header": any(line.startswith("##INFO=<ID=ANN,") for line in selected),
            "member_crc_verified": False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--inventory", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    inventory_bytes = args.inventory.read_bytes()
    inventory = json.loads(inventory_bytes)
    by_name = {e["name"]: e for e in inventory["entries"]}
    if any(name not in by_name for name in SELECTED):
        raise ValueError("selected member missing from the frozen inventory")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    stream = RemoteZip(inventory["url"], 8 * 1024 * 1024)
    if stream.size != inventory["archive_bytes"] or stream.head["Last-Modified"] != inventory["head"]["Last-Modified"]:
        raise ValueError("remote archive metadata differs from the inventory")
    results = []
    for name in SELECTED:
        try:
            results.append(inspect(stream, by_name[name], 256 * 1024))
        except (OSError, EOFError, ValueError, struct.error) as exc:
            results.append({"name": name, "header_complete": False, "error": f"{type(exc).__name__}: {exc}"})
    data = {"inventory_sha256": hashlib.sha256(inventory_bytes).hexdigest(), "head": stream.head,
            "bytes_transferred": stream.used, "range_requests": stream.requests,
            "prefix_limit_per_member": 256 * 1024, "results": results,
            "limits": "Selected prefixes and headers only; full member CRCs and archive MD5 were not verified."}
    report = output / "headers.json"
    report.write_text(json.dumps(data, indent=2) + "\n")
    receipt = {"python": sys.version, "script_sha256": hashlib.sha256(Path(__file__).resolve().read_bytes()).hexdigest(),
               "headers_sha256": hashlib.sha256(report.read_bytes()).hexdigest()}
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(data, indent=2))
    if any(not row["header_complete"] for row in results):
        raise SystemExit("one or more headers were incomplete; results retained")


if __name__ == "__main__":
    main()
