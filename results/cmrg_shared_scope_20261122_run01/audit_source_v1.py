#!/usr/bin/env python3
"""Measure exact HG002 CMRG allele overlap inside shared benchmark masks."""

import argparse
from bisect import bisect_right
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
import datetime
import gzip
import hashlib
import json
from pathlib import Path
import re
import time
from urllib.request import urlopen

FTP = "https://ftp-trace.ncbi.nlm.nih.gov/ReferenceSamples/giab/release/AshkenazimTrio/HG002_NA24385_son/"
MIRROR = "https://giab.s3.amazonaws.com/release/AshkenazimTrio/HG002_NA24385_son/"
CMRG = "CMRG_v1.00/GRCh38/StructuralVariant/HG002_GRCh38_CMRG_SV_v1.00"
V5 = "v5.0q/HG002_GRCh38_v5.0q_stvar"
INPUTS = (
    ("cmrg_vcf", CMRG + ".vcf.gz", 262144, None),
    ("cmrg_bed", CMRG + ".bed", 262144, None),
    ("v5_vcf", V5 + ".vcf.gz", 62 * 1024 * 1024, "34dbeeac5eb3fc09e94c5cb8cfe9e24f"),
    ("v5_bed", V5 + ".benchmark.bed", 524288, "55fc11c80ff376c0a8da99d0c69004f3"),
)
A_BASES = re.compile("[ACGT]+")
AUTOSOMES = {f"chr{i}" for i in range(1, 23)}
PROTOCOL = "d1be3a8"


def get(url, limit):
    with urlopen(url, timeout=35) as response:
        data = response.read(limit + 1)
    if len(data) > limit:
        raise ValueError(f"Fixed transfer cap exceeded for {url}")
    return data


def acquire(spec, cache):
    key, relative, limit, expected_md5 = spec
    data = get(FTP + relative, limit)
    md5 = hashlib.md5(data).hexdigest()
    if expected_md5 and md5 != expected_md5:
        raise ValueError(f"Publisher MD5 mismatch for {key}")
    mirror = None
    if expected_md5 is None:
        try:
            alternate = get(MIRROR + relative, limit)
        except OSError as exc:
            mirror = {"url": MIRROR + relative, "error": str(exc)}
        else:
            if alternate != data:
                raise ValueError(f"CMRG mirror mismatch for {key}")
            mirror = {"url": MIRROR + relative, "byte_identical": True}
    path = cache / Path(relative).name
    with path.open("xb") as output:
        output.write(data)
    return key, path, {"url": FTP + relative, "bytes": len(data), "md5": md5,
                      "publisher_md5": expected_md5, "sha256": hashlib.sha256(data).hexdigest(),
                      "cmrg_mirror": mirror}


def mask(path):
    raw = defaultdict(list)
    for line in path.read_text().splitlines():
        if not line or line.startswith(("#", "track ", "browser ")):
            continue
        chrom, start, end, *_ = line.split("\t")
        start, end = int(start), int(end)
        if start < 0 or end <= start:
            raise ValueError(f"Invalid BED interval in {path.name}")
        if chrom in AUTOSOMES:
            raw[chrom].append((start, end))
    output = {}
    for chrom, bounds in raw.items():
        union = []
        for start, end in sorted(bounds):
            if union and start <= union[-1][1]:
                union[-1] = (union[-1][0], max(end, union[-1][1]))
            else:
                union.append((start, end))
        output[chrom] = ([a for a, _ in union], [b for _, b in union])
    return output


def contains(ranges, chrom, start, end):
    starts, ends = ranges.get(chrom, ((), ()))
    i = bisect_right(starts, start) - 1
    return i >= 0 and end <= ends[i]


def shared_bases(one, two):
    total = 0
    for chrom in one.keys() & two.keys():
        a, b = one[chrom], two[chrom]
        i = j = 0
        while i < len(a[0]) and j < len(b[0]):
            total += max(0, min(a[1][i], b[1][j]) - max(a[0][i], b[0][j]))
            if a[1][i] <= b[1][j]:
                i += 1
            else:
                j += 1
    return total


