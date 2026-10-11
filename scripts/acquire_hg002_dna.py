#!/usr/bin/env python3
"""Prospective S1a acquisition only; running this file requires separate launch approval."""
import argparse
import hashlib
import http.client
import json
import os
import platform
import re
import resource
import shutil
import signal
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

if __package__:
    from . import acquire_parent_sva_region as helper
else:
    import acquire_parent_sva_region as helper

ROOT = "https://stergachis-manuscript-data.s3.us-west-1.amazonaws.com/2023/Vollger_et_al_long-read_multi-ome/"
SOURCES = (
    {"name": "HG002_WGS.haplotagged.bam", "url": ROOT + "HG002_WGS.haplotagged.bam",
     "size_bytes": 48_727_325_910, "etag": '"8c384718d3e41cbe000453b6846a7451-5809"'},
    {"name": "HG002_WGS.haplotagged.bam.bai", "url": ROOT + "HG002_WGS.haplotagged.bam.bai",
     "size_bytes": 21_582_928, "etag": '"b45b35aa8fd900989a2798ed22faec3c-3"'},
)
BODY_LIMIT, PRIOR_BYTES = 52 * 1024**3, 196_608
WALL_SECONDS, CHUNK, MIN_FREE = 4 * 3600, 1024**2, 160 * 1024**3
HELPER_SHA256 = "c0f47e522d4f88b2e068f035b78eb558e63e4abc94839b4a78e32f3c6f09034b"
SCRATCH_EXPERIMENTS = Path("/beegfs/scratch/ws/ws1/igorno-alignssl_restart_20260922/experiments")
AcquisitionError, BudgetExceeded = helper.AcquisitionError, helper.BudgetExceeded
_pending_signal = None


def check_deadline(deadline):
    if _pending_signal is not None:
        raise BudgetExceeded(f"cancellation requested by signal {_pending_signal}")
    if time.monotonic() >= deadline:
        raise BudgetExceeded("wall deadline reached")


class Ledger(helper.BodyLedger):
    """Keep the existing flushed journal, with generic fixed-budget diagnostics."""
    def __init__(self, path, deadline, *, prior=PRIOR_BYTES):
        if type(prior) is not int or not PRIOR_BYTES <= prior < BODY_LIMIT:
            raise AcquisitionError("invalid cumulative prior body charge")
        super().__init__(path, deadline, limit=BODY_LIMIT, prior=prior)

    def reserve(self, amount):
        with self.lock:
            check_deadline(self.deadline)
            if not 0 < amount <= CHUNK:
                raise AcquisitionError("invalid bounded read reservation")
            available = self.limit - self.prior - self.used - self.reserved
            if available <= 0:
                raise BudgetExceeded("cumulative body-byte budget exhausted")
            grant = min(amount, available)
            self.reserved += grant
            return grant

    def charge(self, key, grant, actual):
        if actual < 0 or not 0 < grant <= self.reserved:
            raise AcquisitionError("body ledger reservation underflow")
        super().charge(key, grant, actual)
        if actual > grant or self.prior + self.used > self.limit:
            raise BudgetExceeded("response exceeded its body-byte reservation")


def download(meta, out, ledger, opener):
    path = out / meta["name"]
    partial = path.with_name(path.name + ".partial")
    if path.exists() or path.is_symlink():
        raise AcquisitionError("complete output already exists")
    headers = {"Range": f"bytes=0-{meta['size_bytes']-1}",
               "If-Match": meta["etag"], "Accept-Encoding": "identity"}
    key = ledger.begin("full_object", meta["url"], headers)
    try:
        with partial.open("xb") as sink:
            check_deadline(ledger.deadline)
            if not ledger.can_fit(meta["size_bytes"]):
                raise BudgetExceeded("object exceeds remaining cumulative body-byte budget")
            with opener(urllib.request.Request(meta["url"], headers=headers), timeout=30) as response:
                ledger.headers(key, response)
                length = helper.validate_206(response, 0, meta["size_bytes"]-1, meta["size_bytes"], meta["etag"])
                total = 0
                while total < length:
                    grant = ledger.reserve(min(CHUNK, length-total))
                    try:
                        block = response.read(grant)
                    except http.client.IncompleteRead as exc:
                        ledger.charge(key, grant, len(exc.partial))
                        sink.write(exc.partial)
                        sink.flush()
                        check_deadline(ledger.deadline)
                        raise
                    except BaseException:
                        ledger.charge(key, grant, 0)
                        raise
                    ledger.charge(key, grant, len(block))  # Journal flush precedes each write.
                    if not block:
                        raise AcquisitionError("body ended before declared Content-Length")
                    sink.write(block)
                    sink.flush()
                    total += len(block)
                    check_deadline(ledger.deadline)
        digest = bounded_hash(partial, ledger.deadline)
        check_deadline(ledger.deadline)
        os.link(partial, path)  # Atomic exclusive publication; never replace a destination.
        partial.unlink()
        ledger.finish(key, "verified")
        return {"path": str(path), "size_bytes": path.stat().st_size, "sha256": digest}
    except urllib.error.HTTPError as exc:
        ledger.headers(key, exc)
        ledger.finish(key, "rejected", f"HTTP {exc.code}")
        exc.close()  # Do not read redirects or error bodies.
        raise AcquisitionError(f"object request returned HTTP {exc.code}") from exc
    except BaseException as exc:
        ledger.finish(key, "incomplete", str(exc))
        raise


