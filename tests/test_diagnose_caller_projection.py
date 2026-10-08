"""Synthetic field-localization controls, never real caller data."""
import json

import pytest

from analysis import diagnose_caller_projection as diag
from analysis import prepare_released_callers as prep

HEADER = (
    "##fileformat=VCFv4.2\n##contig=<ID=synthetic,length=1000>\n"
    '##INFO=<ID=AF,Number=A,Type=Float,Description="Synthetic">\n'
    '##INFO=<ID=RNAMES,Number=.,Type=String,Description="Synthetic">\n'
    '##FORMAT=<ID=GT,Number=1,Type=String,Description="Synthetic">\n'
    '##FORMAT=<ID=GQ,Number=1,Type=Float,Description="Synthetic">\n'
    "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tNULL\n"
)
ROW = "synthetic\t10\t.\tA\tAA\t60\tPASS\tAF=0.125;RNAMES=SYNTH_NAME\tGT:GQ\t0/1:20\n"


def prepared(tmp_path, raw=HEADER + ROW):
    pysam = pytest.importorskip("pysam")
    source, annotated, split = [tmp_path / name for name in ("source.vcf", "annotated.vcf", "split.vcf")]
    source.write_text(raw)
    counts = {"children": 0, "pos_zero": 0, "pos_length_plus_one": 0}
    policy = {"expected_sample_label": "NULL", "expected_source_records": 1,
              "max_children": 1, "source_sha256": "a" * 64, "omit_info_rnames": True}
    prep._annotate(source, annotated, policy, pysam, counts)
    split.write_bytes(annotated.read_bytes())
    return pysam, source, annotated, split


def test_complete_matching_population(tmp_path):
    pysam, source, annotated, split = prepared(tmp_path)
    result = diag.compare_streams(source, annotated, split, pysam, 1)
    assert result["records"] == 1
    assert set(result["semantic_mismatch_rows"].values()) == {0}
    assert set(result["serialized_mismatch_rows"].values()) == {0}
    assert all(not changes for changes in result["changed_field_occurrences"].values())


@pytest.mark.parametrize("old,new,category", [
    ("\t60\t", "\t61\t", "QUAL"),
    ("AF=0.125", "AF=0.25", "INFO/AF"),
    ("0/1:20", "0/1:21", "FORMAT/GQ"),
    ("0/1:20", "1/1:20", "FORMAT/GT"),
    ("\tA\tAA\t", "\tA\tAAA\t", "ALT"),
    ("\t10\t", "\t11\t", "pos"),
])
def test_field_corruption_is_localized_not_accepted(tmp_path, old, new, category):
    pysam, source, annotated, split = prepared(tmp_path)
    raw = split.read_text()
    assert raw.count(old) == 1
    split.write_text(raw.replace(old, new))
    result = diag.compare_streams(source, annotated, split, pysam, 1)
    assert result["semantic_mismatch_rows"]["annotated_to_split"] == 1
    assert result["changed_field_occurrences"]["annotated_to_split"][category] == 1
    assert result["semantic_mismatch_rows"]["source_to_annotated"] == 0


@pytest.mark.parametrize("edit", ["missing", "extra", "wrong_order", "wrong_alt", "multiallelic", "wrong_sample"])
def test_incomplete_or_unjoined_input_stops(tmp_path, edit):
    pysam, source, annotated, split = prepared(tmp_path)
    raw = split.read_text()
    if edit == "missing": raw = "\n".join(raw.splitlines()[:-1]) + "\n"
    elif edit == "extra": raw += raw.splitlines()[-1] + "\n"
    elif edit == "wrong_order": raw = raw.replace("CTRL_SRCORD=1", "CTRL_SRCORD=2")
    elif edit == "wrong_alt": raw = raw.replace("CTRL_ALTIDX=1", "CTRL_ALTIDX=2")
    elif edit == "multiallelic": raw = raw.replace("\tA\tAA\t", "\tA\tAA,AAA\t")
    else: raw = raw.replace("\tNULL\n", "\tOTHER_SAMPLE\n")
    split.write_text(raw)
    with pytest.raises(prep.CallerPreparationGuardError):
        diag.compare_streams(source, annotated, split, pysam, 1)


def test_arbitrary_field_names_or_values_are_not_reported():
    left = [None] * len(diag.FIELDS)
    right = left.copy()
    left[9], right[9] = {"PRIVATE_LOOKING_NAME": ["SYNTH_SECRET"]}, {}
    changes = diag.compare_fields(json.dumps(left), json.dumps(right))
    assert changes == ["INFO/OTHER"]
    assert "PRIVATE_LOOKING_NAME" not in str(changes) and "SYNTH_SECRET" not in str(changes)


def test_projection_schema_mismatch_stops():
    with pytest.raises(prep.CallerPreparationGuardError, match="schema"):
        diag.compare_fields("[]", "[]")
