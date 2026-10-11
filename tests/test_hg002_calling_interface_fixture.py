"""Standard-library tests; synthetic text and fake BAM interfaces only."""
import copy
import json
from pathlib import Path
import sys
import subprocess
import tempfile
import types
import unittest
from unittest.mock import patch

from scripts import make_hg002_calling_interface_fixture as fixture
from analysis.hg002_cds_overlap_cohort import build_manifest


class FixtureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="hg002-synthetic-caller-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.inputs = self.root / "inputs"
        self.truth = fixture.make_fixture(self.inputs)

    def write_calls(self, change=None):
        refs = fixture.fasta(self.inputs / "reference.fa")
        header = ('##fileformat=VCFv4.2\n##INFO=<ID=SVLEN,Number=1,Type=Integer,Description="Size">\n'
                  '#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\t' + fixture.SAMPLE + '\n')
        records = []
        for e in self.truth["events"]:
            anchor = e["start0"] - 1; ref = refs[e["chrom"]][anchor:e["end0"]]
            if e["svtype"] == "DEL": alt = ref[0]; delta = -e["size_bp"]
            else: alt = ref + e["inserted_sequence"]; delta = e["size_bp"]
            records.append([e["chrom"], str(anchor+1), e["event_id"], ref, alt, ".", "PASS",
                            f"SVTYPE={e['svtype']};END={e['end0']};SVLEN={delta}", "GT", "0/1"])
        if change: change(records)
        vcf = self.root / "calls.vcf"; vcf.write_text(header + "".join("\t".join(r)+"\n" for r in records))
        counts = {}; rows = build_manifest(vcf, self.inputs / "cds.gtf", fixture.SAMPLE, counts)
        cohort = self.root / "cohort.jsonl"
        cohort.write_text("".join(json.dumps(x)+"\n" for x in [dict(final_D=None, counters=counts, sample=fixture.SAMPLE), *rows]))
        return vcf, cohort

    def comparison(self, change=None):
        vcf, cohort = self.write_calls(change)
        return fixture.compare(self.inputs, vcf, cohort, self.root / "comparison.json")

    def test_three_independent_full_references_and_fai(self):
        refs = fixture.fasta(self.inputs / "reference.fa")
        self.assertEqual({k: len(v) for k, v in refs.items()}, {k: 30000 for k in self.truth["contigs"]})
        kmers = [set(seq[i:i+31] for i in range(len(seq)-30)) for seq in refs.values()]
        self.assertTrue(all(len(k) == 29970 for k in kmers))
        self.assertTrue(kmers[0].isdisjoint(kmers[1]) and kmers[1].isdisjoint(kmers[2]) and kmers[0].isdisjoint(kmers[2]))
        raw = (self.inputs / "reference.fa").read_bytes()
        for line in (self.inputs / "reference.fa.fai").read_text().splitlines():
            name, length, offset, bases, width = line.split("\t")
            self.assertEqual(raw[int(offset):int(offset)+int(bases)].decode(), refs[name][:60])
            self.assertEqual((int(length), int(bases), int(width)), (30000, 60, 61))

    def test_fixed_whole_alleles_and_event_positions(self):
        refs = fixture.fasta(self.inputs / "reference.fa"); alleles = fixture.fasta(self.inputs / "alleles.fa")
        for e in self.truth["events"]:
            self.assertEqual(e["start0"], 15000)
            expected = refs[e["chrom"]][:15000] + e["inserted_sequence"] + refs[e["chrom"]][e["end0"]:]
            self.assertEqual(alleles[e["chrom"] + "|ALT"], expected)
            self.assertEqual(fixture.sha(expected.encode()), e["alternate_sha256"])
        self.assertEqual([(e["svtype"], e["size_bp"]) for e in self.truth["events"]], [("DEL", 120), ("INS", 150)])
        self.assertEqual([e["alternate_sha256"] for e in self.truth["events"]], [
            "00b76ee181a48f9e4db48c14b00d5c0993d687606e06c5d2f9cdd5ed4d5b4d03",
            "aad9c395e8fee03aadd9cda17bc6e48990e23845297789721da9c84d395688b8"])

    def test_all_sixty_read_ids_quality_strands_sample_and_support(self):
        lines = (self.inputs / "reads.fastq").read_text().splitlines()
        self.assertEqual(len(lines), 240)
        alleles = fixture.fasta(self.inputs / "alleles.fa"); balance = {}
        self.assertEqual(len({r["qname"] for r in self.truth["reads"]}), 60)
        for i, read in enumerate(self.truth["reads"]):
            name, sequence, plus, quality = lines[4*i:4*i+4]
            self.assertEqual(name, "@" + read["qname"]); self.assertEqual(plus, "+")
            forward = alleles[read["chrom"] + "|" + read["allele"]]
            self.assertEqual(sequence, forward if read["strand"] == "+" else fixture.rc(forward))
            self.assertEqual(quality, "I" * len(sequence))
            self.assertEqual(fixture.sha(sequence.encode()), read["sequence_sha256"])
            self.assertEqual((read["sample"], read["rg"]), (fixture.SAMPLE, fixture.RG))
            key = read["chrom"], read["allele"], read["strand"]
            balance[key] = balance.get(key, 0) + 1
        self.assertEqual(len(balance), 10)
        self.assertTrue(all(n == (10 if k[0] == "toy_ref_v1" else 5) for k, n in balance.items()))

    def test_deterministic_complete_manifests(self):
        second = self.root / "second"; fixture.make_fixture(second)
        for path in self.inputs.iterdir(): self.assertEqual(path.read_bytes(), (second/path.name).read_bytes())
        fixture.verify_inputs(self.inputs)
        self.assertLess(fixture.guard(self.root), 8 * 1024 * 1024)
        self.assertEqual(fixture.sha((self.inputs/"reads.fastq").read_bytes()),
                         "0a612a9d9799b8efa49607484d0a3308b4ec9022163b7c35f8fd7b3ba7e7f6f5")

    def test_existing_empty_leaf_refused(self):
        out = self.root / "existing"; out.mkdir()
        with self.assertRaises(FileExistsError): fixture.make_fixture(out)
        self.assertEqual(list(out.iterdir()), [])

    def test_dangling_symlink_refused(self):
        out = self.root / "dangling"; out.symlink_to(self.root / "absent")
        with self.assertRaises(FileExistsError): fixture.make_fixture(out)

    def test_fixture_mutation_refused(self):
        (self.inputs / "truth.json").write_text("{}")
        with self.assertRaisesRegex(ValueError, "mutated"): fixture.verify_inputs(self.inputs)

    def test_small_guard_and_symlink_refused(self):
        with patch.object(fixture, "MAX_BYTES", 20):
            with self.assertRaisesRegex(ValueError, "exceeds"): fixture.make_fixture(self.root / "oversized")
        self.assertFalse((self.root / "oversized").exists())
        (self.inputs / "alias").symlink_to(self.inputs / "truth.json")
        with self.assertRaisesRegex(ValueError, "symlink"): fixture.guard(self.inputs)

    def test_literal_truth_and_unchanged_cohort_phase_unknown(self):
        report = self.comparison(); self.assertTrue(report["complete"], report)
        self.assertEqual(len(report["cohort_rows"]), 2)
        self.assertTrue(all(len(row["transcripts"]) == 2 and row["p1_state"] == "NOT_ASSESSED" for row in report["cohort_rows"]))
        self.assertEqual(report["cohort_summary"]["counters"]["OVERLAPS_CDS"], 2)

    def test_exact_symbolic_deletion_allowed(self):
        def change(rows): rows[0][3] = rows[0][3][0]; rows[0][4] = "<DEL>"
        report = self.comparison(change)
        self.assertTrue(report["complete"], report)
        self.assertIn("symbolic_allele_sequence_unavailable", report["cohort_rows"][0]["unknown_reasons"])

    def test_exact_suffix_anchor_representations_allowed(self):
        def change(rows):
            refs = fixture.fasta(self.inputs / "reference.fa")
            e = self.truth["events"][0]; right = refs[e["chrom"]][e["end0"]]
            rows[0][1] = str(e["start0"] + 1)
            rows[0][3:5] = [refs[e["chrom"]][e["start0"]:e["end0"]] + right, right]
            e = self.truth["events"][1]; right = refs[e["chrom"]][e["start0"]]
            rows[1][1] = str(e["start0"] + 1); rows[1][3:5] = [right, e["inserted_sequence"] + right]
        report = self.comparison(change); self.assertTrue(report["complete"], report)

    def test_missing_and_extra_preserved(self):
        def change(rows):
            rows.pop(0)
            extra = rows[0].copy(); extra[0] = "toy_ref_v1"; extra[2] = "EXTRA"
            extra[3] = fixture.fasta(self.inputs/"reference.fa")[extra[0]][14999]
            extra[4] = extra[3] + "A"*150; rows.append(extra)
        report = self.comparison(change)
        self.assertFalse(report["complete"]); self.assertEqual(report["missing"], ["TOY_DEL.1"])
        self.assertEqual(report["extra_observation_indices"], [1]); self.assertEqual(len(report["observed"]), 2)

    def test_duplicates_preserved(self):
        report = self.comparison(lambda rows: rows.append(rows[0].copy()))
        self.assertEqual(report["duplicate_truth"], ["TOY_DEL.1"]); self.assertFalse(report["complete"])
        self.assertEqual(report["cohort_summary"]["counters"]["input_records"], 3)

    def test_filter_and_genotype_not_tuned(self):
        for field, value, reason in ((6, "NearContigEnd", "FILTER_not_PASS"), (9, "1/1", "not_unphased_heterozygote")):
            with self.subTest(value=value):
                for name in ("calls.vcf", "cohort.jsonl", "comparison.json"):
                    (self.root/name).unlink(missing_ok=True)
                report = self.comparison(lambda rows: rows[0].__setitem__(field, value))
                self.assertFalse(report["complete"]); self.assertIn(reason, report["observed"][0]["reasons"])

    def test_symbolic_insertion_is_unresolved_not_success(self):
        report = self.comparison(lambda rows: rows[1].__setitem__(4, "<INS>"))
        self.assertFalse(report["complete"]); self.assertEqual(report["missing"], ["TOY_INS.1"])
        self.assertIn("sequence_unresolved_or_other_type", report["observed"][1]["reasons"])

    def test_ref_mismatch_and_wrong_size_retained(self):
        report = self.comparison(lambda rows: rows[0].__setitem__(3, "N" + rows[0][3][1:]))
        self.assertFalse(report["complete"]); self.assertIn("REF_mismatch", report["observed"][0]["reasons"])

    def test_wrong_insert_sequence_and_size_not_matched(self):
        for case in ("sequence", "size"):
            with self.subTest(case=case):
                for name in ("calls.vcf", "cohort.jsonl", "comparison.json"):
                    (self.root/name).unlink(missing_ok=True)
                def change(rows):
                    if case == "sequence":
                        rows[1][4] = rows[1][4][:-1] + ("A" if rows[1][4][-1] != "A" else "C")
                    else: rows[1][7] = rows[1][7].replace("SVLEN=150", "SVLEN=151")
                report = self.comparison(change); self.assertFalse(report["complete"])
                self.assertIn("TOY_INS.1", report["missing"])

    def test_reference_GT_is_accounted_not_called_truth(self):
        report = self.comparison(lambda rows: rows[0].__setitem__(9, "0/0"))
        self.assertEqual(report["missing"], ["TOY_DEL.1"])
        self.assertEqual(report["cohort_summary"]["counters"]["out_of_primary_uncalled_ALT"], 1)
        self.assertFalse(report["complete"])

    def test_fake_phase_rejected(self):
        def change(rows): rows[0][8:10] = ["GT:PS", "0|1:15000"]
        report = self.comparison(change); self.assertFalse(report["complete"])
        self.assertIn("unexpected_phase_tag", report["observed"][0]["reasons"])

    def test_cohort_provenance_and_geometry_mutations_refused(self):
        for case in ("empty_sources", "coordinates", "swapped_sources", "wrong_sample",
                     "source_line", "source_ref", "source_filter", "source_gt", "source_alt_index",
                     "alternate", "event_key"):
            with self.subTest(case=case):
                for name in ("calls.vcf", "cohort.jsonl", "comparison.json"):
                    (self.root/name).unlink(missing_ok=True)
                vcf, cohort = self.write_calls()
                rows = [json.loads(line) for line in cohort.read_text().splitlines()]
                if case == "empty_sources":
                    for row in rows[1:]: row["source_records"] = []
                elif case == "coordinates":
                    for row in rows[1:]: row.update(start0=0, end0=1)
                elif case == "swapped_sources":
                    rows[1]["source_records"], rows[2]["source_records"] = rows[2]["source_records"], rows[1]["source_records"]
                elif case == "wrong_sample":
                    for row in rows: row["sample"] = "WRONG_SAMPLE"
                elif case.startswith("source_"):
                    key, value = {"source_line": ("line", 999), "source_ref": ("REF", "N"),
                        "source_filter": ("FILTER", "bad"), "source_gt": ("GT", "1/1"),
                        "source_alt_index": ("alt_index", 2)}[case]
                    rows[1]["source_records"][0][key] = value
                else: rows[1][case] = "WRONG"
                cohort.write_text("".join(json.dumps(row)+"\n" for row in rows))
                report = fixture.compare(self.inputs, vcf, cohort, self.root/"comparison.json")
                self.assertFalse(report["complete"], case)
                self.assertTrue(report["errors"], case)

    def test_conflicting_duplicate_format_gt_rejected_before_interpretation(self):
        def change(rows): rows[0][8:10] = ["GT:GT", "1/1:0/1"]
        report = self.comparison(change)
        self.assertFalse(report["complete"])
        self.assertIn("duplicate_FORMAT_key", report["observed"][0]["reasons"])
        self.assertEqual(report["observed"][0]["FORMAT"], {})

    def test_format_cardinality_mismatch_rejected(self):
        def change(rows): rows[0][8:10] = ["GT:DP", "0/1"]
        report = self.comparison(change)
        self.assertFalse(report["complete"])
        self.assertIn("FORMAT_cardinality_mismatch", report["observed"][0]["reasons"])

    def test_native_ids_need_not_equal_truth_ids(self):
        def change(rows):
            rows[0][2] = "pbsv.DEL.native-id"
            rows[1][2] = "pbsv.INS.native-id"
        report = self.comparison(change)
        self.assertTrue(report["complete"], report)

    def test_comparison_output_existing_refused(self):
        vcf, cohort = self.write_calls(); out = self.root / "result.json"; out.write_text("keep")
        with self.assertRaises(FileExistsError): fixture.compare(self.inputs, vcf, cohort, out)
        self.assertEqual(out.read_text(), "keep")

    def test_existing_source_receipts_pinned(self):
        out = self.root / "with-source"
        fixture.make_fixture(out, Path(__file__).resolve().parents[1])
        fixture.verify_inputs(out)
        self.assertEqual(fixture.sha((out / "sources/analysis/hg002_cds_overlap_cohort.py").read_bytes()), fixture.COHORT_SHA)
        self.assertEqual(len(list((out / "sources/receipts").iterdir())), 5)

    def test_mock_bam_all_source_identity_orientation_quality_and_RG(self):
        lines = (self.inputs / "reads.fastq").read_text().splitlines(); records = []
        for i, wanted in enumerate(self.truth["reads"]):
            sequence = lines[4*i+1]
            records.append(types.SimpleNamespace(query_name=wanted["qname"], is_secondary=False,
                is_supplementary=False, is_unmapped=False, reference_name=wanted["chrom"],
                is_reverse=wanted["strand"] == "-", get_forward_sequence=lambda s=sequence: s,
                get_forward_qualities=lambda s=sequence: [40]*len(s),
                has_tag=lambda tag: tag == "RG", get_tag=lambda tag: fixture.RG))
        class MockBam:
            references = tuple(self.truth["contigs"])
            lengths = (30000,)*3
            header = types.SimpleNamespace(to_dict=lambda: {"RG": [{"ID": fixture.RG, "SM": fixture.SAMPLE}]})
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def fetch(self, **kwargs): return iter(records)
            def has_index(self): return True
            def check_index(self): return True
        module = types.SimpleNamespace(AlignmentFile=lambda *a: MockBam(), __version__="MOCK_ONLY")
        with patch.dict(sys.modules, {"pysam": module}):
            report = fixture.audit_bam(self.inputs, "no-real-bam", self.root/"bam-good.json")
            self.assertTrue(report["complete"], report); self.assertEqual(report["primary_identities"], 60)
            records[0].is_reverse = True; records.append(copy.copy(records[0])); records.pop(1)
            report = fixture.audit_bam(self.inputs, "no-real-bam", self.root/"bam-bad.json")
            self.assertFalse(report["complete"]); self.assertTrue(report["missing"] and report["duplicated"])

    def test_step_logs_exit_and_no_retry(self):
        self.assertEqual(fixture.step(self.root, "mock-command", 2, [sys.executable, "-B", "-c", 'print("once"); raise SystemExit(7)']), 7)
        self.assertEqual((self.root/"mock-command.log").read_text(), "once\n")
        self.assertEqual(json.loads((self.root/"mock-command.exit.json").read_text())["exit_code"], 7)
        with self.assertRaises(FileExistsError): fixture.step(self.root, "mock-command", 2, [sys.executable, "-B", "-c", "pass"])

    def test_step_timeout_and_failure_manifest(self):
        self.assertNotEqual(fixture.step(self.root, "timeout", 0.01, [sys.executable, "-B", "-c", "while True: pass"]), 0)
        self.assertEqual(json.loads((self.root/"timeout.exit.json").read_text())["stopped"], "timeout")
        fixture.finalize(self.root, 2)
        status = json.loads((self.root/"status.json").read_text()); self.assertEqual(status["state"], "INCOMPLETE")
        manifest = json.loads((self.root/"artifact-manifest.json").read_text())
        self.assertIn("timeout.exit.json", manifest["files"])
        self.assertNotIn("artifact-manifest.json", manifest["files"])
        for name, entry in manifest["files"].items():
            self.assertEqual(fixture.sha((self.root/name).read_bytes()), entry["sha256"])

    def test_step_launch_failure_and_invalid_limits(self):
        self.assertEqual(fixture.step(self.root, "absent", 1, [str(self.root/"no-executable")]), 127)
        self.assertEqual(json.loads((self.root/"absent.exit.json").read_text())["stopped"], "launch_failure")
        for label, seconds in (("../escape", 1), ("negative", -1), ("long", 121)):
            with self.subTest(label=label), self.assertRaises(ValueError):
                fixture.step(self.root, label, seconds, [sys.executable, "-B", "-c", "pass"])

    def test_transient_test_symlinks_counted_without_following(self):
        temp = self.root/"test-tmp"; temp.mkdir()
        alias = temp/"dangling"; alias.symlink_to(temp/"absent")
        with self.assertRaises(ValueError): fixture.guard(self.root)
        self.assertLess(fixture.guard(self.root, transient_test_links=True), fixture.MAX_BYTES)
        alias.unlink(); alias.symlink_to(self.root/"inputs/reference.fa")
        with self.assertRaises(ValueError): fixture.guard(self.root, transient_test_links=True)

    def test_success_cannot_be_finalized_without_native_reports(self):
        with self.assertRaises(FileNotFoundError): fixture.finalize(self.root, 0)
        self.assertFalse((self.root/"status.json").exists())

    def test_runner_syntax_contract_and_preallocation_refusals(self):
        runner = Path(__file__).resolve().parents[1]/"scripts/run_hg002_calling_interface_fixture.sh"
        self.assertEqual(subprocess.run(["bash", "-n", str(runner)], capture_output=True).returncode, 0)
        text = runner.read_text()
        for token in ("#SBATCH --cpus-per-task=3", "#SBATCH --mem=4G", "#SBATCH --time=00:05:00",
                      "-j 1 -J 1 -m 256M", "discover --hifi", "call --hifi -j 1",
                      "MinMemoryNode=(4G|4096M)", "hg2_other + 67108864 <= 8589934592"):
            self.assertIn(token, text)
        for args in ([], ["/unresolved", "/unresolved", "899", "0", "a"*64],
                     ["/unresolved", "/unresolved", "900", "8589934592", "a"*64]):
            with self.subTest(args=args):
                self.assertNotEqual(subprocess.run(["bash", str(runner), *args], capture_output=True).returncode, 0)


if __name__ == "__main__":
    unittest.main()
