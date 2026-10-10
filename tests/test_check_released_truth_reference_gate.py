from hashlib import sha256
import gzip
import json
from pathlib import Path

import pytest

from analysis import check_released_truth_reference_gate as gate

HEADER = (
    "##fileformat=VCFv4.2\n"
    '##INFO=<ID=SVTYPE,Number=1,Type=String,Description="type">\n'
    '##INFO=<ID=SVLEN,Number=1,Type=Integer,Description="length">\n'
    '##FORMAT=<ID=GT,Number=1,Type=String,Description="genotype">\n'
    "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tHG002\n"
)
IDS = ("a" * 64, "b" * 64)
NATIVE_PROTOCOL = gate.EXPECTED["native_protocol_sha256"]
NATIVE_PINS = {
    "native_source_script_sha256": gate.EXPECTED["native_source_script_sha256"],
    "native_truth_units_script_sha256": sha256(
        Path(gate.__file__).with_name("released_truth_units.py").read_bytes()).hexdigest(),
    "native_bounded_reader_script_sha256": sha256(
        Path(gate.__file__).with_name("diagnose_released_truth_metadata.py").read_bytes()).hexdigest(),
    "native_sealed_buffer_script_sha256": sha256(
        Path(gate.__file__).with_name("check_released_truth_metadata.py").read_bytes()).hexdigest(),
}


def rows_for(ids=IDS):
    return [f"1\t1\t{ids[0]}\tAC\tA\t.\tPASS\tSVTYPE=DEL;SVLEN=-1\tGT\t0/1\n",
            f"1\t5\t{ids[1]}\tTA\tT\t.\tPASS\tSVTYPE=DEL;SVLEN=-1\tGT\t0/1\n"]


def make_case(tmp_path, *, rows=None, fasta=b">1 reference\nACGTTA\n",
              fai=b"1\t6\t13\t6\t7\n", order_pin=None):
    tmp_path.mkdir(parents=True, exist_ok=True)
    truth = tmp_path / "truth.vcf"
    truth.write_text(HEADER + "".join(rows if rows is not None else rows_for()))
    reference = tmp_path / "reference.fa.gz"
    reference.write_bytes(gzip.compress(fasta, mtime=0))
    fai_path = tmp_path / "reference.fa.gz.fai"
    fai_path.write_bytes(fai)
    native_path = tmp_path / "native.json"
    native_protocol = NATIVE_PROTOCOL
    identities = [row.split("\t")[2] for row in (rows if rows is not None else rows_for())]
    truth_bytes = truth.read_bytes()
    expected = dict(
        expected_records=len(identities), expected_input_bytes=len(truth_bytes),
        eligible_truth_sha256=sha256(truth_bytes).hexdigest(),
        identity_order_sha256=(order_pin or sha256(("".join(i + "\n" for i in identities)).encode()).hexdigest()),
        reference_compressed_bytes=reference.stat().st_size,
        reference_sha256=sha256(reference.read_bytes()).hexdigest(),
        fai_sha256=sha256(fai_path.read_bytes()).hexdigest(),
        reference_runtime=gate._reference_runtime()[0],
    )
    expected["native_protocol_sha256"] = NATIVE_PROTOCOL
    expected["native_source_script_sha256"] = NATIVE_PINS["native_source_script_sha256"]
    kinds = {"INS": 0, "DEL": len(identities)}
    native = {
        "status": "complete", "purpose": gate.NATIVE_PURPOSE,
        "records": len(identities), "unique_ids": len(identities),
        "canonical_kind_counts": kinds, "global_sign_only_flags_retained": 0,
        "identity_order_sha256": expected["identity_order_sha256"],
        "eligible_truth_sha256": expected["eligible_truth_sha256"],
        "input_bytes": expected["expected_input_bytes"], "source_snapshot_stable": True,
        "versions": {"python": "3.10.20", "pysam": "0.24.0", "truvari": "5.4.0",
                     "bcftools": "1.23.1", "htslib": "1.23.1"},
        "protocol_sha256": native_protocol,
        "source_script_sha256": NATIVE_PINS["native_source_script_sha256"],
        "truth_units_script_sha256": NATIVE_PINS["native_truth_units_script_sha256"],
        "bounded_reader_script_sha256": NATIVE_PINS["native_bounded_reader_script_sha256"],
        "sealed_buffer_script_sha256": NATIVE_PINS["native_sealed_buffer_script_sha256"],
        "native_metadata_consistency": "PASS", "normative_compliance_claim": False,
        "reference_validation": "UNASSESSED", "denominator_validation": "NOT_VALIDATED",
        "scoring_performed": False, "input_unmodified": True, "rows_repaired_or_dropped": 0,
        "parser_input_kernel_sealed": True, "parser_streams_share_pysam_backend": True,
        "serialized_rows_unchanged_by_native_calls": True,
        "input_read_reservation_bytes": 66 * 1024**2,
        "opaque_parser_traffic_measured": False,
    }
    native_bytes = (json.dumps(native, sort_keys=True) + "\n").encode()
    native_path.write_bytes(native_bytes)
    protocol = {
        "reference_gate_approved": True, "purpose": gate.PURPOSE,
        "expected_sample": "HG002", **expected,
        "native_report_sha256": sha256(native_bytes).hexdigest(),
        "native_protocol_sha256": native_protocol, "resource_limits": dict(gate.RESOURCE_LIMITS),
        **NATIVE_PINS,
    }
    for key, filename in gate.CODE_PINS.items():
        protocol[key] = sha256(Path(gate.__file__).with_name(filename).read_bytes()).hexdigest()
    protocol_path = tmp_path / "protocol.json"
    protocol_bytes = (json.dumps(protocol, sort_keys=True) + "\n").encode()
    protocol_path.write_bytes(protocol_bytes)
    output = tmp_path / "ref-report.json"
    return dict(truth=truth, reference=reference, fai=fai_path, native=native_path,
                protocol=protocol_path, protocol_sha256=sha256(protocol_bytes).hexdigest(),
                output=output, expected=expected)


