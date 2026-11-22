#!/usr/bin/env python3
"""Prepare a truth-independent search territory from fixed public gene annotations."""

import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
import csv
import gzip
import hashlib
import json
from pathlib import Path
import re
from urllib.request import urlopen

GTF = "https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_46/gencode.v46.annotation.gtf.gz"
FAI = "https://storage.googleapis.com/gcp-public-data--broad-references/hg38/v0/Homo_sapiens_assembly38.fasta.fai"
OUT_PROTOCOL = "a173624"
AUTOSOMES = {f"chr{i}" for i in range(1, 23)}
PAD = 2000
ATTRIBUTE = re.compile(r'(?:^|;\s*)(gene_id|gene_name) "([^"]+)"')


def acquire(url, cache, limit, algorithm, digest):
    path = cache / url.rsplit("/", 1)[-1]
    if path.exists():
        if path.stat().st_size > limit:
            raise ValueError(f"Cached file exceeds size limit for {url}")
        data = path.read_bytes()
    else:
        with urlopen(url, timeout=45) as response:
            data = response.read(limit + 1)
    if len(data) > limit or hashlib.new(algorithm, data).hexdigest() != digest:
        raise ValueError(f"Source size or hash mismatch for {url}")
    if not path.exists():
        with path.open("xb") as stream:
            stream.write(data)
    return path, {"url": url, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                  "verified_hash": {algorithm: digest}}


def read_candidates(path, wanted, lengths):
    result = defaultdict(set)
    with gzip.open(path, "rt") as stream:
        for line in stream:
            if line.startswith("#"):
                continue
            chrom, _, kind, start, end, _, _, _, attributes = line.rstrip("\n").split("\t", 8)
            if kind != "gene" or chrom not in AUTOSOMES:
                continue
            # Avoid consuming the delimiter before the next attribute.
            attrs = dict(ATTRIBUTE.findall(attributes))
            if attrs.get("gene_name") not in wanted:
                continue
            start, end = int(start) - 1, int(end)
            if start < 0 or end <= start or end > lengths[chrom]:
                raise ValueError(f"Unexpected annotation coordinates for {attrs['gene_name']}")
            result[attrs["gene_name"]].add((attrs["gene_id"], chrom, start, end))
    return result


def union_intervals(intervals):
    merged = []
    for chrom, start, end in sorted(intervals, key=lambda a: (int(a[0][3:]), a[1], a[2])):
        if merged and chrom == merged[-1][0] and start <= merged[-1][2]:
            merged[-1] = chrom, merged[-1][1], max(end, merged[-1][2])
        else:
            merged.append((chrom, start, end))
    return merged


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--roster", type=Path, required=True)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.cache.mkdir(parents=True, exist_ok=True)
    args.out.mkdir(parents=True, exist_ok=False)
    roster_bytes = args.roster.read_bytes()
    roster_receipt = json.loads((args.roster.parent / "receipt.json").read_text())
    if hashlib.sha256(roster_bytes).hexdigest() != roster_receipt["genes_tsv_sha256"]:
        raise ValueError("Roster hash mismatch")
    roster = [row["gene"] for row in csv.DictReader(roster_bytes.decode().splitlines(), delimiter="\t")]
    if len(roster) != 395 or len(set(roster)) != len(roster):
        raise ValueError("Roster must contain 395 distinct symbols")
    with ThreadPoolExecutor(max_workers=2) as pool:
        gtf_job = pool.submit(acquire, GTF, args.cache, 64 * 1024 * 1024, "md5",
                              "68070e3c87f6a0e70af6e4ff4d55f61c")
        fai_job = pool.submit(acquire, FAI, args.cache, 512 * 1024, "sha256",
                              "edefd93c489dc1baefad312f40388089f8db5cf6dcc3ba0955669ead274e8b6b")
        gtf, gtf_receipt = gtf_job.result()
        fai, fai_receipt = fai_job.result()
    names_and_lengths = [line.split("\t", 2)[:2] for line in fai.read_text().splitlines()]
    lengths = {name: int(length) for name, length in names_and_lengths if name in AUTOSOMES}
    candidates = read_candidates(gtf, set(roster), lengths)
    rows, provisional = [], []
    for gene in roster:
        found = sorted(candidates[gene])
        status = "placed" if len(found) == 1 else "multi_match" if found else "no_match"
        rows.append({"gene": gene, "status": status, "matches": found})
        if status == "placed":
            _, chrom, start, end = found[0]
            provisional.append((chrom, max(start - PAD, 0), min(end + PAD, lengths[chrom]), gene))
    merged = union_intervals([x[:3] for x in provisional])
    for filename, values in (("matched_genes.bed", provisional), ("territory_provisional.bed", merged)):
        with (args.out / filename).open("x") as output:
            output.writelines("\t".join(map(str, row)) + "\n" for row in values)
    report = {"protocol_commit": OUT_PROTOCOL, "roster_sha256": hashlib.sha256(roster_bytes).hexdigest(),
              "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "sources": {"gencode": gtf_receipt, "reference_index": fai_receipt},
              "status_counts": dict(Counter(row["status"] for row in rows)),
              "union_intervals": len(merged), "union_bases": sum(end - start for _, start, end in merged),
              "bed_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in args.out.glob("*.bed")},
              "rows": rows, "scope": "Annotation only; exact gene-name placement. No read, truth, or variant data."}
    with (args.out / "receipt.json").open("x") as output:
        json.dump(report, output, indent=2)
        output.write("\n")
    print(report["status_counts"], "merged intervals", len(merged), "bp", report["union_bases"])


if __name__ == "__main__":
    main()
