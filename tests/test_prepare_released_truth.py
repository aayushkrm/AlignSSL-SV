import gzip
import hashlib
import json
import subprocess
import sys
import uuid
from pathlib import Path

import pytest

from analysis.prepare_released_truth import (
    GIB,
    GZIP_READ_AHEAD_RESERVATION_BYTES,
    MAX_BED_BYTES,
    MAX_LINE_BYTES,
    MAX_TRUTH_DECODED_BYTES,
    TruthPreparationError,
    main,
    prepare_released_truth,
)
import analysis.prepare_released_truth as preparer_module
from analysis.released_truth_units import truth_identity


SAMPLE = "SYNTHETIC_SAMPLE"
HEADER = (
    b"##fileformat=VCFv4.2\n"
    b"##contig=<ID=chr1,length=10000>\n"
    b"##source=synthetic-fixture\n"
    b"#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\t"
    + SAMPLE.encode("ascii") + b"\n"
)
CURRENT_BED = b"chr1\t0\t10000\nchrX\t0\t10000\n"
TIER1_BED = b"chr1\t5000\t10000\n"


def record(
    chrom="chr1", pos=2501, original_id="id", *, alt=None, fmt="GT",
    sample="0/1", info="DP=10", ending=b"\n",
):
    if alt is None:
        alt = "A" + "C" * 50
    fields = [chrom, str(pos), original_id, "A", alt, ".", "PASS", info, fmt, sample]
    return "\t".join(fields).encode("utf-8") + ending


def gzip_bytes(raw: bytes) -> bytes:
    return gzip.compress(raw, mtime=0)


def make_case(
    tmp_path: Path,
    raw_vcf: bytes = HEADER,
    *,
    current_bed: bytes = CURRENT_BED,
    tier1_bed: bytes = TIER1_BED,
    compressed: bytes | None = None,
    protocol_updates: dict | None = None,
):
    inputs = tmp_path / "inputs"
    inputs.mkdir(exist_ok=True)
    truth_path = inputs / "synthetic-truth.vcf.gz"
    current_path = inputs / "synthetic-current.bed"
    tier1_path = inputs / "synthetic-tier1.bed"
    protocol_path = inputs / "synthetic-protocol.json"
    compressed = gzip_bytes(raw_vcf) if compressed is None else compressed
    truth_path.write_bytes(compressed)
    current_path.write_bytes(current_bed)
    tier1_path.write_bytes(tier1_bed)

    max_truth = 100_000
    max_bed = 4_096
    protocol = {
        "truth_preparation_approved": True,
        "independent_approval_ref": "synthetic-review:fixture-01",
        "truth_sha256": hashlib.sha256(compressed).hexdigest(),
        "current_bed_sha256": hashlib.sha256(current_bed).hexdigest(),
        "tier1_bed_sha256": hashlib.sha256(tier1_bed).hexdigest(),
        "expected_truth_sample_label": SAMPLE,
        "unknown_contig_length_policy": (
            "do_not_infer_n_plus_one_without_unique_declared_length"
        ),
        "max_truth_decoded_bytes": max_truth,
        "max_truth_compressed_bytes": 1_000_000,
        "max_line_bytes": 4_096,
        "charged_prior_global_decoded_bytes": 0,
        "truth_preparation_reservation_bytes": (max_truth + 1 + GZIP_READ_AHEAD_RESERVATION_BYTES
                                                + 2 * (max_bed + 1)),
        "max_bed_bytes": max_bed,
        "max_bed_rows": 1_000,
        "max_mapping_bytes": 1_000_000,
    }
    if protocol_updates:
        protocol.update(protocol_updates)
    protocol_path.write_text(json.dumps(protocol, sort_keys=True), encoding="utf-8")
    return {
        "truth_path": truth_path,
        "current_path": current_path,
        "tier1_path": tier1_path,
        "protocol_path": protocol_path,
        "protocol": protocol,
        "protocol_sha256": hashlib.sha256(protocol_path.read_bytes()).hexdigest(),
        "outdir": tmp_path / "prepared",
        "raw_vcf": raw_vcf,
        "compressed": compressed,
    }


def prepare(case, *, outdir=None):
    return prepare_released_truth(
        case["truth_path"],
        case["current_path"],
        case["tier1_path"],
        outdir or case["outdir"],
        case["protocol_path"],
        case["protocol_sha256"],
    )


