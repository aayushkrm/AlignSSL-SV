"""Finite source-contract checks; no allele-effect or biological controls."""

import importlib.util
import math
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location(
    "prime_inventory", Path(__file__).parents[1] / "analysis/prime_deletion_table_inventory.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
HEADER = ["oligo_id_short", "gene_name", "gene_group_label", "L2FC", "dropout",
          "enriched", "positive_control_gene", "HAP1_exonic", "freq_BFP"]


def table(rows, header=HEADER):
    return "\n".join("\t".join(row) for row in [header] + rows) + "\n"


def row(name="id1", label="-2", dropout="TRUE"):
    return [name, "gene", "group", label, dropout, "FALSE", "TRUE", "TRUE", "0.1"]


class SourceContracts(unittest.TestCase):
    def test_known_and_unknown_are_separate(self):
        unknown = row("id2", "NA", "NA")
        unknown[5:8] = ["NA", "NA", "NA"]
        result = MODULE.summarize(table([row(), unknown]))
        self.assertEqual(result["records"], 2)
        self.assertEqual(result["numeric_L2FC_records"], 1)
        self.assertEqual(result["missing_L2FC_records"], 1)
        self.assertEqual(result["L2FC_lt_minus_one"], 1)
        self.assertEqual(result["positive_control_exonic_records"], 1)
        self.assertEqual(result["missing_flag_values"]["dropout"], 1)

    def test_exact_threshold_and_disagreement(self):
        result = MODULE.summarize(table([row(label="-1", dropout="TRUE")]))
        self.assertEqual(result["L2FC_lt_minus_one"], 0)
        self.assertEqual(result["dropout_flag_disagreements_known_rows"], 1)

    def test_duplicate_identity_ragged_and_missing_fields_rejected(self):
        cases = [table([row(), row()]), table([row()[:-1]]), table([row()], HEADER[:-1])]
        for case in cases:
            with self.subTest(case=case), self.assertRaises(ValueError):
                MODULE.summarize(case)

    def test_duplicate_headers_only_when_all_cells_equal(self):
        header = HEADER + ["gene_name"]
        result = MODULE.summarize(table([row() + ["gene"]], header))
        self.assertEqual(result["duplicate_header_positions_zero_based"], {"gene_name": [1, 9]})
        with self.assertRaises(ValueError):
            MODULE.summarize(table([row() + ["other"]], header))

    def test_nonfinite_and_bad_flags_rejected(self):
        for value in ("nan", "inf", "-inf", "text"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                MODULE.number(value)
        with self.assertRaises(ValueError):
            MODULE.summarize(table([row(dropout="yes")]))
        self.assertIsNone(MODULE.number("NA"))
        self.assertIsNone(MODULE.number(""))
        self.assertEqual(MODULE.number("0"), 0)

    def test_empty_source_rejected(self):
        for source in ("", "\t".join(HEADER)):
            with self.subTest(source=source), self.assertRaises(ValueError):
                MODULE.summarize(source)


if __name__ == "__main__":
    unittest.main()
