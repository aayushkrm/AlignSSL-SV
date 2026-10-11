"""Build and validate a tiny deterministic CIGAR-only synthetic BAM fixture."""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import stat
from pathlib import Path

import pysam


CONTIG = "chrSynthetic"
SAMPLE = "SYNTH"
SEED = 1729
REFERENCE_LENGTH = 4000
INSERTION_OFFSET = 1500
INSERTION_SEQUENCE = "A" * 60
MAX_OUTPUT_BYTES = 1024 * 1024
FASTA_NAME = "reference.fa"
TRUTH_NAME = "truth.json"
MANIFEST_NAME = "manifest.json"
BAM_NAMES = ("canonical.bam", "fragmented.bam", "reference_only.bam")
ARTIFACT_NAMES = frozenset(
    {FASTA_NAME, FASTA_NAME + ".fai", TRUTH_NAME, MANIFEST_NAME}
    | {name + suffix for name in BAM_NAMES for suffix in ("", ".bai")}
)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _reference_sequence() -> str:
    rng = random.Random(SEED)
    bases = "ACGT"
    left = "".join(bases[rng.getrandbits(2)] for _ in range(1000))
    right = "".join(bases[rng.getrandbits(2)] for _ in range(1000))
    return left + "A" * 2000 + right


def _fasta_bytes(sequence: str) -> bytes:
    lines = [sequence[offset:offset + 60] for offset in range(0, len(sequence), 60)]
    return (f">{CONTIG}\n" + "\n".join(lines) + "\n").encode("ascii")


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2) + "\n").encode("utf-8")


