import hashlib
import json

import pytest

import analysis.breakinator_native_controls as controls
from analysis.breakinator_native_controls import (
    BAM_NAME,
    RELEASE_ASSET_BYTES,
    RELEASE_ASSET_SHA256,
    UPSTREAM_COMMIT,
    UPSTREAM_SEMANTICS,
    UPSTREAM_TAG,
    create_controls_bam,
    parse_native_report,
    run_native_controls,
    validate_expected_controls,
)


REPORT = (
    "#Break1_chr\tBreak1_loc\tBreak_direction\tBreak2_chr\tBreak2_loc\tMapQ"
    "\tRead_ID\tClassification\tbreak1_read\tbreak2_read\n"
    "chrSynthetic\t1500\t><\tchrSynthetic\t1500\t60\t10_foldback_center"
    "\tFoldback\t500\t500\n"
    "chrSynthetic\t2250\t><\tchrSynthetic\t2250\t60\t20_foldback_j250"
    "\tPass\t250\t250\n"
    "chrSynthetic\t3500\t>>\tchrOther\t4000\t60\t30_two_chromosomes"
    "\tChimeric\t500\t500\n"
)

SUMMARY = """Breakinator summary report:
Num reads passed filter: 4
Num breakpoints detected: 3 on 3 unique reads
Num Foldback READS detected: 1  (25.000% of all reads)
Num Foldback BREAKPOINTS detected: 1  (33.333% of all breakpoints)
Num Chimeric READS detected: 1  (25.000% of all reads)
Num chimeric BREAKPOINTS detected: 1  (33.333% of all breakpoints)
"""


def _mock_binary(path, *, fail=False):
    source = (
        "#!/usr/bin/env python3\n"
        "import pathlib, sys\n"
        "if sys.argv[1:] == ['--version']:\n"
        "    print('breakinator 1.0')\n"
        "    raise SystemExit(0)\n"
        "expected = ['-i', 'controls.namesorted.bam', '-o', 'native-report.txt', "
        "'--rcoord', '-t', '1']\n"
        "if sys.argv[1:] != expected:\n"
        "    print('wrong native argv: ' + repr(sys.argv[1:]), file=sys.stderr)\n"
        "    raise SystemExit(19)\n"
        "if not pathlib.Path('controls.namesorted.bam').is_file():\n"
        "    print('missing BAM', file=sys.stderr)\n"
        "    raise SystemExit(20)\n"
    )
    if fail:
        source += "print('native failed', file=sys.stderr)\nraise SystemExit(7)\n"
    else:
        source += (
            f"pathlib.Path('native-report.txt').write_text({REPORT!r}, encoding='utf-8')\n"
            f"print({SUMMARY!r}, end='')\n"
        )
    path.write_text(source, encoding="utf-8")
    path.chmod(0o755)
    return path


def test_source_and_release_asset_are_pinned():
    assert UPSTREAM_TAG == "v1.1.1"
    assert UPSTREAM_COMMIT == "2a5b7138aee9368c6c613c0837f3d8152437957c"
    assert RELEASE_ASSET_BYTES == 3_547_379
    assert RELEASE_ASSET_SHA256 == (
        "00747b208e25887eac9e61db57496085d2a593cb6899e1b2940ca9ab1c9c2310"
    )
    assert "consecutive equal-QNAME" in UPSTREAM_SEMANTICS["qname_groups"]
    assert "supplementary records are retained" in UPSTREAM_SEMANTICS["filters"]
    assert "r2_loc to both local variables" in UPSTREAM_SEMANTICS["symmetric_window_detail"]


def test_bam_has_full_query_records_and_expected_name_sorted_geometry(tmp_path):
    pysam = pytest.importorskip("pysam")
    bam_path = create_controls_bam(tmp_path / BAM_NAME)
    with pysam.AlignmentFile(bam_path, "rb") as bam:
        assert bam.header.to_dict()["HD"]["SO"] == "queryname"
        records = list(bam.fetch(until_eof=True))

    assert len(records) == 7
    assert [record.query_name for record in records] == sorted(
        record.query_name for record in records
    )
    by_name = {}
    for record in records:
        by_name.setdefault(record.query_name, []).append(record)
        assert len(record.query_sequence) == 1000
        assert len(record.query_qualities) == 1000
        assert record.get_tag("RG") == "ABI"
        assert record.get_tag("NM") == 0
        assert not record.is_secondary

    assert len(by_name["00_reference"]) == 1
    assert by_name["00_reference"][0].cigarstring == "1000M"
    center = by_name["10_foldback_center"]
    assert [record.flag for record in center] == [0, 0x810]
    assert [record.cigarstring for record in center] == ["500M500S", "500M500S"]
    assert all(record.is_supplementary or index == 0 for index, record in enumerate(center))
    assert all(record.has_tag("SA") for record in center)
    offcenter = by_name["20_foldback_j250"]
    assert [record.flag for record in offcenter] == [0, 0x810]
    assert [record.cigarstring for record in offcenter] == ["250M750S", "750M250S"]
    chimera = by_name["30_two_chromosomes"]
    assert [record.reference_name for record in chimera] == ["chrSynthetic", "chrOther"]
    assert [record.flag for record in chimera] == [0, 0x800]
    assert all(record.has_tag("SA") for record in chimera)