def replace_id(raw: bytes, identity: str) -> bytes:
    if raw.endswith(b"\r\n"):
        ending, body = b"\r\n", raw[:-2]
    elif raw.endswith(b"\n"):
        ending, body = b"\n", raw[:-1]
    else:
        ending, body = b"", raw
    fields = body.split(b"\t")
    fields[2] = identity.encode("ascii")
    return b"\t".join(fields) + ending


def test_success_preserves_source_rows_and_maps_every_ordinal_without_alleles(tmp_path):
    rows = [
        record(pos=7501, original_id="duplicate", sample="1|0:11", fmt="GT:DP", ending=b"\r\n"),
        record(pos=2501, original_id="duplicate", sample="0/1"),
        record(pos=4900, original_id="boundary"),
        record(chrom="chrX", pos=2501, original_id="nonautosome"),
        record(pos=2700, original_id="multi", alt="A," + "G" * 50),
        record(pos=2800, original_id="no-format-gt", fmt=".", sample="."),
        record(pos=2900, original_id="partial-gt", sample="0/."),
    ]
    raw_vcf = HEADER + b"".join(rows)
    case = make_case(tmp_path, raw_vcf)

    inventory = prepare(case)

    ids = [truth_identity(hashlib.sha256(case["compressed"]).hexdigest(), i)
           for i in range(1, len(rows) + 1)]
    expected_vcf = HEADER + replace_id(rows[0], ids[0]) + replace_id(rows[1], ids[1])
    vcf_path = case["outdir"] / "eligible_truth.vcf"
    map_path = case["outdir"] / "truth_record_map.jsonl"
    inventory_path = case["outdir"] / "truth_preparation_inventory.json"
    assert vcf_path.read_bytes() == expected_vcf

    mapping = [json.loads(line) for line in map_path.read_text(encoding="utf-8").splitlines()]
    assert [entry["ordinal"] for entry in mapping] == list(range(1, 8))
    assert [entry["identity"] for entry in mapping] == ids
    assert mapping[0] == {
        "ordinal": 1, "identity": ids[0], "original_id": "duplicate",
        "territory": "intersection",
    }
    assert mapping[1]["territory"] == "current_minus_tier1"
    assert mapping[2]["territory"] == "boundary_or_mixed_territory"
    assert mapping[3]["exclusion_reason"] == "out_of_scope_chromosome"
    assert mapping[4]["exclusion_reason"] == "multiallelic"
    assert mapping[5]["exclusion_reason"] == "missing_or_partial_gt"
    assert mapping[6]["exclusion_reason"] == "missing_or_partial_gt"
    assert b"C" * 50 not in map_path.read_bytes()

    assert inventory["status"] == "complete"
    assert inventory["body_records"] == 7
    assert inventory["truth_decoded_bytes"] == len(raw_vcf)
    assert inventory["eligible_counts"] == {"current_minus_tier1": 1, "intersection": 1}
    assert inventory["boundary_counts"] == {
        "boundary_or_mixed_territory": 1,
        "ineligible_boundary": 0,
    }
    assert inventory["exclusion_counts"] == {
        "out_of_scope_chromosome": 1,
        "multiallelic": 1,
        "missing_or_partial_gt": 2,
    }
    assert inventory["gt_absent_records"] == 1
    assert inventory["gt_duplicate_records"] == 0
    assert inventory["sample_label_validation"] == "exact_protocol_string_match_only"
    assert inventory["contig_dictionary_validation"] == (
        "bed_autosomes_validated_against_truth_header_reference_gate_still_required"
    )
    assert inventory["unknown_contig_length_policy"] == (
        "do_not_infer_n_plus_one_without_unique_declared_length"
    )
    assert inventory["current_bed_counts"] == {
        "rows": 2, "autosomal_rows": 1, "non_autosomal_rows": 1,
    }
    assert inventory["eligible_truth_vcf_sha256"] == hashlib.sha256(expected_vcf).hexdigest()
    assert inventory["truth_record_map_sha256"] == hashlib.sha256(map_path.read_bytes()).hexdigest()
    assert json.loads(inventory_path.read_text(encoding="utf-8")) == inventory
    assert not list(case["outdir"].glob("*.partial"))


