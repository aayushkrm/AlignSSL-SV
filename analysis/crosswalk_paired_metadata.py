#!/usr/bin/env python3
"""Join public RNA sample titles to exact DNA-manifest sample IDs."""

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path
import re
import subprocess


AUTHOR_COMMIT = "70f64b309fd3325ec518857270b78d5f4e2a80f9"
AUTHOR_FILE = "scripts/02_transcript_quantification/04_bambu_transcript_quantification.R"
DNA_FILES = ["vienna_manifest.tsv", "vienna_manifest_20240112.tsv", "vienna_manifest_20240215.tsv"]
SAMPLE = re.compile(r"^(?:HG|NA)\d{5}$")
DNA_PATH = re.compile(r"(?:^|/)(hg38|t2t|gaf)/((?:HG|NA)\d{5})\.(?:hg38\.cram|t2t\.cram|gaf\.gz)$")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_rna(path):
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def read_dna(paths):
    by_path = {}
    conflicts = []
    for path in paths:
        with path.open(newline="") as handle:
            for line_number, row in enumerate(csv.reader(handle, delimiter="\t"), 1):
                if len(row) != 3:
                    raise ValueError(f"unexpected manifest row: {path}:{line_number}")
                match = DNA_PATH.search(row[0])
                if not match:
                    continue
                value = {"path": row[0], "bytes": int(row[1]), "md5": row[2],
                         "mode": match.group(1), "sample": match.group(2)}
                if row[0] in by_path and by_path[row[0]] != value:
                    conflicts.append({"old": by_path[row[0]], "new": value})
                else:
                    by_path[row[0]] = value
    groups = defaultdict(list)
    for value in by_path.values():
        groups[value["sample"]].append(value)
    return groups, conflicts


def crosswalk(rna, dna, authors):
    runs = defaultdict(list)
    unresolved = []
    seen = set()
    for row in rna:
        run, title = row["run_accession"], row["sample_title"]
        if not run or run in seen:
            raise ValueError("missing or duplicate RNA run ID")
        seen.add(run)
        if not SAMPLE.fullmatch(title):
            unresolved.append({"run": run, "sample_title": title, "sample_alias": row["sample_alias"]})
            continue
        runs[title].append({k: row[k] for k in ["run_accession", "sample_accession", "sample_alias",
                                                "sample_title", "secondary_sample_accession", "library_strategy"]})
    rows = []
    for sample in sorted(runs):
        entries = dna.get(sample, [])
        rows.append({"sample_title": sample, "author_list_member": sample in authors,
                     "rna_runs": sorted(runs[sample], key=lambda x: x["run_accession"]),
                     "listed_dna_modes": sorted(set(x["mode"] for x in entries)),
                     "listed_dna_files": sorted(entries, key=lambda x: x["path"])})
    return {"rna_runs": len(rna), "distinct_matching_format_titles": len(runs),
            "unresolved_rna_rows": unresolved, "dna_distinct_manifest_ids": len(dna),
            "dna_matching_rna_titles": sum(bool(r["listed_dna_files"]) for r in rows),
            "rna_titles_not_in_dna_manifests": [r["sample_title"] for r in rows if not r["listed_dna_files"]],
            "rna_titles_not_in_author_list": sorted(set(runs) - authors),
            "author_list_not_in_rna_titles": sorted(authors - set(runs)),
            "dna_modes_among_rna_titles": dict(Counter(mode for r in rows for mode in r["listed_dna_modes"])),
            "rows": rows}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--metadata", type=Path, required=True)
    p.add_argument("--titles", type=Path, required=True)
    p.add_argument("--author-source", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    source_receipt = json.loads((a.metadata / "receipt.json").read_text())
    for source in source_receipt["sources"]:
        if "sha256" in source and digest(a.metadata / "sources" / source["name"]) != source["sha256"]:
            raise ValueError(f"metadata hash mismatch: {source['name']}")
    title_file = a.titles / "ena_titles.tsv"
    if digest(title_file) != json.loads((a.titles / "receipt.json").read_text())["sha256"]:
        raise ValueError("ENA title report hash mismatch")
    root = a.author_source.resolve()
    commit = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    if commit != AUTHOR_COMMIT:
        raise ValueError("unexpected author code commit")
    subprocess.run(["git", "-C", str(root), "diff", "--quiet", "HEAD", "--", AUTHOR_FILE], check=True)
    author_text = (root / AUTHOR_FILE).read_text()
    matched = re.search(r"sample_ids\s*<-\s*c\s*\((.*?)\)", author_text, re.S)
    if not matched:
        raise ValueError("author sample list not found")
    author_values = re.findall(r'"((?:HG|NA)\d{5})"', matched.group(1))
    if len(author_values) != len(set(author_values)):
        raise ValueError("duplicate sample IDs in author list")
    prior = read_rna(a.metadata / "sources" / "ena_prjeb76585_read_runs.tsv")
    titles = read_rna(title_file)
    prior_by_run = {r["run_accession"]: r for r in prior}
    if len(prior_by_run) != len(prior) or len(titles) != len(prior):
        raise ValueError("ENA report row counts or run IDs differ")
    for row in titles:
        old = prior_by_run.get(row["run_accession"])
        if not old or any(old[k] != row[k] for k in ["study_accession", "sample_accession", "sample_alias",
                                                       "secondary_sample_accession", "library_strategy"]):
            raise ValueError("ENA report fields differ between requests")
    dna, conflicts = read_dna([a.metadata / "sources" / n for n in DNA_FILES])
    result = crosswalk(titles, dna, set(author_values))
    result.update({"dna_manifest_conflicts": conflicts, "author_code_commit": commit,
                   "author_file": AUTHOR_FILE, "author_file_sha256": digest(root / AUTHOR_FILE),
                   "author_sample_ids": author_values, "ena_titles_sha256": digest(title_file),
                   "rna_run_report_sha256": digest(a.metadata / "sources" / "ena_prjeb76585_read_runs.tsv"),
                   "dna_manifest_sha256": {name: digest(a.metadata / "sources" / name) for name in DNA_FILES},
                   "limits": "Exact public metadata joins only; no reads, allele-level truth or sample identity verification."})
    out = a.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    report = out / "crosswalk.json"
    report.write_text(json.dumps(result, indent=2) + "\n")
    receipt = {"script_sha256": digest(Path(__file__).resolve()), "crosswalk_sha256": digest(report)}
    (out / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k not in ("rows", "author_sample_ids")}, indent=2))


if __name__ == "__main__":
    main()