def classify(chrom, start, ref, alt, filt):
    if chrom not in AUTOSOMES:
        return "non_autosomal", None
    if filt != "PASS":
        return "non_pass", None
    if "," in alt:
        return "multiallelic", None
    if not all(A_BASES.fullmatch(x) for x in (ref, alt)):
        return "non_acgt", None
    if abs(len(ref) - len(alt)) <= 50:
        return "size_at_most_50", None
    prefix = 0
    shortest = min(len(ref), len(alt))
    while prefix < shortest and ref[prefix] == alt[prefix]:
        prefix += 1
    ref, alt = ref[prefix:], alt[prefix:]
    while ref and alt and ref[-1] == alt[-1]:
        ref, alt = ref[:-1], alt[:-1]
    if ref and alt:
        return "complex_after_trimming", None
    return "DEL" if ref else "INS", (chrom, start + prefix, ref, alt)


def vcf(path):
    with gzip.open(path, "rt") as data:
        for line in data:
            if line.startswith("#"):
                continue
            chrom, pos, rid, ref, alt, _, filt, _ = line.split("\t", 7)
            yield chrom, int(pos) - 1, rid, ref, alt, filt


def score(paths):
    cmrg, v5 = mask(paths["cmrg_bed"]), mask(paths["v5_bed"])
    cmrg_rows, wanted = [], set()
    for chrom, start, rid, ref, alt, filt in vcf(paths["cmrg_vcf"]):
        status, key = classify(chrom, start, ref, alt, filt)
        row = {"chrom": chrom, "pos1": start + 1, "source_id": rid, "status": status}
        if key is not None:
            row["type"] = status
            row["length"] = abs(len(ref) - len(alt))
            inside_cmrg = contains(cmrg, chrom, start, start + len(ref))
            inside_v5 = contains(v5, chrom, start, start + len(ref))
            if inside_cmrg and inside_v5:
                wanted.add(key)
                row["status"] = "shared_scope"
                row["normalized_edit_start0"] = key[1]
            elif inside_cmrg:
                row["status"] = "outside_v5_only"
            elif inside_v5:
                row["status"] = "outside_cmrg_only"
            else:
                row["status"] = "outside_both"
        cmrg_rows.append((row, key))

    counts = Counter()
    v5_shared_types = Counter()
    for chrom, start, _, ref, alt, filt in vcf(paths["v5_vcf"]):
        if not (contains(cmrg, chrom, start, start + len(ref)) and contains(v5, chrom, start, start + len(ref))):
            continue
        status, key = classify(chrom, start, ref, alt, filt)
        if key is not None:
            v5_shared_types[status] += 1
            if key in wanted:
                counts[key] += 1
    summaries = defaultdict(Counter)
    source_status = Counter(row["status"] for row, _ in cmrg_rows)
    for row, key in cmrg_rows:
        if row["status"] == "shared_scope":
            cardinality = counts[key]
            row["v5_exact_status"] = ("exact_unique" if cardinality == 1 else
                                      "exact_multiple" if cardinality > 1 else "unresolved_no_exact_match")
            row["v5_exact_rows"] = cardinality
        if key is not None:
            summary = row.get("v5_exact_status", row["status"])
            summaries[row["type"]][summary] += 1
    return {"shared_autosomal_bp": shared_bases(cmrg, v5),
            "cmrg_autosomal_mask_bp": sum(end - start for starts, ends in cmrg.values() for start, end in zip(starts, ends)),
            "cmrg_row_status_counts": dict(source_status),
            "cmrg_distinct_shared_edit_keys": len(wanted),
            "cmrg_eligible_row_status_by_type": {k: dict(v) for k, v in summaries.items()},
            "v5_eligible_rows_in_shared_scope_by_type": dict(v5_shared_types),
            "cmrg_rows": [row for row, _ in cmrg_rows]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.cache.mkdir(parents=True, exist_ok=False)
    with ThreadPoolExecutor(max_workers=4) as pool:
        sources = list(pool.map(lambda spec: acquire(spec, args.cache), INPUTS))
    start_cpu = time.process_time()
    result = score({key: path for key, path, _ in sources})
    result["receipt"] = {
        "protocol_commit": PROTOCOL,
        "scoring_cpu_seconds": round(time.process_time() - start_cpu, 3),
        "checked_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "sources": {key: metadata for key, _, metadata in sources},
        "scope": "Exact sequence and position equality with a full REF-span mask check. Unmatched alleles are unresolved.",
    }
    with args.out.open("x") as out:
        json.dump(result, out, indent=2)
        out.write("\n")
    print("Shared base pairs", result["shared_autosomal_bp"])
    print("CMRG rows", result["cmrg_eligible_row_status_by_type"])


if __name__ == "__main__":
    main()
