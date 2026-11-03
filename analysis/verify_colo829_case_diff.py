"""Check byte-level differences between two plain VCFs without the normalizer."""

import argparse
from collections import Counter
import hashlib
import json
import re
from pathlib import Path


def inspect(original, normalized):
    source = original.read_bytes()
    target = normalized.read_bytes()
    a, b = source.splitlines(keepends=True), target.splitlines(keepends=True)
    if len(a) != len(b):
        raise ValueError("Different line counts")
    contigs = [m.group(1) for line in a if (m := re.match(rb"##contig=<ID=([^,>]+)", line))]
    folded = Counter(x.lower() for x in contigs)
    changed = []
    unchanged = 0
    for line_number, (x, y) in enumerate(zip(a, b), 1):
        if x == y:
            unchanged += 1
            continue
        if x.startswith(b"#") or y.startswith(b"#"):
            raise ValueError(f"Changed header at line {line_number}")
        old_fields, new_fields = x.split(b"\t"), y.split(b"\t")
        if len(old_fields) != len(new_fields) or any(
            old != new for i, (old, new) in enumerate(zip(old_fields, new_fields)) if i != 4
        ):
            raise ValueError(f"Non-ALT difference at line {line_number}")
        old_alt, new_alt = old_fields[4], new_fields[4]
        old = re.search(rb"([\[\]])([^:\[\]]+):(\d+)\1", old_alt)
        new = re.search(rb"([\[\]])([^:\[\]]+):(\d+)\1", new_alt)
        if not old or not new:
            raise ValueError(f"Missing BND mate token at line {line_number}")
        before, after = old.group(2), new.group(2)
        if (before == after or before.lower() != after.lower() or after not in contigs
                or folded[after.lower()] != 1
                or old_alt[:old.start(2)] + after + old_alt[old.end(2):] != new_alt):
            raise ValueError(f"Change is not a unique header case alias at line {line_number}")
        changed.append({"line": line_number, "id": old_fields[2].decode(),
                        "old_remote": before.decode(), "new_remote": after.decode()})
    return {"original_sha256": hashlib.sha256(source).hexdigest(),
            "normalized_sha256": hashlib.sha256(target).hexdigest(),
            "lines": len(a), "unchanged_lines": unchanged,
            "header_contigs": len(contigs), "changed_lines": len(changed),
            "changes": changed}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("original", type=Path)
    parser.add_argument("normalized", type=Path)
    args = parser.parse_args()
    print(json.dumps(inspect(args.original, args.normalized), indent=2))


if __name__ == "__main__":
    main()