def run(case):
    return gate._check_reference_gate(
        case["truth"], case["reference"], case["fai"], case["native"],
        case["protocol"], case["protocol_sha256"], case["output"], expected=case["expected"])


def test_all_original_ref_queries_match_and_report_pins(tmp_path):
    case = make_case(tmp_path)
    result = run(case)
    assert result["native_precondition"] == "PASS"
    assert result["records"] == result["checked_REF_records"] == 2
    assert result["unique_ids"] == 2
    assert result["truth_source_snapshot"]["size_bytes"] == case["expected"]["expected_input_bytes"]
    assert result["eligible_truth_sha256"] == case["expected"]["eligible_truth_sha256"]
    assert result["reference_sha256"] == case["expected"]["reference_sha256"]
    assert result["whole_gzip_eof_crc_verified"]
    assert result["original_anchored_REF_validation"] == "PASS"
    assert result["denominator_validation"] == "NOT_VALIDATED"
    assert not result["scoring_performed"] and not result["genomic_output_written"]
    saved = json.loads(case["output"].read_text())
    assert saved["native_report_sha256"] == result["native_report_sha256"]


def test_original_ref_mismatch_fails_without_report(tmp_path):
    case = make_case(tmp_path, fasta=b">1 reference\nTCGTTA\n")
    with pytest.raises(ValueError, match="REF mismatch"):
        run(case)
    assert not case["output"].exists()


def test_core_checks_overlapping_refs_across_lines_and_unqueried_decoy():
    fasta = b">1 description\nACG\nTTA\n>decoy\nNN\n"
    queries = {"1": [("truth-a", 1, b"CGT"), ("truth-b", 2, b"GTT")]}
    result = gate._check_reference_bytes(gzip.compress(fasta, mtime=0),
                                         {"1": 6, "decoy": 2}, queries)
    assert result["checked_REF_records"] == 2
    assert result["reference_contigs"] == 2
    assert result["reference_delivered_decoded_bytes"] == len(fasta)
    assert result["whole_gzip_eof_crc_verified"]


