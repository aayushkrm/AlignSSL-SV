"""Bounded synthetic integrity controls for the native-fixture observer."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pysam
import pytest

import analysis.observe_native_fixture as observer


_helper_spec = spec_from_file_location(
    "_native_observer_test_helpers",
    Path(__file__).with_name("test_observe_native_fixture.py"),
)
assert _helper_spec is not None and _helper_spec.loader is not None
_helpers = module_from_spec(_helper_spec)
_helper_spec.loader.exec_module(_helpers)
_fixture = _helpers._fixture
_row = _helpers._row


_BGZF_EOF = bytes.fromhex(
    "1f8b08040000000000ff0600424302001b0003000000000000000000"
)
_INPUT_ROLES = ("reference", "truth", "bed", "candidate", "final", "bam")
_MAX_TEST_INPUT_BYTES = 1024**2


def _bgzf_data_blocks(payload):
    assert payload.endswith(_BGZF_EOF)
    data_end = len(payload) - len(_BGZF_EOF)
    blocks = []
    offset = 0
    while offset < data_end:
        assert payload[offset:offset + 2] == b"\x1f\x8b"
        assert len(payload) >= offset + 18
        block_size = int.from_bytes(payload[offset + 16:offset + 18], "little") + 1
        assert block_size >= 26
        assert offset + block_size <= data_end
        blocks.append((offset, block_size))
        offset += block_size
    assert offset == data_end
    assert blocks
    return blocks


def _observe(case):
    for role in _INPUT_ROLES:
        assert case[role].stat().st_size < _MAX_TEST_INPUT_BYTES
    return observer.observe_native_fixture(
        case["reference"], case["truth"], case["bed"], case["candidate"],
        case["final"], case["bam"], case["report"],
    )


def _write_bgzf_final(case, *, records=1):
    raw_path = case["final"]
    original = raw_path.read_text(encoding="ascii")
    header_end = original.index("#CHROM")
    header = original[:header_end]
    columns = "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSYNTH\n"
    rows = "".join(
        _row(1500, "A", "A" * 61, filt="PASS", gt="0/1")
        for _ in range(records)
    )
    raw_path.write_text(header + columns + rows, encoding="ascii")
    assert raw_path.stat().st_size < _MAX_TEST_INPUT_BYTES

    compressed_path = raw_path.with_suffix(".vcf.gz")
    pysam.tabix_compress(str(raw_path), str(compressed_path), force=False)
    case["final"] = compressed_path
    return compressed_path


def test_truncated_bgzf_final_vcf_is_rejected_without_report(tmp_path):
    case = _fixture(tmp_path)
    compressed = _write_bgzf_final(case, records=1200)
    payload = compressed.read_bytes()
    blocks = _bgzf_data_blocks(payload)
    assert len(blocks) >= 2

    last_start, last_size = blocks[-1]
    compressed.write_bytes(payload[:last_start + last_size - 12])

    with pytest.raises(observer.FixtureError):
        _observe(case)

    assert not case["report"].exists()


@pytest.mark.parametrize("damage", ["truncated", "corrupt_crc"])
def test_damaged_bam_is_rejected_without_report(tmp_path, damage):
    case = _fixture(tmp_path)
    payload = case["bam"].read_bytes()
    blocks = _bgzf_data_blocks(payload)
    last_start, last_size = blocks[-1]

    if damage == "truncated":
        case["bam"].write_bytes(payload[:last_start + last_size - 12])
    else:
        corrupted = bytearray(payload)
        corrupted[last_start + last_size - 8] ^= 0x01
        case["bam"].write_bytes(corrupted)

    with pytest.raises(observer.FixtureError):
        _observe(case)

    assert not case["report"].exists()


def test_malformed_tail_in_plain_vcf_is_not_accepted_as_valid_prefix(tmp_path):
    case = _fixture(tmp_path)
    assert case["final"].suffix == ".vcf"
    case["final"].write_bytes(
        case["final"].read_bytes() + b"chrSynthetic\t1501\t.\tA\t"
    )

    with pytest.raises(observer.FixtureError):
        _observe(case)

    assert not case["report"].exists()


def test_duplicate_truth_key_is_rejected_without_report(tmp_path):
    case = _fixture(tmp_path)
    truth = case["truth"].read_text(encoding="utf-8")
    assert '"version": 1,' in truth
    case["truth"].write_text(
        truth.replace('"version": 1,', '"version": 1, "version": 1,', 1),
        encoding="utf-8",
    )

    with pytest.raises(observer.FixtureError, match="duplicate key"):
        _observe(case)

    assert not case["report"].exists()


@pytest.mark.parametrize(
    "old, new",
    [
        ('"version": 1,', '"version": true,'),
        ('"reference_length": 4000,', '"reference_length": 4000.0,'),
        ('"sample": "SYNTH"', '"sample": "SYNTH", "unexpected": 1'),
    ],
    ids=("boolean-integer", "float-integer", "unknown-field"),
)
def test_truth_schema_rejects_permissive_types_and_unknown_fields(
    tmp_path, old, new
):
    case = _fixture(tmp_path)
    truth = case["truth"].read_text(encoding="utf-8")
    assert old in truth
    case["truth"].write_text(truth.replace(old, new, 1), encoding="utf-8")

    with pytest.raises(observer.FixtureError, match="fixed version-1 synthetic scope"):
        _observe(case)

    assert not case["report"].exists()


def _write_mixed_format_final(case, *, format_fields, sample_value):
    original = case["final"].read_text(encoding="ascii")
    header_end = original.index("#CHROM")
    header = original[:header_end]
    header += (
        '##FORMAT=<ID=DP,Number=1,Type=Integer,Description="read depth">\n'
        '##FORMAT=<ID=AD,Number=R,Type=Integer,Description="allelic depths">\n'
    )
    columns = "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSYNTH\n"
    row = _row(1500, "A", "A" * 61, filt="PASS").rstrip("\n")
    case["final"].write_text(
        header + columns + row + f"\t{format_fields}\t{sample_value}\n",
        encoding="ascii",
    )


@pytest.mark.parametrize(
    "format_fields, sample_value, recovered",
    [
        ("DP:AD", "40:20,20", False),
        ("GT:DP", "1/1:40", False),
        ("GT:DP", "0/1:40", True),
    ],
    ids=("missing-GT", "wrong-GT", "mixed-FORMAT-control"),
)
def test_plain_mixed_format_requires_heterozygous_gt_for_recovery(
    tmp_path, format_fields, sample_value, recovered
):
    case = _fixture(tmp_path)
    _write_mixed_format_final(
        case, format_fields=format_fields, sample_value=sample_value
    )

    result = _observe(case)

    assert result["complete_parse"] is True
    assert result["final"]["exact_allele_records"] == 1
    assert result["final"]["pass_exact_allele_records"] == 1
    assert result["final"]["heterozygous_gt_0_1_or_1_0_exact_records"] == int(recovered)
    assert result["final"]["pass_heterozygous_exact_allele_records"] == int(recovered)
    assert result["final"]["exact_pass_heterozygous_recovery_state"] == (
        "RECOVERED" if recovered else "EXACT_ALLELE_PRESENT_ENDPOINT_NOT_MET"
    )
