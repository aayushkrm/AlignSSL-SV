import hashlib
import json
import random

import pysam
import pytest

import analysis.observe_native_fixture as observer


_rng = random.Random(1729)
_bases = "ACGT"
REFERENCE = (
    "".join(_bases[_rng.getrandbits(2)] for _ in range(1000))
    + "A" * 2000
    + "".join(_bases[_rng.getrandbits(2)] for _ in range(1000))
)
REFERENCE_SHA256 = hashlib.sha256(REFERENCE.encode("ascii")).hexdigest()
assert REFERENCE_SHA256 == "1e9e223b565b9f0847946d777a5c7fd4f2ba09f076174e4fab96f473156fe9ef"
REFERENCE_SHA256_BASIS = "uppercase sequence ASCII bytes; FASTA header and wrapping excluded"
HEADER = (
    "##fileformat=VCFv4.2\n"
    "##contig=<ID=chrSynthetic,length=4000>\n"
    '##FILTER=<ID=LowQual,Description="low quality">\n'
    '##FORMAT=<ID=GT,Number=1,Type=String,Description="genotype">\n'
)


def _row(pos, ref, alt, *, filt="PASS", gt=None):
    fields = ["chrSynthetic", str(pos), ".", ref, alt, ".", filt, "."]
    if gt is not None:
        fields.extend(["GT", gt])
    return "\t".join(fields) + "\n"


def _write_vcf(path, rows, *, samples=None):
    columns = "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO"
    if samples is not None:
        columns += "\tFORMAT\t" + "\t".join(samples)
    path.write_text(HEADER + columns + "\n" + "".join(rows), encoding="ascii")


def _write_bam(path):
    header = {"HD": {"VN": "1.6"}, "SQ": [{"SN": "chrSynthetic", "LN": 4000}]}
    with pysam.AlignmentFile(str(path), "wb", header=header) as bam:
        mapped = pysam.AlignedSegment()
        mapped.query_name = "synthetic-read-name"
        mapped.query_sequence = "A" * 40
        mapped.flag = 0
        mapped.reference_id = 0
        mapped.reference_start = 1480
        mapped.mapping_quality = 60
        mapped.cigar = [(0, 40)]
        mapped.query_qualities = pysam.qualitystring_to_array("I" * 40)
        bam.write(mapped)

        unmapped = pysam.AlignedSegment()
        unmapped.query_name = "synthetic-unmapped-name"
        unmapped.query_sequence = "A" * 10
        unmapped.flag = 4
        unmapped.query_qualities = pysam.qualitystring_to_array("I" * 10)
        bam.write(unmapped)


def _fixture(tmp_path, *, candidate_rows=None, final_rows=None,
             final_samples=("SYNTH",), bed_text="chrSynthetic\t1490\t1510\n",
             reference_sequence=REFERENCE, final_bcf=False):
    reference = tmp_path / "reference.fa"
    reference.write_text(">chrSynthetic\n" + reference_sequence + "\n", encoding="ascii")
    truth = tmp_path / "truth.json"
    truth.write_text(json.dumps({
        "version": 1,
        "contig": "chrSynthetic",
        "reference_length": 4000,
        "reference_sha256": REFERENCE_SHA256,
        "reference_sha256_basis": REFERENCE_SHA256_BASIS,
        "insertion_offset": 1500,
        "inserted_sequence": "A" * 60,
        "expected_alt_length": 4060,
        "sample": "SYNTH",
    }), encoding="utf-8")
    bed = tmp_path / "assembly.bed"
    bed.write_text(bed_text, encoding="ascii")
    candidate = tmp_path / "candidate.vcf"
    _write_vcf(candidate, [_row(900, "A", "A" * 61)] if candidate_rows is None
               else candidate_rows)
    final_source = tmp_path / "final.vcf"
    _write_vcf(final_source, [_row(1500, "A", "A" * 61, gt="0|1")]
               if final_rows is None else final_rows,
               samples=final_samples)
    final = final_source
    if final_bcf:
        final = tmp_path / "final.bcf"
        with pysam.VariantFile(str(final_source), "r") as source:
            with pysam.VariantFile(str(final), "wb", header=source.header) as output:
                for record in source:
                    output.write(record)
        final_source.unlink()
    bam = tmp_path / "contig.bam"
    _write_bam(bam)
    report = tmp_path / "report.json"
    return {
        "reference": reference,
        "truth": truth,
        "bed": bed,
        "candidate": candidate,
        "final": final,
        "bam": bam,
        "report": report,
    }


