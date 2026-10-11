"""Synthetic diagnostics for caller projection serialization behavior.

These controls use tiny local VCFs only. They do not inspect caller inputs or
claim to identify the cause of any real preparation failure.
"""
import json

import pytest

from analysis import prepare_released_callers as prep


HEADER = (
    "##fileformat=VCFv4.2\n"
    "##contig=<ID=chrSynthetic,length=1000>\n"
    '##INFO=<ID=IA,Number=A,Type=Float,Description="alternate values">\n'
    '##INFO=<ID=IR,Number=R,Type=Float,Description="reference and alternate values">\n'
    '##INFO=<ID=END,Number=1,Type=Integer,Description="synthetic end">\n'
    '##FORMAT=<ID=GT,Number=1,Type=String,Description="genotype">\n'
    '##FORMAT=<ID=FA,Number=A,Type=Float,Description="alternate values">\n'
    '##FORMAT=<ID=FR,Number=R,Type=Float,Description="reference and alternate values">\n'
    '##FORMAT=<ID=FG,Number=G,Type=Float,Description="genotype values">\n'
    "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSYNTH\n"
)

# Deliberately include more decimal precision than ordinary VCF serialization
# on the local HTSlib stack retains. The symbolic multiallelic record makes END
# and the original caller ID observable in _semantic_child as well.
RECORD = (
    "chrSynthetic\t100\toriginal_id\tN\t<DEL>,<DUP>\t123.123456789\tPASS\t"
    "IA=0.123456789,0.234567891;"
    "IR=0.345678912,0.456789123,0.567891234;END=200\t"
    "GT:FA:FR:FG\t"
    "1/2:0.123456789,0.234567891:"
    "0.345678912,0.456789123,0.567891234:"
    "0.0123456789,0.0234567891,0.0345678912,"
    "0.0456789123,0.0567891234,0.0678912345\n"
)


def _ordinary_round_trip(tmp_path):
    pysam = pytest.importorskip("pysam")
    source = tmp_path / "synthetic-source.vcf"
    serialized = tmp_path / "synthetic-round-trip.vcf"
    source.write_text(HEADER + RECORD)

    with pysam.VariantFile(str(source)) as reader:
        source_records = list(reader)
        assert len(source_records) == 1
        record = source_records[0]
        before_row = prep._row(record)
        source_values = {
            "qual": record.qual,
            "IA": tuple(record.info["IA"]),
            "IR": tuple(record.info["IR"]),
            "FA": tuple(record.samples[0]["FA"]),
            "FR": tuple(record.samples[0]["FR"]),
            "FG": tuple(record.samples[0]["FG"]),
        }
        before = [
            json.loads(prep._semantic_child(record, alt_index))
            for alt_index in (1, 2)
        ]
        output_header = reader.header.copy()
        record.translate(output_header)
        with pysam.VariantFile(str(serialized), "w", header=output_header) as writer:
            writer.write(record)

    with pysam.VariantFile(str(serialized)) as reader:
        output_records = list(reader)
        assert len(output_records) == 1
        round_tripped = output_records[0]
        after_row = prep._row(round_tripped)
        after = [
            json.loads(prep._semantic_child(round_tripped, alt_index))
            for alt_index in (1, 2)
        ]

    return pysam, source, serialized, before_row, before, after_row, after, source_values


def test_float_serialization_can_change_semantics_with_identical_record_text(tmp_path):
    _, source, _, before_row, before, after_row, after, source_values = _ordinary_round_trip(tmp_path)

    # The helper's standard record text is identical. The parsed float values
    # are not: the writer rounds the source values before the second parse.
    assert before_row == after_row
    assert "123.123456789" in source.read_text()
    assert "123.123\tPASS" in before_row
    assert before != after

    for alt_index, (child_before, child_after) in enumerate(zip(before, after), start=1):
        # Identity, coordinates, explicit END, original ID, alleles, filters,
        # schema, sample, GT, and phase are preserved by this ordinary pass.
        assert child_before[:7] == child_after[:7]
        assert child_before[8] == child_after[8]
        assert child_before[10:12] == child_after[10:12]
        assert child_before[12]["GT"] == child_after[12]["GT"]
        assert child_before[13] == child_after[13]
        assert child_before[2] == 200
        assert child_before[3] == ["END=200"]
        assert child_before[4] == "original_id"

        # Both projected children retain the expected A, R, and diploid G
        # cardinalities. Their float values expose the serialization change.
        for child in (child_before, child_after):
            assert len(child[9]["IA"]) == 1
            assert len(child[9]["IR"]) == 2
            assert len(child[12]["FA"]) == 1
            assert len(child[12]["FR"]) == 2
            assert len(child[12]["FG"]) == 3

        # Check the actual ALT selection against the full parsed source arrays.
        # The explicit G offsets are the diploid ordering for alleles 0/1/2.
        g_offsets = (0, 1, 2) if alt_index == 1 else (0, 3, 5)
        assert child_before[7] == source_values["qual"]
        assert child_before[9]["IA"] == pytest.approx(
            [source_values["IA"][alt_index - 1]]
        )
        assert child_before[9]["IR"] == pytest.approx(
            [source_values["IR"][0], source_values["IR"][alt_index]]
        )
        assert child_before[12]["FA"] == pytest.approx(
            [source_values["FA"][alt_index - 1]]
        )
        assert child_before[12]["FR"] == pytest.approx(
            [source_values["FR"][0], source_values["FR"][alt_index]]
        )
        assert child_before[12]["FG"] == pytest.approx(
            [source_values["FG"][offset] for offset in g_offsets]
        )

        assert child_before[7] != child_after[7]  # QUAL
        assert child_before[9] != child_after[9]  # INFO Float A and R
        for key in ("FA", "FR", "FG"):
            assert child_before[12][key] != child_after[12][key]

    # ALT-specific selection follows Number=A/R/G projection. For diploid
    # Number=G, the two children use offsets (0,1,2) and (0,3,5).
    assert before[0][6] == "<DEL>" and before[1][6] == "<DUP>"
    assert before[0][12]["GT"] == [1, None]
    assert before[1][12]["GT"] == [None, 1]
    assert before[0][12]["FG"][1:] != before[1][12]["FG"][1:]


def test_projection_diagnostic_detects_a_deliberately_corrupted_info_value(tmp_path):
    pysam, _, serialized, _, _, _, after, _ = _ordinary_round_trip(tmp_path)
    text = serialized.read_text()
    original = "IA=0.123457,0.234568"
    corrupted = "IA=9.123457,0.234568"
    assert text.count(original) == 1
    serialized.write_text(text.replace(original, corrupted, 1))

    with pysam.VariantFile(str(serialized)) as reader:
        record = next(reader)
        observed = json.loads(prep._semantic_child(record, 1))

    # This is a negative control: the changed INFO value must remain visible to
    # the semantic projection check. It is never treated as an accepted value.
    assert observed != after[0]
    assert observed[9]["IA"] != after[0][9]["IA"]
    assert observed[9]["IA"][0] == pytest.approx(9.123457, rel=1e-6)
