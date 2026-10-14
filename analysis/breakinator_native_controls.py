"""Tiny synthetic BAM controls for the pinned Breakinator native CLI.

Upstream tag v1.1.1 resolves to jheinz27/breakinator commit
2a5b7138aee9368c6c613c0837f3d8152437957c. The reviewed CLI, SAM, and report
semantics are in breakinator/src/{cli.rs,sam.rs,lib.rs} at that commit.
The native CLI reports `Pass`, `Foldback`, or `Chimeric`; `Pass` is exposed as
the paper's TrueBreak-style class, not as biological truth.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path


UPSTREAM_REPOSITORY = "https://github.com/jheinz27/breakinator"
UPSTREAM_TAG = "v1.1.1"
UPSTREAM_COMMIT = "2a5b7138aee9368c6c613c0837f3d8152437957c"
RELEASE_ASSET = "breakinator-v1.1.1-x86_64-unknown-linux-musl.tar.gz"
RELEASE_ASSET_URL = (
    "https://github.com/jheinz27/breakinator/releases/download/v1.1.1/"
    "breakinator-v1.1.1-x86_64-unknown-linux-musl.tar.gz"
)
RELEASE_ASSET_BYTES = 3_547_379
# These release values identify the .tar.gz asset; `binary` metadata hashes the extracted executable.
RELEASE_ASSET_SHA256 = "00747b208e25887eac9e61db57496085d2a593cb6899e1b2940ca9ab1c9c2310"
UPSTREAM_CLI_VERSION = "breakinator 1.0"
UPSTREAM_SOURCE_FILES = (
    "breakinator/src/cli.rs",
    "breakinator/src/sam.rs",
    "breakinator/src/lib.rs",
)
UPSTREAM_SEMANTICS = {
    "default_input": "SAM/BAM/CRAM; PAF mode is off unless --paf is set",
    "qname_groups": "consecutive equal-QNAME records; input must be name-sorted",
    "within_group_order": (
        "filtered records sort by query_loc: forward uses leading soft/hard clip; "
        "reverse uses trailing soft/hard clip"
    ),
    "filters": (
        "drop unmapped, secondary, MAPQ<10, and query-aligned length<200; "
        "supplementary records are retained"
    ),
    "foldback": (
        "opposing directions, same-contig reference distance<=200; default requires "
        "the implementation's symmetric-window check with margin=0.1"
    ),
    "symmetric_window_detail": (
        "source check_sym assigns r2_loc to both local variables; effective default "
        "window tests r2_loc against read_length/2 +/- margin*read_length"
    ),
    "chimera": "different contigs or same-contig reference distance>=1000000",
    "report_coordinates": (
        "--rcoord adds break1_read=read_length-query_end(first) and "
        "break2_read=query_loc(second)"
    ),
}

BAM_NAME = "controls.namesorted.bam"
REPORT_NAME = "native-report.txt"
REPORT_HEADER = (
    "#Break1_chr", "Break1_loc", "Break_direction", "Break2_chr",
    "Break2_loc", "MapQ", "Read_ID", "Classification", "break1_read",
    "break2_read",
)
NATIVE_KIND = {
    "Pass": "TrueBreak",
    "Foldback": "PutativeFoldback",
    "Chimeric": "PutativeChimeric",
}


@dataclass(frozen=True)
class AlignmentSpec:
    read_id: str
    contig: str
    start: int
    flag: int
    cigar: str
    sa: str | None = None


CONTROL_ALIGNMENTS = (
    AlignmentSpec("00_reference", "chrSynthetic", 100, 0, "1000M"),
    AlignmentSpec(
        "10_foldback_center", "chrSynthetic", 1000, 0, "500M500S",
        "chrSynthetic,1001,-,500M500S,60,0;",
    ),
    AlignmentSpec(
        "10_foldback_center", "chrSynthetic", 1000, 0x810, "500M500S",
        "chrSynthetic,1001,+,500M500S,60,0;",
    ),
    AlignmentSpec(
        "20_foldback_j250", "chrSynthetic", 2000, 0, "250M750S",
        "chrSynthetic,1501,-,750M250S,60,0;",
    ),
    AlignmentSpec(
        "20_foldback_j250", "chrSynthetic", 1500, 0x810, "750M250S",
        "chrSynthetic,2001,+,250M750S,60,0;",
    ),
    AlignmentSpec(
        "30_two_chromosomes", "chrSynthetic", 3000, 0, "500M500S",
        "chrOther,4001,+,500S500M,60,0;",
    ),
    AlignmentSpec(
        "30_two_chromosomes", "chrOther", 4000, 0x800, "500S500M",
        "chrSynthetic,3001,+,500M500S,60,0;",
    ),
)


@dataclass(frozen=True)
class BreakpointCall:
    break1_chr: str
    break1_loc: int
    direction: str
    break2_chr: str
    break2_loc: int
    mapq: int
    read_id: str
    native_class: str
    class_name: str
    break1_read: int
    break2_read: int


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _reverse_complement(sequence: str) -> str:
    return sequence.translate(str.maketrans("ACGT", "TGCA"))[::-1]


def _pysam_module():
    try:
        import pysam
    except ImportError as exc:
        raise RuntimeError("pysam is required to create the native-control BAM") from exc
    return pysam


def create_controls_bam(path: str | Path) -> Path:
    """Write and validate the four name-sorted, synthetic ABI control groups."""
    pysam = _pysam_module()
    bam_path = Path(path)
    _require(not bam_path.exists() and not bam_path.is_symlink(),
             f"BAM output already exists: {bam_path}")
    header = {
        "HD": {"VN": "1.6", "SO": "queryname"},
        "SQ": [
            {"SN": "chrSynthetic", "LN": 10_000},
            {"SN": "chrOther", "LN": 10_000},
        ],
        "RG": [{"ID": "ABI", "SM": "ABI"}],
    }
    read_sequence = "ACGT" * 250
    qualities = pysam.qualitystring_to_array("I" * len(read_sequence))
    with pysam.AlignmentFile(os.fspath(bam_path), "wb", header=header) as bam:
        for spec in CONTROL_ALIGNMENTS:
            read = pysam.AlignedSegment(bam.header)
            read.query_name = spec.read_id
            read.flag = spec.flag
            read.reference_id = bam.get_tid(spec.contig)
            read.reference_start = spec.start
            read.mapping_quality = 60
            read.cigarstring = spec.cigar
            read.query_sequence = (
                _reverse_complement(read_sequence)
                if spec.flag & 0x10 else read_sequence
            )
            read.query_qualities = qualities
            read.set_tag("RG", "ABI", value_type="Z")
            read.set_tag("NM", 0, value_type="i")
            if spec.sa is not None:
                read.set_tag("SA", spec.sa, value_type="Z")
            bam.write(read)
    _validate_controls_bam(bam_path)
    return bam_path


def _validate_controls_bam(path: Path) -> None:
    pysam = _pysam_module()
    expected_names = [spec.read_id for spec in CONTROL_ALIGNMENTS]
    observed = []
    with pysam.AlignmentFile(os.fspath(path), "rb") as bam:
        header = bam.header.to_dict()
        _require(header.get("HD", {}).get("SO") == "queryname",
                 "control BAM must declare queryname order")
        records = list(bam.fetch(until_eof=True))
        _require(len(records) == len(CONTROL_ALIGNMENTS),
                 "control BAM record count mismatch")
        for read, spec in zip(records, CONTROL_ALIGNMENTS):
            observed.append(read.query_name)
            _require(read.query_name == spec.read_id, "control BAM read-group order mismatch")
            _require(read.flag == spec.flag, f"{spec.read_id}: flag mismatch")
            _require(read.reference_name == spec.contig
                     and read.reference_start == spec.start,
                     f"{spec.read_id}: reference placement mismatch")
            _require(read.mapping_quality == 60 and read.cigarstring == spec.cigar,
                     f"{spec.read_id}: MAPQ/CIGAR mismatch")
            _require(read.query_sequence is not None and len(read.query_sequence) == 1000,
                     f"{spec.read_id}: full sequence is required")
            _require(read.query_qualities is not None and len(read.query_qualities) == 1000,
                     f"{spec.read_id}: full qualities are required")
            _require(read.get_tag("RG") == "ABI" and read.get_tag("NM") == 0,
                     f"{spec.read_id}: RG/NM tags mismatch")
            _require(read.has_tag("SA") == (spec.sa is not None),
                     f"{spec.read_id}: SA tag presence mismatch")
            if spec.sa is not None:
                _require(read.get_tag("SA") == spec.sa,
                         f"{spec.read_id}: SA tag mismatch")
    _require(observed == expected_names, "control BAM is not in expected QNAME group order")


def parse_native_report(raw_report: str | bytes) -> list[BreakpointCall]:
    """Parse the pinned v1.1.1 --rcoord TSV; reject unrecognized content."""
    if isinstance(raw_report, bytes):
        raw_report = raw_report.decode("utf-8", errors="strict")
    lines = raw_report.splitlines()
    expected_header = "\t".join(REPORT_HEADER)
    if not lines or lines[0] != expected_header:
        raise ValueError("native report header does not match v1.1.1 --rcoord TSV")

    calls = []
    int_fields = (1, 4, 5, 8, 9)
    for line_number, line in enumerate(lines[1:], start=2):
        if not line:
            raise ValueError(f"native report has a blank row at line {line_number}")
        fields = line.split("\t")
        if len(fields) != len(REPORT_HEADER):
            raise ValueError(f"native report row {line_number} has {len(fields)} fields")
        try:
            numbers = {index: int(fields[index]) for index in int_fields}
        except ValueError as exc:
            raise ValueError(f"native report row {line_number} has a non-integer field") from exc
        native_class = fields[7]
        if native_class not in NATIVE_KIND:
            raise ValueError(
                f"native report row {line_number} has unknown class {native_class!r}"
            )
        if not fields[0] or not fields[2] or not fields[3] or not fields[6]:
            raise ValueError(f"native report row {line_number} has an empty text field")
        if any(numbers[index] < 0 for index in int_fields):
            raise ValueError(f"native report row {line_number} has a negative coordinate/value")
        calls.append(BreakpointCall(
            break1_chr=fields[0], break1_loc=numbers[1], direction=fields[2],
            break2_chr=fields[3], break2_loc=numbers[4], mapq=numbers[5],
            read_id=fields[6], native_class=native_class,
            class_name=NATIVE_KIND[native_class],
            break1_read=numbers[8], break2_read=numbers[9],
        ))
    return calls


def _summary_count(stdout: str, label: str) -> int:
    matches = re.findall(rf"^{re.escape(label)}:\s*([0-9,]+)", stdout, re.MULTILINE)
    if len(matches) != 1:
        raise ValueError(f"native stdout is missing one {label!r} count")
    return int(matches[0].replace(",", ""))


def validate_expected_controls(calls: list[BreakpointCall], stdout: str) -> None:
    """Assert the expected geometry outcomes, without biological interpretation."""
    expected = {
        "10_foldback_center": (
            "Foldback", "chrSynthetic", 1500, "><", "chrSynthetic", 1500, 500, 500,
        ),
        "20_foldback_j250": (
            "Pass", "chrSynthetic", 2250, "><", "chrSynthetic", 2250, 250, 250,
        ),
        "30_two_chromosomes": (
            "Chimeric", "chrSynthetic", 3500, ">>", "chrOther", 4000, 500, 500,
        ),
    }
    observed_ids = [call.read_id for call in calls]
    _require(observed_ids == list(expected),
             f"unexpected native read/report order or rows: {observed_ids}")
    for call in calls:
        values = (
            call.native_class, call.break1_chr, call.break1_loc, call.direction,
            call.break2_chr, call.break2_loc, call.break1_read, call.break2_read,
        )
        _require(values == expected[call.read_id],
                 f"{call.read_id}: native breakpoint geometry/class mismatch: {values}")
        _require(call.mapq == 60, f"{call.read_id}: unexpected breakpoint MAPQ")
    _require(_summary_count(stdout, "Num reads passed filter") == 4,
             "native summary did not retain all four control reads")
    _require(_summary_count(stdout, "Num Foldback READS detected") == 1,
             "native summary did not flag exactly one foldback read")
    _require(_summary_count(stdout, "Num Chimeric READS detected") == 1,
             "native summary did not flag exactly one chimeric read")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _output_directory(path: str | Path) -> Path:
    directory = Path(path)
    try:
        info = directory.lstat()
    except FileNotFoundError as exc:
        raise ValueError("output directory must already exist and be empty") from exc
    if not stat.S_ISDIR(info.st_mode) or directory.is_symlink():
        raise ValueError("output path must be an existing, non-link directory")
    if any(directory.iterdir()):
        raise ValueError("output directory must be empty")
    return directory.resolve()


def _binary_info(path: str | Path) -> dict:
    binary = Path(path)
    try:
        info = binary.lstat()
    except FileNotFoundError as exc:
        raise ValueError("native --binary path does not exist") from exc
    if not stat.S_ISREG(info.st_mode) or binary.is_symlink():
        raise ValueError("native --binary must be a regular non-link file")
    if not os.access(binary, os.X_OK):
        raise ValueError("native --binary is not executable")
    resolved = binary.resolve()
    return {
        "path": str(resolved),
        "bytes": info.st_size,
        "sha256": _sha256(resolved),
    }


def _save_bytes(path: Path, payload: bytes) -> None:
    with path.open("xb") as handle:
        handle.write(payload)


def _decode(payload: bytes) -> str:
    return payload.decode("utf-8", errors="replace")


def _invoke(command: list[str], output_dir: Path) -> dict:
    try:
        result = subprocess.run(
            command, cwd=output_dir, capture_output=True, check=False, timeout=60,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "exit_code": None,
            "timed_out": True,
            "stdout": exc.stdout or b"",
            "stderr": exc.stderr or b"",
        }
    return {
        "exit_code": result.returncode,
        "timed_out": False,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def run_native_controls(binary: str | Path, output_dir: str | Path) -> dict:
    """Create the tiny BAM, run the pinned native route, and preserve its evidence."""
    directory = _output_directory(output_dir)
    binary_data = _binary_info(binary)
    bam_path = create_controls_bam(directory / BAM_NAME)
    binary_path = binary_data["path"]

    version_command = [binary_path, "--version"]
    version = _invoke(version_command, directory)
    _save_bytes(directory / "native-version.stdout.txt", version["stdout"])
    _save_bytes(directory / "native-version.stderr.txt", version["stderr"])
    observed_version = _decode(version["stdout"]).strip()
    version_ok = (
        version["exit_code"] == 0
        and not version["timed_out"]
        and observed_version == UPSTREAM_CLI_VERSION
    )

    command = [
        binary_path, "-i", BAM_NAME, "-o", REPORT_NAME,
        "--rcoord", "-t", "1",
    ]
    if version_ok:
        native = _invoke(command, directory)
    else:
        native = {
            "exit_code": None,
            "timed_out": False,
            "stdout": b"",
            "stderr": b"",
            "skipped": "native --version did not match the pinned v1.1.1 source",
        }
    _save_bytes(directory / "native-stdout.txt", native["stdout"])
    _save_bytes(directory / "native-stderr.txt", native["stderr"])
    report_path = directory / REPORT_NAME
    report = report_path.read_bytes() if report_path.exists() else b""
    if not report_path.exists():
        _save_bytes(report_path, report)

    validation_error = None
    parsed = []
    if not version_ok:
        validation_error = "native --version did not match pinned source output"
    elif native["exit_code"] != 0 or native["timed_out"]:
        validation_error = "native control command failed or timed out"
    else:
        try:
            parsed = parse_native_report(report)
            validate_expected_controls(parsed, _decode(native["stdout"]))
        except (UnicodeDecodeError, ValueError) as exc:
            validation_error = str(exc)

    manifest = {
        "schema_version": 1,
        "upstream": {
            "repository": UPSTREAM_REPOSITORY,
            "tag": UPSTREAM_TAG,
            "commit": UPSTREAM_COMMIT,
            "release_asset": RELEASE_ASSET,
            "release_asset_url": RELEASE_ASSET_URL,
            "release_asset_bytes": RELEASE_ASSET_BYTES,
            "release_asset_sha256": RELEASE_ASSET_SHA256,
            "cli_version_output_from_source": UPSTREAM_CLI_VERSION,
            "source_files": list(UPSTREAM_SOURCE_FILES),
            "semantics": UPSTREAM_SEMANTICS,
        },
        "binary": binary_data,
        "version_command": {
            "argv": version_command,
            "exit_code": version["exit_code"],
            "timed_out": version["timed_out"],
            "stdout_file": "native-version.stdout.txt",
            "stderr_file": "native-version.stderr.txt",
            "observed_stdout": observed_version,
        },
        "native_command": {
            "argv": command,
            "exit_code": native["exit_code"],
            "timed_out": native["timed_out"],
            "stdout_file": "native-stdout.txt",
            "stderr_file": "native-stderr.txt",
            "report_file": REPORT_NAME,
            "report_bytes": len(report),
            "report_sha256": hashlib.sha256(report).hexdigest(),
        },
        "controls_bam": {
            "file": bam_path.name,
            "bytes": bam_path.stat().st_size,
            "sha256": _sha256(bam_path),
        },
        "parsed_breakpoints": [asdict(call) for call in parsed],
        "validation_error": validation_error,
    }
    with (directory / "run.json").open("x", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, sort_keys=True)
        handle.write("\n")
    if validation_error is not None:
        raise RuntimeError(
            f"native ABI controls failed: {validation_error}; evidence is in {directory}"
        )
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", required=True, help="already-fetched native executable")
    parser.add_argument(
        "--output-dir", required=True,
        help="existing empty directory for the BAM, native outputs, and manifest",
    )
    args = parser.parse_args(argv)
    try:
        manifest = run_native_controls(args.binary, args.output_dir)
    except (OSError, ValueError, RuntimeError) as exc:
        parser.exit(1, f"breakinator native controls: {exc}\n")
    print(json.dumps({
        "output_dir": str(Path(args.output_dir).resolve()),
        "binary_sha256": manifest["binary"]["sha256"],
        "native_exit_code": manifest["native_command"]["exit_code"],
        "report_sha256": manifest["native_command"]["report_sha256"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
