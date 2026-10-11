import hashlib
import json
from pathlib import Path

import pytest

import analysis.diagnose_released_truth_metadata as census


HEADER = (
    "##fileformat=VCFv4.2\n"
    '##INFO=<ID=SVLEN,Number=1,Type=Integer,Description="length">\n'
    '##INFO=<ID=SVTYPE,Number=1,Type=String,Description="type">\n'
    '##FORMAT=<ID=GT,Number=1,Type=String,Description="genotype">\n'
    "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tHG002\n"
)
EXPECTED_PROTOCOL = {
    "diagnosis_approved": True,
    "purpose": census.PURPOSE,
    "expected_sample": "HG002",
    "source_read_reservation_bytes": census.RESERVATION,
}


def row(number, info, *, gt="0/1", identity=None, pos=100):
    identity = identity or f"{number:064x}"
    return (f"1\t{pos}\t{identity}\tA{'C' * 60}\tA\t.\tPASS\t{info}"
            f"\tGT\t{gt}\n")


def fixture(tmp_path, body, header=HEADER):
    raw = (header + body).encode("utf-8")
    truth = tmp_path / "synthetic.vcf"
    truth.write_bytes(raw)
    digest = hashlib.sha256(raw).hexdigest()
    expected = {
        "expected_records": body.count("\n"),
        "expected_input_bytes": len(raw),
        "eligible_truth_sha256": digest,
    }
    protocol_value = dict(EXPECTED_PROTOCOL, expected_records=expected["expected_records"],
                          expected_input_bytes=len(raw), eligible_truth_sha256=digest,
                          source_script_sha256=hashlib.sha256(Path(census.__file__).read_bytes()).hexdigest(),
                          truth_units_script_sha256=hashlib.sha256(
                              Path(census.__file__).with_name("released_truth_units.py").read_bytes()
                          ).hexdigest())
    protocol = tmp_path / "synthetic-protocol.json"
    protocol_bytes = (json.dumps(protocol_value, sort_keys=True) + "\n").encode("utf-8")
    protocol.write_bytes(protocol_bytes)
    protocol_sha = hashlib.sha256(protocol_bytes).hexdigest()
    report = tmp_path / "report.json"
    return truth, protocol, protocol_sha, report, expected, raw


def run_fixture(tmp_path, body):
    truth, protocol, protocol_sha, report, expected, raw = fixture(tmp_path, body)
    result = census._run_diagnosis(truth, protocol, protocol_sha, report, expected)
    return result, json.loads(report.read_text()), raw


def test_complete_literal_census_counts_overlapping_flags_and_first_row(tmp_path):
    body = "".join((
        row(1, "SVTYPE=DEL;SVLEN=60"),                         # abs agrees, sign differs
        row(2, "SVTYPE=DEL"),                                  # absent SVLEN
        row(3, "SVTYPE=DEL;SVLEN=."),                          # dot SVLEN
        row(4, "SVTYPE=DEL;SVLEN=-59"),                        # wrong magnitude
        row(5, "SVTYPE=DEL;SVLEN=-60,abc"),                    # multivalue plus noninteger
        row(6, "SVTYPE=DEL;SVLEN=-60;SVLEN=abc"),              # duplicate plus noninteger
        row(7, "SVTYPE=INS;SVLEN=-60"),                        # type disagreement
        row(8, "SVTYPE=DEL,INS;SVLEN=-60"),                     # multivalue type
        row(9, "SVTYPE=DEL;SVLEN=-60", gt="0/0"),              # eligibility issue
        row(10, "SVTYPE=DEL;SVLEN=-60"),                       # clean
        row(11, "SVLEN=-60"),                                  # absent SVTYPE
        row(12, "SVTYPE=DEL;SVLEN=abc"),                       # noninteger
        row(13, "SVTYPE=DEL;SVTYPE=DEL;SVLEN=-60"),            # duplicate SVTYPE
        (f"1\t100\t{14:064x}\tA\tA{'C' * 50}\t.\tPASS\t"
         "SVTYPE=INS;SVLEN=-49\tGT\t0/1\n"),                 # sign and magnitude both differ
        row(15, "SVTYPE=DEL;SVLEN=0"),                          # zero has wrong sign and magnitude
    ))
    result, report, _ = run_fixture(tmp_path, body)
    counts = report["counts"]
    assert result["status"] == "complete"
    assert counts["eligible"] == 14 and counts["ineligible"] == 1
    assert counts["canonical_kind_counts"] == {"DEL": 13, "INS": 1}
    assert counts["all_rows_retained_in_census"] is True
    assert counts["rows_with_any_contract_flag"] == 14
    assert counts["rows_without_any_contract_flag"] == 1
    flags = counts["overlapping_flags"]
    assert flags["svlen_absent"] == 1
    assert flags["svlen_dot"] == 1
    assert flags["svlen_sign_mismatch"] == 3
    assert flags["svlen_magnitude_mismatch"] == 3
    assert flags["svlen_multivalue"] == 1
    assert flags["svlen_duplicate_info"] == 1
    assert flags["svlen_noninteger"] == 3
    assert flags["svtype_absent"] == 1
    assert flags["svtype_multivalue"] == 1
    assert flags["svtype_duplicate_info"] == 1
    assert flags["svtype_disagreement"] == 2
    assert counts["svlen_comparisons"]["absolute_magnitude_agree"] == 6
    assert counts["svlen_comparisons"]["sign_mismatch"] == 3
    assert counts["svlen_comparisons"]["sign_only_mismatch"] == 1
    first = report["first_strict_guard_contradiction_not_replayed_old_guard"]
    assert first["record_ordinal"] == 1
    assert first["first_guard_contradiction"] == "SVLEN sign disagreement"
    assert first["canonical_kind"] == "DEL"
    assert first["canonical_length"] == 60
    assert first["raw_length_delta"] == -60
    assert first["info_states"]["SVLEN"]["state"] == "integer"
    assert first["info_states"]["SVLEN"]["integer_value"] == 60
    assert first["info_states"]["SVLEN"]["sign"] == "positive"
    assert first["info_states"]["SVLEN"]["absolute_magnitude"] == 60
    assert report["native_validation"] == "UNASSESSED"
    assert report["reference_validation"] == "UNASSESSED"
    assert report["denominator_validation"] == "NOT_VALIDATED"
    assert report["scoring_performed"] is False
    assert report["headers"]["fileformat_raw_line"] == "##fileformat=VCFv4.2"
    assert report["headers"]["info_declarations"][0]["number"] == "1"
    assert report["headers"]["info_declarations"][0]["type"] == "Integer"
    serialized = json.dumps(report)
    assert "CCCCCCCC" not in serialized and "GT\t0/1" not in serialized
    assert hashlib.sha256(("".join(f"{i:064x}\n" for i in range(1, 16))).encode()).hexdigest() == report[
        "identity_order_sha256"
    ]


