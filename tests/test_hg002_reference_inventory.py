import gzip
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from analysis.hg002_reference_inventory import run_inventory
from analysis import hg002_reference_inventory as inventory_module


def gtf_line(chrom, feature, start, end, strand, phase, attributes, source="test"):
    return f"{chrom}\t{source}\t{feature}\t{start}\t{end}\t.\t{strand}\t{phase}\t{attributes}\n"


def write_gtf(path, text):
    path.write_text(text, encoding="utf-8")
    return path


def run_fixture(tmp_path, text, *, measure=False, deadline=30, clock=None):
    source = write_gtf(tmp_path / "reference.gtf", text)
    raw = source.read_bytes()
    out = tmp_path / "inventory-leaf"
    result = run_inventory(
        source,
        out,
        expected_sha256=hashlib.sha256(raw).hexdigest(),
        expected_size_bytes=len(raw),
        deadline_seconds=deadline,
        checkpoint_seconds=0,
        measure_existing_index=measure,
        _monotonic=clock,
    )
    return result, json.loads((out / "inventory.json").read_text()), json.loads(
        (out / "manifest.json").read_text()
    )


class ReferenceInventoryTests(unittest.TestCase):
    def setUp(self):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        self.tmp_path = Path(temp_dir.name)

    def test_junction_spanning_start_and_stop_blocks_sum_on_both_strands(self):
        rows = []
        # Each declared codon uses two coordinate blocks. The coordinate gaps
        # are introns; only the annotated block lengths count toward the total.
        for feature, blocks in (
            (
                "start_codon",
                [(10, 11, "+", "tp"), (30, 30, "+", "tp"),
                 (130, 130, "-", "tm"), (150, 151, "-", "tm")],
            ),
            (
                "stop_codon",
                [(40, 40, "+", "tp"), (60, 61, "+", "tp"),
                 (230, 231, "-", "tm"), (250, 250, "-", "tm")],
            ),
        ):
            for start, end, strand, transcript in blocks:
                gene = "gp" if transcript == "tp" else "gm"
                rows.append(
                    gtf_line(
                        "chr1",
                        feature,
                        start,
                        end,
                        strand,
                        ".",
                        f'gene_id "{gene}"; transcript_id "{transcript}";',
                    )
                )

        result, inventory, manifest = run_fixture(self.tmp_path, "".join(rows))

        self.assertEqual(result["run_status"], "COMPLETE")
        self.assertIs(manifest["source"]["initial_sha256_verified"], True)
        self.assertIs(manifest["source"]["final_sha256_verified"], True)
        self.assertEqual(manifest["source"]["stable_file_check"], "PASS")
        self.assertEqual(inventory["scope"]["counts_scope"], "FULL_SOURCE_EOF")
        for codon in ("start_codon", "stop_codon"):
            with self.subTest(codon=codon):
                report = inventory["declared_codon_features"][codon]
                self.assertEqual(report["feature_rows"], 4)
                self.assertEqual(
                    report["total_annotated_bases_sum_over_coordinate_blocks"], 6
                )
                self.assertEqual(report["bases_by_strand"], {"+": 3, "-": 3})
                self.assertEqual(
                    report["transcript_ids_with_valid_coordinate_blocks"], 2
                )
                self.assertEqual(
                    report["transcript_block_count_classes"], {"multiple_blocks": 2}
                )
                self.assertEqual(
                    report["transcript_base_sum_distribution"], {"3": 2}
                )
                self.assertNotIn("complete", report)

    def test_source_types_partial_tags_cds_no_cds_and_conflicting_ids(self):
        rows = [
            gtf_line("chr1", "gene", 1, 100, "+", ".", 'gene_id "gpc"; gene_type "protein_coding"; gene_name "PC";'),
            gtf_line("chr1", "transcript", 1, 100, "+", ".", 'gene_id "gpc"; transcript_id "tpc"; gene_type "protein_coding"; transcript_type "protein_coding"; tag "cds_start_NF"; tag "cds_end_NF";'),
            gtf_line("chr1", "CDS", 10, 11, "+", "1", 'gene_id "gpc"; transcript_id "tpc"; gene_type "protein_coding"; transcript_type "protein_coding";'),
            gtf_line("chr1", "CDS", 20, 21, "+", "2", 'gene_id "gpc"; transcript_id "tpc"; gene_type "protein_coding"; transcript_type "protein_coding";'),
            gtf_line("chr1", "CDS", 30, 30, "+", ".", 'gene_id "gpc"; transcript_id "tpc"; gene_type "protein_coding"; transcript_type "protein_coding";'),
            gtf_line("chr1", "gene", 200, 300, "+", ".", 'gene_id "gfree"; gene_type "protein_coding";'),
            gtf_line("chr1", "transcript", 200, 300, "+", ".", 'gene_id "gfree"; transcript_id "tfree"; transcript_type "protein_coding";'),
            gtf_line("chr1", "gene", 400, 500, "+", ".", 'gene_id "gnc"; gene_type "lincRNA";'),
            gtf_line("chr1", "transcript", 400, 500, "+", ".", 'gene_id "gnc"; transcript_id "tnc"; transcript_type "lincRNA";'),
            gtf_line("chr1", "transcript", 600, 700, "+", ".", 'gene_id "gpc"; transcript_id "tshared"; transcript_type "protein_coding";'),
            gtf_line("chr2", "transcript", 600, 700, "-", ".", 'gene_id "gnc"; transcript_id "tshared"; transcript_type "protein_coding";'),
            gtf_line("chr1", "gene", 800, 900, "+", ".", 'gene_id "gconf"; gene_type "protein_coding"; gene_name "A";'),
            gtf_line("chr2", "gene", 800, 900, "-", ".", 'gene_id "gconf"; gene_biotype "lincRNA"; gene_name "B";'),
            # A malformed-width row still contributes its visible feature type
            # and issue count. It is not an annotation feature with IDs.
            "chr1\ttest\texon\tbad-width\n",
        ]

        _, inventory, _ = run_fixture(self.tmp_path, "".join(rows))

        self.assertIs(inventory["scope"]["counts_complete"], True)
        self.assertEqual(inventory["feature_type_counts"]["gene"], 5)
        self.assertEqual(inventory["feature_type_counts"]["transcript"], 5)
        self.assertEqual(inventory["feature_type_counts"]["CDS"], 3)
        self.assertEqual(inventory["feature_type_counts"]["exon"], 1)
        self.assertEqual(inventory["counts"]["malformed_column_count_rows"], 1)
        self.assertEqual(
            inventory["source_unique_gene_ids_by_declared_type"],
            {"CONFLICTING_DECLARATIONS": 1, "lincRNA": 1, "protein_coding": 2},
        )
        self.assertEqual(
            inventory["source_unique_transcript_ids_by_declared_type"],
            {"lincRNA": 1, "protein_coding": 3},
        )
        self.assertEqual(
            inventory["protein_coding_gene_CDS_status"]["total_unique_ids"], 2
        )
        self.assertEqual(inventory["protein_coding_gene_CDS_status"]["with_CDS"], 1)
        self.assertEqual(
            inventory["protein_coding_gene_CDS_status"]["without_CDS"], 1
        )
        self.assertEqual(
            inventory["protein_coding_transcript_CDS_status"]["total_unique_ids"], 3
        )
        self.assertEqual(
            inventory["protein_coding_transcript_CDS_status"]["with_CDS"], 1
        )
        self.assertEqual(
            inventory["protein_coding_transcript_CDS_status"]["without_CDS"], 2
        )
        self.assertEqual(inventory["tags"]["source_transcript_ids_with_cds_start_NF"], 1)
        self.assertEqual(inventory["tags"]["source_transcript_ids_with_cds_end_NF"], 1)
        self.assertEqual(
            inventory["CDS"]["phase_counts"],
            {"0": 0, "1": 1, "2": 1, "unknown": 1, "malformed": 0},
        )
        self.assertEqual(inventory["CDS"]["malformed_phase_value_counts"], {})
        self.assertEqual(
            inventory["CDS"]["transcript_phase_annotation_status_counts"],
            {"MIXED_NUMERIC_AND_UNKNOWN": 1},
        )
        self.assertEqual(
            inventory["CDS"]["transcript_annotated_length_mod_3_counts"], {"2": 1}
        )
        conflicts = inventory["identifier_and_location_conflicts"]
        self.assertEqual(
            conflicts["gene_id_conflict_counts"],
            {
                "multiple_contigs": 2,
                "multiple_declared_types": 1,
                "multiple_gene_names": 1,
                "multiple_strands": 2,
            },
        )
        self.assertEqual(
            conflicts["transcript_id_conflict_counts"],
            {"multiple_contigs": 1, "multiple_gene_ids": 1, "multiple_strands": 1},
        )

    def test_transl_except_sec_and_selenocysteine_feature_are_counted(self):
        rows = [
            gtf_line("chr1", "CDS", 10, 30, "+", "0", 'gene_id "g1"; transcript_id "t1"; transl_except "(pos:chr1:10..12,aa:Sec)";'),
            gtf_line("chr1", "Selenocysteine", 10, 12, "+", ".", 'gene_id "g1"; transcript_id "t1"; tag "selenocysteine";'),
        ]

        _, inventory, _ = run_fixture(self.tmp_path, "".join(rows))

        sec = inventory["selenocysteine_and_transl_except"]
        self.assertEqual(sec["transl_except_attribute_occurrences"], 1)
        self.assertEqual(sec["feature_rows_with_transl_except"], 1)
        self.assertEqual(sec["transl_except_amino_acid_value_counts"], {"Sec": 1})
        self.assertEqual(sec["transl_except_Sec_or_U_occurrences"], 1)
        self.assertEqual(sec["selenocysteine_feature_rows_by_type"], {"Selenocysteine": 1})
        self.assertEqual(sec["selenocysteine_feature_bases_by_type"], {"Selenocysteine": 3})
        self.assertEqual(sec["selenocysteine_related_tag_occurrences"], {"selenocysteine": 1})

    def test_existing_index_probe_measures_and_compares_actual_selection(self):
        rows = [
            gtf_line("chr1", "CDS", 10, 20, "+", "0", 'gene_id "g1"; transcript_id "t1"; gene_type "protein_coding";'),
            gtf_line("chr1", "CDS", 30, 40, "+", "1", 'gene_id "g2"; transcript_id "t2"; gene_type "pseudogene";'),
            gtf_line("chr1", "CDS", 50, 60, "-", "2", 'gene_id "g3"; transcript_id "t3"; transcript_type "protein_coding";'),
            gtf_line("chr1", "CDS", 70, 80, "+", ".", 'gene_name "missing IDs";'),
        ]

        _, inventory, manifest = run_fixture(self.tmp_path, "".join(rows), measure=True)

        prediction = inventory["existing_cohort_index_selection_prediction"]
        actual = manifest["execution"]["existing_index_measurement"]
        self.assertEqual(prediction["selected_rows_by_existing_filter"], 3)
        self.assertEqual(prediction["excluded_by_existing_gene_type_filter"], 1)
        self.assertEqual(actual["status"], "MEASURED")
        self.assertIs(actual["selection_fingerprint_concordant"], True)
        self.assertEqual(actual["selection_comparison"], "concordant")
        self.assertGreater(actual["index_process_peak_rss_bytes"], 0)
        self.assertGreaterEqual(actual["existing_index_build_wall_seconds"], 0)
        self.assertGreaterEqual(actual["existing_index_build_cpu_seconds"], 0)

    def test_existing_output_leaf_is_refused_without_modification(self):
        source = write_gtf(
            self.tmp_path / "reference.gtf",
            gtf_line("chr1", "gene", 1, 2, "+", ".", 'gene_id "g";'),
        )
        out = self.tmp_path / "occupied"
        out.mkdir()
        sentinel = out / "keep.txt"
        sentinel.write_text("keep", encoding="utf-8")
        before = sentinel.read_text()

        with self.assertRaises(FileExistsError):
            run_inventory(
                source,
                out,
                expected_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
            )

        self.assertEqual(sentinel.read_text(), before)
        self.assertEqual(sorted(path.name for path in out.iterdir()), ["keep.txt"])

    def test_truncated_gzip_preserves_prefix_and_marks_non_eof_incomplete(self):
        source = self.tmp_path / "broken.gtf.gz"
        with gzip.open(source, "wt", encoding="utf-8") as stream:
            stream.write(gtf_line("chr1", "gene", 1, 10, "+", ".", 'gene_id "g1";'))
            stream.write(gtf_line("chr1", "CDS", 2, 5, "+", "0", 'gene_id "g1"; transcript_id "t1";'))
        compressed = source.read_bytes()
        source.write_bytes(compressed[:-8])
        out = self.tmp_path / "partial-leaf"

        result = run_inventory(
            source,
            out,
            expected_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
            expected_size_bytes=source.stat().st_size,
            deadline_seconds=30,
        )
        inventory = json.loads((out / "inventory.json").read_text())
        manifest = json.loads((out / "manifest.json").read_text())

        self.assertEqual(result["run_status"], "INCOMPLETE")
        self.assertIs(result["eof_reached"], False)
        self.assertEqual(inventory["scope"]["counts_scope"], "OBSERVED_PREFIX")
        self.assertIs(inventory["scope"]["counts_complete"], False)
        self.assertEqual(inventory["observed_feature_type_counts"]["gene"], 1)
        self.assertEqual(inventory["observed_feature_type_counts"]["CDS"], 1)
        self.assertEqual(inventory["observed_CDS_phase_counts"]["0"], 1)
        self.assertIn(manifest["execution"]["observed_error_type"], {"EOFError", "BadGzipFile"})
        self.assertIs(manifest["source"]["final_sha256_verified"], True)

    def test_deadline_after_one_row_preserves_prefix_and_never_marks_counts_complete(self):
        rows = [
            gtf_line("chr1", "gene", 1, 10, "+", ".", 'gene_id "g1";'),
            gtf_line("chr1", "transcript", 1, 10, "+", ".", 'gene_id "g1"; transcript_id "t1";'),
            gtf_line("chr1", "CDS", 2, 5, "+", "0", 'gene_id "g1"; transcript_id "t1";'),
        ]
        source = write_gtf(self.tmp_path / "reference.gtf", "".join(rows))
        ticks = iter(range(1000))
        out = self.tmp_path / "deadline-leaf"

        result = run_inventory(
            source,
            out,
            expected_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
            expected_size_bytes=source.stat().st_size,
            deadline_seconds=7,
            checkpoint_seconds=0,
            _monotonic=lambda: float(next(ticks)),
        )
        inventory = json.loads((out / "inventory.json").read_text())
        manifest = json.loads((out / "manifest.json").read_text())

        self.assertEqual(result["run_status"], "INCOMPLETE")
        self.assertIs(result["eof_reached"], False)
        self.assertIs(inventory["scope"]["counts_complete"], False)
        self.assertEqual(inventory["scope"]["counts_scope"], "OBSERVED_PREFIX")
        self.assertEqual(inventory["observed_counts"]["physical_lines"], 1)
        self.assertEqual(inventory["observed_feature_type_counts"], {"gene": 1})
        self.assertTrue(manifest["stop_reason"].startswith("DeadlineExpired:"))
        self.assertIsNone(manifest["source"]["final_sha256"])

    def test_cancellation_after_one_row_preserves_prefix(self):
        rows = [
            gtf_line("chr1", "gene", 1, 10, "+", ".", 'gene_id "g1";'),
            gtf_line("chr1", "transcript", 1, 10, "+", ".", 'gene_id "g1"; transcript_id "t1";'),
            gtf_line("chr1", "CDS", 2, 5, "+", "0", 'gene_id "g1"; transcript_id "t1";'),
        ]
        source = write_gtf(self.tmp_path / "reference.gtf", "".join(rows))

        class CancelAfterFiveChecks:
            def __init__(self):
                self.checks = 0

            def is_set(self):
                self.checks += 1
                return self.checks >= 5

        out = self.tmp_path / "cancelled-leaf"
        result = run_inventory(
            source,
            out,
            expected_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
            expected_size_bytes=source.stat().st_size,
            deadline_seconds=30,
            checkpoint_seconds=0,
            cancel_event=CancelAfterFiveChecks(),
        )
        inventory = json.loads((out / "inventory.json").read_text())
        manifest = json.loads((out / "manifest.json").read_text())

        self.assertEqual(result["run_status"], "INCOMPLETE")
        self.assertIs(result["eof_reached"], False)
        self.assertIs(inventory["scope"]["counts_complete"], False)
        self.assertEqual(inventory["observed_counts"]["physical_lines"], 1)
        self.assertEqual(inventory["observed_feature_type_counts"], {"gene": 1})
        self.assertTrue(manifest["stop_reason"].startswith("RunCancelled:"))

    def test_gencode_example_numeric_attributes_are_valid_source_declarations(self):
        # Independent projection of the chr19 examples in the official GENCODE
        # format page. Keep its actual coordinates, phases and numeric syntax;
        # unrelated optional attributes are omitted. Do not use the row helper.
        rows = (
            'chr19\tHAVANA\tgene\t405438\t409170\t.\t-\t.\t'
            'gene_id "ENSG00000183186.7"; gene_type "protein_coding"; '
            'gene_name "C2CD4C"; level 2;\n'
            'chr19\tHAVANA\ttranscript\t405438\t409170\t.\t-\t.\t'
            'gene_id "ENSG00000183186.7"; transcript_id "ENST00000332235.7"; '
            'gene_type "protein_coding"; transcript_type "protein_coding"; level 2;\n'
            'chr19\tHAVANA\texon\t409006\t409170\t.\t-\t.\t'
            'gene_id "ENSG00000183186.7"; transcript_id "ENST00000332235.7"; '
            'exon_number 1; exon_id "ENSE00001322986.5"; level 2;\n'
            'chr19\tHAVANA\tCDS\t407099\t408361\t.\t-\t0\t'
            'gene_id "ENSG00000183186.7"; transcript_id "ENST00000332235.7"; '
            'gene_type "protein_coding"; gene_name "C2CD4C"; '
            'transcript_type "protein_coding"; exon_number 2; level 2;\n'
        )
        result, inventory, manifest = run_fixture(self.tmp_path, rows, measure=True)
        self.assertEqual(result["run_status"], "COMPLETE")
        self.assertEqual(inventory["schema_version"], 2)
        self.assertEqual(manifest["schema_version"], 2)
        self.assertEqual(inventory["counts"].get("malformed_attribute_rows", 0), 0)
        self.assertEqual(
            inventory["feature_type_counts"],
            {"gene": 1, "transcript": 1, "exon": 1, "CDS": 1},
        )
        self.assertEqual(inventory["CDS"]["annotated_base_sum_over_feature_rows"], 1263)
        self.assertEqual(
            inventory["identifier_and_location_conflicts"]["issue_counts"], {}
        )
        self.assertFalse(inventory["scope"]["semantic_metadata_has_parse_or_id_issues"])
        self.assertTrue(inventory["protein_coding_gene_CDS_status"]["CDS_membership_complete"])
        probe = manifest["execution"]["existing_index_measurement"]
        self.assertEqual(probe["status"], "MEASURED")
        self.assertTrue(probe["selection_fingerprint_concordant"])
        # Check the exact legacy selection and known=True against a fixed tuple.
        selected = (
            "chr19", 407098, 408361, "ENSG00000183186.7", "C2CD4C",
            "ENST00000332235.7", True,
        )
        digest = hashlib.sha256(json.dumps(
            selected, ensure_ascii=True, separators=(",", ":")
        ).encode("utf-8")).hexdigest()
        self.assertEqual(probe["actual_index_selection"], {
            "row_count": 1,
            "sha256_tuple_digest_xor": digest,
            "sha256_tuple_digest_sum_mod_2_256": digest,
        })

    def test_typed_integer_attributes_accept_quoted_and_unquoted_forms(self):
        for text, expected in (
            ('level 1; exon_number 1;', {"level": ["1"], "exon_number": ["1"]}),
            ('level 2; exon_number 12;', {"level": ["2"], "exon_number": ["12"]}),
            ('level 3; exon_number 123;', {"level": ["3"], "exon_number": ["123"]}),
            ('level "2"; exon_number "1";', {"level": ["2"], "exon_number": ["1"]}),
        ):
            with self.subTest(text=text):
                attributes, problems = inventory_module.parse_attributes(text)
                self.assertEqual(attributes, expected)
                self.assertEqual(problems, [])

    def test_numeric_exceptions_do_not_hide_malformed_strings_or_other_keys(self):
        for text, expected_problem in (
            ('level "two";', 'level:invalid_numeric_attribute_value'),
            ('level two;', 'level:invalid_numeric_attribute_value'),
            ('level 4;', 'level:invalid_numeric_attribute_value'),
            ('level "4";', 'level:invalid_numeric_attribute_value'),
            ('level 2.0;', 'level:invalid_numeric_attribute_value'),
            ('exon_number 0;', 'exon_number:invalid_numeric_attribute_value'),
            ('exon_number -1;', 'exon_number:invalid_numeric_attribute_value'),
            ('exon_number "first";', 'exon_number:invalid_numeric_attribute_value'),
            ('level;', 'attribute_missing_key_or_value'),
            ('level "2;', 'level:unclosed_attribute_value'),
            ('level "2" extra;', 'level:trailing_attribute_text'),
            ('gene_id ENSG00000183186.7;', 'gene_id:unquoted_attribute_value'),
            ('gene_id 123;', 'gene_id:unquoted_attribute_value'),
            ('gene_name 2;', 'gene_name:unquoted_attribute_value'),
            ('transcript_support_level 2;', 'transcript_support_level:unquoted_attribute_value'),
            ('other_numeric 2;', 'other_numeric:unquoted_attribute_value'),
        ):
            with self.subTest(text=text):
                _attributes, problems = inventory_module.parse_attributes(text)
                self.assertIn(expected_problem, problems)

    def test_numeric_parsing_preserves_conflicting_keys_and_missing_id_guards(self):
        rows = (
            'chr1\ttest\texon\t1\t3\t.\t+\t.\t'
            'gene_id "g1"; gene_id "g2"; transcript_id "t1"; '
            'level 2; level 3; exon_number 1; exon_number "2";\n'
            'chr1\ttest\texon\t10\t12\t.\t+\t.\t'
            'gene_id unquoted; transcript_id "t2"; level 2; exon_number 1;\n'
            'chr1\ttest\texon\t20\t22\t.\t+\t.\t'
            'gene_id ""; level 2; exon_number 1;\n'
            'chr1\ttest\texon\t30\t32\t.\t+\t.\t'
            'gene_id "g3"; transcript_id "t3"; level "two"; exon_number 1;\n'
        )
        _, inventory, _ = run_fixture(self.tmp_path, rows)
        self.assertEqual(inventory["counts"]["malformed_attribute_rows"], 2)
        self.assertEqual(inventory["counts"]["valid_width_rows_missing_gene_id"], 1)
        self.assertEqual(inventory["counts"]["valid_width_rows_missing_transcript_id"], 1)
        conflicts = inventory["identifier_and_location_conflicts"]
        self.assertEqual(conflicts["duplicate_attribute_key_row_counts"], {
            "gene_id": 1, "level": 1, "exon_number": 1,
        })
        self.assertEqual(conflicts["conflicting_duplicate_attribute_value_row_counts"], {
            "gene_id": 1, "level": 1, "exon_number": 1,
        })
        self.assertEqual(conflicts["transcript_id_conflict_counts"], {"multiple_gene_ids": 1})
        self.assertEqual(conflicts["issue_counts"], {
            "conflicting_duplicate_attribute:gene_id": 1,
            "malformed_attribute:gene_id:unquoted_attribute_value": 1,
            "malformed_attribute:level:invalid_numeric_attribute_value": 1,
            "missing_gene_id": 1,
            "missing_transcript_id": 1,
        })

    def test_numeric_unknown_and_malformed_cds_phases_keep_separate_meanings(self):
        # Explicit spans and phase combinations give hand-counted expected
        # lengths and every possible nonempty transcript status combination.
        rows = []
        for transcript, blocks in (
            ("numeric", [(1, 3, "0"), (10, 13, "1"), (20, 24, "2")]),
            ("unknown", [(30, 35, ".")]),
            ("bad", [(40, 46, "nonsense")]),
            ("numeric_unknown", [(50, 50, "0"), (60, 61, ".")]),
            ("numeric_bad", [(70, 72, "1"), (80, 83, "x")]),
            ("unknown_bad", [(90, 94, "."), (100, 105, "2.5")]),
            ("all_three", [(110, 116, "2"), (120, 127, "."), (130, 138, "3")]),
        ):
            for start, end, phase in blocks:
                rows.append(gtf_line("chr1", "CDS", start, end, "+", phase,
                                     f'gene_id "g"; transcript_id "{transcript}"; '
                                     'gene_type "protein_coding";'))
        _, inventory, manifest = run_fixture(self.tmp_path, "".join(rows), measure=True)
        cds = inventory["CDS"]
        self.assertEqual(cds["feature_rows"], 14)
        self.assertEqual(cds["phase_counts"], {
            "0": 2, "1": 2, "2": 2, "unknown": 4, "malformed": 4,
        })
        self.assertEqual(cds["annotated_bases_by_phase"], {
            "0": 4, "1": 7, "2": 12, "unknown": 21, "malformed": 26,
        })
        self.assertEqual(cds["annotated_base_sum_over_feature_rows"], 70)
        self.assertEqual(cds["malformed_phase_value_counts"], {
            "nonsense": 1, "x": 1, "2.5": 1, "3": 1,
        })
        self.assertEqual(cds["transcript_phase_annotation_status_counts"], {
            "ALL_NUMERIC": 1, "ALL_UNKNOWN": 1, "ALL_MALFORMED": 1,
            "MIXED_NUMERIC_AND_UNKNOWN": 1, "MIXED_NUMERIC_AND_MALFORMED": 1,
            "MIXED_UNKNOWN_AND_MALFORMED": 1,
            "MIXED_NUMERIC_AND_UNKNOWN_AND_MALFORMED": 1,
        })
        self.assertEqual(cds["transcript_annotated_length_mod_3_counts"], {
            "0": 4, "1": 2, "2": 1,
        })
        issues = inventory["identifier_and_location_conflicts"]["issue_counts"]
        self.assertEqual(issues, {"malformed_CDS_phase": 4})
        probe = manifest["execution"]["existing_index_measurement"]
        self.assertEqual(probe["actual_index_selection"]["row_count"], 14)
        self.assertTrue(probe["selection_fingerprint_concordant"])

    def test_non_eof_prefix_retains_unknown_and_malformed_phases_and_statuses(self):
        source = self.tmp_path / "phase-prefix.gtf.gz"
        with gzip.open(source, "wt", encoding="utf-8") as stream:
            stream.write(
                'chr1\ttest\tCDS\t1\t3\t.\t+\t0\tgene_id "g"; transcript_id "t"; level 2;\n'
                'chr1\ttest\tCDS\t10\t13\t.\t+\t.\tgene_id "g"; transcript_id "t"; exon_number 1;\n'
                'chr1\ttest\tCDS\t20\t24\t.\t+\tbad\tgene_id "g"; transcript_id "t";\n'
            )
        source.write_bytes(source.read_bytes()[:-8])
        out = self.tmp_path / "phase-prefix-leaf"
        result = run_inventory(
            source, out, expected_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
            expected_size_bytes=source.stat().st_size, deadline_seconds=30,
        )
        inventory = json.loads((out / "inventory.json").read_text())
        self.assertEqual(result["run_status"], "INCOMPLETE")
        self.assertFalse(result["eof_reached"])
        self.assertEqual(inventory["schema_version"], 2)
        self.assertEqual(inventory["scope"]["counts_scope"], "OBSERVED_PREFIX")
        self.assertFalse(inventory["scope"]["counts_complete"])
        self.assertEqual(inventory["observed_counts"].get("malformed_attribute_rows", 0), 0)
        self.assertEqual(inventory["observed_CDS_phase_counts"], {
            "0": 1, "1": 0, "2": 0, "unknown": 1, "malformed": 1,
        })
        self.assertEqual(inventory["observed_CDS_bases_by_phase"], {
            "0": 3, "unknown": 4, "malformed": 5,
        })
        self.assertEqual(inventory["observed_CDS_phase_malformed_value_counts"], {"bad": 1})
        self.assertEqual(inventory["observed_CDS_transcript_phase_annotation_status_counts"], {
            "MIXED_NUMERIC_AND_UNKNOWN_AND_MALFORMED": 1,
        })
        self.assertEqual(inventory["observed_issue_counts"], {"malformed_CDS_phase": 1})
        self.assertNotIn("available_full_EOF_summary", inventory)

    def test_deadline_prefix_with_dot_phase_is_unknown_without_frame_or_eof(self):
        source = write_gtf(self.tmp_path / "reference.gtf", (
            'chr1\ttest\tCDS\t1\t3\t.\t+\t.\tgene_id "g"; transcript_id "t"; level 2;\n'
            'chr1\ttest\tCDS\t10\t12\t.\t+\tbad\tgene_id "g"; transcript_id "t";\n'
        ))
        ticks = iter(range(1000))
        out = self.tmp_path / "unknown-deadline"
        result = run_inventory(
            source, out, expected_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
            expected_size_bytes=source.stat().st_size, deadline_seconds=7,
            checkpoint_seconds=0, _monotonic=lambda: float(next(ticks)),
        )
        inventory = json.loads((out / "inventory.json").read_text())
        manifest = json.loads((out / "manifest.json").read_text())
        self.assertEqual(result["run_status"], "INCOMPLETE")
        self.assertFalse(result["eof_reached"])
        self.assertEqual(inventory["observed_counts"]["physical_lines"], 1)
        self.assertEqual(inventory["observed_CDS_phase_counts"], {
            "0": 0, "1": 0, "2": 0, "unknown": 1, "malformed": 0,
        })
        self.assertEqual(inventory["observed_CDS_bases_by_phase"], {"unknown": 3})
        self.assertEqual(inventory["observed_CDS_phase_malformed_value_counts"], {})
        self.assertEqual(inventory["observed_CDS_transcript_phase_annotation_status_counts"], {
            "ALL_UNKNOWN": 1,
        })
        self.assertFalse(inventory["scope"]["counts_complete"])
        self.assertEqual(inventory["scope"]["counts_scope"], "OBSERVED_PREFIX")
        self.assertTrue(manifest["stop_reason"].startswith("DeadlineExpired:"))
        self.assertIsNone(manifest["source"]["final_sha256"])

    def test_initial_digest_or_size_mismatch_never_scans_source(self):
        source = write_gtf(self.tmp_path / "reference.gtf", gtf_line(
            "chr1", "gene", 1, 10, "+", ".", 'gene_id "g1";'
        ))
        actual_sha = hashlib.sha256(source.read_bytes()).hexdigest()
        for label, digest, size in (
            ("digest", "0" * 64, source.stat().st_size),
            ("size", actual_sha, source.stat().st_size + 1),
        ):
            with self.subTest(label=label):
                out = self.tmp_path / label
                result = run_inventory(source, out, expected_sha256=digest,
                                       expected_size_bytes=size)
                self.assertEqual(result["run_status"], "INCOMPLETE")
                self.assertFalse(result["eof_reached"])
                manifest = json.loads((out / "manifest.json").read_text())
                self.assertFalse(manifest["source"]["initial_sha256_verified"])
                self.assertEqual(manifest["execution"]["last_line_number"], 0)

    def test_source_change_after_eof_cannot_publish_complete_run(self):
        source = write_gtf(self.tmp_path / "reference.gtf", gtf_line(
            "chr1", "gene", 1, 10, "+", ".", 'gene_id "g1";'
        ))
        actual_sha = hashlib.sha256(source.read_bytes()).hexdigest()
        initial_size = source.stat().st_size
        hash_calls = 0
        original_hash = inventory_module._hash_file

        def changed_final_hash(path, control):
            nonlocal hash_calls
            hash_calls += 1
            if hash_calls == 2:
                source.write_text(source.read_text() + "# changed after EOF\n")
            return original_hash(path, control)

        out = self.tmp_path / "changed-source"
        with patch.object(inventory_module, "_hash_file", changed_final_hash):
            result = run_inventory(source, out, expected_sha256=actual_sha,
                                   expected_size_bytes=initial_size)
        self.assertEqual(result["run_status"], "INCOMPLETE")
        self.assertTrue(result["eof_reached"])
        manifest = json.loads((out / "manifest.json").read_text())
        self.assertFalse(manifest["source"]["final_sha256_verified"])
        self.assertEqual(manifest["source"]["stable_file_check"], "FAIL")
        inventory = json.loads((out / "inventory.json").read_text())
        self.assertEqual(inventory["scope"]["status"], "INCOMPLETE")
        self.assertFalse(inventory["scope"]["source_sha256_verified"])

    def test_failed_index_probe_is_distinct_from_complete_inventory(self):
        row = gtf_line("chr1", "CDS", 10, 20, "+", "0",
                       'gene_id "g1"; transcript_id "t1"; gene_type "protein_coding";')
        with patch.object(inventory_module, "_run_index_probe",
                          return_value={"status": "FAILED", "error": "synthetic failure"}):
            result, inventory, manifest = run_fixture(self.tmp_path, row, measure=True)
        self.assertEqual(result["run_status"], "COMPLETE")
        self.assertTrue(inventory["scope"]["source_sha256_verified"])
        probe = manifest["execution"]["existing_index_measurement"]
        self.assertEqual(probe["status"], "FAILED")
        self.assertNotIn("selection_fingerprint_concordant", probe)


if __name__ == "__main__":
    unittest.main()
