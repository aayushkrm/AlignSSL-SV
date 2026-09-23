"""Stream one contig from two indexed FASTAs and count base-level differences."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
from collections import Counter
from itertools import zip_longest
from pathlib import Path
from typing import BinaryIO, Iterator, TextIO


CHUNK_SIZE = 1024 * 1024


def sequence_chunks(source: BinaryIO, chunk_size: int = CHUNK_SIZE) -> Iterator[bytes]:
    header = source.readline()
    if not header.startswith(b">"):
        raise ValueError("samtools faidx output has no FASTA header")
    pending = bytearray()
    for line in source:
        if line.startswith(b">"):
            raise ValueError("Expected one contig, got another FASTA header")
        pending.extend(line.strip().upper())
        while len(pending) >= chunk_size:
            yield bytes(pending[:chunk_size])
            del pending[:chunk_size]
    if pending:
        yield bytes(pending)


def compare_streams(
    left: BinaryIO, right: BinaryIO, *, contig: str = "chr1", bed: TextIO | None = None
) -> dict:
    """Compare equal-length sequences and optionally emit all differences as BED3.

    Adjacent differences are merged across FASTA lines and comparison chunks.
    BED coordinates are zero-based, half-open, relative to ``contig``.
    """
    mismatches = Counter()
    first = []
    position = 0
    run_start = None
    n_intervals = 0
    bed_digest = hashlib.sha256() if bed is not None else None

    def finish_run(end: int) -> None:
        nonlocal run_start, n_intervals
        if run_start is None:
            return
        n_intervals += 1
        if bed is not None:
            line = f"{contig}\t{run_start}\t{end}\n"
            bed.write(line)
            bed_digest.update(line.encode("ascii"))
        run_start = None

    for a, b in zip_longest(sequence_chunks(left), sequence_chunks(right)):
        if a is None or b is None or len(a) != len(b):
            raise ValueError("Reference contigs have different lengths")
        if a == b:
            finish_run(position)
            position += len(a)
            continue
        for index, (base_a, base_b) in enumerate(zip(a, b)):
            if base_a != base_b:
                if run_start is None:
                    run_start = position + index
                mismatches[f"{chr(base_a)}>{chr(base_b)}"] += 1
                if len(first) < 20:
                    first.append({"position_1based": position + index + 1,
                                  "left": chr(base_a), "right": chr(base_b)})
            else:
                finish_run(position + index)
        position += len(a)
    finish_run(position)
    result = {
        "length": position,
        "n_different_bases": sum(mismatches.values()),
        "n_difference_intervals": n_intervals,
        "difference_types": dict(sorted(mismatches.items())),
        "first_differences": first,
    }
    if bed_digest is not None:
        result["difference_bed_sha256"] = bed_digest.hexdigest()
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samtools", required=True)
    parser.add_argument("--left-fasta", required=True)
    parser.add_argument("--right-fasta", required=True)
    parser.add_argument("--contig", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--out-bed", type=Path,
                        help="Complete BED3 intervals of all differing bases")
    args = parser.parse_args()
    if args.out_bed is not None and args.out.resolve() == args.out_bed.resolve():
        parser.error("--out and --out-bed must be different paths")
    left_command = [args.samtools, "faidx", args.left_fasta, args.contig]
    right_command = [args.samtools, "faidx", args.right_fasta, args.contig]
    left = subprocess.Popen(left_command, stdout=subprocess.PIPE)
    right = subprocess.Popen(right_command, stdout=subprocess.PIPE)
    bed_temp = None
    try:
        if args.out_bed is not None:
            args.out_bed.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="ascii", newline="\n",
                dir=args.out_bed.parent, prefix=f".{args.out_bed.name}.",
                suffix=".partial", delete=False,
            ) as bed_file:
                bed_temp = Path(bed_file.name)
                result = compare_streams(
                    left.stdout, right.stdout, contig=args.contig, bed=bed_file
                )
        else:
            result = compare_streams(left.stdout, right.stdout, contig=args.contig)
    except BaseException:
        for process in (left, right):
            if process.poll() is None:
                process.terminate()
            process.wait()
        if bed_temp is not None:
            bed_temp.unlink(missing_ok=True)
        raise
    finally:
        left.stdout.close()
        right.stdout.close()
    left_status = left.wait()
    right_status = right.wait()
    if left_status or right_status:
        if bed_temp is not None:
            bed_temp.unlink(missing_ok=True)
        raise RuntimeError("One or both samtools faidx commands failed")
    result.update({"left_fasta": args.left_fasta,
                   "right_fasta": args.right_fasta, "contig": args.contig})
    if args.out_bed is not None:
        result["difference_bed_path"] = str(args.out_bed)
        os.replace(bed_temp, args.out_bed)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(f"{args.contig}: {result['n_different_bases']} / {result['length']} bases differ")


if __name__ == "__main__":
    main()