@pytest.mark.parametrize(("corruption", "error"), [
    ("truncated_trailer", EOFError),
    ("wrong_isize", gzip.BadGzipFile),
])
def test_gzip_truncated_or_wrong_isize_trailer_fails(corruption, error):
    fasta = b">1 description\nACGTTA\n>decoy\nNN\n"
    compressed = bytearray(gzip.compress(fasta, mtime=0))
    if corruption == "truncated_trailer":
        compressed = compressed[:-4]
    else:
        compressed[-1] ^= 1
    queries = {"1": [("truth-a", 1, b"CGT")]}
    with pytest.raises(error):
        gate._check_reference_bytes(bytes(compressed), {"1": 6, "decoy": 2}, queries)


def test_gzip_member_boundary_inside_contig_sequence_passes():
    first = gzip.compress(b">1 description\nACG", mtime=0)
    second = gzip.compress(b"TTA\n>decoy\nNN\n", mtime=0)
    queries = {"1": [("truth-a", 1, b"CGT"), ("truth-b", 2, b"GTT")]}
    result = gate._check_reference_bytes(first + second, {"1": 6, "decoy": 2}, queries)
    assert result["checked_REF_records"] == 2
    assert result["reference_contigs"] == 2
    assert result["whole_gzip_eof_crc_verified"]


def test_multiple_members_and_all_fai_contigs_pass(tmp_path):
    case = make_case(tmp_path, fasta=b"", fai=b"1\t6\t0\t6\t7\ndecoy\t2\t0\t2\t3\n")
    members = gzip.compress(b">1 ref\nACGTTA\n", mtime=0) + gzip.compress(b">decoy\nNN\n", mtime=0)
    case["reference"].write_bytes(members)
    _repin_reference(case, members)
    result = run(case)
    assert result["reference_contigs"] == 2
    assert result["checked_REF_records"] == 2


def _repin_reference(case, compressed):
    case["reference"].write_bytes(compressed)
    case["expected"]["reference_compressed_bytes"] = len(compressed)
    case["expected"]["reference_sha256"] = sha256(compressed).hexdigest()
    _rewrite_pins(case)


def _rewrite_pins(case, *, native_changes=None, protocol_changes=None):
    native = json.loads(case["native"].read_text())
    native.update(native_changes or {})
    native_bytes = (json.dumps(native, sort_keys=True) + "\n").encode()
    case["native"].write_bytes(native_bytes)
    protocol = json.loads(case["protocol"].read_text())
    protocol.update(case["expected"])
    protocol["native_report_sha256"] = sha256(native_bytes).hexdigest()
    protocol.update(protocol_changes or {})
    protocol_bytes = (json.dumps(protocol, sort_keys=True) + "\n").encode()
    case["protocol"].write_bytes(protocol_bytes)
    case["protocol_sha256"] = sha256(protocol_bytes).hexdigest()


def test_late_member_crc_failure_has_no_output(tmp_path):
    case = make_case(tmp_path, fasta=b"", fai=b"1\t6\t0\t6\t7\ndecoy\t2\t0\t2\t3\n")
    payload = gzip.compress(b">1 ref\nACGTTA\n", mtime=0) + gzip.compress(b">decoy\nNN\n", mtime=0)
    broken = bytearray(payload)
    broken[-8] ^= 1
    _repin_reference(case, bytes(broken))
    with pytest.raises(gzip.BadGzipFile):
        run(case)
    assert not case["output"].exists()