@pytest.mark.parametrize("header,error", [
    ("##fileformat=VCFv4.2\n", "missing VCF column header"),
    (HEADER.replace("##fileformat=VCFv4.2", "##fileformat=bad"),
     "malformed or missing VCF fileformat header"),
    (HEADER.replace("##fileformat=VCFv4.2\n", "##fileformat=VCFv4.2\n##fileformat=VCFv4.2\n"),
     "duplicate VCF fileformat header"),
    (HEADER.replace('##INFO=<ID=SVLEN,Number=1,Type=Integer,Description="length">\n',
                    '##INFO=<ID=SVLEN,Number=1,Type=Integer,Description="length">\n'
                    '##INFO=<ID=SVLEN,Number=1,Type=Integer,Description="again">\n'),
     "duplicate SVLEN/SVTYPE header declaration"),
])
def test_malformed_or_ambiguous_header_stops_without_report(tmp_path, header, error):
    truth, protocol, protocol_sha, report, expected, _ = fixture(tmp_path, "", header=header)
    with pytest.raises(census.CensusError, match=error):
        census._run_diagnosis(truth, protocol, protocol_sha, report, expected)
    assert not report.exists()


def test_sample_must_be_exactly_hg002(tmp_path):
    truth, protocol, protocol_sha, report, expected, raw = fixture(tmp_path, row(1, "SVTYPE=DEL;SVLEN=-60"))
    changed = raw.replace(b"\tHG002\n", b"\tOTHER\n", 1)
    truth.write_bytes(changed)
    expected.update(expected_input_bytes=len(changed), eligible_truth_sha256=hashlib.sha256(changed).hexdigest())
    # Update the pinned source fields and protocol digest; the sample gate must still stop first.
    value = json.loads(protocol.read_text())
    value["expected_input_bytes"] = len(changed)
    value["eligible_truth_sha256"] = expected["eligible_truth_sha256"]
    protocol.write_text(json.dumps(value, sort_keys=True) + "\n")
    protocol_sha = hashlib.sha256(protocol.read_bytes()).hexdigest()
    with pytest.raises(census.CensusError, match="exactly the HG002 sample"):
        census._run_diagnosis(truth, protocol, protocol_sha, report, expected)
    assert not report.exists()


def test_short_trailing_format_values_are_missing_and_gt_is_not_imputed(tmp_path):
    body = row(1, "SVTYPE=DEL;SVLEN=-60").replace("\tGT\t0/1\n", "\tGT:DP\t0/1\n")
    body += row(2, "SVTYPE=DEL;SVLEN=-60").replace("\tGT\t0/1\n", "\tDP:GT\t10\n")
    result, report, _ = run_fixture(tmp_path, body)
    assert result["records"] == 2
    assert report["counts"]["eligible"] == 1
    assert report["counts"]["ineligible"] == 1
    assert report["counts"]["eligibility_reasons"] == {"missing_or_partial_gt": 1}


