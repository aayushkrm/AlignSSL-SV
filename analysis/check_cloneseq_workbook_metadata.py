#!/usr/bin/env python3
"""Verify a public supplement and inspect only workbook/legend metadata."""

import datetime
import hashlib
import json
import pathlib
import posixpath
import shlex
import shutil
import subprocess
import xml.etree.ElementTree as ET
import zipfile

REPO = pathlib.Path(__file__).resolve().parent.parent
OUT = REPO / "results/cloneseq_workbook_metadata_20261106_run01"
RUN = REPO.parent / "runs/cloneseq_workbook_metadata_20261106_run01"
URL = "https://pmc-oa-opendata.s3.amazonaws.com/PMC12629990.1/41586_2025_9580_MOESM1_ESM.zip?md5=053c2a18cbd1da4a250efc78e49b57e7"
SIZE = 18466636
MD5 = "053c2a18cbd1da4a250efc78e49b57e7"
MAX_BYTES = 20 * 1024 * 1024
CLUSTER = REPO.parent / "tools/cluster.sh"
MEMBERS = {"2024-08-17508B-s1/SupplementaryTables.xlsx": ("SupplementaryTables.xlsx", 19158931),
           "2024-08-17508B-s1/SupplementaryTables-legends.docx": ("SupplementaryTables-legends.docx", 15174)}
MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def digest(path, name):
    h = hashlib.new(name)
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def workbook_metadata(path):
    with zipfile.ZipFile(path) as book:
        root = ET.fromstring(book.read("xl/workbook.xml"))
        rels = ET.fromstring(book.read("xl/_rels/workbook.xml.rels"))
        targets = {r.get("Id"): r.get("Target") for r in rels.findall(f"{{{PKG_NS}}}Relationship")}
        sheets = []
        for sheet in root.findall(f".//{{{MAIN_NS}}}sheet"):
            target = targets[sheet.get(f"{{{REL_NS}}}id")]
            member = target.lstrip("/") if target.startswith("/") else posixpath.normpath("xl/" + target)
            dimension = None
            with book.open(member) as stream:
                for _, element in ET.iterparse(stream, events=("start",)):
                    if element.tag == f"{{{MAIN_NS}}}dimension":
                        dimension = element.get("ref")
                        break
                    if element.tag == f"{{{MAIN_NS}}}sheetData":
                        break
            sheets.append({"name": sheet.get("name"), "declared_dimension": dimension})
        return sheets


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    RUN.mkdir(parents=True, exist_ok=False)
    curl = ["curl", "--fail", "--silent", "--show-error", "--location",
            "--connect-timeout", "10", "--max-time", "60", "--max-filesize", str(MAX_BYTES), URL]
    receipt = {"url": URL, "expected_size": SIZE, "expected_md5": MD5,
               "transfer_cap_bytes": MAX_BYTES, "script_sha256": digest(pathlib.Path(__file__), "sha256"),
               "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "attempts": []}
    archive_path = None
    for number, command in enumerate([curl, [str(CLUSTER), shlex.join(curl)]], 1):
        target, stderr_path = RUN / f"attempt{number:02d}.zip", OUT / f"attempt{number:02d}.stderr.txt"
        with target.open("wb") as body, stderr_path.open("wb") as stderr:
            try:
                code = subprocess.run(command, stdout=body, stderr=stderr, timeout=90, check=False).returncode
            except subprocess.TimeoutExpired:
                code = None
        attempt = {"route": "local" if number == 1 else "cluster", "argv": command,
                   "exit_code": code, "bytes": target.stat().st_size,
                   "md5": digest(target, "md5"), "sha256": digest(target, "sha256"),
                   "stderr_sha256": digest(stderr_path, "sha256"), "local_file": str(target)}
        receipt["attempts"].append(attempt)
        (OUT / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
        if code == 0 and attempt["bytes"] == SIZE and attempt["md5"] == MD5:
            archive_path = target
            receipt["successful_attempt"] = number
            break
    if archive_path is None:
        raise SystemExit("No archive attempt matched the declared size and MD5")

    extracted = {}
    with zipfile.ZipFile(archive_path) as archive:
        for source, (name, expected) in MEMBERS.items():
            info = archive.getinfo(source)
            if info.file_size != expected:
                raise ValueError("Unexpected member size: " + source)
            path = RUN / name
            with archive.open(info) as source_stream, path.open("wb") as dest:
                shutil.copyfileobj(source_stream, dest)
            extracted[name] = {"bytes": path.stat().st_size, "sha256": digest(path, "sha256"),
                               "zip_crc32_verified_on_full_read": f"{info.CRC:08x}"}

    sheets = workbook_metadata(RUN / "SupplementaryTables.xlsx")
    with zipfile.ZipFile(RUN / "SupplementaryTables-legends.docx") as document:
        root = ET.fromstring(document.read("word/document.xml"))
        paragraphs = []
        for p in root.findall(f".//{{{WORD_NS}}}p"):
            text = "".join(x.text or "" for x in p.findall(f".//{{{WORD_NS}}}t"))
            if text.strip():
                paragraphs.append(text)
    (RUN / "legend_text.txt").write_text("\n".join(paragraphs) + "\n")
    summary = {"sheets": sheets, "legend_nonempty_paragraphs": len(paragraphs),
               "legend_text_sha256": digest(RUN / "legend_text.txt", "sha256"),
               "limits": "Workbook sheet names and declared dimensions plus document legends only; no worksheet rows inspected."}
    (OUT / "metadata.json").write_text(json.dumps(summary, indent=2) + "\n")
    receipt.update({"extracted": extracted, "metadata_sha256": digest(OUT / "metadata.json", "sha256")})
    (OUT / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print("Verified archive and", len(extracted), "members; sheets", len(sheets),
          "legend paragraphs", len(paragraphs))


if __name__ == "__main__":
    main()
