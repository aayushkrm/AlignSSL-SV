#!/usr/bin/env python3
"""S0: checksum-bound reference expansion; no donor annotation or path decisions."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import time

NAMES = {"GRCh38.primary_assembly.genome.fa.gz", "gencode.v50.primary_assembly.annotation.gff3.gz",
         "gencode.v50.primary_assembly.annotation.gtf.gz", "gencode.v50.metadata.Selenocysteine.gz",
         "gencode.v50.pc_translations.fa.gz"}
EXTERNAL_RESERVE = 8 * 1024**3
PAYLOAD_CAP = 12 * 1024**3 - 16 * 1024**2  # Room for two expanded copies plus metadata within S0's32GiB.
WALL = 840


def expand(source, output):
    source, output = Path(source), Path(output)
    if output.exists() or output.is_symlink() or not output.parent.is_dir():
        raise ValueError("exclusive new output leaf required")
    if signal.getitimer(signal.ITIMER_REAL)[0]:
        raise ValueError("existing wall timer")
    output.mkdir(mode=0o700)
    started, pending = time.monotonic(), []
    old = {sig: signal.getsignal(sig) for sig in (signal.SIGALRM, signal.SIGTERM)}
    result = {"status": "INCOMPLETE", "scope": "S0_REFERENCE_EXPANSION_ONLY", "objects": [],
              "external_reserve_bytes": EXTERNAL_RESERVE, "reserve_measurement": "planning reserve, not observed file total",
              "payload_cap_bytes": PAYLOAD_CAP, "reserved_copies": 2, "written_payload_bytes": 0}
    def guard():
        if pending or time.monotonic()-started >= WALL:
            raise RuntimeError("cancelled or wall deadline reached")
    try:
        for sig in old: signal.signal(sig, lambda signum, _: pending.append(signum))
        signal.setitimer(signal.ITIMER_REAL, WALL)
        (output/"manifest.initial.json").write_text(json.dumps(result, sort_keys=True))
        if shutil.disk_usage(output).free < 32*1024**3:
            raise ValueError("32 GiB filesystem free required")
        manifest = json.loads((source/"manifest.json").read_text())
        objects = manifest["objects"]
        if manifest["status"] != "STAGED_CHECKSUM_VERIFIED" or len(objects) != 5 or {Path(o["path"]).name for o in objects} != NAMES:
            raise ValueError("require all five matched verified reference objects")
        for obj in objects:
            guard()
            name = Path(obj["path"]).name
            path = source/name
            if path.stat().st_size != obj["size_bytes"]:
                raise ValueError("compressed source size differs")
            digest = hashlib.sha256()
            with path.open("rb") as stream:
                while block := stream.read(4*1024**2):
                    guard(); digest.update(block)
            if digest.hexdigest() != obj["sha256"]:
                raise ValueError("compressed source checksum differs")
            destination = output/name[:-3]
            partial = destination.with_name(destination.name+".partial")
            digest, written = hashlib.sha256(), 0
            with gzip.open(path, "rb") as stream, partial.open("xb") as sink:
                while block := stream.read(1024**2):
                    guard()
                    if result["written_payload_bytes"]+len(block) > PAYLOAD_CAP:
                        raise ValueError("expanded payload and future custody exceed S0 reserve")
                    sink.write(block)
                    digest.update(block); written += len(block)
                    result["written_payload_bytes"] += len(block)
            guard()  # gzip EOF/CRC must pass before exclusive publication.
            os.link(partial, destination); partial.unlink()
            result["objects"].append({"name": destination.name, "size_bytes": written,
                                      "sha256": digest.hexdigest(), "compressed_sha256": obj["sha256"]})
        guard()
        result["status"] = "EXPANDED_CRC_VERIFIED"
    except BaseException as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        if pending or time.monotonic()-started >= WALL:
            result.update(status="INCOMPLETE", error="cancelled or wall deadline reached")
        result["wall_seconds"] = time.monotonic()-started
        try:
            with (output/"manifest.json").open("x") as stream:
                json.dump(result, stream, sort_keys=True, indent=2)
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            for sig, handler in old.items(): signal.signal(sig, handler)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = expand(args.reference, args.output)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "EXPANDED_CRC_VERIFIED" else 2


if __name__ == "__main__": main()
