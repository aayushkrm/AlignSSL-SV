"""Small synthetic controls, not genomic or intervention evidence."""

import importlib.util
import io
import math
from pathlib import Path
import unittest
import warnings
import zipfile


SPEC = importlib.util.spec_from_file_location(
    "sven_audit", Path(__file__).parents[1] / "analysis/sven_source_table_audit.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class RankControls(unittest.TestCase):
    def test_ties_are_average_ranks(self):
        self.assertEqual(MODULE.average_ranks([3, 1, 1, 2]), [4, 1.5, 1.5, 3])

    def test_monotone_and_reverse(self):
        self.assertEqual(MODULE.spearman_correlation([1, 2, 2, 3], [4, 5, 5, 8]), 1)
        self.assertEqual(MODULE.spearman_correlation([1, 2, 2, 3], [8, 5, 5, 4]), -1)

    def test_partly_tied_known_value(self):
        self.assertTrue(math.isclose(
            MODULE.spearman_correlation([1, 2, 3], [1, 1, 2]), math.sqrt(3) / 2
        ))

    def test_zero_correlation(self):
        self.assertEqual(MODULE.spearman_correlation([1, 2, 3], [1, 3, 1]), 0)

    def test_invalid_vector_lengths_and_constant(self):
        for x, y in (([1], [2]), ([1, 2], [1]), ([1, 1], [1, 2])):
            with self.subTest(x=x, y=y), self.assertRaises(ValueError):
                MODULE.spearman_correlation(x, y)

    def test_member_cap_and_missing(self):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w") as archive:
            archive.writestr("known", b"abc")
        with zipfile.ZipFile(io.BytesIO(stream.getvalue())) as archive:
            self.assertEqual(MODULE.unique_member(archive, "known", 3), b"abc")
            with self.assertRaises(ValueError):
                MODULE.unique_member(archive, "known", 2)
            with self.assertRaises(ValueError):
                MODULE.unique_member(archive, "absent", 3)

    def test_duplicate_member_is_rejected(self):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w") as archive, warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            archive.writestr("same", b"abc")
            archive.writestr("same", b"abc")
        with zipfile.ZipFile(io.BytesIO(stream.getvalue())) as archive:
            with self.assertRaises(ValueError):
                MODULE.unique_member(archive, "same", 3)

    def test_source_pair_contract(self):
        class Sheet:
            title = "synthetic"
            max_column = 2

            def __init__(self, rows):
                self.rows = rows

            def iter_rows(self, **kwargs):
                return iter(self.rows)

        header = ("True value", "Predicted Value")
        result = MODULE.absolute_expression_summary(
            Sheet([header, (1, 2), (3, 4)]), expected_rows=2
        )
        self.assertEqual(result["data_rows"], 2)
        self.assertEqual(result["causal_effect_accuracy"],
                         "NOT_IDENTIFIABLE_FROM_THIS_SHEET")
        for row in ((None, 2), (True, 2), (math.nan, 2), (math.inf, 2), ("=1+1", 2)):
            with self.subTest(row=row), self.assertRaises(ValueError):
                MODULE.absolute_expression_summary(Sheet([header, row]), expected_rows=1)
        with self.assertRaises(ValueError):
            MODULE.absolute_expression_summary(Sheet([("other", "header"), (1, 2)]), 1)
        with self.assertRaises(ValueError):
            MODULE.absolute_expression_summary(Sheet([header, (1, 2), (3, 4)]), 3)


if __name__ == "__main__":
    unittest.main()
