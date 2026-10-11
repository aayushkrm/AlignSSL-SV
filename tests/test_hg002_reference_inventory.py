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
            {"0": 0, "1": 1, "2": 1, "malformed": 1},
        )
        self.assertEqual(inventory["CDS"]["malformed_phase_value_counts"], {"dot": 1})
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