@pytest.mark.parametrize("fasta,fai,message", [
    (b">1\nACGTT\n", b"1\t6\t0\t6\t7\n", "length mismatch"),
    (b">1\nACGTTA\n", b"1\t6\t0\t6\t7\n1\t6\t0\t6\t7\n", "duplicate FAI"),
    (b">1\nACGTTA\n", b"2\t1\t0\t1\t2\n", "absent from FAI"),
    (b">1\nACGTTA\n", b"1\t6\t0\t6\t7\textra\n", "FAI hash mismatch"),
    (b">1\nACGTTA\n", b"1\t6\t0\tnan\t7\n", "invalid FAI numeric field"),
    (b">1\nACGTTA\n", b"1\t6\t0\t6\t7\n2\t1\t0\t1\t2\n", "missing reference contig"),
])
def test_fai_and_complete_reference_dictionary_fail_closed(tmp_path, fasta, fai, message):
    case = make_case(tmp_path, fasta=fasta, fai=fai)
    if message == "FAI hash mismatch":
        # Pin the malformed FAI deliberately so the strict parser sees it.
        case["expected"]["fai_sha256"] = sha256(fai).hexdigest()
        _rewrite_pins(case)
        with pytest.raises(ValueError, match="FAI format"):
            run(case)
    else:
        with pytest.raises(ValueError, match=message):
            run(case)
    assert not case["output"].exists()


def test_duplicate_truth_ids_order_pin_and_source_hash_fail_without_output(tmp_path):
    duplicate = rows_for((IDS[0], IDS[0]))
    case = make_case(tmp_path / "duplicate", rows=duplicate)
    with pytest.raises(ValueError, match="duplicate truth identity"):
        run(case)
    assert not case["output"].exists()

    case = make_case(tmp_path / "order", order_pin="f" * 64)
    with pytest.raises(ValueError, match="identity order mismatch"):
        run(case)
    assert not case["output"].exists()

    case = make_case(tmp_path / "truth-hash")
    case["truth"].write_bytes(case["truth"].read_bytes() + b"\n")
    with pytest.raises(ValueError, match="truth source pin"):
        run(case)
    assert not case["output"].exists()


@pytest.mark.parametrize("change,message", [
    ({"reference_gate_approved": False}, "approval"),
    ({"reference_sha256": "f" * 64}, "protocol input pin"),
    ({"source_script_sha256": "f" * 64}, "local code pin"),
    ({"unexpected": "field"}, "schema mismatch"),
    ({"resource_limits": {**gate.RESOURCE_LIMITS, "decoded_reference_bytes": 1}},
     "resource limits"),
])
def test_protocol_approval_and_source_pins_fail_before_truth_read(tmp_path, monkeypatch, change, message):
    case = make_case(tmp_path)
    protocol = json.loads(case["protocol"].read_text())
    protocol.update(change)
    raw = (json.dumps(protocol, sort_keys=True) + "\n").encode()
    case["protocol"].write_bytes(raw)
    case["protocol_sha256"] = sha256(raw).hexdigest()

    def no_truth(*args):
        raise AssertionError("truth body was read before protocol acceptance")

    monkeypatch.setattr(gate.census, "_read_source", no_truth)
    with pytest.raises(ValueError, match=message):
        run(case)
    assert not case["output"].exists()


def test_wrong_protocol_hash_fails_before_truth_read(tmp_path, monkeypatch):
    case = make_case(tmp_path)
    monkeypatch.setattr(gate.census, "_read_source",
                        lambda *args: (_ for _ in ()).throw(AssertionError("truth read")))
    with pytest.raises(ValueError, match="protocol hash"):
        gate._check_reference_gate(case["truth"], case["reference"], case["fai"], case["native"],
                                   case["protocol"], "0" * 64, case["output"],
                                   expected=case["expected"])
    assert not case["output"].exists()


def test_wrong_reference_runtime_fails_before_truth_read(tmp_path, monkeypatch):
    case = make_case(tmp_path)
    wrong_runtime = dict(case["expected"]["reference_runtime"])
    wrong_runtime["gzip_module_sha256"] = "0" * 64
    case["expected"] = {**case["expected"], "reference_runtime": wrong_runtime}
    _rewrite_pins(case, protocol_changes={"reference_runtime": wrong_runtime})

    def no_truth(*args):
        raise AssertionError("truth body was read before runtime acceptance")

    monkeypatch.setattr(gate.census, "_read_source", no_truth)
    with pytest.raises(ValueError, match="reference decoder runtime mismatch"):
        run(case)
    assert not case["output"].exists()