def test_concatenated_gzip_members_are_read_as_one_original_stream(tmp_path):
    raw_vcf = HEADER + record(pos=2501, original_id="first") + record(pos=7501, original_id="second")
    split = len(raw_vcf) // 2
    compressed = gzip_bytes(raw_vcf[:split]) + gzip_bytes(raw_vcf[split:])
    case = make_case(tmp_path, raw_vcf, compressed=compressed)

    inventory = prepare(case)

    assert inventory["truth_decoded_bytes"] == len(raw_vcf)
    rows = [row for row in (case["outdir"] / "eligible_truth.vcf").read_bytes().splitlines()
            if not row.startswith(b"#")]
    assert [row.split(b"\t")[1] for row in rows] == [b"2501", b"7501"]


def test_telomeric_pos_zero_and_declared_length_plus_one_are_boundary_rows(tmp_path):
    header = HEADER
    rows = [
        record(pos=0, original_id="left-telomere"),
        record(pos=10001, original_id="right-telomere"),
        record(pos=2501, original_id="interior"),
    ]
    case = make_case(tmp_path, header + b"".join(rows))

    inventory = prepare(case)

    mapping_path = case["outdir"] / "truth_record_map.jsonl"
    mapping = [json.loads(line) for line in mapping_path.read_text().splitlines()]
    source_sha = hashlib.sha256(case["compressed"]).hexdigest()
    assert [entry["ordinal"] for entry in mapping] == [1, 2, 3]
    assert [entry["identity"] for entry in mapping] == [
        truth_identity(source_sha, ordinal) for ordinal in (1, 2, 3)
    ]
    assert [entry["original_id"] for entry in mapping] == [
        "left-telomere", "right-telomere", "interior",
    ]
    assert [entry["territory"] for entry in mapping] == [
        "ineligible_boundary", "ineligible_boundary", "current_minus_tier1",
    ]
    assert all("exclusion_reason" not in entry for entry in mapping[:2])
    assert inventory["body_records"] == 3
    assert inventory["boundary_counts"] == {
        "boundary_or_mixed_territory": 0,
        "ineligible_boundary": 2,
    }
    assert inventory["exclusion_counts"] == {}
    assert inventory["truth_decoded_bytes"] == len(header + b"".join(rows))
    assert case["truth_path"].read_bytes() == case["compressed"]
    expected_vcf = header + replace_id(rows[2], truth_identity(source_sha, 3))
    assert (case["outdir"] / "eligible_truth.vcf").read_bytes() == expected_vcf


@pytest.mark.parametrize(
    "contig_lines",
    [
        b"",
        b"##contig=<ID=chr1,length=10000>\n"
        b"##contig=<ID=chr1,length=10000>\n",
    ],
    ids=["missing-length", "duplicate-length"],
)
def test_n_plus_one_requires_unique_declared_contig_length(tmp_path, contig_lines):
    header = HEADER.replace(b"##contig=<ID=chr1,length=10000>\n", b"").replace(
        b"##source=synthetic-fixture\n",
        contig_lines + b"##source=synthetic-fixture\n",
    )
    rows = [
        record(pos=0, original_id="left-telomere"),
        record(pos=10001, original_id="unknown-length"),
    ]
    case = make_case(tmp_path, header + b"".join(rows),
                     current_bed=b"chrX\t0\t10000\n", tier1_bed=b"chrX\t0\t10000\n")

    inventory = prepare(case)

    mapping = [
        json.loads(line)
        for line in (case["outdir"] / "truth_record_map.jsonl")
        .read_text(encoding="utf-8").splitlines()
    ]
    assert [entry["territory"] for entry in mapping] == [
        "ineligible_boundary", "boundary_or_mixed_territory",
    ]
    assert all("exclusion_reason" not in entry for entry in mapping)
    assert inventory["boundary_counts"] == {
        "boundary_or_mixed_territory": 1,
        "ineligible_boundary": 1,
    }
    assert inventory["unknown_contig_length_policy"] == (
        "do_not_infer_n_plus_one_without_unique_declared_length"
    )


def test_unknown_contig_length_policy_must_be_pinned_explicitly(tmp_path):
    case = make_case(tmp_path)
    case["protocol"].pop("unknown_contig_length_policy")
    case["protocol_path"].write_text(
        json.dumps(case["protocol"], sort_keys=True), encoding="utf-8",
    )
    case["protocol_sha256"] = hashlib.sha256(
        case["protocol_path"].read_bytes()
    ).hexdigest()
    case["truth_path"].unlink()

    with pytest.raises(ValueError, match="unknown_contig_length_policy"):
        prepare(case)

    assert not case["outdir"].exists()