def test_raw_v111_report_parser_keeps_native_and_semantic_classes():
    calls = parse_native_report(REPORT)
    assert [(call.read_id, call.native_class, call.class_name) for call in calls] == [
        ("10_foldback_center", "Foldback", "PutativeFoldback"),
        ("20_foldback_j250", "Pass", "TrueBreak"),
        ("30_two_chromosomes", "Chimeric", "PutativeChimeric"),
    ]
    assert [(call.break1_loc, call.break2_loc, call.break1_read, call.break2_read)
            for call in calls] == [
        (1500, 1500, 500, 500),
        (2250, 2250, 250, 250),
        (3500, 4000, 500, 500),
    ]
    validate_expected_controls(calls, SUMMARY)


@pytest.mark.parametrize("bad_report", [
    REPORT.replace("Foldback", "Unrecognized", 1),
    REPORT.replace("#Break1_chr", "Break1_chr", 1),
    REPORT + "unknown nonempty row\n",
    REPORT.replace("\t500\t500\n", "\t500\n", 1),
])
def test_report_parser_rejects_unknown_or_malformed_lines(bad_report):
    with pytest.raises(ValueError):
        parse_native_report(bad_report)


def test_runner_uses_exact_native_route_and_preserves_evidence(tmp_path, monkeypatch):
    def mock_bam(path):
        path.write_bytes(b"mock ABI BAM placeholder\n")
        return path

    monkeypatch.setattr(controls, "create_controls_bam", mock_bam)
    binary = _mock_binary(tmp_path / "mock-breakinator")
    output_dir = tmp_path / "out"
    output_dir.mkdir()

    manifest = run_native_controls(binary, output_dir)
    assert manifest["native_command"]["argv"][1:] == [
        "-i", BAM_NAME, "-o", "native-report.txt", "--rcoord", "-t", "1",
    ]
    assert manifest["native_command"]["exit_code"] == 0
    assert manifest["native_command"]["report_sha256"] == hashlib.sha256(
        REPORT.encode("utf-8")
    ).hexdigest()
    assert manifest["binary"]["sha256"] == hashlib.sha256(binary.read_bytes()).hexdigest()
    assert (output_dir / "native-report.txt").read_text(encoding="utf-8") == REPORT
    assert (output_dir / "native-stdout.txt").read_text(encoding="utf-8") == SUMMARY
    assert (output_dir / "native-stderr.txt").read_bytes() == b""
    assert (output_dir / "native-version.stdout.txt").read_text() == "breakinator 1.0\n"
    saved = json.loads((output_dir / "run.json").read_text(encoding="utf-8"))
    assert saved["upstream"]["release_asset_sha256"] == RELEASE_ASSET_SHA256
    assert saved["native_command"]["exit_code"] == 0
    assert saved["validation_error"] is None


def test_runner_records_native_failure_before_raising(tmp_path, monkeypatch):
    def mock_bam(path):
        path.write_bytes(b"mock ABI BAM placeholder\n")
        return path

    monkeypatch.setattr(controls, "create_controls_bam", mock_bam)
    binary = _mock_binary(tmp_path / "mock-breakinator", fail=True)
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    with pytest.raises(RuntimeError, match="native control command failed"):
        run_native_controls(binary, output_dir)
    manifest = json.loads((output_dir / "run.json").read_text(encoding="utf-8"))
    assert manifest["native_command"]["exit_code"] == 7
    assert (output_dir / "native-stderr.txt").read_text() == "native failed\n"
    assert (output_dir / "native-report.txt").read_bytes() == b""


def test_runner_requires_existing_empty_output_directory(tmp_path):
    binary = _mock_binary(tmp_path / "mock-breakinator")
    with pytest.raises(ValueError, match="already exist and be empty"):
        run_native_controls(binary, tmp_path / "missing")

    output_dir = tmp_path / "not-empty"
    output_dir.mkdir()
    (output_dir / "keep.txt").write_text("keep")
    with pytest.raises(ValueError, match="must be empty"):
        run_native_controls(binary, output_dir)
    assert (output_dir / "keep.txt").read_text() == "keep"


def test_runner_rejects_binary_symlink(tmp_path):
    target = _mock_binary(tmp_path / "real-binary")
    link = tmp_path / "binary-link"
    link.symlink_to(target)
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    with pytest.raises(ValueError, match="regular non-link"):
        run_native_controls(link, output_dir)
