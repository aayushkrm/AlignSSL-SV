#!/usr/bin/env python3
"""Record the reference dictionaries of two public HG002 BAM headers."""

import argparse
import datetime
import hashlib
import json
import pathlib
import struct
import urllib.request
import zlib

GCS = "https://storage.googleapis.com/"
OLD = "deepvariant/performance-testdata/HG002_NIST_150bp_downsampled_30x.bam"
NOVA = ("brain-genomics-public/research/sequencing/grch38/bam/novaseq/"
        "wgs_pcr_free/30x/HG002.novaseq.pcr-free.30x.dedup.grch38.bam")
OBJECTS = (
    ("deepvariant_legacy", OLD, "1511805283906087", 71929103696),
    ("novaseq_grch38", NOVA, "1607665356367383", 43667905004),
)
SIZE = 256 * 1024


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def read_prefix(key, version, object_size):
    url = f"{GCS}{key}?generation={version}"
    last = SIZE - 1
    request = urllib.request.Request(url, headers={"Range": f"bytes=0-{last}"})
    with urllib.request.urlopen(request, timeout=25) as response:
        if response.status != 206 or response.headers.get("Content-Range") != f"bytes 0-{last}/{object_size}":
            raise ValueError(f"Exact bounded range unavailable for {key}")
        data = response.read(SIZE + 1)
    if len(data) != SIZE:
        raise ValueError(f"Wrong response length for {key}")
    return url, data


def decode_text_header(raw):
    # BGZF blocks have a BC extra field containing the total block size minus one.
    start = 0
    decoded = bytearray()
    while start + 18 <= len(raw):
        if raw[start:start + 4] != b"\x1f\x8b\x08\x04" or raw[start + 12:start + 16] != b"BC\x02\x00":
            raise ValueError("Unexpected BGZF block header")
        block_size = struct.unpack_from("<H", raw, start + 16)[0] + 1
        end = start + block_size
        if end > len(raw):
            break
        decoded.extend(zlib.decompress(raw[start:end], 31))
        start = end
        if len(decoded) < 8:
            continue
        if decoded[:4] != b"BAM\x01":
            raise ValueError("Missing BAM signature")
        text_len = struct.unpack_from("<i", decoded, 4)[0]
        if text_len <= 0:
            raise ValueError("Invalid BAM text-header length")
        if len(decoded) >= 8 + text_len:
            return bytes(decoded[8:8 + text_len])
    raise ValueError("Complete text header unavailable in fixed range")


def summarize(header):
    contigs, samples, programs, order = [], [], [], None
    for line in header.decode("utf-8").splitlines():
        tag, *fields = line.split("\t")
        if tag not in ("@SQ", "@RG", "@PG", "@HD"):
            continue
        values = dict(field.split(":", 1) for field in fields if ":" in field)
        if tag == "@SQ":
            contigs.append([values["SN"], int(values["LN"]), values.get("M5")])
        elif tag == "@RG":
            samples.append({"sample": values.get("SM"), "platform": values.get("PL")})
        elif tag == "@PG":
            programs.append({name: values.get(name) for name in ("PN", "VN")})
        elif tag == "@HD":
            order = values.get("SO")
    if len({contig[0] for contig in contigs}) != len(contigs):
        raise ValueError("Duplicate reference contig names")
    return {"sort_order": order, "read_groups": samples, "programs": programs,
            "contigs": len(contigs), "contigs_with_md5": sum(c[2] is not None for c in contigs),
            "contig_name_length_sha256": sha256(json.dumps([c[:2] for c in contigs], separators=(",", ":")).encode()),
            "chromosome_examples": {c[0]: c[1] for c in contigs if c[0] in {"chr1", "1", "chr22", "22"}}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipt", type=pathlib.Path)
    args = parser.parse_args()
    results = {}
    for name, key, version, object_size in OBJECTS:
        url, raw = read_prefix(key, version, object_size)
        header = decode_text_header(raw)
        results[name] = {"url": url, "object_bytes": object_size,
                         "range_bytes": len(raw), "range_sha256": sha256(raw),
                         "header_bytes": len(header), "header_sha256": sha256(header),
                         **summarize(header)}
    receipt = {"checked_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
               "script_sha256": sha256(pathlib.Path(__file__).read_bytes()), "objects": results,
               "scope": "BAM text headers only. No alignment records decoded or retained."}
    with args.receipt.open("x") as f:
        json.dump(receipt, f, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()
