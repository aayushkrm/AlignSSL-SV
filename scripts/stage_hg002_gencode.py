#!/usr/bin/env python3
"""Stage the five fixed, matched GENCODE50 products; no donor reads or analysis."""
import argparse
import hashlib
import json
import shutil
import signal
import time
import urllib.request
from pathlib import Path

from . import acquire_hg002_dna as transfer

helper = transfer.helper
ROOT = "https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_50/"
FILES = (
    ("GRCh38.primary_assembly.genome.fa.gz", 845635028, "da1a11258be075cfa7af718162c894e7"),
    ("gencode.v50.primary_assembly.annotation.gff3.gz", 160763187, "bfa97cfbd5fe76ce5fb19ac08c16f25b"),
    ("gencode.v50.primary_assembly.annotation.gtf.gz", 124650284, "289b91e5e95e8b0450d223246f10a12e"),
    ("gencode.v50.metadata.Selenocysteine.gz", 893, "cf5f185bdfa2dcd0582e2f747f3a4e9b"),
    ("gencode.v50.pc_translations.fa.gz", 21136991, "509a89a4c3bb8c594baac50d4d57e589"),
)
LIMIT, WALL, MIN_FREE = 2 * 1024**3, 3600, 32 * 1024**3
SCRATCH = transfer.SCRATCH_EXPERIMENTS


class ReferenceLedger(transfer.Ledger):
    def __init__(self, path, deadline):
        helper.BodyLedger.__init__(self, path, deadline, limit=LIMIT, prior=0)


def md5(path, deadline):
    digest = hashlib.md5()
    with path.open("rb") as stream:
        while True:
            transfer.check_deadline(deadline)
            block = stream.read(4 * 1024**2)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def stage(output, *, opener=None):
    output = Path(output)
    if output.exists() or output.is_symlink() or not output.parent.is_dir():
        raise helper.AcquisitionError("new output directory under an existing parent required")
    if signal.getitimer(signal.ITIMER_REAL)[0]:
        raise helper.AcquisitionError("existing wall timer")
    output.mkdir(mode=0o700)
    start, cpu_start = time.monotonic(), helper.cpu_seconds()
    deadline = start + WALL
    ledger = ReferenceLedger(output / "body_ledger.jsonl", deadline)
    result = {"stage": "S0_REFERENCES", "status": "INCOMPLETE", "objects": [],
              "started_utc": helper.utcnow(), "scope": "matched reference acquisition, not annotation",
              "expected_bytes": sum(x[1] for x in FILES), "body_limit": LIMIT,
              "prior_reference_body_bytes": 0, "retries": 0}
    saved = (signal.getsignal(signal.SIGALRM), signal.getsignal(signal.SIGTERM), transfer._pending_signal)
    transfer._pending_signal = None
    try:
        signal.signal(signal.SIGALRM, transfer.wall_alarm)
        signal.signal(signal.SIGTERM, transfer.wall_alarm)
        signal.setitimer(signal.ITIMER_REAL, WALL)
        result["source_hashes"] = {str(Path(x.__file__).name): helper.sha256_file(Path(x.__file__))
                                   for x in (transfer, helper)}
        result["code_sha256"] = helper.sha256_file(Path(__file__))
        helper.write_json(output / "manifest.initial.json", result)
        result["free_bytes_before"] = shutil.disk_usage(output).free
        if result["free_bytes_before"] < MIN_FREE:
            raise helper.AcquisitionError("32 GiB free required")
        opener = opener or helper.make_opener()
        for name, size, expected_md5 in FILES:
            transfer.check_deadline(deadline)
            url = ROOT + name
            key = ledger.begin("reference_head", url, {"Accept-Encoding": "identity"})
            try:
                with opener(urllib.request.Request(url, method="HEAD", headers={"Accept-Encoding": "identity"}), timeout=30) as response:
                    ledger.headers(key, response)
                    helper.check_identity(response.headers)
                    if helper.http_status(response) != 200 or helper.h(response.headers, "Content-Length") != str(size):
                        raise helper.AcquisitionError("reference HEAD status/size drift")
                    etag = helper.h(response.headers, "ETag")
                    if not etag:
                        raise helper.AcquisitionError("reference ETag absent")
                ledger.finish(key, "verified")
            except BaseException as exc:
                ledger.finish(key, "rejected", str(exc))
                raise
            artifact = transfer.download({"name": name, "url": url, "size_bytes": size, "etag": etag}, output, ledger, opener)
            artifact.update(url=url, etag=etag, published_md5=expected_md5, actual_md5=md5(output/name, deadline))
            result["objects"].append(artifact)
            if artifact["actual_md5"] != expected_md5:
                raise helper.AcquisitionError("published reference checksum mismatch")
        transfer.check_deadline(deadline)
        result["status"] = "STAGED_CHECKSUM_VERIFIED"
    except BaseException as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        ledger.event({"event": "stage_failed", "error": result["error"]})
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, saved[0]); signal.signal(signal.SIGTERM, saved[1])
        transfer._pending_signal = saved[2]
        result.update(finished_utc=helper.utcnow(), wall_seconds=time.monotonic()-start,
                      cpu_seconds=helper.cpu_seconds()-cpu_start, body_ledger=ledger.snapshot())
        ledger.close()
        helper.write_json(output / "manifest.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    path = args.output
    if not path.is_absolute() or path.name != "hg002_gencode_s0_20261010_01" or path.parent.resolve(strict=True) != SCRATCH:
        parser.error("use the fixed new project scratch reference leaf")
    result = stage(path)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "STAGED_CHECKSUM_VERIFIED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