def test_duplicate_protocol_keys_and_wrong_native_report_hash_fail(tmp_path):
    case = make_case(tmp_path / "protocol")
    raw = case["protocol"].read_text()
    malformed = raw.replace("{", '{"purpose":"duplicate",', 1).encode()
    case["protocol"].write_bytes(malformed)
    case["protocol_sha256"] = sha256(malformed).hexdigest()
    with pytest.raises(ValueError, match="duplicate protocol"):
        run(case)
    assert not case["output"].exists()

    case = make_case(tmp_path / "native")
    case["native"].write_bytes(case["native"].read_bytes() + b" ")
    with pytest.raises(ValueError, match="native report hash"):
        run(case)
    assert not case["output"].exists()


@pytest.mark.parametrize("native_change,message", [
    ({"status": "incomplete"}, "not PASS"),
    ({"native_metadata_consistency": "FAIL"}, "not PASS"),
    ({"records": 1}, "records mismatch"),
    ({"protocol_sha256": "f" * 64}, "native protocol hash"),
    ({"source_script_sha256": "f" * 64}, "source pin mismatch"),
])
def test_native_report_must_be_complete_and_match_pins(tmp_path, native_change, message):
    case = make_case(tmp_path)
    _rewrite_pins(case, native_changes=native_change)
    with pytest.raises(ValueError, match=message):
        run(case)
    assert not case["output"].exists()


def test_reference_mutation_after_stream_fails_posthash(tmp_path, monkeypatch):
    case = make_case(tmp_path)
    original = gate._check_reference_bytes

    def mutate_after_stream(*args):
        result = original(*args)
        case["reference"].write_bytes(case["reference"].read_bytes() + b"x")
        return result

    monkeypatch.setattr(gate, "_check_reference_bytes", mutate_after_stream)
    with pytest.raises(ValueError, match="snapshot or size changed"):
        run(case)
    assert not case["output"].exists()


def test_reference_posthash_growth_reads_no_more_than_cap(tmp_path, monkeypatch):
    case = make_case(tmp_path)
    cap = case["reference"].stat().st_size
    reference_stat = case["reference"].stat()
    monkeypatch.setattr(gate, "MAX_REFERENCE_COMPRESSED", cap)

    real_open_regular = gate.census._open_regular
    real_read = gate.os.read
    real_posthash = gate._posthash
    state = {"armed": False, "grew": False, "requested": 0, "returned": 0}

    def open_regular(path):
        fd, snapshot = real_open_regular(path)
        if state["armed"] and Path(path) == case["reference"] and not state["grew"]:
            with case["reference"].open("ab") as stream:
                stream.write(b"x")
            state["grew"] = True
        return fd, snapshot

    def bounded_read(fd, requested):
        stat = gate.os.fstat(fd)
        is_reference = (stat.st_dev, stat.st_ino) == (reference_stat.st_dev,
                                                       reference_stat.st_ino)
        if state["armed"] and is_reference:
            state["requested"] += requested
        payload = real_read(fd, requested)
        if state["armed"] and is_reference:
            state["returned"] += len(payload)
        return payload

    def watched_posthash(path, snapshot, digest, size, byte_cap, label):
        if Path(path) == case["reference"]:
            state["armed"] = True
        try:
            return real_posthash(path, snapshot, digest, size, byte_cap, label)
        finally:
            state["armed"] = False

    monkeypatch.setattr(gate.census, "_open_regular", open_regular)
    monkeypatch.setattr(gate.os, "read", bounded_read)
    monkeypatch.setattr(gate, "_posthash", watched_posthash)
    with pytest.raises(ValueError, match="compressed reference posthash or snapshot failed"):
        run(case)
    assert state["grew"]
    assert state["requested"] <= cap
    assert state["returned"] <= cap
    assert not case["output"].exists()