@pytest.mark.parametrize("which", ["current", "tier1"])
@pytest.mark.parametrize("bad_bed, message", [
    (b"1\t0\t9000\n", "exact unique"),
    (b"chr1\t0\t10001\n", "exceeds"),
])
def test_bed_namespace_or_bounds_fail_before_first_body_row(tmp_path, which, bad_bed, message):
    kw = {"current_bed" if which == "current" else "tier1_bed": bad_bed}
    case = make_case(tmp_path, HEADER + record(), **kw)
    with pytest.raises(TruthPreparationError, match=message):
        prepare(case)
    report = json.loads((case["outdir"] / "truth_preparation_failure.json").read_text())
    assert report["body_records_seen"] == 0
    assert report["record_map_bytes_written"] == 0


def test_approval_gate_precedes_source_open_and_output_creation(tmp_path):
    case = make_case(
        tmp_path,
        protocol_updates={
            "truth_preparation_approved": False,
            "independent_approval_ref": "",
        },
    )
    case["truth_path"].unlink()

    with pytest.raises(ValueError, match="explicitly true"):
        prepare(case)

    assert not case["outdir"].exists()


def test_approval_reference_is_required_even_when_approval_is_true(tmp_path):
    case = make_case(tmp_path, protocol_updates={"independent_approval_ref": "  "})

    with pytest.raises(ValueError, match="independent_approval_ref"):
        prepare(case)

    assert not case["outdir"].exists()


def test_protocol_hash_is_checked_before_creating_output_or_reading_inputs(tmp_path):
    case = make_case(tmp_path)

    with pytest.raises(ValueError, match="protocol SHA-256 mismatch"):
        prepare_released_truth(
            case["truth_path"], case["current_path"], case["tier1_path"],
            case["outdir"], case["protocol_path"], "0" * 64,
        )

    assert not case["outdir"].exists()


@pytest.mark.parametrize(
    ("updates", "message"),
    [
        ({"max_truth_decoded_bytes": MAX_TRUTH_DECODED_BYTES + 1}, "max_truth_decoded_bytes"),
        ({"max_line_bytes": MAX_LINE_BYTES + 1}, "max_line_bytes"),
        ({"max_bed_bytes": MAX_BED_BYTES + 1}, "max_bed_bytes"),
        ({"charged_prior_global_decoded_bytes": 6 * GIB}, "prior global charge"),
    ],
)
def test_protocol_resource_bounds_are_typed_and_fail_closed(tmp_path, updates, message):
    case = make_case(tmp_path, protocol_updates=updates)

    with pytest.raises(ValueError, match=message):
        prepare(case)

    assert not case["outdir"].exists()


def test_reservation_must_cover_caps_and_fit_global_budget(tmp_path):
    case = make_case(tmp_path, protocol_updates={"truth_preparation_reservation_bytes": 1})

    with pytest.raises(ValueError, match="must cover the truth cap"):
        prepare(case)

    assert not case["outdir"].exists()


def test_reservation_includes_one_overflow_probe_for_each_bed(tmp_path):
    max_truth = 100_000
    max_bed = 4_096
    case = make_case(
        tmp_path,
        protocol_updates={
            "truth_preparation_reservation_bytes": (max_truth + 1 + GZIP_READ_AHEAD_RESERVATION_BYTES
                                                    + 2 * max_bed),
        },
    )

    with pytest.raises(ValueError, match="both BED caps plus overflow probes"):
        prepare(case)

    assert not case["outdir"].exists()


def test_bed_row_limit_is_enforced_before_truth_body_decode(tmp_path):
    case = make_case(tmp_path, protocol_updates={"max_bed_rows": 1})

    with pytest.raises(TruthPreparationError, match="1-row BED limit") as caught:
        prepare(case)

    report = json.loads(caught.value.report_path.read_text(encoding="utf-8"))
    assert report["truth_decoded_bytes_delivered"] == 0
    assert report["bed_decoded_bytes_read"] == len(CURRENT_BED)