def _observe(case):
    return observer.observe_native_fixture(
        case["reference"], case["truth"], case["bed"], case["candidate"],
        case["final"], case["bam"], case["report"],
    )


def test_exact_full_haplotype_summary_accepts_left_shift_and_reads_bcf(tmp_path):
    case = _fixture(
        tmp_path,
        candidate_rows=[_row(1200, "A", "A" * 61)],
        final_rows=[
            _row(1500, "A", "A" * 61, filt="PASS", gt="0/0"),
            _row(1200, "A", "A" * 61, filt="LowQual", gt="1|0"),
            _row(1100, "A", "A" * 61, filt=".", gt="0/1"),
        ],
        final_bcf=True,
    )

    result = _observe(case)
    saved = json.loads(case["report"].read_text(encoding="utf-8"))

    assert result["status"] == "complete"
    assert result["complete_parse"] is True
    assert result["truth"]["validated_exact_scope"] is True
    assert result["reference"]["sequence_sha256"] == REFERENCE_SHA256
    assert result["candidate"]["sample_columns"] == 0
    assert result["candidate"]["total_records"] == 1
    assert result["candidate"]["exact_allele_records"] == 1
    assert result["candidate"]["single_record_output_state"] == "PRESENT"
    assert result["candidate"]["non_equivalent_literal_records"] == 0
    assert result["final"]["exact_allele_records"] == 3
    assert result["final"]["pass_exact_allele_records"] == 1
    assert result["final"]["heterozygous_gt_0_1_or_1_0_exact_records"] == 2
    assert result["final"]["pass_heterozygous_exact_allele_records"] == 0
    assert result["final"]["phased_heterozygous_exact_records"] == 1
    assert result["final"]["unphased_heterozygous_exact_records"] == 1
    assert result["final"]["filter_counts"] == {".": 1, "LowQual": 1, "PASS": 1}
    assert result["final"]["exact_pass_heterozygous_recovery_state"] == (
        "EXACT_ALLELE_PRESENT_ENDPOINT_NOT_MET"
    )
    assert result["assembly_bed"]["insertion_offset_covered"] is True
    assert result["contig_bam"]["alignment_records"] == 2
    assert result["contig_bam"]["mapped_alignment_records"] == 1
    assert result["contig_bam"]["unmapped_alignment_records"] == 1
    assert result["contig_bam"]["unique_contig_names"] == 2
    assert result["contig_bam"]["query_length_counts_by_alignment"] == {"10": 1, "40": 1}
    assert result["contig_bam"]["reference_lengths"] == [
        {"name": "chrSynthetic", "length": 4000}
    ]
    assert result["input_integrity"]["all_before_after_hashes_and_snapshots_match"] is True
    assert saved == result
    report_text = case["report"].read_text(encoding="utf-8")
    assert "synthetic-read-name" not in report_text
    assert "synthetic-unmapped-name" not in report_text
    assert "A" * 100 not in report_text
    assert case["report"].stat().st_size <= observer.MAX_REPORT


def test_non_equivalent_invalid_ref_symbolic_and_multiallelic_rows_are_counted(tmp_path):
    case = _fixture(tmp_path, candidate_rows=[
        _row(1500, "A", "A" * 60),
        _row(1500, "C", "T"),
        _row(1400, "A", "<INS>"),
        _row(1300, "A", "A" * 61 + ",<INS>"),
    ])

    result = _observe(case)
    counts = result["candidate"]
    assert counts["total_records"] == 4
    assert counts["exact_allele_records"] == 0
    assert counts["non_equivalent_literal_records"] == 1
    assert counts["invalid_ref_records"] == 1
    assert counts["symbolic_records"] == 2
    assert counts["multiallelic_unresolved_records"] == 1
    assert counts["unresolved_records"] == 3
    assert counts["single_record_output_state"] == "UNRESOLVED"
    assert counts["full_haplotype_absence_claim"] is False


def test_two_nonmatching_literal_edits_in_a_run_keep_negative_unresolved(tmp_path):
    case = _fixture(tmp_path, candidate_rows=[
        _row(1500, "A", "A" * 60),
        _row(1400, "A", "AA"),
    ])

    result = _observe(case)
    counts = result["candidate"]
    assert counts["exact_allele_records"] == 0
    assert counts["non_equivalent_literal_records"] == 2
    assert counts["non_equivalent_literal_records_in_A_repeat"] == 2
    assert counts["single_record_output_state"] == "UNRESOLVED"
    assert counts["negative_inference_unresolved_reasons"] == {
        "multiple_non_equivalent_literal_records_on_chrSynthetic": 2
    }


