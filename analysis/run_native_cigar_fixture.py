"""Run one frozen, synthetic-only Sawfish CIGAR diagnostic in a fresh root.

Invoke only through the reviewed timed Slurm wrapper. No real genomic input
is selected here. A complete observer report is not an experiment pass.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import resource
import stat
import subprocess
import sys
import tarfile
import urllib.request

sys.path.insert(0, str(Path(__file__).parent.parent))

EXPERIMENT = "native-cigar-invariance-20261009-01"
ROOT = Path("/scratch/igorno-alignssl_restart_20260922") / EXPERIMENT
ASSET_URL = ("https://github.com/PacificBiosciences/sawfish/releases/download/v2.2.1/"
             "sawfish-v2.2.1-x86_64-unknown-linux-gnu.tar.gz")
ASSET_SHA = "869d866d1399bd9803b3c60cc0e260ed1f60aa38a6f40d46f3093cd4bf5631f4"
MIB = 1024**2


def new_json(path, value):
    payload = (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()
    if len(payload) > 64 * 1024:
        raise ValueError("metadata report exceeds 64 KiB")
    with Path(path).open("xb") as handle:
        handle.write(payload)


def tree_size(path, cap, max_files=128, allow_test_links=False):
    total = count = 0
    for directory, dirs, files in os.walk(path, followlinks=False):
        for name in dirs + files:
            entry = Path(directory) / name
            info = entry.lstat()
            if stat.S_ISLNK(info.st_mode):
                if allow_test_links:
                    # Tests deliberately make links. Do not follow or read them.
                    count += 1
                    if count > max_files:
                        raise ValueError("control tree exceeds its file-count cap")
                    continue
                raise ValueError("output tree contains a link")
            if name in files:
                if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                    raise ValueError("output is not a regular single-link file")
                total += info.st_size
                count += 1
                if total > cap or count > max_files:
                    raise ValueError("output tree exceeds its cap")
    return total


def extract_binary(archive, target):
    """Extract only one authenticated executable; never use extractall."""
    with tarfile.open(archive, "r:gz") as bundle:
        members = bundle.getmembers()
        if len(members) > 64:
            raise ValueError("archive has too many members")
        expanded = 0
        binaries = []
        for member in members:
            name = PurePosixPath(member.name)
            if (name.is_absolute() or ".." in name.parts
                    or not (member.isfile() or member.isdir())):
                raise ValueError("archive contains an unsafe member")
            expanded += member.size
            if expanded > 16 * MIB:
                raise ValueError("archive expansion exceeds 16 MiB")
            if member.isfile() and name.name == "sawfish":
                binaries.append(member)
        if len(binaries) != 1:
            raise ValueError("archive must contain one sawfish executable")
        member = binaries[0]
        source = bundle.extractfile(member)
        if source is None:
            raise ValueError("executable payload missing")
        with source, Path(target).open("xb") as output:
            remaining = member.size
            while remaining:
                chunk = source.read(min(64 * 1024, remaining))
                if not chunk:
                    raise ValueError("truncated executable")
                output.write(chunk)
                remaining -= len(chunk)
    Path(target).chmod(0o700)
    return hashlib.sha256(Path(target).read_bytes()).hexdigest()


def install_tool(root):
    archive = root / "sawfish.tar.gz"
    digest = hashlib.sha256()
    size = 0
    with urllib.request.urlopen(ASSET_URL, timeout=30) as response, archive.open("xb") as handle:
        while True:
            chunk = response.read(64 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > 4 * MIB:
                raise ValueError("compressed asset exceeds 4 MiB")
            digest.update(chunk)
            handle.write(chunk)
    if (size != 3616061 or digest.hexdigest() != ASSET_SHA
            or hashlib.sha256(archive.read_bytes()).hexdigest() != ASSET_SHA):
        raise ValueError("author release bytes do not match the frozen asset")
    binary = root / "sawfish"
    binary_sha = extract_binary(archive, binary)
    run_command(root, "version", [str(binary), "--version"])
    version_path = root / "version.log"
    if version_path.stat().st_size > 16 * 1024:
        raise ValueError("version output exceeds 16 KiB")
    version = version_path.read_text().strip()
    if not re.fullmatch(r"sawfish 2\.2\.1", version):
        raise ValueError("unexpected native version")
    new_json(root / "tool.json", {"version": version, "asset_bytes": size,
             "asset_sha256": digest.hexdigest(), "binary_sha256": binary_sha})
    return binary


def run_command(root, label, argv):
    # Persist each command claim before execution. Never rerun an existing claim.
    new_json(root / (label + ".command.json"), {"argv": argv})
    with (root / (label + ".log")).open("xb") as output:
        subprocess.run(argv, stdout=output, stderr=subprocess.STDOUT,
                       check=True, timeout=120)
    if (root / (label + ".log")).stat().st_size > 64 * 1024:
        raise ValueError("command log exceeds 64 KiB")


def validate_outcome(name, report):
    """Fail closed on uncertainty; never use unresolved_records alone."""
    for stage in ("candidate", "final"):
        data = report[stage]
        if data["single_record_output_state"] == "UNRESOLVED":
            raise ValueError(f"{name}: unresolved {stage} representation")
    if name == "canonical" and report["final"]["pass_heterozygous_exact_allele_records"] < 1:
        raise ValueError("canonical exact PASS heterozygous control failed")
    if name == "reference_only":
        if any(report[stage]["single_record_output_state"] != "ABSENT_FROM_OUTPUT"
               for stage in ("candidate", "final")):
            raise ValueError("REF-only exact-allele negative control failed")


def run(root):
    from analysis.native_cigar_fixture import create_fixture, validate_fixture
    from analysis.observe_native_fixture import observe_native_fixture
    from analysis.check_native_fixture_settings import check_native_settings

    if root != ROOT or root.is_symlink() or not root.is_dir():
        raise ValueError("unexpected or absent experiment root")
    new_json(root / "payload.claim.json", {"experiment": EXPERIMENT})
    fixture = create_fixture(root / "fixture")
    validate_fixture(fixture)
    tree_size(fixture, 64 * 1024)
    binary = install_tool(root)
    # Asset/extraction needs up to16MiB; native output files are limited to1MiB.
    resource.setrlimit(resource.RLIMIT_FSIZE, (MIB, MIB))
    cases = [("canonical", "canonical.bam", 10),
             ("fragmented", "fragmented.bam", 10),
             ("reference_only", "reference_only.bam", 10),
             ("fragmented_rescue", "fragmented.bam", 30)]
    prior_settings = None
    summaries = {}
    for name, bam_name, margin in cases:
        arm = root / name
        arm.mkdir(mode=0o700)
        discover, joint = arm / "discover", arm / "joint"
        bam, reference = fixture / bam_name, fixture / "reference.fa"
        argv = [str(binary), "discover", "--threads", "1", "--ref", str(reference),
                "--bam", str(bam), "--disable-cnv", "--cov-regex", "^chrSynthetic$",
                "--output-dir", str(discover)]
        if margin == 30:
            argv += ["--min-indel-size-noise-margin", "30"]
        run_command(root, name + ".discover", argv)
        tree_size(arm, MIB, 64)
        validate_fixture(fixture)
        settings = check_native_settings(discover / "discover.settings.json",
            expected_bam=bam, expected_reference=reference,
            expected_output_dir=discover, expected_noise_margin=margin)
        common = {key: value for key, value in settings.items()
                  if key not in ("bam_filename", "output_dir", "min_indel_size_noise_margin")}
        if prior_settings is not None and common != prior_settings:
            raise ValueError("unplanned settings differ across arms")
        prior_settings = common
        run_command(root, name + ".joint", [str(binary), "joint-call", "--threads", "1",
                    "--sample", str(discover), "--disable-cnv", "--output-dir", str(joint)])
        tree_size(arm, MIB, 64)
        validate_fixture(fixture)
        report = observe_native_fixture(reference, fixture / "truth.json",
            discover / "assembly.regions.bed", discover / "candidate.sv.bcf",
            joint / "genotyped.sv.vcf.gz", discover / "contig.alignment.bam",
            arm / "observation.json")
        tree_size(arm, MIB, 64)
        validate_outcome(name, report)
        summaries[name] = {"candidate": report["candidate"], "final": report["final"],
                           "settings_verified": True, "native_output_bytes": tree_size(arm, MIB)}
        new_json(root / (name + ".complete.json"), summaries[name])
    validate_fixture(fixture)
    new_json(root / "result.json", {"status": "COMPLETE_SYNTHETIC_DIAGNOSTIC",
        "experiment": EXPERIMENT, "cases": summaries, "publication_result": False})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    args = parser.parse_args()
    try:
        run(args.root)
    except Exception as error:
        if args.root == ROOT and args.root.is_dir() and not args.root.is_symlink():
            new_json(args.root / "failure.json", {"status": "INCOMPLETE",
                     "error_type": type(error).__name__, "reason": str(error)[:2000],
                     "publication_result": False})
        raise


if __name__ == "__main__":
    main()