def _digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(64 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _manifest_bytes(directory: Path) -> bytes:
    files = {}
    for name in sorted(ARTIFACT_NAMES - {MANIFEST_NAME}):
        path = directory / name
        files[name] = {"bytes": path.stat().st_size, "sha256": _digest(path)}
    return _json_bytes({"version": 1, "seed": SEED, "files": files})


def _truth_payload(sequence: str) -> dict:
    return {
        "version": 1,
        "contig": CONTIG,
        "reference_sha256": hashlib.sha256(sequence.encode("ascii")).hexdigest(),
        "reference_sha256_basis": "uppercase sequence ASCII bytes; FASTA header and wrapping excluded",
        "reference_length": REFERENCE_LENGTH,
        "insertion_offset": INSERTION_OFFSET,
        "inserted_sequence": INSERTION_SEQUENCE,
        "expected_alt_length": REFERENCE_LENGTH + len(INSERTION_SEQUENCE),
        "sample": SAMPLE,
    }


def _new_output_directory(output_dir: str | Path) -> Path:
    directory = Path(output_dir)
    _require(not any(parent.is_symlink() for parent in directory.absolute().parents),
             "output directory ancestors must not be links")
    try:
        directory.lstat()
    except FileNotFoundError:
        pass
    else:
        raise FileExistsError(f"output directory already exists: {directory}")
    directory.mkdir(parents=False, exist_ok=False)
    return directory


def _reference_only_spec(sequence: str, index: int) -> dict:
    start = 300 + (index % 10) * 11
    end = 3700 - (index % 7) * 9
    span = end - start
    return {
        "name": f"REF{index:03d}",
        "start": start,
        "end": end,
        "sequence": sequence[start:end],
        "cigar": ((pysam.CEQUAL, span),),
        "nm": 0,
        "md": str(span),
    }


def _alternate_spec(sequence: str, index: int, fragmented: bool) -> dict:
    start = 300 + (index % 10) * 11
    end = 3700 - (index % 7) * 9
    left = INSERTION_OFFSET - start
    right = end - INSERTION_OFFSET
    if fragmented:
        cigar = (
            (pysam.CEQUAL, left),
            (pysam.CINS, 20),
            (pysam.CEQUAL, 5),
            (pysam.CINS, 20),
            (pysam.CEQUAL, 5),
            (pysam.CINS, 20),
            (pysam.CEQUAL, end - (INSERTION_OFFSET + 10)),
        )
    else:
        cigar = (
            (pysam.CEQUAL, left),
            (pysam.CINS, len(INSERTION_SEQUENCE)),
            (pysam.CEQUAL, right),
        )
    return {
        "name": f"ALT{index:03d}",
        "start": start,
        "end": end,
        "sequence": sequence[start:INSERTION_OFFSET]
        + INSERTION_SEQUENCE
        + sequence[INSERTION_OFFSET:end],
        "cigar": cigar,
        "nm": len(INSERTION_SEQUENCE),
        "md": str(end - start),
    }


def _primary_specs(sequence: str, fragmented: bool) -> list[dict]:
    specs = [_reference_only_spec(sequence, i) for i in range(20)]
    specs.extend(_alternate_spec(sequence, i, fragmented) for i in range(20))
    return sorted(specs, key=lambda item: (item["start"], item["name"]))


def _write_bam(path: Path, specs: list[dict]) -> None:
    header = {
        "HD": {"VN": "1.6", "SO": "coordinate"},
        "SQ": [{"SN": CONTIG, "LN": REFERENCE_LENGTH}],
        "RG": [{"ID": SAMPLE, "SM": SAMPLE}],
    }
    with pysam.AlignmentFile(str(path), "wb", header=header) as bam:
        for spec in specs:
            read = pysam.AlignedSegment(bam.header)
            read.query_name = spec["name"]
            read.query_sequence = spec["sequence"]
            read.flag = 0
            read.reference_id = 0
            read.reference_start = spec["start"]
            read.mapping_quality = 60
            read.cigartuples = list(spec["cigar"])
            read.query_qualities = [40] * len(spec["sequence"])
            read.set_tag("RG", SAMPLE, value_type="Z")
            read.set_tag("NM", spec["nm"], value_type="i")
            read.set_tag("MD", spec["md"], value_type="Z")
            bam.write(read)
    pysam.index(str(path))


def create_fixture(output_dir: str | Path) -> Path:
    """Create the fixture in a new directory and return that directory path."""
    directory = _new_output_directory(output_dir)
    sequence = _reference_sequence()
    fasta_path = directory / FASTA_NAME
    with fasta_path.open("xb") as fasta:
        fasta.write(_fasta_bytes(sequence))
    pysam.faidx(str(fasta_path))

    with (directory / TRUTH_NAME).open("xb") as handle:
        handle.write(_json_bytes(_truth_payload(sequence)))

    _write_bam(directory / "canonical.bam", _primary_specs(sequence, fragmented=False))
    _write_bam(directory / "fragmented.bam", _primary_specs(sequence, fragmented=True))
    reference_specs = [_reference_only_spec(sequence, i) for i in range(40)]
    reference_specs.sort(key=lambda item: (item["start"], item["name"]))
    _write_bam(directory / "reference_only.bam", reference_specs)

    with (directory / MANIFEST_NAME).open("xb") as handle:
        handle.write(_manifest_bytes(directory))
    _require(_directory_size(directory) <= MAX_OUTPUT_BYTES,
             "generated fixture exceeds the 1 MiB output limit")
    return directory


def _directory_size(directory: Path) -> int:
    return sum(path.lstat().st_size for path in directory.iterdir())


def _validate_read(read: pysam.AlignedSegment, spec: dict, reference: str) -> tuple:
    name = spec["name"]
    _require(read.query_name == name, f"unexpected read name: {read.query_name}")
    _require(read.flag == 0, f"{name}: primary flag must be zero")
    _require(read.reference_id == 0 and read.reference_start == spec["start"],
             f"{name}: alignment start mismatch")
    _require(read.reference_end == spec["end"], f"{name}: alignment endpoint mismatch")
    _require(read.mapping_quality == 60, f"{name}: MAPQ mismatch")
    _require(read.query_sequence == spec["sequence"], f"{name}: query sequence mismatch")
    qualities = read.query_qualities
    _require(qualities is not None and tuple(qualities) == (40,) * len(spec["sequence"]),
             f"{name}: base quality mismatch")
    cigar = tuple((int(op), int(length)) for op, length in (read.cigartuples or ()))
    _require(cigar == spec["cigar"], f"{name}: CIGAR mismatch")

    query_consumed = sum(length for op, length in cigar
                         if op in (pysam.CMATCH, pysam.CINS, pysam.CSOFT_CLIP,
                                   pysam.CEQUAL, pysam.CDIFF))
    reference_consumed = sum(length for op, length in cigar
                             if op in (pysam.CMATCH, pysam.CDEL, pysam.CREF_SKIP,
                                       pysam.CEQUAL, pysam.CDIFF))
    aligned_equal = sum(length for op, length in cigar if op == pysam.CEQUAL)
    _require(query_consumed == len(spec["sequence"]), f"{name}: query consumption mismatch")
    _require(reference_consumed == spec["end"] - spec["start"],
             f"{name}: reference consumption mismatch")
    _require(aligned_equal == spec["end"] - spec["start"],
             f"{name}: aligned '=' bases mismatch")

    query_pos, reference_pos = 0, spec["start"]
    for op, length in cigar:
        if op == pysam.CEQUAL:
            _require(spec["sequence"][query_pos:query_pos + length]
                     == reference[reference_pos:reference_pos + length],
                     f"{name}: aligned sequence differs from reference")
            query_pos += length
            reference_pos += length
        elif op == pysam.CINS:
            query_pos += length
    _require(query_pos == len(spec["sequence"]) and reference_pos == spec["end"],
             f"{name}: final query/reference endpoint mismatch")

    tags = read.get_tags()
    _require(len(tags) == 3 and dict(tags) == {
        "RG": SAMPLE, "NM": spec["nm"], "MD": spec["md"]
    }, f"{name}: RG/NM/MD tags mismatch")
    sam_fields = read.to_string().split("\t")
    _require(len(sam_fields) >= 11, f"{name}: invalid SAM record")
    other_fields = tuple(sam_fields[:5] + sam_fields[6:])
    return read.cigarstring, other_fields


def _validate_bam(path: Path, expected_specs: list[dict], reference: str) -> dict[str, tuple]:
    expected_by_name = {spec["name"]: spec for spec in expected_specs}
    result = {}
    seen = set()
    previous_key = None
    with pysam.AlignmentFile(str(path), "rb") as bam:
        header = bam.header.to_dict()
        _require(header.get("HD", {}).get("SO") == "coordinate",
                 f"{path.name}: BAM is not marked coordinate-sorted")
        _require(tuple(bam.references) == (CONTIG,)
                 and tuple(bam.lengths) == (REFERENCE_LENGTH,),
                 f"{path.name}: reference header mismatch")
        _require(header.get("RG") == [{"ID": SAMPLE, "SM": SAMPLE}],
                 f"{path.name}: read-group sample mismatch")
        _require(bam.has_index(), f"{path.name}: missing or unreadable BAM index")
        for read in bam.fetch(until_eof=True):
            _require(read.query_name in expected_by_name,
                     f"{path.name}: unexpected read name {read.query_name}")
            _require(read.query_name not in seen,
                     f"{path.name}: duplicate read name {read.query_name}")
            key = (read.reference_start, read.query_name)
            _require(previous_key is None or previous_key <= key,
                     f"{path.name}: records are not coordinate-sorted")
            previous_key = key
            seen.add(read.query_name)
            result[read.query_name] = _validate_read(
                read, expected_by_name[read.query_name], reference
            )
    _require(seen == set(expected_by_name), f"{path.name}: read count/name set mismatch")
    with pysam.AlignmentFile(str(path), "rb") as bam:
        indexed_names = [read.query_name for read in bam.fetch(CONTIG)]
    _require(indexed_names == [spec["name"] for spec in expected_specs],
             f"{path.name}: index does not return all sorted records")
    return result


def _validate_directory(directory: Path) -> None:
    try:
        mode = directory.lstat().st_mode
    except FileNotFoundError as error:
        raise ValueError(f"fixture directory does not exist: {directory}") from error
    _require(stat.S_ISDIR(mode), "fixture output path must be a real directory, not a link")
    entries = list(directory.iterdir())
    _require({entry.name for entry in entries} == ARTIFACT_NAMES,
             "fixture file set does not match the generated artifact set")
    for entry in entries:
        entry_mode = entry.lstat().st_mode
        _require(stat.S_ISREG(entry_mode) and entry.lstat().st_nlink == 1,
                 f"fixture artifact must be a regular unlinked file: {entry.name}")
    _require(_directory_size(directory) <= MAX_OUTPUT_BYTES,
             "fixture exceeds the 1 MiB aggregate output limit")


def validate_fixture(output_dir: str | Path) -> None:
    """Check file identity, contents, alignment semantics, and manifest hashes."""
    directory = Path(output_dir)
    _validate_directory(directory)
    sequence = _reference_sequence()
    fasta_path = directory / FASTA_NAME
    _require(fasta_path.read_bytes() == _fasta_bytes(sequence), "reference FASTA mismatch")
    expected_fai = f"{CONTIG}\t{REFERENCE_LENGTH}\t14\t60\t61\n".encode("ascii")
    _require((directory / (FASTA_NAME + ".fai")).read_bytes() == expected_fai,
             "reference FASTA index mismatch")
    with pysam.FastaFile(str(fasta_path)) as fasta:
        _require(tuple(fasta.references) == (CONTIG,)
                 and fasta.fetch(CONTIG) == sequence, "indexed reference sequence mismatch")
    _require((directory / TRUTH_NAME).read_bytes() == _json_bytes(_truth_payload(sequence)),
             "truth JSON mismatch")

    canonical = _validate_bam(directory / "canonical.bam",
                              _primary_specs(sequence, fragmented=False), sequence)
    fragmented = _validate_bam(directory / "fragmented.bam",
                               _primary_specs(sequence, fragmented=True), sequence)
    reference_specs = [_reference_only_spec(sequence, i) for i in range(40)]
    reference_specs.sort(key=lambda item: (item["start"], item["name"]))
    reference_only = _validate_bam(directory / "reference_only.bam",
                                   reference_specs, sequence)

    _require(set(canonical) == set(fragmented), "primary BAM read-name sets differ")
    differing_cigars = set()
    for name in canonical:
        canonical_cigar, canonical_fields = canonical[name]
        fragmented_cigar, fragmented_fields = fragmented[name]
        _require(canonical_fields == fragmented_fields,
                 f"{name}: primary BAM fields other than CIGAR differ")
        if canonical_cigar != fragmented_cigar:
            differing_cigars.add(name)
    _require(differing_cigars == {f"ALT{i:03d}" for i in range(20)},
             "expected exactly 20 ALT CIGAR differences and no REF differences")
    _require(set(reference_only) == {f"REF{i:03d}" for i in range(40)},
             "reference-only negative control contains ALT or missing reads")
    _require((directory / MANIFEST_NAME).read_bytes() == _manifest_bytes(directory),
             "manifest hashes or frozen seed mismatch")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, help="new directory for fixture files")
    args = parser.parse_args(argv)
    directory = create_fixture(args.output_dir)
    validate_fixture(directory)
    print(f"Validated deterministic CIGAR fixture in {directory}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