def write_new_json(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write("\n")
        stream.flush()


def wall_alarm(signum=None, *_):
    # Never throw between a returned response.read and its durable accounting.
    # The socket has a 30-second timeout; safe points enforce cancellation.
    global _pending_signal
    _pending_signal = signum or signal.SIGALRM


def bounded_hash(path, deadline):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while True:
            check_deadline(deadline)
            block = stream.read(4 * 1024**2)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def acquire(output, *, opener=None, prior_body_bytes=PRIOR_BYTES):
    """Acquire into a new directory; tests may use any existing local parent."""
    global _pending_signal
    if type(prior_body_bytes) is not int or not PRIOR_BYTES <= prior_body_bytes < BODY_LIMIT:
        raise AcquisitionError("prior body charge must include all prefixes and remain below the fixed cap")
    if signal.getitimer(signal.ITIMER_REAL)[0]:
        raise AcquisitionError("an existing wall timer prevents exclusive deadline control")
    output = Path(output)
    if output.exists() or output.is_symlink() or not output.parent.is_dir():
        raise AcquisitionError("output must be a new directory under an existing parent")
    started, cpu_start = time.monotonic(), helper.cpu_seconds()
    deadline = started + WALL_SECONDS
    output.mkdir(mode=0o700)
    out = output.resolve()
    ledger = Ledger(out / "body_ledger.jsonl", deadline, prior=prior_body_bytes)
    manifest = {"stage": "S1a", "status": "INCOMPLETE", "scope": "ACQUISITION_ONLY",
                "full_S1_readiness": "NOT_ASSESSED", "started_utc": helper.utcnow(), "output_dir": str(out),
                "sources": SOURCES, "objects": [], "source_head": [], "helper_expected_sha256": HELPER_SHA256,
                "runtime": {"python": sys.version, "executable": sys.executable, "platform": platform.platform()},
                "limits": {"body_bytes_including_prior": BODY_LIMIT, "prior_body_bytes": prior_body_bytes,
                           "wall_seconds": WALL_SECONDS, "minimum_free_bytes": MIN_FREE, "retries": 0,
                           "prospective_allocation": {"cpus": 1, "memory_bytes": 8 * 1024**3, "wall_seconds": WALL_SECONDS}}}
    old_handler = signal.getsignal(signal.SIGALRM)
    old_term_handler = signal.getsignal(signal.SIGTERM)
    previous_pending_signal, _pending_signal = _pending_signal, None
    try:
        write_new_json(out / "manifest.initial.json", manifest)
        signal.signal(signal.SIGALRM, wall_alarm)
        signal.signal(signal.SIGTERM, wall_alarm)
        signal.setitimer(signal.ITIMER_REAL, max(0.001, deadline-time.monotonic()))
        manifest["code_sha256"] = helper.sha256_file(Path(__file__))
        manifest["helper_current_sha256"] = helper.sha256_file(Path(helper.__file__))
        if manifest["helper_current_sha256"] != HELPER_SHA256:
            raise AcquisitionError("executed helper hash differs from the fixed helper")
        manifest["free_bytes_before_transfer"] = shutil.disk_usage(out).free
        if manifest["free_bytes_before_transfer"] < MIN_FREE:
            raise AcquisitionError("at least 160 GiB free space is required before transfer")
        if not ledger.can_fit(sum(meta["size_bytes"] for meta in SOURCES)):
            raise BudgetExceeded("both objects exceed remaining cumulative body-byte budget")
        opener = opener or helper.make_opener()
        for meta in SOURCES:
            check_deadline(deadline)
            manifest["source_head"].append(helper.source_head(meta["url"], meta["size_bytes"], meta["etag"], ledger, opener))
            check_deadline(deadline)
        for meta in SOURCES:
            manifest["objects"].append(download(meta, out, ledger, opener))
        check_deadline(deadline)
        manifest["status"] = "ACQUIRED"
    except BaseException as exc:
        manifest["error"] = f"{type(exc).__name__}: {exc}"
        ledger.event({"event": "stage_failed", "error": manifest["error"]})
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old_handler)
        signal.signal(signal.SIGTERM, old_term_handler)
        _pending_signal = previous_pending_signal
        manifest.update(finished_utc=helper.utcnow(), wall_seconds=time.monotonic()-started,
                        cpu_seconds=helper.cpu_seconds()-cpu_start, body_ledger=ledger.snapshot())
        manifest["peak_rss_bytes"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if sys.platform == "darwin" else 1024)
        ledger.close()
        write_new_json(out / "manifest.json", manifest)
    return manifest


def cli_output(path):
    if not path.is_absolute() or not re.fullmatch(r"hg002_dna_s1a_[A-Za-z0-9_-]{1,64}", path.name):
        raise AcquisitionError("output must be an absolute new hg002_dna_s1a_* scratch leaf")
    root = SCRATCH_EXPERIMENTS.resolve(strict=True)
    if root != SCRATCH_EXPERIMENTS or path.parent.resolve(strict=True) != root:
        raise AcquisitionError("output must be directly within the known project scratch experiments directory")
    if not root.is_dir() or not os.access(root, os.W_OK | os.X_OK):
        raise AcquisitionError("project scratch experiments directory is not writable")
    if path.exists() or path.is_symlink():
        raise AcquisitionError("output already exists")
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--prior-body-bytes", type=int, default=PRIOR_BYTES, help="May increase, never reduce, the cumulative prior charge")
    args = parser.parse_args()
    try:
        result = acquire(cli_output(args.output), prior_body_bytes=args.prior_body_bytes)
    except Exception as exc:
        result = {"stage": "S1a", "status": "INCOMPLETE", "error": str(exc)}
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "ACQUIRED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
