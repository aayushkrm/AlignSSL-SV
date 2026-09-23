"""Stream a FASTA into a complete non-ACGT BED and verify sequence M5s."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from typing import BinaryIO, TextIO


AMBIGUOUS = re.compile(rb"[^ACGT]+")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def expected_from_dict(path: Path) -> dict[str, tuple[int, str]]:
    expected = {}
    for line in path.read_text().splitlines():
        if not line.startswith("@SQ\t"):
            continue
        tags = dict(field.split(":", 1) for field in line.split("\t")[1:])
        expected[tags["SN"]] = (int(tags["LN"]), tags["M5"].lower())
    if not expected:
        raise ValueError(f"No @SQ records in {path}")
    return expected


def expected_from_audit(path: Path) -> dict[str, tuple[int, str]]:
    records = json.loads(path.read_text())["contigs"]
    return {
        name: (record["length"], record["canonical_m5"].lower())
        for name, record in records.items()
    }


def scan_fasta(
    source: BinaryIO, bed: TextIO, expected: dict[str, tuple[int, str]]
) -> dict:
    contigs = {}
    name = None
    length = ambiguous_bases = intervals = 0
    run_start = run_end = None
    sequence_m5 = hashlib.md5()
    bed_digest = hashlib.sha256()

    def finish_run() -> None:
        nonlocal run_start, run_end, intervals
        if run_start is None:
            return
        row = f"{name}\t{run_start}\t{run_end}\n"
        bed.write(row)
        bed_digest.update(row.encode("ascii"))
        intervals += 1
        run_start = run_end = None

    def finish_contig() -> None:
        if name is None:
            return
        finish_run()
        if name not in expected:
            raise ValueError(f"Unexpected FASTA contig: {name}")
        actual_m5 = sequence_m5.hexdigest()
        if (length, actual_m5) != expected[name]:
            raise ValueError(f"{name}: length or M5 differs from expected dictionary")
        contigs[name] = {
            "length": length, "canonical_m5": actual_m5,
            "n_ambiguous_bases": ambiguous_bases,
            "n_ambiguous_intervals": intervals,
        }

    for raw_line in source:
        if raw_line.startswith(b">"):
            finish_contig()
            name = raw_line[1:].split(maxsplit=1)[0].decode("ascii")
            if name in contigs:
                raise ValueError(f"Duplicate FASTA contig: {name}")
            length = ambiguous_bases = intervals = 0
            run_start = run_end = None
            sequence_m5 = hashlib.md5()
            continue
        if name is None:
            raise ValueError("Sequence appeared before FASTA header")
        sequence = raw_line.rstrip(b"\r\n").upper()
        sequence_m5.update(sequence)
        for match in AMBIGUOUS.finditer(sequence):
            start, end = length + match.start(), length + match.end()
            if run_start is None:
                run_start, run_end = start, end
            elif start == run_end:
                run_end = end
            else:
                finish_run()
                run_start, run_end = start, end
            ambiguous_bases += end - start
        length += len(sequence)
    finish_contig()
    if not contigs or set(contigs) != set(expected):
        raise ValueError(f"FASTA/dictionary contig sets differ: {set(expected) - set(contigs)} missing")
    return {
        "contigs": contigs,
        "n_contigs": len(contigs),
        "n_bases": sum(record["length"] for record in contigs.values()),
        "n_ambiguous_bases": sum(record["n_ambiguous_bases"] for record in contigs.values()),
        "n_ambiguous_intervals": sum(record["n_ambiguous_intervals"] for record in contigs.values()),
        "bed_sha256": bed_digest.hexdigest(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fasta", type=Path, required=True)
    expectation = parser.add_mutually_exclusive_group(required=True)
    expectation.add_argument("--expected-dict", type=Path)
    expectation.add_argument("--expected-m5-json", type=Path)
    parser.add_argument("--out-bed", type=Path, required=True)
    parser.add_argument("--out-json", type=Path, required=True)
    args = parser.parse_args()
    if args.out_bed.resolve() == args.out_json.resolve():
        parser.error("--out-bed and --out-json must be different paths")
    expected = (expected_from_dict(args.expected_dict) if args.expected_dict
                else expected_from_audit(args.expected_m5_json))
    input_hash = file_sha256(args.fasta)
    args.out_bed.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="ascii", newline="\n", dir=args.out_bed.parent,
            prefix=f".{args.out_bed.name}.", suffix=".partial", delete=False,
        ) as bed:
            temp_path = Path(bed.name)
            opener = gzip.open if args.fasta.suffix == ".gz" else Path.open
            with opener(args.fasta, "rb") as source:
                result = scan_fasta(source, bed, expected)
        result.update({"fasta": str(args.fasta), "fasta_sha256": input_hash,
                       "expected_source": str(args.expected_dict or args.expected_m5_json),
                       "bed_path": str(args.out_bed)})
        os.replace(temp_path, args.out_bed)
        args.out_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    except BaseException:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
        raise
    print(f"{result['n_contigs']} contigs; {result['n_ambiguous_bases']} "
          f"non-ACGT bases in {result['n_ambiguous_intervals']} intervals")


if __name__ == "__main__":
    main()
