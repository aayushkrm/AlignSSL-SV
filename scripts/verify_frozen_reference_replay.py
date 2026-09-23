"""Verify that a frozen-FASTA replay exactly reproduces the 18-contig map."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

if __package__:
    from .verify_reference_difference_map import CONTIGS, verify as verify_original
else:
    from verify_reference_difference_map import CONTIGS, verify as verify_original


HGSVC_SHA256 = "90f1dcdb28a81ac26f6eaa1afc285e7ec459c195c2134fb25af0e82be2f11729"
IGSR_SHA256 = "3b103f4742abfd54938fb0333e19ad067635c8eb86f1dbf0ce44b165c4292b50"
HGSVC_FASTA = "/scratch/igorno-alignssl_restart_20260922/hgsvc-noalt-reference/hg38.no_alt.fa.gz"
IGSR_FASTA = "/scratch/igorno-alignssl_restart_20260922/igsr-reference/GRCh38_full_analysis_set_plus_decoy_hla.fa"
SCIENTIFIC_FIELDS = (
    "contig", "length", "n_different_bases", "n_difference_intervals",
    "difference_types", "first_differences", "difference_bed_sha256",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_manifest(path: Path, expected_names: set[str]) -> dict[str, str]:
    observed = {}
    for line in path.read_text().splitlines():
        fields = line.split(maxsplit=1)
        if len(fields) != 2:
            raise ValueError(f"{path}: malformed SHA256SUMS row")
        digest, name = fields
        if name not in expected_names or name in observed or len(digest) != 64:
            raise ValueError(f"{path}: unexpected, duplicate, or invalid entry: {name}")
        observed[name] = digest.lower()
    if set(observed) != expected_names:
        raise ValueError(f"{path}: missing entries: {expected_names - set(observed)}")
    return observed


def read_source(path: Path) -> dict[str, str]:
    fields = dict(line.split("=", 1) for line in path.read_text().splitlines())
    if fields.get("purpose") != "frozen-reference-provenance-rerun":
        raise ValueError(f"{path}: unexpected purpose")
    if fields.get("hgsvc_sha256") != HGSVC_SHA256 or fields.get("igsr_sha256") != IGSR_SHA256:
        raise ValueError(f"{path}: source FASTA hashes differ")
    if not fields.get("job_id", "").isdigit():
        raise ValueError(f"{path}: missing numeric job ID")
    return fields


def verify(historical: Path, frozen: Path) -> dict:
    original = verify_original(historical)
    if original["n_contigs"] != len(CONTIGS):
        raise ValueError("Historical map has an unexpected contig count")
    expected_names = {
        f"{contig}_base_differences{suffix}"
        for contig in CONTIGS for suffix in (".bed", "_full.json")
    }
    manifest = read_manifest(frozen / "SHA256SUMS", expected_names)
    source = read_source(frozen / "SOURCE.txt")
    files = []
    for contig in CONTIGS:
        bed_name = f"{contig}_base_differences.bed"
        json_name = f"{contig}_base_differences_full.json"
        old_bed = historical / bed_name
        new_bed = frozen / bed_name
        old_json = json.loads((historical / json_name).read_text())
        new_json = json.loads((frozen / json_name).read_text())
        bed_hash = sha256(new_bed)
        json_hash = sha256(frozen / json_name)
        if bed_hash != manifest[bed_name] or json_hash != manifest[json_name]:
            raise ValueError(f"{contig}: frozen file differs from SHA256SUMS")
        if bed_hash != sha256(old_bed) or new_bed.read_bytes() != old_bed.read_bytes():
            raise ValueError(f"{contig}: frozen BED differs from historical BED")
        if any(new_json[field] != old_json[field] for field in SCIENTIFIC_FIELDS):
            raise ValueError(f"{contig}: frozen scientific summary differs")
        if new_json["left_fasta"] != HGSVC_FASTA or new_json["right_fasta"] != IGSR_FASTA:
            raise ValueError(f"{contig}: frozen FASTA paths differ")
        if Path(new_json["difference_bed_path"]).name != bed_name:
            raise ValueError(f"{contig}: frozen BED path differs")
        files.append({
            "contig": contig, "bed_sha256": bed_hash, "json_sha256": json_hash,
            "n_different_bases": new_json["n_different_bases"],
            "n_difference_intervals": new_json["n_difference_intervals"],
        })
    return {
        "interpretation": "Exact replay of the saved 18-contig base-difference map from frozen source FASTAs; not a donor-callability result",
        "job_id": source["job_id"],
        "hgsvc_fasta_sha256": HGSVC_SHA256,
        "igsr_fasta_sha256": IGSR_SHA256,
        "n_contigs": len(files),
        "n_different_bases": sum(item["n_different_bases"] for item in files),
        "n_difference_intervals": sum(item["n_difference_intervals"] for item in files),
        "n_compared_bases": original["n_compared_bases"],
        "source_txt_sha256": sha256(frozen / "SOURCE.txt"),
        "manifest_sha256": sha256(frozen / "SHA256SUMS"),
        "files": files,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--historical", type=Path, required=True)
    parser.add_argument("--frozen", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.historical, args.frozen)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(f"Exact replay: {result['n_contigs']} contigs, "
          f"{result['n_different_bases']} unequal bases in "
          f"{result['n_difference_intervals']} intervals")


if __name__ == "__main__":
    main()
