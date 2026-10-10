"""Synthetic controls for INFO/END serialization across caller annotation.

The test runs the unchanged _annotate helper on a tiny VCF, then inspects the
emitted text and reads that VCF again with ordinary pysam APIs. It uses no
caller data and does not infer the cause of any real preparation result.
"""
import json

import pytest

from analysis import prepare_released_callers as prep


HEADER = (
    "##fileformat=VCFv4.2\n"
    "##contig=<ID=chrSynthetic,length=1000>\n"
    '##INFO=<ID=END,Number=1,Type=Integer,Description="synthetic end">\n'
    '##FORMAT=<ID=GT,Number=1,Type=String,Description="genotype">\n'
    "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSYNTH\n"
)

RECORDS = (
    "chrSynthetic\t10\tliteral_ins_no_end\tA\tAT\t.\tPASS\t.\tGT\t0/1\n",
    "chrSynthetic\t20\tliteral_del_no_end\tAT\tA\t.\tPASS\t.\tGT\t0/1\n",
    "chrSynthetic\t30\tliteral_ins_redundant_end\tA\tAT\t.\tPASS\tEND=30\tGT\t0/1\n",
    "chrSynthetic\t40\tliteral_del_redundant_end\tAT\tA\t.\tPASS\tEND=41\tGT\t0/1\n",
    "chrSynthetic\t50\tsymbolic_redundant_end\tN\t<DEL>\t.\tPASS\tEND=50\tGT\t0/1\n",
    "chrSynthetic\t60\tsymbolic_nonredundant_end\tN\t<DEL>\t.\tPASS\tEND=80\tGT\t0/1\n",
)


def _raw_end(row):
    info = row.rstrip("\r\n").split("\t")[7]
    return tuple(token for token in info.split(";")
                 if token.partition("=")[0] == "END")


def _raw_rows(path):
    rows = {}
    for row in path.read_text().splitlines():
        if not row or row.startswith("#"):
            continue
        fields = row.split("\t")
        rows[fields[2]] = row
    return rows


def _without_end_and_stop(fields):
    fields = json.loads(json.dumps(fields))
    fields[2] = "<STOP>"
    fields[3] = "<END-TOKENS>"
    fields[9].pop("END", None)
    return fields


def test_annotate_end_serialization_controls_and_changed_end_negative_control(
    tmp_path, monkeypatch
):
    pysam = pytest.importorskip("pysam")
    from pysam.version import __htslib_version__

    source = tmp_path / "synthetic-source.vcf"
    annotated = tmp_path / "synthetic-annotated.vcf"
    tampered = tmp_path / "synthetic-changed-end.vcf"
    source.write_text(HEADER + "".join(RECORDS))

    original_semantic_child = prep._semantic_child
    before = {}

    def capture_before_write(record, index=None, omitted_info=()):
        result = original_semantic_child(record, index, omitted_info)
        before[record.id] = {
            "row": prep._row(record),
            "stop": record.stop,
            "semantic": json.loads(result),
        }
        return result

    # Capture the exact projection point used by the unchanged _annotate
    # implementation: after identity annotation and before writer serialization.
    monkeypatch.setattr(prep, "_semantic_child", capture_before_write)
    counts = {
        "source_records": 0,
        "children": 0,
        "pos_zero": 0,
        "pos_length_plus_one": 0,
    }
    expected, projected = prep._annotate(
        source,
        annotated,
        {
            "expected_sample_label": "SYNTH",
            "expected_source_records": len(RECORDS),
            "max_children": len(RECORDS),
            "source_sha256": "0" * 64,
        },
        pysam,
        counts,
    )
    monkeypatch.setattr(prep, "_semantic_child", original_semantic_child)

    assert counts["source_records"] == len(RECORDS)
    assert counts["children"] == len(RECORDS)
    assert expected["records"] == projected["records"] == len(RECORDS)
    assert set(before) == {row.split("\t")[2] for row in RECORDS}

    raw_output = _raw_rows(annotated)
    raw_source = _raw_rows(source)
    assert set(raw_output) == set(before)
    after = {}
    with pysam.VariantFile(str(annotated)) as reader:
        for record in reader:
            after[record.id] = {
                "row": prep._row(record),
                "stop": record.stop,
                "semantic": json.loads(original_semantic_child(record, 1)),
            }

    assert set(after) == set(before)
    witnesses = []
    observations = {}
    for record_id in before:
        before_end = _raw_end(before[record_id]["row"])
        output_raw_end = _raw_end(raw_output[record_id])
        after_row_end = _raw_end(after[record_id]["row"])
        after_semantic_end = tuple(after[record_id]["semantic"][3])

        # _semantic_child reads END from _row; raw output text is measured
        # independently because parser and writer views are the subject here.
        assert after_row_end == after_semantic_end

        stop_equal = before[record_id]["stop"] == after[record_id]["stop"]
        other_fields_equal = (
            _without_end_and_stop(before[record_id]["semantic"])
            == _without_end_and_stop(after[record_id]["semantic"])
        )
        if before_end != output_raw_end and stop_equal and other_fields_equal:
            witnesses.append(record_id)
        observations[record_id] = {
            "source_raw_end": _raw_end(raw_source[record_id]),
            "prewrite_row_end": before_end,
            "annotated_file_raw_end": output_raw_end,
            "reparsed_row_end": after_row_end,
            "prewrite_stop": before[record_id]["stop"],
            "reparsed_stop": after[record_id]["stop"],
            "other_projected_fields_equal": other_fields_equal,
            "prewrite_projection": before[record_id]["semantic"],
            "reparsed_projection": after[record_id]["semantic"],
        }

    # An empty witness list is a valid diagnostic result. The companion note
    # records the observed result for this local pysam/HTSlib stack.

    # Genuine negative control: changing symbolic END must change parsed stop
    # and the helper's projection while leaving all other projected fields fixed.
    output_lines = annotated.read_text().splitlines()
    changed_lines = []
    for line in output_lines:
        if line and not line.startswith("#") and line.split("\t")[2] == "symbolic_nonredundant_end":
            assert _raw_end(line) == ("END=80",)
            fields = line.split("\t")
            fields[7] = fields[7].replace("END=80", "END=81", 1)
            line = "\t".join(fields)
        changed_lines.append(line)
    tampered.write_text("\n".join(changed_lines) + "\n")

    changed_row = None
    with pysam.VariantFile(str(tampered)) as reader:
        changed_record = next(
            record for record in reader if record.id == "symbolic_nonredundant_end"
        )
        changed_row = prep._row(changed_record)
        changed = json.loads(original_semantic_child(changed_record, 1))
        changed_stop = changed_record.stop

    control = after["symbolic_nonredundant_end"]
    assert _raw_end(changed_row) == ("END=81",)
    assert control["stop"] == 80
    assert changed_stop == 81
    assert control["semantic"][3] == ["END=80"]
    assert changed[3] == ["END=81"]
    assert _without_end_and_stop(control["semantic"]) == _without_end_and_stop(changed)

    report = {
        "pysam": pysam.__version__,
        "htslib": __htslib_version__,
        "end_serialization_witnesses": witnesses,
        "records": observations,
        "negative_control": {
            "record": "symbolic_nonredundant_end",
            "original_end": "END=80",
            "changed_end": "END=81",
            "original_stop": control["stop"],
            "changed_stop": changed_stop,
            "other_projected_fields_equal": (
                _without_end_and_stop(control["semantic"])
                == _without_end_and_stop(changed)
            ),
        },
    }
    (tmp_path / "observations.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )
