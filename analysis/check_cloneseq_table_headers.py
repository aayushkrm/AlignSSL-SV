#!/usr/bin/env python3
"""Inspect the first row of each public CloneSeq workbook sheet only."""

import datetime
import hashlib
import json
import pathlib
import re
import sys

import openpyxl

REPO = pathlib.Path(__file__).resolve().parent.parent
WORKBOOK = REPO.parent / "runs/cloneseq_workbook_metadata_20261106_run01/SupplementaryTables.xlsx"
INPUT_RECEIPT = REPO / "results/cloneseq_workbook_metadata_20261106_run01/receipt.json"
SHEET_META = REPO / "results/cloneseq_workbook_metadata_20261106_run01/metadata.json"
OUT = REPO / "results/cloneseq_schema_20261122_run01"
HEADER_HINT = re.compile(r"patient|sample|clone|variant|coverage|read|count|depth|error|type|time|date|tumou?r|locus|chrom|position|treatment|clinical|surgery|recurr|status|marker|support|vaf|allele|\bid\b", re.I)
OBSERVATION_ID = re.compile(r"^(?:OV|PATIENT|PT|P)[-_ ]?\d{2,}(?:[-_.].*)?$", re.I)


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    old = json.loads(INPUT_RECEIPT.read_text())
    expected = old["extracted"]["SupplementaryTables.xlsx"]["sha256"]
    actual = sha(WORKBOOK)
    result = {"source_workbook_sha256": actual, "expected_sha256": expected,
              "script_sha256": sha(pathlib.Path(__file__)), "python": sys.version,
              "openpyxl": openpyxl.__version__,
              "checked_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "protocol_commit": "7499eef", "sheets": [],
              "limits": "Only the first row of each sheet was inspected; no patient observations or later rows were analyzed."}
    if actual != expected:
        result["error"] = "Workbook SHA256 mismatch; no rows inspected"
        (OUT / "schema.json").write_text(json.dumps(result, indent=2) + "\n")
        raise SystemExit(result["error"])
    expected_names = [x["name"] for x in json.loads(SHEET_META.read_text())["sheets"]]
    book = openpyxl.load_workbook(WORKBOOK, read_only=True, data_only=False)
    try:
        if book.sheetnames != expected_names:
            raise ValueError("Workbook sheet list differs from prior metadata")
        for sheet in book.worksheets:
            entry = {"sheet": sheet.title, "row": 1}
            try:
                if sheet.max_column is None or sheet.max_column > 1024:
                    raise ValueError("Unknown or excessive sheet width")
                row = next(sheet.iter_rows(min_row=1, max_row=1, max_col=sheet.max_column,
                                           values_only=True), ())
                values = [x for x in row if x is not None]
                if (len(values) < 2 or not all(isinstance(x, str) for x in values)
                        or any(x.startswith("=") or OBSERVATION_ID.fullmatch(x.strip()) for x in values)
                        or not any(HEADER_HINT.search(x) for x in values)):
                    entry.update({"status": "unresolved", "reason": "First row was not safely identifiable as field labels"})
                else:
                    entry.update({"status": "header", "fields": list(row)})
            except Exception as exc:
                entry.update({"status": "unresolved", "reason": f"{type(exc).__name__}: {exc}"})
            result["sheets"].append(entry)
    finally:
        book.close()
    (OUT / "schema.json").write_text(json.dumps(result, indent=2) + "\n")
    print("Sheets", len(result["sheets"]), "resolved headers",
          sum(x["status"] == "header" for x in result["sheets"]))


if __name__ == "__main__":
    main()