def test_exact_record_presence_survives_other_unresolved_records(tmp_path):
    case = _fixture(tmp_path, candidate_rows=[
        _row(1500, "A", "A" * 61),
        _row(1400, "A", "<INS>"),
    ])

    result = _observe(case)
    counts = result["candidate"]
    assert counts["exact_allele_records"] == 1
    assert counts["single_record_output_state"] == "PRESENT"
    assert counts["negative_inference_unresolved_reasons"] == {"symbolic_records": 1,
                                                               "other_unresolved_records": 1}


def test_single_nonmatching_literal_row_reports_no_exact_record_not_full_absence(tmp_path):
    case = _fixture(tmp_path, candidate_rows=[_row(1500, "A", "A" * 60)])

    result = _observe(case)

    assert result["candidate"]["single_record_output_state"] == "ABSENT_FROM_OUTPUT"
    assert result["candidate"]["exact_single_record_presence"] is False
    assert result["candidate"]["full_haplotype_absence_claim"] is False


def test_joint_final_recovery_counts_one_record_with_pass_and_heterozygous_gt(tmp_path):
    case = _fixture(tmp_path, final_rows=[_row(1500, "A", "A" * 61, gt="1|0")])

    result = _observe(case)

    assert result["final"]["pass_exact_allele_records"] == 1
    assert result["final"]["heterozygous_gt_0_1_or_1_0_exact_records"] == 1
    assert result["final"]["pass_heterozygous_exact_allele_records"] == 1
    assert result["final"]["exact_pass_heterozygous_recovery_state"] == "RECOVERED"


def test_final_requires_synth_sample_and_does_not_create_report(tmp_path):
    case = _fixture(tmp_path, final_samples=("OTHER",))

    with pytest.raises(observer.FixtureError, match="exactly the SYNTH sample"):
        _observe(case)

    assert not case["report"].exists()


def test_symlink_input_is_rejected(tmp_path):
    case = _fixture(tmp_path)
    link = tmp_path / "assembly-link.bed"
    link.symlink_to(case["bed"])
    case["bed"] = link

    with pytest.raises(observer.FixtureError, match="regular nonlink"):
        _observe(case)

    assert not case["report"].exists()


def test_reference_negative_does_not_match_fixed_truth_scope(tmp_path):
    case = _fixture(tmp_path, reference_sequence="C" * 4000)

    with pytest.raises(observer.FixtureError, match="fixed 4,000-base synthetic reference"):
        _observe(case)

    assert not case["report"].exists()


def test_changed_input_is_detected_before_report_creation(tmp_path, monkeypatch):
    case = _fixture(tmp_path)
    parse_callset = observer._summarize_callset

    def change_candidate_after_parse(payload, reference, alternate, *, role, final=False):
        result = parse_callset(payload, reference, alternate, role=role, final=final)
        if role == "candidate":
            original = case["candidate"].read_bytes()
            changed = original.replace(b"900", b"901", 1)
            assert changed != original
            case["candidate"].write_bytes(changed)
        return result

    monkeypatch.setattr(observer, "_summarize_callset", change_candidate_after_parse)
    with pytest.raises(observer.FixtureError, match="snapshot changed|bytes or snapshots changed"):
        _observe(case)

    assert not case["report"].exists()


def test_input_caps_reject_oversized_and_combined_inputs_before_parse(tmp_path):
    per_file_dir = tmp_path / "per-file"
    per_file_dir.mkdir()
    case = _fixture(per_file_dir)
    case["bed"].write_bytes(b"x" * (observer.MAX_INPUT_PER_FILE + 1))
    with pytest.raises(observer.FixtureError, match="8-MiB per-file cap"):
        _observe(case)
    assert not case["report"].exists()

    aggregate_dir = tmp_path / "aggregate"
    aggregate_dir.mkdir()
    aggregate = _fixture(aggregate_dir)
    aggregate["bed"].write_bytes(b"x" * observer.MAX_INPUT_PER_FILE)
    aggregate["candidate"].write_bytes(b"x" * observer.MAX_INPUT_PER_FILE)
    with pytest.raises(observer.FixtureError, match="combined inputs exceed the 16-MiB cap"):
        _observe(aggregate)
    assert not aggregate["report"].exists()