def test_truth_mutation_after_query_derivation_fails_posthash(tmp_path, monkeypatch):
    case = make_case(tmp_path)
    original = gate._truth_queries

    def mutate_after_queries(*args):
        result = original(*args)
        case["truth"].write_bytes(case["truth"].read_bytes() + b"x")
        return result

    monkeypatch.setattr(gate, "_truth_queries", mutate_after_queries)
    with pytest.raises(ValueError, match="snapshot changed before posthash"):
        run(case)
    assert not case["output"].exists()


def test_protocol_mutation_during_reference_check_fails_without_report(tmp_path, monkeypatch):
    case = make_case(tmp_path)
    original = gate._check_reference_bytes

    def mutate_protocol_after_stream(*args):
        result = original(*args)
        case["protocol"].write_bytes(case["protocol"].read_bytes() + b" ")
        return result

    monkeypatch.setattr(gate, "_check_reference_bytes", mutate_protocol_after_stream)
    with pytest.raises(ValueError, match="protocol snapshot changed"):
        run(case)
    assert not case["output"].exists()


def test_late_pinned_code_snapshot_failure_has_no_output(tmp_path, monkeypatch):
    case = make_case(tmp_path)
    original = gate._posthash
    code_paths = set(gate.CODE_PINS.values())

    def fail_pinned_code(path, *args):
        if Path(path).name in code_paths:
            raise ValueError("simulated pinned code snapshot failure")
        return original(path, *args)

    monkeypatch.setattr(gate, "_posthash", fail_pinned_code)
    with pytest.raises(ValueError, match="pinned code snapshot failure"):
        run(case)
    assert not case["output"].exists()


def test_public_api_rejects_synthetic_population_before_truth_read(tmp_path, monkeypatch):
    case = make_case(tmp_path)

    def no_truth(*args):
        raise AssertionError("public API read synthetic truth")

    monkeypatch.setattr(gate.census, "_read_source", no_truth)
    with pytest.raises(ValueError, match="protocol input pin mismatch: expected_records"):
        gate.check_reference_gate(case["truth"], case["reference"], case["fai"], case["native"],
                                  case["protocol"], case["protocol_sha256"], case["output"])
    assert not case["output"].exists()


def test_decoded_and_compressed_budgets_fail_without_report(tmp_path, monkeypatch):
    case = make_case(tmp_path)
    monkeypatch.setattr(gate.reference_checker, "MAX_FASTA_DECODED", 6)
    with pytest.raises(ValueError, match="decoded-byte cap"):
        run(case)
    assert not case["output"].exists()

    monkeypatch.undo()
    case = make_case(tmp_path / "compressed")
    monkeypatch.setattr(gate, "MAX_REFERENCE_COMPRESSED", case["reference"].stat().st_size - 1)
    with pytest.raises(ValueError, match="byte cap"):
        run(case)
    assert not case["output"].exists()


def test_gzip_decoded_prefetch_stays_within_failure_read_ahead(monkeypatch):
    decoded_cap = 128
    fasta = b">1\n" + b"A" * 200_000 + b"\n"
    observed = {"bytes": 0}
    original_add_read_data = gzip._GzipReader._add_read_data

    def count_decoded(reader, data):
        observed["bytes"] += len(data)
        return original_add_read_data(reader, data)

    monkeypatch.setattr(gzip._GzipReader, "_add_read_data", count_decoded)
    monkeypatch.setattr(gate.reference_checker, "MAX_FASTA_DECODED", decoded_cap)
    with pytest.raises(ValueError, match="FASTA decoded-byte cap exceeded"):
        gate._check_reference_bytes(gzip.compress(fasta, mtime=0),
                                    {"1": 200_000}, {"1": []})
    assert observed["bytes"] > decoded_cap
    assert observed["bytes"] <= decoded_cap + gate.FAILURE_READ_AHEAD