def test_truth_and_bed_pins_are_checked_and_failures_are_reported(tmp_path):
    case = make_case(tmp_path)
    case["protocol"]["truth_sha256"] = "0" * 64
    case["protocol_path"].write_text(json.dumps(case["protocol"]), encoding="utf-8")
    case["protocol_sha256"] = hashlib.sha256(case["protocol_path"].read_bytes()).hexdigest()

    with pytest.raises(TruthPreparationError, match="truth compressed-byte SHA-256 mismatch") as caught:
        prepare(case)

    report = json.loads(caught.value.report_path.read_text(encoding="utf-8"))
    assert report["status"] == "incomplete"
    assert report["truth_decoded_bytes_delivered"] == 0
    assert report["truth_preparation_reservation_bytes"] == case["protocol"][
        "truth_preparation_reservation_bytes"
    ]
    assert not list(case["outdir"].glob("*.partial"))


def test_bed_hash_mismatch_is_reported_before_truth_body_decode(tmp_path):
    case = make_case(tmp_path)
    case["protocol"]["current_bed_sha256"] = "f" * 64
    case["protocol_path"].write_text(json.dumps(case["protocol"]), encoding="utf-8")
    case["protocol_sha256"] = hashlib.sha256(case["protocol_path"].read_bytes()).hexdigest()

    with pytest.raises(TruthPreparationError, match="current.bed SHA-256 mismatch") as caught:
        prepare(case)

    report = json.loads(caught.value.report_path.read_text(encoding="utf-8"))
    assert report["truth_decoded_bytes_delivered"] == 0
    assert report["bed_decoded_bytes_read"] == len(CURRENT_BED)


def test_bad_gzip_trailer_preserves_partial_vcf_map_and_full_reservation(tmp_path):
    raw_vcf = HEADER + record(pos=2501, original_id="kept")
    bad_empty_member = bytearray(gzip_bytes(b""))
    bad_empty_member[-8] ^= 0x01  # Corrupt a later member after the valid truth member.
    compressed = gzip_bytes(raw_vcf) + bytes(bad_empty_member)
    case = make_case(tmp_path, raw_vcf, compressed=compressed)

    with pytest.raises(TruthPreparationError) as caught:
        prepare(case)

    report = json.loads(caught.value.report_path.read_text(encoding="utf-8"))
    assert report["status"] == "incomplete"
    assert report["truth_preparation_reservation_bytes"] == case["protocol"][
        "truth_preparation_reservation_bytes"
    ]
    assert "eligible_truth.vcf.partial" in report["partial_files_preserved"]
    assert "truth_record_map.jsonl.partial" in report["partial_files_preserved"]
    partial_vcf = case["outdir"] / "eligible_truth.vcf.partial"
    partial_map = case["outdir"] / "truth_record_map.jsonl.partial"
    assert partial_vcf.read_bytes().startswith(HEADER)
    assert json.loads(partial_map.read_text(encoding="utf-8"))["ordinal"] == 1


def test_overlong_body_line_is_counted_and_partial_report_is_preserved(tmp_path):
    long_line = record(pos=2501, info="x" * 250)
    raw_vcf = HEADER + long_line
    case = make_case(
        tmp_path,
        raw_vcf,
        protocol_updates={"max_line_bytes": 128},
    )

    with pytest.raises(TruthPreparationError, match="line exceeds 128 bytes") as caught:
        prepare(case)

    report = json.loads(caught.value.report_path.read_text(encoding="utf-8"))
    assert report["body_records_seen"] == 1
    assert report["truth_decoded_bytes_delivered"] <= len(HEADER) + 129
    assert (case["outdir"] / "eligible_truth.vcf.partial").read_bytes() == HEADER


def test_truth_decoded_budget_counts_header_and_stops_at_one_overflow_byte(tmp_path):
    row = record(pos=2501)
    raw_vcf = HEADER + row
    cap = len(HEADER) + len(row) - 1
    case = make_case(
        tmp_path,
        raw_vcf,
        protocol_updates={
            "max_truth_decoded_bytes": cap,
            "max_line_bytes": 128,
            "truth_preparation_reservation_bytes": (cap + 1 + GZIP_READ_AHEAD_RESERVATION_BYTES
                                                    + 2 * (4_096 + 1)),
        },
    )

    with pytest.raises(TruthPreparationError, match="decoded-byte budget exceeded") as caught:
        prepare(case)

    report = json.loads(caught.value.report_path.read_text(encoding="utf-8"))
    assert report["truth_decoded_bytes_delivered"] == cap + 1
    assert report["body_records_seen"] == 1
    assert report["truth_preparation_reservation_bytes"] == (
        cap + 1 + GZIP_READ_AHEAD_RESERVATION_BYTES + 2 * (4_096 + 1))


