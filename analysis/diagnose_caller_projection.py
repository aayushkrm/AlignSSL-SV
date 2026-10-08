"""Read-only, biallelic field diagnosis of a stopped caller preparation.

No preparation, norm, sort, scoring, repair or genomic output. Source bytes
must match the original pin. Previously unhashed partial files are observations,
not retrospectively authenticated launch outputs. External limits required.
"""
from __future__ import annotations

import argparse
from collections import Counter
from itertools import zip_longest
import json
from pathlib import Path
import sys
from urllib.parse import quote

try:
    from . import prepare_released_callers as prep
except ImportError:
    import prepare_released_callers as prep

FIELDS = ("contig", "pos", "stop", "serialized_END", "ID", "REF", "ALT",
          "QUAL", "FILTER", "INFO", "FORMAT_order", "samples", "FORMAT", "phase")
# Report only fixed categories, not arbitrary field names or values.
SAFE_TAGS = frozenset(("AF", "DP", "SVLEN", "SVTYPE", "END", "GT", "DR",
                      "DV", "PL", "GL", "GQ", "RE", "RNAMES", "PRECISE",
                      "IMPRECISE", "CIPOS", "CILEN", *prep.TAGS))
EXPECTED_ROWS = 51_561
INPUTS = {"source": (29_410_475, "inputs/cutesv.vcf"),
          "annotated": (31_780_495, "prepared/cutesv/annotated.vcf"),
          "split": (31_780_495, "prepared/cutesv/split.vcf")}
SOURCE_SHA = "9603595adebb54e656513c3ffba416e0d2173763030abef20f804e1c877209c1"
RESERVATION_BYTES = 320 * 1024**2
PRODUCTION_SHA = "f975699c57ec61ac4ab9062ad417623218b867213dbde127937b7b183e1c95d3"


def compare_fields(left, right):
    """No values, identifiers, coordinates, sequences or unknown tags escape."""
    a, b = json.loads(left), json.loads(right)
    prep._need(len(a) == len(b) == len(FIELDS), "projection schema differs")
    result = []
    for index, name in enumerate(FIELDS):
        if a[index] == b[index]:
            continue
        if name in ("INFO", "FORMAT"):
            prep._need(isinstance(a[index], dict) and isinstance(b[index], dict),
                       "projection mapping schema differs")
            for tag in sorted(set(a[index]) | set(b[index])):
                if tag not in a[index] or tag not in b[index] or a[index][tag] != b[index][tag]:
                    result.append(name + "/" + (tag if tag in SAFE_TAGS else "OTHER"))
        else:
            result.append(name)
    return result