def test_fai_query_and_contig_budgets_fail_closed(tmp_path, monkeypatch):
    case = make_case(tmp_path / "fai-cap")
    monkeypatch.setattr(gate, "MAX_FAI_BYTES", case["fai"].stat().st_size - 1)
    with pytest.raises(ValueError, match="byte cap"):
        run(case)
    assert not case["output"].exists()

    monkeypatch.undo()
    case = make_case(tmp_path / "query-cap")
    monkeypatch.setattr(gate.reference_checker, "MAX_QUERY_RECORDS", 1)
    with pytest.raises(ValueError, match="query count or REF-byte budget"):
        run(case)
    assert not case["output"].exists()

    monkeypatch.undo()
    case = make_case(tmp_path / "ref-cap")
    monkeypatch.setattr(gate.reference_checker, "MAX_QUERY_REF_BYTES", 1)
    with pytest.raises(ValueError, match="query count or REF-byte budget"):
        run(case)
    assert not case["output"].exists()

    monkeypatch.undo()
    case = make_case(tmp_path / "contig-cap")
    monkeypatch.setattr(gate.reference_checker, "MAX_CONTIG_BYTES", 5)
    with pytest.raises(ValueError, match="invalid FAI length"):
        run(case)
    assert not case["output"].exists()

    monkeypatch.undo()
    case = make_case(tmp_path / "line-cap")
    monkeypatch.setattr(gate.reference_checker, "MAX_LINE", 2)
    with pytest.raises(ValueError, match="FASTA line cap"):
        run(case)
    assert not case["output"].exists()


def test_fai_and_reference_source_hash_mismatch_fail_without_report(tmp_path):
    case = make_case(tmp_path / "fai")
    case["fai"].write_bytes(case["fai"].read_bytes() + b" ")
    with pytest.raises(ValueError, match="FAI hash mismatch"):
        run(case)
    assert not case["output"].exists()

    case = make_case(tmp_path / "reference")
    case["reference"].write_bytes(case["reference"].read_bytes() + b"x")
    with pytest.raises(ValueError, match="compressed reference source pin"):
        run(case)
    assert not case["output"].exists()


def test_fai_and_native_report_snapshot_changes_fail(tmp_path, monkeypatch):
    case = make_case(tmp_path)
    original = gate._check_reference_bytes

    def mutate_fai_after_stream(*args):
        result = original(*args)
        case["fai"].write_bytes(case["fai"].read_bytes() + b" ")
        return result

    monkeypatch.setattr(gate, "_check_reference_bytes", mutate_fai_after_stream)
    with pytest.raises(ValueError, match="FAI snapshot or size changed"):
        run(case)
    assert not case["output"].exists()


def test_native_report_mutation_during_reference_check_fails(tmp_path, monkeypatch):
    case = make_case(tmp_path)
    original = gate._check_reference_bytes

    def mutate_report_after_stream(*args):
        result = original(*args)
        case["native"].write_bytes(case["native"].read_bytes() + b" ")
        return result

    monkeypatch.setattr(gate, "_check_reference_bytes", mutate_report_after_stream)
    with pytest.raises(ValueError, match="native report snapshot or size changed"):
        run(case)
    assert not case["output"].exists()


def test_fasta_duplicate_unknown_trailing_data_and_bad_line_fail(tmp_path):
    cases = [
        (b">1\nACGTTA\n>1\nACGTTA\n", b"1\t6\t0\t6\t7\n", "duplicate FASTA"),
        (b">other\nACGTTA\n", b"1\t6\t0\t6\t7\n", "unknown or duplicate"),
        (b">1\nAC GTTA\n", b"1\t6\t0\t6\t7\n", "invalid FASTA"),
    ]
    for index, (fasta, fai, message) in enumerate(cases):
        case = make_case(tmp_path / str(index), fasta=fasta, fai=fai)
        with pytest.raises(ValueError, match=message):
            run(case)
        assert not case["output"].exists()

    case = make_case(tmp_path / "trailing")
    _repin_reference(case, gzip.compress(b">1\nACGTTA\n", mtime=0) + b"tail")
    with pytest.raises(gzip.BadGzipFile):
        run(case)
    assert not case["output"].exists()
