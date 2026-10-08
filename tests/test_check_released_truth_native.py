from hashlib import sha256
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pysam
import pytest

from analysis import check_released_truth_native as gate

HEADER = ("##fileformat=VCFv4.2\n##contig=<ID=1,length=10000>\n"
          '##INFO=<ID=SVTYPE,Number=1,Type=String,Description="type">\n'
          '##INFO=<ID=SVLEN,Number=1,Type=Integer,Description="length">\n'
          '##FORMAT=<ID=GT,Number=1,Type=String,Description="genotype">\n'
          "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tHG002\n")


def fixture(tmp_path, kind="DEL", size=-60, gt="0/1", info=None, alt=None):
    ref = "A" * 61 if kind == "DEL" else "A"
    alternate = ("A" if kind == "DEL" else "A" * 61) if alt is None else alt
    annotation = f"SVTYPE={kind};SVLEN={size}" if info is None else info
    path = tmp_path / "synthetic.vcf"
    path.write_text(HEADER + f"1\t100\t{'a' * 64}\t{ref}\t{alternate}"
                    f"\t.\tPASS\t{annotation}\tGT\t{gt}\n")
    with pysam.VariantFile(str(path)) as source:
        record = next(source).copy()
    return path, record


class Native:
    def __init__(self, record, kind="DEL", size=60, mutate=False):
        self.record, self.kind, self.size, self.mutate = record, kind, size, mutate

    def __str__(self):
        return str(self.record)

    def var_size(self):
        if self.mutate:
            self.record.info["SVLEN"] = 61
        return self.size

    def var_type(self):
        return SimpleNamespace(name=self.kind)


def protocol(tmp_path, truth, **changes):
    expected = dict(expected_records=1, expected_input_bytes=truth.stat().st_size,
                    eligible_truth_sha256=sha256(truth.read_bytes()).hexdigest(),
                    identity_order_sha256=sha256(("a" * 64 + "\n").encode()).hexdigest())
    config = dict(expected, native_gate_approved=True, purpose=gate.PURPOSE,
                  expected_sample="HG002", versions=gate.VERSIONS,
                  input_read_reservation_bytes=gate.RESERVATION)
    for key, name in gate.PIN_FILES.items():
        config[key] = sha256(Path(gate.__file__).with_name(name).read_bytes()).hexdigest()
    config.update(changes)
    path = tmp_path / "protocol.json"
    path.write_text(json.dumps(config))
    return path, sha256(path.read_bytes()).hexdigest(), expected


@pytest.mark.parametrize("kind,size", [("DEL", -60), ("DEL", 60), ("INS", -60), ("INS", 60)])
def test_uniform_sign_tolerance_preserves_fields(tmp_path, kind, size):
    _, rec = fixture(tmp_path, kind=kind, size=size, gt="1|1")
    before = str(rec)
    observed_kind, sign_flag = gate.canonical_metadata(rec, Native(rec, kind))
    assert observed_kind == kind
    assert sign_flag == (size != (60 if kind == "INS" else -60))
    assert str(rec) == before


@pytest.mark.parametrize("info,gt,alt,message", [
    ("SVTYPE=DEL", "0/1", None, "SVLEN"),
    ("SVTYPE=DEL;SVLEN=.", "0/1", None, "SVLEN"),
    ("SVTYPE=DEL;SVLEN=59", "0/1", None, "SVLEN"),
    ("SVTYPE=DEL;SVLEN=0", "0/1", None, "SVLEN"),
    ("SVTYPE=INS;SVLEN=-60", "0/1", None, "SVTYPE"),
    ("SVLEN=-60", "0/1", None, "SVTYPE"),
    (None, "./1", None, "eligibility"),
    (None, "0/0", None, "eligibility"),
    (None, "0", None, "diploid"),
    (None, "0/1", "<DEL>", "eligibility"),
    (None, "0/1", "A,AA", "biallelic"),
    (None, "0/1", "N", "eligibility"),
])
def test_invalid_records_are_not_repaired_or_dropped(tmp_path, info, gt, alt, message):
    _, rec = fixture(tmp_path, info=info, gt=gt, alt=alt)
    before = str(rec)
    with pytest.raises(ValueError, match=message):
        gate.canonical_metadata(rec, Native(rec))
    assert str(rec) == before