def compare_streams(source_path, annotated_path, split_path, pysam, expected_rows):
    counters = {name: Counter() for name in
                ("source_to_annotated", "annotated_to_split", "source_to_split")}
    mismatch_rows = Counter()
    serialized_mismatch_rows = Counter()
    sentinel, rows = object(), 0
    with pysam.VariantFile(str(source_path)) as source, \
            pysam.VariantFile(str(annotated_path)) as annotated, \
            pysam.VariantFile(str(split_path)) as split:
        prep._need(list(source.header.samples) == list(annotated.header.samples)
                   == list(split.header.samples) == ["NULL"], "sample label/count differs")
        prep._need(not any(tag in source.header.info for tag in prep.TAGS), "source identity tags already exist")
        prep._need(all(tag in annotated.header.info and tag in split.header.info for tag in prep.TAGS),
                   "partial identity header tags absent")
        for original, annotated_rec, split_rec in zip_longest(source, annotated, split, fillvalue=sentinel):
            prep._need(all(rec is not sentinel for rec in (original, annotated_rec, split_rec)),
                       "stream lengths differ")
            rows += 1
            prep._need(rows <= expected_rows, "record count exceeds fixed population")
            prep._need(all(len(rec.alts or ()) == 1 for rec in (original, annotated_rec, split_rec)),
                       "diagnosis requires the complete biallelic population")
            for rec in (annotated_rec, split_rec):
                alt_index = prep._items(rec.info[prep.TAGS[1]])
                ordinal = rec.info[prep.TAGS[0]]
                prep._need(type(ordinal) is int and ordinal == rows
                           and len(alt_index) == 1 and type(alt_index[0]) is int
                           and alt_index[0] == 1,
                           "ordered source/ALT correspondence differs")
            original.translate(annotated.header)
            original.info[prep.TAGS[0]] = rows
            original.info[prep.TAGS[1]] = (1,)
            orig_id = quote(original.id or ".", safe="")
            original.info[prep.TAGS[2]] = "%2E" if orig_id == "." else orig_id
            expected = prep._semantic_child(original, 1, ("RNAMES",))
            if "RNAMES" in original.info:
                del original.info["RNAMES"]
            serial = tuple(prep._row(rec) for rec in (original, annotated_rec, split_rec))
            projections = (expected, prep._semantic_child(annotated_rec), prep._semantic_child(split_rec))
            for name, i, j in (("source_to_annotated", 0, 1),
                               ("annotated_to_split", 1, 2), ("source_to_split", 0, 2)):
                changes = compare_fields(projections[i], projections[j])
                counters[name].update(changes)
                mismatch_rows[name] += bool(changes)
                serialized_mismatch_rows[name] += serial[i] != serial[j]
    prep._need(rows == expected_rows, "complete population differs")
    return {"records": rows,
            "semantic_mismatch_rows": {key: mismatch_rows[key] for key in counters},
            "serialized_mismatch_rows": {key: serialized_mismatch_rows[key] for key in counters},
            "changed_field_occurrences": {key: dict(value) for key, value in counters.items()}}


def diagnose(root, report_path):
    root, report_path = Path(root), Path(report_path)
    prep._need(report_path.parent.is_dir() and not report_path.exists(), "fresh report path required")
    prep._need(not any((p / ".git").exists() for p in (report_path.parent.resolve(), *report_path.parent.resolve().parents)),
               "report must be outside Git")
    prep._need(prep._hash(Path(prep.__file__), 64 * 1024)[0] == PRODUCTION_SHA, "production code pin differs")
    pysam, _, _, versions = prep._runtime()
    observed, snapshots = {}, {}
    for name, (size, relative) in INPUTS.items():
        path = root / relative
        digest, actual_size, snapshot = prep._hash(path, size)
        prep._need(actual_size == size, "input size differs")
        if name == "source":
            prep._need(digest == SOURCE_SHA, "original source pin differs")
        observed[name] = {"bytes": actual_size, "sha256": digest}
        snapshots[name] = snapshot
    result = compare_streams(*(root / INPUTS[key][1] for key in ("source", "annotated", "split")),
                             pysam, EXPECTED_ROWS)
    for name, (size, relative) in INPUTS.items():
        prep._need(prep._hash(root / relative, size) ==
                   (observed[name]["sha256"], size, snapshots[name]), "input changed during diagnosis")
    result.update(status="complete_read_only_diagnosis", runtime=versions, inputs=observed,
                  reservation_bytes=RESERVATION_BYTES,
                  source_pin_verified=True, current_input_hashes_and_snapshots_stable=True,
                  annotated_and_split_bytes_identical=observed["annotated"] == observed["split"],
                  partial_hashes_not_recorded_at_original_failure=True,
                  no_preparation_normalization_scoring_or_genomic_output=True,
                  opaque_or_physical_IO_not_measured=True,
                  cause_is_field_localization_not_biological_performance=True)
    prep._need(len((json.dumps(result, indent=2, sort_keys=True) + "\n").encode()) <= 64 * 1024,
               "diagnostic report exceeds fixed cap")
    prep._save_report(report_path, result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    try:
        result = diagnose(args.root, args.report)
    except Exception as exc:
        # Never print external exception text or a source record.
        print(json.dumps({"status": "incomplete", "error_type": type(exc).__name__}), file=sys.stderr)
        return 2
    print(json.dumps({"status": result["status"], "records": result["records"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
