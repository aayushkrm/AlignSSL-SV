"""Acquire one pinned author ZIP and inventory metadata, never member outcomes.

Use only in the separately reviewed, timed cluster launch. No extraction,
caller, scoring, retry, alternate archive or old experiment continuation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import stat
import sys
import urllib.request

sys.path.insert(0, str(Path(__file__).parent.parent))

EXPERIMENT = "svupp-inventory-20261009-01"
ROOT = Path("/beegfs/scratch/ws/ws1/igorno-alignssl_restart_20260922") / EXPERIMENT
ASSET_URL = "https://zenodo.org/api/records/17569072/files/SVUPP_paper.zip/content"
ASSET_BYTES = 47443427
ASSET_MD5 = "5469337ca9249691b2b376ceb9b67e1d"


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
        raise ValueError("unexpected or linked physical inventory root")
    return root


def control_tree_size(path):
    """Count test artifacts without following intentional links.

    Negative controls create both symbolic and hard links. This accounting
    permits those test objects only; it does not relax the asset validator.
    """
    total = count = 0
    for directory, dirs, files in os.walk(path, followlinks=False):
        for name in dirs + files:
            info = (Path(directory) / name).lstat()
            count += 1
            if stat.S_ISREG(info.st_mode):
                total += info.st_size
            elif not (stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode)):
                raise ValueError("unexpected special test artifact")
            if total > 32 * 1024**2 or count > 4096:
                raise ValueError("synthetic control tree exceeds its cap")
    return total


def run(root):
    from analysis.inspect_pinned_research_zip import inspect_zip

    root = trusted_root(root)
    new_metadata(root / "payload.claim.json", {"experiment": EXPERIMENT,
                 "outcomes_not_read": True, "root": str(root)})
    archive = root / "SVUPP_paper.zip"
    md5, sha = hashlib.md5(), hashlib.sha256()
    size = 0
    with urllib.request.urlopen(ASSET_URL, timeout=30) as response, archive.open("xb") as output:
        while True:
            block = response.read(64 * 1024)
            if not block:
                break
            size += len(block)
            if size > ASSET_BYTES:
                raise ValueError("download exceeds the frozen asset size")
            md5.update(block)
            sha.update(block)
            output.write(block)
    if size != ASSET_BYTES or md5.hexdigest() != ASSET_MD5:
        raise ValueError("download does not match the frozen author asset")
    new_metadata(root / "acquisition.json", {"bytes": size,
        "md5": md5.hexdigest(), "sha256": sha.hexdigest(),
        "source": ASSET_URL, "member_bodies_decoded": False,
        "opaque_zip_bytes_hashed": True})
    # The stored ZIP is below64MiB. All later report/log files are at most1MiB.
    resource.setrlimit(resource.RLIMIT_FSIZE, (1024**2, 1024**2))
    report = inspect_zip(archive, expected_bytes=ASSET_BYTES, expected_md5=ASSET_MD5,
                         output_manifest=root / "inventory.json")
    if report["actual_asset_sha256"] != sha.hexdigest():
        raise ValueError("stored archive differs from the acquired stream")
    # An inventory alone is not a successful acquisition/integrity result.
    # Preserve any partial evidence on failure, but publish completion only
    # after the stored and acquired stream digests agree.
    new_metadata(root / "result.json", {
        "status": "COMPLETE_METADATA_INVENTORY", "experiment": EXPERIMENT,
        "asset_sha256": sha.hexdigest(), "member_count": report["member_count"],
        "outcomes_not_read": True, "member_bodies_decoded": False,
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
            new_metadata(root / "failure.json", {"status": "INCOMPLETE",
                         "error_type": type(error).__name__, "reason": str(error)[:2000],
                         "outcomes_not_read": True, "publication_result": False})
        raise


if __name__ == "__main__":
    main()