@pytest.mark.parametrize("value", [(60, -60), (), [60, -60]])
def test_scalar_cardinality(value):
    with pytest.raises(ValueError, match="scalar"):
        gate.scalar(value)


@pytest.mark.parametrize("size,kind,mutate,message", [
    (59, "DEL", False, "native size"),
    (True, "DEL", False, "native size"),
    (60, "INS", False, "native type"),
    (60, "DEL", True, "changed serialized"),
])
def test_native_contradictions_and_mutation(tmp_path, size, kind, mutate, message):
    _, rec = fixture(tmp_path)
    with pytest.raises(ValueError, match=message):
        gate.canonical_metadata(rec, Native(rec, kind, size, mutate))


def test_whole_row_pairing(tmp_path):
    _, rec = fixture(tmp_path)
    other = rec.copy()
    other.qual = 20
    with pytest.raises(ValueError, match="whole rows"):
        gate.canonical_metadata(rec, Native(other))


@pytest.mark.parametrize("drift", ["position", "alleles", "genotype", "phase", "format"])
def test_agreeing_parser_streams_cannot_hide_literal_field_drift(tmp_path, drift):
    truth, rec = fixture(tmp_path)
    fields = truth.read_text().splitlines()[-1].split("\t")
    original, fmt = gate.literal_unit(fields, 1)
    if drift == "position":
        rec.pos = 101
    elif drift == "alleles":
        rec.ref, rec.alts = "C" * 61, ("C",)
    elif drift == "genotype":
        rec.samples[0]["GT"] = (1, 1)
    elif drift == "phase":
        rec.samples[0].phased = True
    else:
        rec.header.formats.add("DP", 1, "Integer", "synthetic depth")
        rec.samples[0]["DP"] = 20
    # Both mocked streams share exactly the same modified rendering. Their
    # kind and size still agree; only the independent literal check rejects.
    assert str(rec) == str(Native(rec))
    with pytest.raises(ValueError, match="literal/native"):
        gate.canonical_metadata(rec, Native(rec), original_unit=original, original_format=fmt)


@pytest.mark.parametrize("gt", ["./1", "0/0", "1", "0/2", "."])
def test_literal_gt_is_not_imputed(tmp_path, gt):
    truth, _ = fixture(tmp_path, gt=gt)
    with pytest.raises(ValueError, match="literal record"):
        gate.literal_unit(truth.read_text().splitlines()[-1].split("\t"), 1)


@pytest.mark.parametrize("change,message", [
    ({"native_gate_approved": False}, "flag"),
    ({"purpose": "scoring"}, "scope"),
    ({"expected_records": True}, "input contract"),
    ({"source_script_sha256": "0" * 64}, "code pin"),
    ({"versions": {}}, "stack"),
    ({"extra": 1}, "schema"),
    ({"input_read_reservation_bytes": 0}, "reservation"),
])
def test_protocol_defects_precede_source_reads(tmp_path, monkeypatch, change, message):
    truth, _ = fixture(tmp_path)
    config, digest, expected = protocol(tmp_path, truth, **change)
    monkeypatch.setattr(gate, "_versions", lambda: gate.VERSIONS)
    def no_read(*args):
        raise AssertionError("scientific input was opened")
    monkeypatch.setattr(gate.bounded, "_read_source", no_read)
    output = tmp_path / "report.json"
    with pytest.raises(ValueError, match=message):
        gate._check_native(truth, config, digest, output, expected)
    assert not output.exists()


