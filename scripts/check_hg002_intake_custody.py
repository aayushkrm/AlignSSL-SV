#!/usr/bin/env python3
"""Read-only verification of retained intake objects; not BAM/annotation readiness."""
import argparse
import hashlib
import json
from pathlib import Path
import time


def verify(root):
    manifest = json.loads((root / "manifest.json").read_text())
    expected = {"S1a": ("ACQUIRED", 2), "S0_REFERENCES": ("STAGED_CHECKSUM_VERIFIED", 5)}
    status, count = expected[manifest["stage"]]
    if manifest["status"] != status or len(manifest["objects"]) != count:
        raise ValueError("incomplete or unexpected intake manifest")
    if len({Path(obj["path"]).name for obj in manifest["objects"]}) != count:
        raise ValueError("duplicate custody objects")
    checked = []
    for obj in manifest["objects"]:
        path = root / Path(obj["path"]).name
        if not path.is_file() or path.stat().st_size != obj["size_bytes"]:
            raise ValueError(f"custody size mismatch: {path.name}")
        hasher = hashlib.sha256()
        with path.open("rb") as stream:
            while block := stream.read(4 * 1024**2):
                hasher.update(block)
        actual = hasher.hexdigest()
        if actual != obj["sha256"]:
            raise ValueError(f"custody SHA256 mismatch: {path.name}")
        checked.append({"name": path.name, "size_bytes": path.stat().st_size, "sha256": actual})
    return {"root": str(root), "stage": manifest["stage"], "objects": checked}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("roots", nargs="+", type=Path)
    args = parser.parse_args()
    started = time.monotonic()
    result = {"status": "CUSTODY_HASHES_VERIFIED", "scope": "copies only; full read and annotation readiness NOT_ASSESSED",
              "checks": [verify(root) for root in args.roots]}
    result["wall_seconds"] = time.monotonic()-started
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