def test_actual_gzip_read_ahead_is_covered_on_early_failure(tmp_path, monkeypatch):
    decoded = []
    add_data = gzip._GzipReader._add_read_data

    def observed(reader, data):
        decoded.append(len(data))
        return add_data(reader, data)

    monkeypatch.setattr(gzip._GzipReader, "_add_read_data", observed)
    cap = len(HEADER) + 64
    case = make_case(tmp_path, HEADER + record(alt="A" + "C" * 20000), protocol_updates={
        "max_truth_decoded_bytes": cap, "max_line_bytes": cap,
        "truth_preparation_reservation_bytes": (
            cap + 1 + GZIP_READ_AHEAD_RESERVATION_BYTES + 2 * (4096 + 1)),
    })
    with pytest.raises(TruthPreparationError, match="decoded-byte"):
        prepare(case)
    report = json.loads((case["outdir"] / "truth_preparation_failure.json").read_text())
    assert sum(decoded) > report["truth_decoded_bytes_delivered"] == cap + 1
    assert sum(decoded) <= cap + 1 + GZIP_READ_AHEAD_RESERVATION_BYTES
    assert report["gzip_read_ahead_reservation_bytes"] == GZIP_READ_AHEAD_RESERVATION_BYTES


def test_header_after_data_is_fatal_and_keeps_prior_eligible_rows(tmp_path):
    first = record(pos=2501, original_id="first")
    raw_vcf = HEADER + first + b"##late-header=value\n"
    case = make_case(tmp_path, raw_vcf)

    with pytest.raises(TruthPreparationError, match="header or comment line after VCF data") as caught:
        prepare(case)

    report = json.loads(caught.value.report_path.read_text(encoding="utf-8"))
    assert report["body_records_seen"] == 2
    partial = (case["outdir"] / "eligible_truth.vcf.partial").read_bytes()
    assert partial == HEADER + replace_id(first, truth_identity(
        hashlib.sha256(case["compressed"]).hexdigest(), 1,
    ))


@pytest.mark.parametrize(
    ("bad_header", "message"),
    [
        (b"##fileformat=VCFv4.2\n#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tOTHER\n", "sample label"),
        (b"##fileformat=VCFv4.2\n#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSYNTHETIC_SAMPLE\tEXTRA\n", "one sample column"),
        (b"##fileformat=VCFv4.2\n#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n", "one FORMAT"),
    ],
)
def test_sample_header_must_match_protocol_and_have_one_sample(tmp_path, bad_header, message):
    case = make_case(tmp_path, bad_header)

    with pytest.raises(TruthPreparationError, match=message):
        prepare(case)

    assert (case["outdir"] / "truth_preparation_failure.json").exists()


@pytest.mark.parametrize(
    ("bad_row", "message"),
    [
        (b"chr1\t-1\tid\tA\tAC\t.\tPASS\t.\tGT\t0/1\n", "POS"),
        (b"chr1\ttext\tid\tA\tAC\t.\tPASS\t.\tGT\t0/1\n", "POS"),
        (b"\t10\tid\tA\tAC\t.\tPASS\t.\tGT\t0/1\n", "CHROM"),
        (b"chr1\t10\tid\tA\tAC\t.\tPASS\t.\tGT:DP\t0/1:10:extra\n", "extra or empty values"),
        (b"chr1\t10\tid\tA\tAC\t.\tPASS\t.\tDP:GT\t10:0/1\n", "GT must be the first"),
    ],
)
def test_malformed_body_chrom_pos_and_format_are_fatal(tmp_path, bad_row, message):
    case = make_case(tmp_path, HEADER + bad_row)

    with pytest.raises(TruthPreparationError, match=message):
        prepare(case)

    report = json.loads((case["outdir"] / "truth_preparation_failure.json").read_text())
    assert report["body_records_seen"] == 1


def test_duplicate_gt_is_counted_then_fails_closed(tmp_path):
    row = record(pos=2501, fmt="GT:GT", sample="0/1:0/1")
    case = make_case(tmp_path, HEADER + row)

    with pytest.raises(TruthPreparationError, match="duplicate GT FORMAT key") as caught:
        prepare(case)

    report = json.loads(caught.value.report_path.read_text(encoding="utf-8"))
    assert report["gt_duplicate_records"] == 1
    assert report["body_records_seen"] == 1