def test_bad_protocol_hash_and_duplicate_keys_precede_source(tmp_path, monkeypatch):
    truth, _ = fixture(tmp_path)
    config, digest, expected = protocol(tmp_path, truth)
    output = tmp_path / "report.json"
    with pytest.raises(ValueError, match="protocol hash"):
        gate._check_native(truth, config, "0" * 64, output, expected)
    config.write_text('{"purpose": "a", "purpose": "b"}')
    digest = sha256(config.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="duplicate protocol"):
        gate._check_native(truth, config, digest, output, expected)
    assert not output.exists()


def test_actual_stack_mismatch_precedes_source(tmp_path, monkeypatch):
    truth, _ = fixture(tmp_path)
    config, digest, expected = protocol(tmp_path, truth)
    monkeypatch.setattr(gate, "_versions", lambda: dict(gate.VERSIONS, python="wrong"))
    with pytest.raises(ValueError, match="stack"):
        gate._check_native(tmp_path / "absent.vcf", config, digest, tmp_path / "report", expected)


def test_reuses_corrected_bounded_source_helpers():
    from analysis import diagnose_released_truth_metadata as census
    assert gate.bounded._read_source is census._read_source
    assert gate.bounded._posthash is census._posthash
    assert gate.bounded._read_pinned is census._read_pinned


def require_native_stack():
    pytest.importorskip("truvari")
    if sys.platform != "linux" or gate._versions() != gate.VERSIONS:
        pytest.skip("requires exact pinned Linux cluster stack")


@pytest.mark.parametrize("kind,size", [("DEL", -60), ("DEL", 60), ("INS", -60), ("INS", 60)])
def test_exact_native_complete_endpoint(tmp_path, kind, size):
    require_native_stack()
    truth, _ = fixture(tmp_path, kind=kind, size=size)
    config, digest, expected = protocol(tmp_path, truth)
    before = truth.read_bytes()
    output = tmp_path / "report.json"
    result = gate._check_native(truth, config, digest, output, expected)
    assert result["canonical_kind_counts"][kind] == 1
    assert result["records"] == result["unique_ids"] == 1
    assert result["native_metadata_consistency"] == "PASS"
    assert result["denominator_validation"] == "NOT_VALIDATED"
    assert not result["normative_compliance_claim"] and not result["scoring_performed"]
    assert result["global_sign_only_flags_retained"] == (size != (60 if kind == "INS" else -60))
    assert truth.read_bytes() == before


@pytest.mark.parametrize("info,message", [
    ("SVTYPE=DEL;SVLEN=-59", "SVLEN magnitude"),
    ("SVTYPE=DEL;SVLEN=-60;SVLEN=-60", "literal INFO"),
    ("SVTYPE=DEL;SVLEN=-60,60", "literal INFO"),
    ("SVTYPE=DEL;SVLEN=oops", "literal SVLEN"),
])
def test_exact_native_rejects_bad_literal_without_report(tmp_path, info, message):
    require_native_stack()
    truth, _ = fixture(tmp_path, info=info)
    config, digest, expected = protocol(tmp_path, truth)
    before = truth.read_bytes()
    output = tmp_path / "report.json"
    with pytest.raises(ValueError, match=message):
        gate._check_native(truth, config, digest, output, expected)
    assert not output.exists() and truth.read_bytes() == before


@pytest.mark.parametrize("which", ["identity_order_sha256", "eligible_truth_sha256"])
def test_exact_native_integrity_failure_no_report(tmp_path, which):
    require_native_stack()
    truth, _ = fixture(tmp_path)
    config, digest, expected = protocol(tmp_path, truth)
    expected[which] = "0" * 64
    content = json.loads(config.read_text())
    content[which] = "0" * 64
    config.write_text(json.dumps(content))
    digest = sha256(config.read_bytes()).hexdigest()
    output = tmp_path / "report.json"
    with pytest.raises(ValueError, match="pin mismatch|order mismatch"):
        gate._check_native(truth, config, digest, output, expected)
    assert not output.exists()