@pytest.mark.parametrize("body", [
    row(1, "SVTYPE=DEL;SVLEN=-60", identity="x" * 64),
    row(1, "SVTYPE=DEL;SVLEN=-60", identity="1" * 64)
    + row(2, "SVTYPE=DEL;SVLEN=-60", identity="1" * 64),
])
def test_invalid_or_duplicate_ids_stop_census(tmp_path, body):
    truth, protocol, protocol_sha, report, expected, _ = fixture(tmp_path, body)
    with pytest.raises(census.CensusError, match="truth identity"):
        census._run_diagnosis(truth, protocol, protocol_sha, report, expected)
    assert not report.exists()


def test_source_hash_mismatch_stops_without_success_report(tmp_path):
    truth, protocol, protocol_sha, report, expected, raw = fixture(
        tmp_path, row(1, "SVTYPE=DEL;SVLEN=-60"))
    changed = raw.replace(b"SVLEN=-60", b"SVLEN=-61", 1)
    truth.write_bytes(changed)
    with pytest.raises(census.CensusError, match="truth source SHA-256 mismatch"):
        census._run_diagnosis(truth, protocol, protocol_sha, report, expected)
    assert not report.exists()


def test_protocol_hash_and_code_pins_are_enforced(tmp_path):
    truth, protocol, protocol_sha, report, expected, _ = fixture(
        tmp_path, row(1, "SVTYPE=DEL;SVLEN=-60"))
    with pytest.raises(census.CensusError, match="protocol hash mismatch"):
        census._run_diagnosis(truth, protocol, "0" * 64, report, expected)
    value = json.loads(protocol.read_text())
    value["source_script_sha256"] = "0" * 64
    protocol.write_text(json.dumps(value, sort_keys=True) + "\n")
    protocol_sha = hashlib.sha256(protocol.read_bytes()).hexdigest()
    with pytest.raises(census.CensusError, match="diagnostic script pin mismatch"):
        census._run_diagnosis(truth, protocol, protocol_sha, report, expected)
    assert not report.exists()


def test_output_must_be_exclusive(tmp_path):
    truth, protocol, protocol_sha, report, expected, _ = fixture(
        tmp_path, row(1, "SVTYPE=DEL;SVLEN=-60"))
    report.write_text("existing")
    with pytest.raises(census.CensusError, match="report path already exists"):
        census._run_diagnosis(truth, protocol, protocol_sha, report, expected)
    assert report.read_text() == "existing"


def test_input_must_not_be_a_symlink(tmp_path):
    truth, protocol, protocol_sha, report, expected, raw = fixture(
        tmp_path, row(1, "SVTYPE=DEL;SVLEN=-60"))
    target = tmp_path / "target.vcf"
    target.write_bytes(raw)
    truth.unlink()
    truth.symlink_to(target)
    with pytest.raises(census.CensusError, match="regular file"):
        census._run_diagnosis(truth, protocol, protocol_sha, report, expected)
    assert not report.exists()


def test_source_snapshot_is_rechecked_after_parse(tmp_path, monkeypatch):
    truth, protocol, protocol_sha, report, expected, raw = fixture(
        tmp_path, row(1, "SVTYPE=DEL;SVLEN=-60"))
    original = census._parse_payload

    def mutate_after_parse(payload, source_sha):
        result = original(payload, source_sha)
        truth.write_bytes(raw.replace(b"SVLEN=-60", b"SVLEN=-61", 1))
        return result

    monkeypatch.setattr(census, "_parse_payload", mutate_after_parse)
    with pytest.raises(census.CensusError, match="snapshot changed"):
        census._run_diagnosis(truth, protocol, protocol_sha, report, expected)
    assert not report.exists()


@pytest.mark.parametrize("stage", ["acquisition", "posthash"])
def test_growth_at_cap_does_not_consume_overflow_byte(tmp_path, monkeypatch, stage):
    source = tmp_path / "synthetic-growth.bin"
    payload = b"x" * 64
    source.write_bytes(payload)
    monkeypatch.setattr(census, "MAX_INPUT", len(payload))
    snapshot = census._snapshot(source.stat())
    real_read = census.os.read
    consumed = []

    def grow_on_first_read(fd, requested):
        if not consumed:
            with source.open("ab") as stream:
                stream.write(b"z")
        block = real_read(fd, requested)
        consumed.append(len(block))
        return block

    monkeypatch.setattr(census.os, "read", grow_on_first_read)
    with pytest.raises(census.CensusError, match="changed"):
        if stage == "acquisition":
            census._read_source(source)
        else:
            census._posthash(source, snapshot, hashlib.sha256(payload).hexdigest(), len(payload))
    assert sum(consumed) == len(payload)
    assert source.stat().st_size == len(payload) + 1