def test_report_size_cap_and_exclusive_creation(tmp_path):
    report = tmp_path / "new-report.json"
    with pytest.raises(observer.FixtureError, match="64-KiB cap"):
        observer._write_exclusive_report(report, b"x" * (observer.MAX_REPORT + 1))
    assert not report.exists()

    report.write_bytes(b"keep")
    with pytest.raises(observer.FixtureError, match="must be new"):
        observer._write_exclusive_report(report, b"replacement")
    assert report.read_bytes() == b"keep"


def test_cli_requires_and_uses_each_explicit_input_and_report_path(tmp_path, capsys):
    case = _fixture(tmp_path)
    status = observer.main([
        "--reference-fasta", str(case["reference"]),
        "--truth-json", str(case["truth"]),
        "--assembly-bed", str(case["bed"]),
        "--candidate-vcf-bcf", str(case["candidate"]),
        "--final-vcf-bcf", str(case["final"]),
        "--contig-bam", str(case["bam"]),
        "--report", str(case["report"]),
    ])

    assert status == 0
    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "complete"
    assert output["report"] == str(case["report"])


def test_invalid_truth_contract_is_rejected_without_report(tmp_path):
    case = _fixture(tmp_path)
    truth = json.loads(case["truth"].read_text(encoding="utf-8"))
    truth["insertion_offset"] = 1501
    case["truth"].write_text(json.dumps(truth), encoding="utf-8")

    with pytest.raises(observer.FixtureError, match="fixed version-1 synthetic scope"):
        _observe(case)

    assert not case["report"].exists()


def test_bgzip_final_native_output_is_supported(tmp_path):
    case = _fixture(tmp_path, candidate_rows=[_row(1200, "A", "A" * 61)])
    compressed = tmp_path / "genotyped.sv.vcf.gz"
    pysam.tabix_compress(str(case["final"]), str(compressed), force=False)
    case["final"] = compressed
    result = _observe(case)
    assert result["final"]["pass_heterozygous_exact_allele_records"] == 1
    assert result["final"]["exact_pass_heterozygous_recovery_state"] == "RECOVERED"


def test_empty_complete_callsets_are_not_missing_or_unresolved(tmp_path):
    case = _fixture(tmp_path, candidate_rows=[], final_rows=[])
    result = _observe(case)
    for role in ("candidate", "final"):
        assert result[role]["total_records"] == 0
        assert result[role]["exact_allele_records"] == 0
        assert result[role]["single_record_output_state"] == "ABSENT_FROM_OUTPUT"
        assert result[role]["negative_inference_unresolved_reasons"] == {}
    assert result["final"]["pass_heterozygous_exact_allele_records"] == 0


def test_missing_output_is_not_treated_as_empty(tmp_path):
    case = _fixture(tmp_path)
    case["candidate"].unlink()
    with pytest.raises(observer.FixtureError, match="could not be opened"):
        _observe(case)
    assert not case["report"].exists()


@pytest.mark.parametrize("role", ["candidate", "final"])
@pytest.mark.parametrize("include_exact", [False, True])
def test_padded_compatible_joint_edits_preserve_uncertainty_and_positive_precedence(
    tmp_path, role, include_exact
):
    padded_ref = REFERENCE[998:1002]
    padded_alt = REFERENCE[998:1001] + "A" * 20 + REFERENCE[1001:1002]
    # Two nonoverlapping valid replacements jointly yield the frozen truth.
    joint = (REFERENCE[:998] + padded_alt + REFERENCE[1002:1499]
             + "A" * 41 + REFERENCE[1500:])
    truth = REFERENCE[:1500] + "A" * 60 + REFERENCE[1500:]
    assert joint == truth
    gt = "0/1" if role == "final" else None
    rows = [_row(999, padded_ref, padded_alt, gt=gt),
            _row(1500, "A", "A" * 41, gt=gt)]
    if include_exact:
        rows.append(_row(1400, "A", "A" * 61, gt=gt))
    case = _fixture(tmp_path, **{role + "_rows": rows})
    counts = _observe(case)[role]
    assert counts["exact_allele_records"] == int(include_exact)
    assert counts["single_record_output_state"] == (
        "PRESENT" if include_exact else "UNRESOLVED"
    )
    assert counts["negative_inference_unresolved_reasons"] == {
        "multiple_non_equivalent_literal_records_on_chrSynthetic": 2
    }
    assert counts["full_haplotype_absence_claim"] is False
