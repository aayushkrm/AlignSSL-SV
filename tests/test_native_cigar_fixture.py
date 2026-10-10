import hashlib
import json
import os
from pathlib import Path

import pysam
import pytest

from analysis.native_cigar_fixture import (
    MAX_OUTPUT_BYTES,
    SEED,
    create_fixture,
    main,
    validate_fixture,
)


FROZEN_REFERENCE_SHA256 = "1e9e223b565b9f0847946d777a5c7fd4f2ba09f076174e4fab96f473156fe9ef"


def _rewrite_bam(bam_path, temp_dir, mutate):
    replacement = temp_dir / "mutated.bam"
    with pysam.AlignmentFile(str(bam_path), "rb") as source:
        with pysam.AlignmentFile(str(replacement), "wb", header=source.header) as output:
            for read in source.fetch(until_eof=True):
                mutate(read)
                output.write(read)
    pysam.index(str(replacement))
    original_index = Path(str(bam_path) + ".bai")
    replacement_index = Path(str(replacement) + ".bai")
    original_index.unlink()
    os.replace(replacement, bam_path)
    os.replace(replacement_index, original_index)


def test_create_is_deterministic_and_validates(tmp_path):
    first = create_fixture(tmp_path / "first")
    second = create_fixture(tmp_path / "second")
    validate_fixture(first)
    validate_fixture(second)

    first_manifest = (first / "manifest.json").read_bytes()
    assert first_manifest == (second / "manifest.json").read_bytes()
    # Freeze scientific content, not compression bytes across HTSlib/zlib stacks.
    truth = json.loads((first / "truth.json").read_text())
    assert truth["reference_sha256"] == FROZEN_REFERENCE_SHA256
    assert json.loads(first_manifest)["files"]["truth.json"]["sha256"] == hashlib.sha256(
        (first / "truth.json").read_bytes()
    ).hexdigest()
    assert SEED == 1729
    assert sum(path.stat().st_size for path in first.iterdir()) <= MAX_OUTPUT_BYTES


def test_cli_creates_then_validates_fixture(tmp_path, capsys):
    output = tmp_path / "from_cli"
    assert main(["--output-dir", str(output)]) == 0
    assert "Validated deterministic CIGAR fixture" in capsys.readouterr().out
    validate_fixture(output)


def test_creation_refuses_existing_directory_and_preserves_contents(tmp_path):
    output = tmp_path / "existing"
    output.mkdir()
    sentinel = output / "keep.txt"
    sentinel.write_text("keep", encoding="utf-8")

    with pytest.raises(FileExistsError):
        create_fixture(output)
    assert sentinel.read_text(encoding="utf-8") == "keep"
    assert list(output.iterdir()) == [sentinel]


def test_creation_refuses_symlink_destination(tmp_path):
    target = tmp_path / "target"
    target.mkdir()
    link = tmp_path / "linked-output"
    link.symlink_to(target, target_is_directory=True)

    with pytest.raises(FileExistsError):
        create_fixture(link)
    assert link.is_symlink()
    assert list(target.iterdir()) == []


def test_creation_refuses_symlink_parent(tmp_path):
    target = tmp_path / "target"
    target.mkdir()
    parent = tmp_path / "parent"
    parent.symlink_to(target, target_is_directory=True)
    with pytest.raises(ValueError, match="ancestors"):
        create_fixture(parent / "fixture")
    assert list(target.iterdir()) == []


@pytest.mark.parametrize(
    "mutation, expected_message",
    [
        ("sequence", "sequence mismatch"),
        ("quality", "quality mismatch"),
        ("NM", "tags mismatch"),
        ("MD", "tags mismatch"),
        ("CIGAR", "CIGAR mismatch"),
        ("MAPQ", "MAPQ mismatch"),
        ("flag", "primary flag"),
        ("RG", "tags mismatch"),
        ("start", "start mismatch"),
        ("name", "unexpected read name"),
    ],
)
def test_validator_rejects_record_mutations(tmp_path, mutation, expected_message):
    output = create_fixture(tmp_path / "fixture")
    bam_path = output / "canonical.bam"

    def change(read):
        if mutation == "sequence" and read.query_name == "REF000":
            sequence = list(read.query_sequence)
            sequence[0] = "A" if sequence[0] != "A" else "C"
            qualities = list(read.query_qualities)
            read.query_sequence = "".join(sequence)
            read.query_qualities = qualities
        elif mutation == "quality" and read.query_name == "REF000":
            qualities = list(read.query_qualities)
            qualities[0] = 39
            read.query_qualities = qualities
        elif mutation == "NM" and read.query_name == "REF000":
            read.set_tag("NM", 1, value_type="i")
        elif mutation == "MD" and read.query_name == "REF000":
            read.set_tag("MD", "0A", value_type="Z")
        elif mutation == "CIGAR" and read.query_name == "ALT000":
            cigar = list(read.cigartuples)
            cigar[0] = (pysam.CMATCH, cigar[0][1])
            read.cigartuples = cigar
        elif mutation == "MAPQ" and read.query_name == "REF000":
            read.mapping_quality = 59
        elif mutation == "flag" and read.query_name == "REF000":
            read.flag = 16
        elif mutation == "RG" and read.query_name == "REF000":
            read.set_tag("RG", "OTHER", value_type="Z")
        elif mutation == "start" and read.query_name == "ALT000":
            read.reference_start -= 1
        elif mutation == "name" and read.query_name == "REF000":
            read.query_name = "UNEXPECTED"

    _rewrite_bam(bam_path, tmp_path, change)
    with pytest.raises(ValueError, match=expected_message):
        validate_fixture(output)
