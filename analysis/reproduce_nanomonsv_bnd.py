#!/usr/bin/env python3
"""Run two pinned, unmodified nanomonsv converters on a tiny synthetic fixture."""

import argparse
import csv
import hashlib
import itertools
import json
import platform
import re
import subprocess
import sys
import types
from collections import Counter
from pathlib import Path

import pysam


COMMITS = {
    "v0.7.1": "88cb30538c3e9004f317caec27dbc953b4c788f5",
    "upstream_fix": "04da795fa71adf495e50c857099ebf3a6ef6f64a",
}
BOOTSTRAP = """\
import importlib, sys, types
from pathlib import Path
root, source, output, reference = sys.argv[1:]
package = types.ModuleType('nanomonsv')
package.__path__ = [str(Path(root) / 'nanomonsv')]
sys.modules['nanomonsv'] = package
module = importlib.import_module('nanomonsv.vcf_convert')
print('converter_version=' + module.__version__)
module.genomesv2vcf_convert(source, output, reference)
"""


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checked_checkout(root, expected):
    head = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    if head != expected:
        raise ValueError(f"{root} is at {head}, expected {expected}")
    files = ["nanomonsv/vcf_convert.py", "nanomonsv/my_seq.py", "nanomonsv/version.py"]
    subprocess.run(["git", "-C", str(root), "diff", "--quiet", "HEAD", "--", *files], check=True)
    return {"path": str(root), "commit": head, "source_sha256": {f: sha(root / f) for f in files}}


def local_sequence(alt):
    match = re.fullmatch(r"([ACGT]+)([\[\]])([^:\[\]]+):(\d+)\2|([\[\]])([^:\[\]]+):(\d+)\5([ACGT]+)", alt)
    if not match:
        raise ValueError(f"Unsupported synthetic ALT: {alt}")
    return ("left", match.group(1)) if match.group(1) else ("right", match.group(8))


def read_records(path):
    records = {}
    for line in path.read_text().splitlines():
        if line.startswith("#"):
            continue
        fields = line.split("\t")
        chrom, pos, name, ref, alt = fields[:5]
        if name in records:
            raise ValueError(f"Duplicate ID {name}")
        side, seq = local_sequence(alt)
        anchor = seq[0] if side == "left" else seq[-1]
        records[name] = {"chrom": chrom, "pos": int(pos), "ref": ref, "alt": alt,
                         "local_sequence": seq, "local_anchor": anchor, "side": side}
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old-source", type=Path, required=True)
    parser.add_argument("--fixed-source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    sources = {"v0.7.1": args.old_source.resolve(), "upstream_fix": args.fixed_source.resolve()}
    checked = {name: checked_checkout(path, COMMITS[name]) for name, path in sources.items()}
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    reference = out / "synthetic.fa"
    reference.write_text(">chrA\n" + "A" * 100 + "\n>chrB\n" + "C" * 100 + "\n")
    pysam.faidx(str(reference))
    tsv = out / "synthetic.tsv"
    columns = ["Chr_1", "Pos_1", "Dir_1", "Chr_2", "Pos_2", "Dir_2", "SV_ID", "Is_Filter",
               "Inserted_Seq", "Checked_Read_Num_Tumor", "Supporting_Read_Num_Tumor"]
    fixtures = []
    with tsv.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for index, (dir1, dir2, insertion) in enumerate(itertools.product("+-", "+-", ["---", "ACG"])):
            name = f"case{index + 1}"
            row = {"Chr_1": "chrA", "Pos_1": 10 + index, "Dir_1": dir1,
                   "Chr_2": "chrB", "Pos_2": 30 + index, "Dir_2": dir2,
                   "SV_ID": name, "Is_Filter": "PASS", "Inserted_Seq": insertion,
                   "Checked_Read_Num_Tumor": 10, "Supporting_Read_Num_Tumor": 3}
            fixtures.append(row)
            writer.writerow(row)
    commands = {}
    for name, root in sources.items():
        command = [sys.executable, "-c", BOOTSTRAP, str(root), str(tsv),
                   str(out / f"{name}.vcf"), str(reference)]
        run = subprocess.run(command, text=True, capture_output=True)
        (out / f"{name}.stdout.txt").write_text(run.stdout)
        (out / f"{name}.stderr.txt").write_text(run.stderr)
        commands[name] = {"argv": command, "exit_code": run.returncode}
        if run.returncode:
            raise RuntimeError(f"{name} converter failed; logs in {out}")
    records = {name: read_records(out / f"{name}.vcf") for name in sources}
    expected_ids = {f"{row['SV_ID']}_{mate}" for row in fixtures for mate in (0, 1)}
    if any(set(data) != expected_ids for data in records.values()):
        raise ValueError("Unexpected record IDs; raw converter files retained")
    cases = []
    for row in fixtures:
        name = row["SV_ID"]
        cases.append({"id": name, "dir1": row["Dir_1"], "dir2": row["Dir_2"],
                      "input_insertion": row["Inserted_Seq"],
                      **{version: {"first": data[name + "_0"], "mate": data[name + "_1"]}
                         for version, data in records.items()}})
    counts = {}
    for version in sources:
        by_dir = {}
        for direction in "+-":
            selected = [c for c in cases if c["dir1"] == direction]
            by_dir[direction] = dict(Counter(c[version]["first"]["local_anchor"] for c in selected))
        counts[version] = {"first_anchors_by_dir1": by_dir,
                           "mate_anchors": dict(Counter(c[version]["mate"]["local_anchor"] for c in cases))}
    comparison = {"cases": cases, "counts": counts}
    (out / "comparison.json").write_text(json.dumps(comparison, indent=2) + "\n")
    receipt = {"python": sys.version, "platform": platform.platform(), "pysam": pysam.__version__,
               "script_sha256": sha(Path(__file__).resolve()), "sources": checked, "commands": commands,
               "files_sha256": {str(path.relative_to(out)): sha(path) for path in sorted(out.rglob("*")) if path.is_file()}}
    (out / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(counts, indent=2))


if __name__ == "__main__":
    main()