def test_duplicate_non_gt_format_key_is_fatal(tmp_path):
    row = record(pos=2501, fmt="GT:DP:DP", sample="0/1:10:10")
    case = make_case(tmp_path, HEADER + row)

    with pytest.raises(TruthPreparationError, match="duplicate VCF FORMAT key"):
        prepare(case)


def test_valid_trailing_format_omission_is_kept_byte_for_byte(tmp_path):
    row = record(pos=2501, fmt="GT:DP:GQ", sample="0/1")
    raw_vcf = HEADER + row
    case = make_case(tmp_path, raw_vcf)

    inventory = prepare(case)

    identity = truth_identity(hashlib.sha256(case["compressed"]).hexdigest(), 1)
    assert (case["outdir"] / "eligible_truth.vcf").read_bytes() == HEADER + replace_id(row, identity)
    assert inventory["eligible_counts"]["current_minus_tier1"] == 1


def test_truth_mutation_during_body_pass_fails_snapshot_and_hash_gate(tmp_path, monkeypatch):
    raw_vcf = HEADER + record(pos=2501, original_id="mutation-check")
    case = make_case(tmp_path, raw_vcf)
    original_parser = preparer_module._parse_body_line
    changed = False

    def mutate_after_parse(content, *, expected_columns=10):
        nonlocal changed
        result = original_parser(content, expected_columns=expected_columns)
        if not changed:
            with case["truth_path"].open("r+b") as source:
                source.seek(4)  # Change only gzip MTIME; decoded records stay the same.
                value = source.read(1)
                source.seek(4)
                source.write(bytes([value[0] ^ 1]))
                source.flush()
            changed = True
        return result

    monkeypatch.setattr(preparer_module, "_parse_body_line", mutate_after_parse)

    with pytest.raises(TruthPreparationError, match="truth source changed") as caught:
        prepare(case)

    report = json.loads(caught.value.report_path.read_text(encoding="utf-8"))
    assert report["status"] == "incomplete"
    assert report["body_records_seen"] == 1
    assert "eligible_truth.vcf.partial" in report["partial_files_preserved"]


def test_autosome_contig_labels_are_not_renamed_or_aliased(tmp_path):
    raw_vcf = HEADER + record(chrom="chr1", pos=2501)
    current = b"1\t0\t10000\n"
    tier1 = b"1\t5000\t10000\n"
    case = make_case(tmp_path, raw_vcf, current_bed=current, tier1_bed=tier1)

    with pytest.raises(TruthPreparationError, match="exact unique"):
        prepare(case)
    report = json.loads((case["outdir"] / "truth_preparation_failure.json").read_text())
    assert report["body_records_seen"] == 0


def test_outdir_inside_git_is_rejected_without_creation(tmp_path):
    case = make_case(tmp_path)
    repo = Path(__file__).resolve().parents[1]
    candidate = repo / "tests" / f".synthetic-truth-output-{uuid.uuid4().hex}"

    with pytest.raises(ValueError, match="outside Git"):
        prepare(case, outdir=candidate)

    assert not candidate.exists()


def test_existing_outdir_is_never_overwritten(tmp_path):
    case = make_case(tmp_path)
    case["outdir"].mkdir()
    marker = case["outdir"] / "keep.txt"
    marker.write_text("synthetic", encoding="utf-8")

    with pytest.raises(FileExistsError, match="fresh"):
        prepare(case)

    assert marker.read_text(encoding="utf-8") == "synthetic"


def test_cli_runs_the_same_bounded_api(tmp_path, capsys):
    case = make_case(tmp_path, HEADER + record(pos=2501))

    status = main([
        "--truth-path", str(case["truth_path"]),
        "--current-bed", str(case["current_path"]),
        "--tier1-bed", str(case["tier1_path"]),
        "--outdir", str(case["outdir"]),
        "--protocol-path", str(case["protocol_path"]),
        "--protocol-sha256", case["protocol_sha256"],
    ])

    captured = capsys.readouterr()
    assert status == 0
    assert json.loads(captured.out)["status"] == "complete"
    assert captured.err == ""


def test_direct_script_cli_imports_sibling_helper(tmp_path):
    script = Path(preparer_module.__file__)

    result = subprocess.run(
        [sys.executable, "-B", str(script), "--help"],
        cwd=script.parents[1],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "--truth-path" in result.stdout
