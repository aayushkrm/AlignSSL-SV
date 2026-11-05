#!/usr/bin/env python3
"""Create controlled BND validator inputs from the synthetic SnpEff fixture."""

import argparse
import hashlib
import json
from pathlib import Path


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    data = args.source.read_text()
    if data.count("A[chrB:20[") != 1 or data.count("]chrA:10]C") != 1:
        raise ValueError("unexpected synthetic source")
    variants = {
        "valid": data,
        "uppercase_remote": data.replace("A[chrB:20[", "A[CHRB:20[").replace("]chrA:10]C", "]CHRA:10]C"),
        "undeclared_remote": data.replace("A[chrB:20[", "A[chrZ:20[").replace("]chrA:10]C", "]chrZ:10]C"),
        "undeclared_local": data.replace("chrA\t10\ta\t", "chrZ\t10\ta\t"),
        "malformed_alt": data.replace("A[chrB:20[", "Z"),
    }
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    inputs = out / "inputs"
    inputs.mkdir()
    for name, content in variants.items():
        (inputs / f"{name}.vcf").write_text(content)
    manifest = {"source": str(args.source), "source_sha256": sha(data.encode()),
                "script_sha256": sha(Path(__file__).resolve().read_bytes()),
                "inputs": {f"{name}.vcf": sha(content.encode()) for name, content in variants.items()}}
    (out / "input-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
