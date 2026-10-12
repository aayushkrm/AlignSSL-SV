"""Fetch a fixed small published comparator panel, not the 2.88GB archive."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile

from inspect_svpg_archive_index import RangeReader


URL = "https://zenodo.org/api/records/18456502/files/SV_callsets.zip/content"
TOTAL_BYTES = 2_879_666_672
PREFIX = "SV_callsets/somatic_SV/hg008/"
FILES = [
    "GRCh38_HG008-T-V0.3_somatic-stvar.draftbenchmark.bed",
    "GRCh38_HG008-T-V0.3_somatic-stvar_PASS.draftbenchmark.vcf",
    "GRCh38_HG008-T-V0.3_somatic-stvar_PASS.draftbenchmark.filtered.vcf",
    "svpg.vcf", "svpg.filter.vcf", "severus.vcf", "severus.filter.vcf",
    "nanomonsv.vcf", "nanomonsv.filter.vcf", "minisv.vcf", "minisv.filter.vcf",
]
START, END = 19_196_736, 19_197_155
LOW, HIGH = START - 1000, END + 1000


def case_rows(text):
    rows, headers, records = [], [], 0
    for line in text.splitlines():
        if line.startswith("#"):
            if line.startswith("#CHROM") or re.match(
                r"##(?:source|reference|fileformat|SVPG|Severus|nanomonsv|version|fileDate)", line, re.I
            ):
                headers.append(line)
            continue
        if not line:
            continue
        fields = line.split("\t")
        if len(fields) < 8:
            raise ValueError("Malformed VCF record")
        chrom, position = fields[0], int(fields[1])
        records += 1
        ends = re.findall(r"(?:^|;)END=(\d+)(?:;|$)", fields[7])
        mates = re.findall(r"[\[\]](chr7|7):(\d+)[\[\]]", fields[4])
        near = chrom in {"chr7", "7"} and (
            LOW <= position <= HIGH or any(LOW <= int(value) <= HIGH for value in ends)
        )
        if near or any(LOW <= int(value) <= HIGH for _, value in mates):
            rows.append({"raw_record": line, "chromosome": chrom, "position": position,
                         "end_field_values": ends, "id": fields[2], "ref": fields[3],
                         "alt": fields[4], "filter": fields[6], "info": fields[7],
                         "format_and_samples": fields[8:]})
    return {"total_records_read": records, "selected_headers": headers, "nearby_records": rows}


def fetch(output_dir):
    reader = RangeReader(URL, TOTAL_BYTES)
    manifest = {"schema": 1, "scope": "PUBLISHED_NAMED_CASE_SOURCE_PANEL",
                "url": URL, "archive_bytes": TOTAL_BYTES,
                "whole_archive_checksum_verified": False,
                "selection": {"paper_chr7_position": START, "reported_deletion_length": 419,
                              "fixed_neighborhood_start": LOW, "fixed_neighborhood_end": HIGH,
                              "chr7_7_alias_is_not_reference_base_identity_proof": True},
                "files": [], "comparative_allele_recovery_claim": "NOT_ASSESSED"}
    with zipfile.ZipFile(reader) as archive:
        for basename in FILES:
            name = PREFIX + basename
            matches = [entry for entry in archive.infolist() if entry.filename == name]
            if len(matches) != 1:
                raise ValueError(f"Missing or duplicate exact archive member: {name}")
            entry = matches[0]
            if entry.file_size > 8 * 1024**2 or entry.flag_bits & 1:
                raise ValueError("Member size or encryption outside scope")
            # A permitted decoded member can exceed the single range cap.
            # ZipExtFile reads bounded chunks and checks CRC at full EOF.
            with archive.open(entry) as member:
                chunks = []
                while chunk := member.read(1024**2):
                    chunks.append(chunk)
                body = b"".join(chunks)
            if len(body) != entry.file_size:
                raise ValueError("Member length mismatch")
            with (output_dir / basename).open("xb") as handle:
                handle.write(body)
            record = {"member": name, "local_basename": basename, "bytes": len(body),
                      "sha256": hashlib.sha256(body).hexdigest(), "crc32": f"{entry.CRC:08x}",
                      "member_crc_verified": True}
            if basename.endswith(".vcf"):
                record.update(case_rows(body.decode("utf-8")))
            manifest["files"].append(record)
    manifest.update({"transferred_range_bytes": reader.transferred,
                     "range_receipts": reader.receipts, "last_modified": reader.last_modified})
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.sources_dir.is_dir():
        raise ValueError("Existing task-specific source directory required")
    result = fetch(args.sources_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, allow_nan=False)
        handle.write("\n")
    print(json.dumps({"source_files": len(result["files"]),
                      "transferred_range_bytes": result["transferred_range_bytes"],
                      "case_records_by_file": {record["local_basename"]: len(record.get("nearby_records", []))
                                               for record in result["files"]}}, indent=2))


if __name__ == "__main__":
    main()
