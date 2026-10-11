"""One fixed provenance/header read, without genotype records or author execution."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

EXPERIMENT = "svupp-provenance-20261009-01"
ROOT = Path("/beegfs/scratch/ws/ws1/igorno-alignssl_restart_20260922") / EXPERIMENT
SOURCE = (ROOT.parent / "svupp-inventory-20261009-02" / "SVUPP_paper.zip")
SOURCE_BYTES = 47_443_427
SOURCE_MD5 = "5469337ca9249691b2b376ceb9b67e1d"
SOURCE_SHA256 = "b15665743d28151bf2e9f656ae32dc8de9a3d6a5582c8033dbf251fec71daa2c"


def new_metadata(path, value):
    payload = (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()
    if len(payload) > 64 * 1024:
        raise ValueError("metadata exceeds 64 KiB")
    with Path(path).open("xb") as output:
        output.write(payload)


def trusted_root(root):
    root = Path(root)
    if (root != ROOT or not root.is_dir() or root.is_symlink()
            or root.resolve(strict=True) != ROOT
            or any(parent.is_symlink() for parent in root.parents)):
        raise ValueError("unexpected or linked physical provenance root")
    return root


def run(root):
    from analysis.inspect_svupp_provenance_headers import inspect_provenance_headers

    root = trusted_root(root)
    new_metadata(root / "payload.claim.json", {
        "experiment": EXPERIMENT, "root": str(root), "source": str(SOURCE),
        "genotype_records_not_interpreted": True, "author_code_not_executed": True})
    report = inspect_provenance_headers(
        SOURCE, expected_bytes=SOURCE_BYTES, expected_md5=SOURCE_MD5,
        expected_sha256=SOURCE_SHA256, output_manifest=root / "provenance_headers.json")
    if (report["inspection_status"] != "COMPLETE_BOUNDED_PROVENANCE_HEADERS"
            or report["source_archive_sha256"] != SOURCE_SHA256
            or report["fixed_member_count"] != 8
            or not report["all_selected_outer_zip_members_read_to_crc_eof"]
            or not report["genotype_records_not_interpreted"]
            or not report["bodies_decoded"]
            or not report["nested_gzip_full_crc_not_assessed"]
            or not report["nested_gzip_body_integrity_not_assessed"]
            or not report["gzip_read_ahead_may_include_body_bytes"]
            or report["author_text_executed"]
            or report["usable_data_readiness_assessed"]):
        raise ValueError("provenance reader did not satisfy the frozen scope")
    new_metadata(root / "result.json", {
        "status": "COMPLETE_PROVENANCE_HEADERS", "experiment": EXPERIMENT,
        "source_sha256": SOURCE_SHA256, "fixed_member_count": 8,
        "member_bodies_decoded": True, "genotype_records_not_interpreted": True,
        "nested_gzip_full_crc_not_assessed": True, "author_code_not_executed": True,
        "scientific_data_readiness": "UNRESOLVED_PROVENANCE_ONLY",
        "publication_result": False, "campaign_approval": False})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    args = parser.parse_args()
    try:
        run(args.root)
    except Exception as error:
        try:
            root = trusted_root(args.root)
        except (ValueError, OSError):
            root = None
        if root is not None:
            new_metadata(root / "failure.json", {
                "status": "INCOMPLETE", "error_type": type(error).__name__,
                "reason": str(error)[:2000], "genotype_records_not_interpreted": True,
                "publication_result": False})
        raise


if __name__ == "__main__":
    main()
