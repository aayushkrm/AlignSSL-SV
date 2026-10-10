#!/usr/bin/env python3
"""Fetch the frozen NA12878 CHM13 region through a byte-capped HTTP range proxy."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import resource
import secrets
import subprocess
import threading
import time
import urllib.error
import urllib.request
from contextlib import contextmanager
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Optional
from urllib.parse import urlsplit

BAM_URL = "https://platinum-pedigree-data.s3.amazonaws.com/data/hifi/mapped/CHM13/NA12878.CHM13.haplotagged.bam"
BAI_URL = BAM_URL + ".bai"
BAM_SIZE, BAI_SIZE = 203_640_216_494, 37_783_472
BAM_ETAG = '"1b4553743c325a8ca9a6d105c0a437eb-6069"'
BAI_ETAG = '"b8da14c8fd291ee149b361f62d168b56-5"'
BODY_LIMIT, PRIOR_BYTES = 4 * 1024**3, 65_536
WALL_SECONDS, CHUNK, MAX_RANGE = 600, 65536, 64 * 1024**2
BUFFER_BED = "chr3\t71539909\t71643317\n"
CORE_BED = "chr3\t71579909\t71603317\n"
REGION, CHR3_LENGTH = "chr3:71539910-71643317", 201_105_948
CONTENT_RANGE = re.compile(r"bytes ([0-9]+)-([0-9]+)/([0-9]+)")


class AcquisitionError(RuntimeError):
    pass


class BudgetExceeded(AcquisitionError):
    pass


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def cpu_seconds() -> float:
    own = resource.getrusage(resource.RUSAGE_SELF)
    children = resource.getrusage(resource.RUSAGE_CHILDREN)
    return own.ru_utime + own.ru_stime + children.ru_utime + children.ru_stime


def h(headers, name: str) -> str:
    value = headers.get(name)
    return "" if value is None else str(value).strip()


def http_status(response) -> int:
    return int(getattr(response, "status", None) or response.getcode())


def parse_range(value: str, size: int) -> tuple[int, int]:
    match = re.fullmatch(r"bytes=([0-9]+)-([0-9]*)", value.strip())
    if not match:
        raise AcquisitionError("one explicit-start byte range is required")
    start = int(match.group(1))
    end = min(int(match.group(2)) if match.group(2) else size - 1, size - 1)
    if start >= size or end < start:
        raise AcquisitionError("range is outside the source object")
    # HTSlib uses open-ended logical streams and closes them when it seeks.
    # Their actual body reads are capped globally, not prepaid as whole files.
    if match.group(2) and end - start + 1 > MAX_RANGE:
        raise AcquisitionError("explicit bounded range exceeds 64 MiB")
    return start, end


class BodyLedger:
    """Flush an event for every upstream response-body read; reserve globally across threads."""

    def __init__(self, path: Path, deadline: float, *, limit=BODY_LIMIT, prior=PRIOR_BYTES):
        self.file, self.lock = path.open("x", encoding="utf-8"), threading.Lock()
        self.deadline, self.limit, self.prior = deadline, limit, prior
        self.used = self.reserved = self.local_bai_bytes = self.serial = 0
        self.attempts: list[dict] = []

    def _write(self, row: dict) -> None:
        self.file.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
        self.file.flush()

    def event(self, row: dict) -> None:
        with self.lock:
            self._write(row)

    def begin(self, kind: str, url: str, request_headers: dict[str, str]) -> int:
        with self.lock:
            self.serial += 1
            row = {"attempt": self.serial, "kind": kind, "url": url,
                   "request_headers": request_headers, "response_status": None,
                   "response_headers": {}, "actual_body_bytes": 0,
                   "started_utc": utcnow(), "outcome": "in_flight"}
            self.attempts.append(row)
            self._write({"event": "attempt_start", **row})
            return self.serial

    def _row(self, key: int) -> dict:
        return self.attempts[key - 1]

    def headers(self, key: int, response) -> None:
        names = ("Content-Length", "Content-Range", "Content-Encoding", "ETag", "Accept-Ranges")
        values = {name: h(response.headers, name) for name in names}
        with self.lock:
            row = self._row(key)
            row["response_status"], row["response_headers"] = http_status(response), values
            self._write({"event": "response_headers", "attempt": key,
                         "status": row["response_status"], "headers": values})

    def can_fit(self, amount: int) -> bool:
        with self.lock:
            return amount <= self.limit - self.prior - self.used - self.reserved

    def reserve(self, amount: int) -> int:
        with self.lock:
            if time.monotonic() >= self.deadline:
                raise BudgetExceeded("10-minute wall limit reached")
            available = self.limit - self.prior - self.used - self.reserved
            if available <= 0:
                raise BudgetExceeded("4 GiB upstream-body limit reached")
            grant = min(amount, available)
            self.reserved += grant
            return grant

    def release(self, grant: int) -> None:
        with self.lock:
            self.reserved -= grant

    def charge(self, key: int, grant: int, actual: int) -> None:
        with self.lock:
            self.reserved -= grant
            self.used += actual
            row = self._row(key)
            row["actual_body_bytes"] += actual
            self._write({"event": "body_read", "attempt": key, "actual_body_bytes": actual,
                         "attempt_total": row["actual_body_bytes"], "upstream_total": self.used,
                         "total_including_prior": self.prior + self.used})

    def finish(self, key: int, outcome: str, error: Optional[str] = None) -> None:
        with self.lock:
            row = self._row(key)
            row.update(outcome=outcome, error=error, finished_utc=utcnow())
            self._write({"event": "attempt_end", "attempt": key, "outcome": outcome,
                         "error": error, "actual_body_bytes": row["actual_body_bytes"]})

    def snapshot(self) -> dict:
        with self.lock:
            return {"measurement": "bytes returned by upstream HTTP response.read; excludes headers and TLS",
                    "limit_including_prior_body": self.limit, "prior_body_bytes": self.prior,
                    "new_upstream_body_bytes": self.used,
                    "total_body_bytes_including_prior": self.prior + self.used,
                    "remaining_bytes": self.limit - self.prior - self.used,
                    "loopback_bai_bytes_served_separately": self.local_bai_bytes,
                    "attempts": self.attempts}

    def close(self) -> None:
        with self.lock:
            self.file.flush()
            self.file.close()


def copy_counted(response, sink, ledger: BodyLedger, key: int, length: int) -> int:
    total = 0
    while total < length:
        grant = ledger.reserve(min(CHUNK, length - total))
        try:
            block = response.read(grant)
        except BaseException:
            ledger.release(grant)
            raise
        ledger.charge(key, grant, len(block))
        if not block:
            raise AcquisitionError("upstream body ended before Content-Length")
        sink.write(block)
        total += len(block)
    return total


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def make_opener():
    return urllib.request.build_opener(NoRedirect()).open


def check_identity(headers) -> None:
    if h(headers, "Content-Encoding").lower() not in ("", "identity"):
        raise AcquisitionError("encoded response is not supported")


def source_head(url: str, size: int, etag: str, ledger: BodyLedger, opener) -> dict:
    req_headers = {"Accept-Encoding": "identity", "If-Match": etag}
    key = ledger.begin("metadata_head", url, req_headers)
    try:
        with opener(urllib.request.Request(url, headers=req_headers, method="HEAD"), timeout=30) as r:
            ledger.headers(key, r)
            found = h(r.headers, "ETag")
            check_identity(r.headers)
            if http_status(r) != 200 or h(r.headers, "Content-Length") != str(size) or found != etag:
                raise AcquisitionError("HEAD size/status/ETag failed the frozen source check")
        ledger.finish(key, "verified")
        return {"url": url, "size_bytes": size, "etag": etag}
    except urllib.error.HTTPError as exc:
        ledger.headers(key, exc)
        ledger.finish(key, "rejected", f"HTTP {exc.code}")
        exc.close()
        raise AcquisitionError(f"source HEAD returned HTTP {exc.code}") from exc
    except Exception as exc:
        ledger.finish(key, "rejected", str(exc))
        raise


def validate_206(r, start: int, end: int, size: int, etag: str) -> int:
    length = end - start + 1
    cr = CONTENT_RANGE.fullmatch(h(r.headers, "Content-Range"))
    if http_status(r) != 206:
        raise AcquisitionError("upstream did not return 206; full-body fallback is forbidden")
    check_identity(r.headers)
    if not cr or tuple(map(int, cr.groups())) != (start, end, size):
        raise AcquisitionError("upstream Content-Range differs from requested range")
    if h(r.headers, "Content-Length") != str(length):
        raise AcquisitionError("upstream Content-Length differs from range length")
    if h(r.headers, "ETag") != etag:
        raise AcquisitionError("upstream ETag differs from pinned ETag")
    return length


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(4 * 1024**2), b""):
            digest.update(block)
    return digest.hexdigest()


def download_bai(meta: dict, path: Path, ledger: BodyLedger, opener) -> dict:
    end = meta["size_bytes"] - 1
    headers = {"Range": f"bytes=0-{end}", "If-Match": meta["etag"], "Accept-Encoding": "identity"}
    key = ledger.begin("bai_download", meta["url"], headers)
    partial = path.with_suffix(path.suffix + ".partial")
    partial.touch(exist_ok=True)
    try:
        if not ledger.can_fit(end + 1):
            raise BudgetExceeded("BAI exceeds remaining body budget")
        with opener(urllib.request.Request(meta["url"], headers=headers), timeout=30) as r:
            ledger.headers(key, r)
            length = validate_206(r, 0, end, meta["size_bytes"], meta["etag"])
            with partial.open("wb") as out:
                copy_counted(r, out, ledger, key, length)
        os.replace(partial, path)
        result = {"path": str(path), "size_bytes": path.stat().st_size, "sha256": sha256_file(path)}
        ledger.finish(key, "verified")
        return result
    except urllib.error.HTTPError as exc:
        ledger.headers(key, exc)
        ledger.finish(key, "rejected", f"HTTP {exc.code}")
        exc.close()
        raise AcquisitionError(f"BAI request returned HTTP {exc.code}") from exc
    except Exception as exc:
        ledger.finish(key, "incomplete", str(exc))
        raise


class ProxyHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"

    def log_message(self, *_):
        pass

    def empty(self, code: int, headers: Optional[dict] = None) -> None:
        self.send_response(code)
        self.send_header("Content-Length", "0")
        self.send_header("Connection", "close")
        for name, value in (headers or {}).items():
            self.send_header(name, value)
        self.end_headers()
        self.close_connection = True

    def route(self):
        path = urlsplit(self.path).path
        return "bam" if path == self.server.bam_path else ("bai" if path in self.server.bai_paths else None)

    def do_HEAD(self):
        kind = self.route()
        if not kind:
            self.empty(404)
            return
        meta = self.server.bam_meta if kind == "bam" else self.server.bai_meta
        self.send_response(200)
        self.send_header("Content-Length", str(meta["size_bytes"]))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("ETag", meta["etag"])
        self.end_headers()

    def do_GET(self):
        kind = self.route()
        if kind == "bai":
            self.serve_bai()
        elif kind == "bam":
            self.serve_range()
        else:
            self.empty(404)

    def serve_bai(self):
        meta, path = self.server.bai_meta, self.server.bai_path
        value = self.headers.get("Range", "")
        try:
            start, end = parse_range(value, meta["size_bytes"]) if value else (0, meta["size_bytes"] - 1)
        except AcquisitionError:
            self.empty(416, {"Content-Range": f"bytes */{meta['size_bytes']}"})
            return
        length = end - start + 1
        self.send_response(206 if value else 200)
        self.send_header("Content-Length", str(length))
        self.send_header("ETag", meta["etag"])
        self.send_header("Accept-Ranges", "bytes")
        if value:
            self.send_header("Content-Range", f"bytes {start}-{end}/{meta['size_bytes']}")
        self.end_headers()
        sent = 0
        try:
            with path.open("rb") as f:
                f.seek(start)
                while sent < length:
                    block = f.read(min(CHUNK, length - sent))
                    if not block:
                        raise AcquisitionError("local BAI ended before its declared length")
                    self.wfile.write(block)
                    sent += len(block)
        except (BrokenPipeError, ConnectionResetError):
            self.close_connection = True
        finally:
            with self.server.ledger.lock:
                self.server.ledger.local_bai_bytes += sent

    def serve_range(self):
        ledger, meta = self.server.ledger, self.server.bam_meta
        value = self.headers.get("Range", "")
        try:
            start, end = parse_range(value or "bytes=0-", meta["size_bytes"])
        except AcquisitionError as exc:
            ledger.event({"event": "range_rejected", "range": value, "reason": str(exc)})
            self.empty(416, {"Content-Range": f"bytes */{meta['size_bytes']}"})
            return
        length = end - start + 1
        req_headers = {"Range": f"bytes={start}-{end}", "If-Match": meta["etag"],
                       "Accept-Encoding": "identity"}
        if not ledger.can_fit(min(CHUNK, length)):
            ledger.event({"event": "range_budget_rejected", "range": req_headers["Range"]})
            self.empty(509)
            return
        key = ledger.begin("bam_range", BAM_URL, req_headers)
        req = urllib.request.Request(BAM_URL, headers=req_headers)
        sent_headers = False
        try:
            with self.server.opener(req, timeout=30) as r:
                ledger.headers(key, r)
                length = validate_206(r, start, end, meta["size_bytes"], meta["etag"])
                self.send_response(206 if value else 200)
                self.send_header("Content-Length", h(r.headers, "Content-Length"))
                if value:
                    self.send_header("Content-Range", h(r.headers, "Content-Range"))
                self.send_header("Accept-Ranges", "bytes")
                self.send_header("ETag", h(r.headers, "ETag"))
                self.end_headers()
                sent_headers = True
                copy_counted(r, self.wfile, ledger, key, length)
            ledger.finish(key, "verified")
        except (BrokenPipeError, ConnectionResetError) as exc:
            ledger.finish(key, "client_closed_partial_stream", str(exc))
            self.close_connection = True
        except urllib.error.HTTPError as exc:
            ledger.headers(key, exc)
            ledger.finish(key, "rejected", f"HTTP {exc.code}")
            exc.close()
            if not sent_headers:
                self.empty(502)
        except Exception as exc:
            ledger.finish(key, "incomplete", str(exc))
            if sent_headers:
                self.close_connection = True
            else:
                self.empty(509 if isinstance(exc, BudgetExceeded) else 502)


class ProxyServer(ThreadingHTTPServer):
    daemon_threads = False
    block_on_close = True


@contextmanager
def running_proxy(bam_meta: dict, bai_meta: dict, bai_path: Path, ledger: BodyLedger, opener):
    token = secrets.token_urlsafe(18)
    bam_path = f"/{token}/NA12878.CHM13.haplotagged.bam"
    server = ProxyServer(("127.0.0.1", 0), ProxyHandler)
    server.bam_meta, server.bai_meta, server.bai_path = bam_meta, bai_meta, bai_path
    server.ledger, server.opener, server.bam_path = ledger, opener, bam_path
    server.bai_paths = {bam_path + ".bai", bam_path.removesuffix(".bam") + ".bai"}
    thread = threading.Thread(target=server.serve_forever, name="range-proxy")
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}{bam_path}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def run_samtools(exe: Path, args: list[str], out: Path, name: str,
                 commands: list[dict], deadline: float, stdout_name: Optional[str] = None) -> str:
    argv = [str(exe), *args]
    stdout_path = out / (stdout_name or f"samtools-{name}.stdout.log")
    stderr_path = out / f"samtools-{name}.stderr.log"
    started, before = utcnow(), time.monotonic()
    try:
        with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
            result = subprocess.run(argv, stdout=stdout, stderr=stderr, check=False, cwd=out,
                                    timeout=max(0.1, deadline - time.monotonic()))
    except subprocess.TimeoutExpired as exc:
        commands.append({"argv": argv, "started_utc": started, "finished_utc": utcnow(),
                         "outcome": "wall_timeout", "stdout": str(stdout_path), "stderr": str(stderr_path)})
        raise AcquisitionError(f"samtools {name} reached the 10-minute wall limit") from exc
    commands.append({"argv": argv, "started_utc": started, "finished_utc": utcnow(),
                     "returncode": result.returncode, "wall_seconds": time.monotonic() - before,
                     "stdout": str(stdout_path), "stderr": str(stderr_path)})
    if result.returncode:
        raise AcquisitionError(f"samtools {name} exited with status {result.returncode}")
    return stdout_path.read_text(encoding="utf-8", errors="replace")


def write_json(path: Path, value: dict) -> None:
    temp = path.with_suffix(".json.tmp")
    temp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temp, path)


def acquire(output: Path, samtools_arg: Path, *, opener=None,
            prior_body_bytes=PRIOR_BYTES) -> dict:
    if not isinstance(prior_body_bytes, int) or not PRIOR_BYTES <= prior_body_bytes < BODY_LIMIT:
        raise AcquisitionError("prior-body charge must include prefix and be below the fixed cap")
    target = output if output.is_absolute() else Path.cwd() / output
    if target.exists() or target.is_symlink() or not target.parent.is_dir():
        raise AcquisitionError("--output must be a new directory under an existing parent")
    target.mkdir(mode=0o700)
    out = target.resolve()
    deadline, started = time.monotonic() + WALL_SECONDS, utcnow()
    manifest_path = out / "acquisition.json"
    ledger = BodyLedger(out / "body_ledger.jsonl", deadline, prior=prior_body_bytes)
    cpu_start = cpu_seconds()
    commands: list[dict] = []
    manifest = {"status": "INCOMPLETE", "started_utc": started, "output_dir": str(out),
                "regional_bam": str(out / "regional.bam"), "regional_bam_basename": "regional.bam",
                "regional_bai": str(out / "regional.bam.bai"),
                "body_ledger_jsonl": str(out / "body_ledger.jsonl"),
                "source": {"bam_url": BAM_URL, "bam_size_bytes": BAM_SIZE, "bam_etag": BAM_ETAG,
                           "bai_url": BAI_URL, "bai_size_bytes": BAI_SIZE, "bai_etag": BAI_ETAG},
                "buffer_bed": BUFFER_BED, "core_bed": CORE_BED, "samtools_commands": commands,
                "limits": {"upstream_body_bytes_including_prior_prefix": BODY_LIMIT,
                           "prior_body_bytes": prior_body_bytes, "wall_seconds": WALL_SECONDS,
                           "max_explicit_bounded_bam_range_bytes": MAX_RANGE,
                           "open_streams_charge_each_actual_body_read": True,
                           "samtools_extra_threads": 0,
                           "expected_slurm_allocation": {"cpus": 3, "memory_bytes": 4 * 1024**3,
                                                          "wall_seconds": 600,
                                                          "cpu_seconds_cap": 1800}}}
    write_json(manifest_path, manifest)
    try:
        if not samtools_arg.is_absolute():
            raise AcquisitionError("--samtools must be an absolute path")
        exe = samtools_arg.resolve(strict=True)
        if not exe.is_file() or not os.access(exe, os.X_OK):
            raise AcquisitionError("--samtools is not executable")
        opener = opener or make_opener()
        manifest["samtools_path"] = str(exe)
        version = run_samtools(exe, ["--version"], out, "version", commands, deadline)
        if not version.splitlines() or version.splitlines()[0].strip() != "samtools 1.9":
            raise AcquisitionError("samtools 1.9 is required")
        manifest["samtools_version"] = "samtools 1.9"
        bam = source_head(BAM_URL, BAM_SIZE, BAM_ETAG, ledger, opener)
        bai = source_head(BAI_URL, BAI_SIZE, BAI_ETAG, ledger, opener)
        manifest["source_head"] = {"bam": bam, "bai": bai}
        source_bai = out / "source.bam.bai"
        manifest["source_bai"] = download_bai(bai, source_bai, ledger, opener)
        (out / "buffer.bed").write_text(BUFFER_BED, encoding="ascii")
        (out / "core.bed").write_text(CORE_BED, encoding="ascii")
        with running_proxy(bam, bai, source_bai, ledger, opener) as remote:
            run_samtools(exe, ["view", "-b", "-h", "-o", str(out / "regional.bam"),
                               remote, REGION], out, "regional-view", commands, deadline)
        if not (out / "regional.bam").is_file() or not (out / "regional.bam").stat().st_size:
            raise AcquisitionError("samtools did not create a nonempty regional BAM")
        if ledger.local_bai_bytes == 0:
            raise AcquisitionError("samtools did not read the pinned local BAI")
        run_samtools(exe, ["quickcheck", "-v", str(out / "regional.bam")],
                     out, "quickcheck", commands, deadline)
        run_samtools(exe, ["index", str(out / "regional.bam"), str(out / "regional.bam.bai")],
                     out, "index", commands, deadline)
        if not (out / "regional.bam.bai").is_file() or not (out / "regional.bam.bai").stat().st_size:
            raise AcquisitionError("samtools did not create the regional BAI")
        header = run_samtools(exe, ["view", "-H", str(out / "regional.bam")],
                              out, "header", commands, deadline, "regional.header.sam")
        sq = [line for line in header.splitlines() if line.startswith("@SQ\t")]
        rg = [line for line in header.splitlines() if line.startswith("@RG\t")]
        if not any(f"\tSN:chr3\t" in line and f"\tLN:{CHR3_LENGTH}" in line for line in sq):
            raise AcquisitionError("regional BAM header lacks chr3 length 201105948")
        if not rg or not all("\tSM:NA12878" in line for line in rg):
            raise AcquisitionError("regional BAM read groups do not all identify NA12878")
        manifest.update(status="COMPLETE", regional_header_validated=True,
                        outcome="Regional extraction complete; no caller or census was run.",
                        scope_limit="Supplementary alignments outside the buffer were not searched.")
    except Exception as exc:
        manifest.update(status="INCOMPLETE", error=f"{type(exc).__name__}: {exc}",
                        outcome="Partial artifacts retained; no whole-BAM fallback.")
    finally:
        manifest["finished_utc"] = utcnow()
        manifest["wall_seconds"] = WALL_SECONDS - max(0.0, deadline - time.monotonic())
        manifest["cpu_seconds"] = round(cpu_seconds() - cpu_start, 3)
        manifest["body_ledger"] = ledger.snapshot()
        ledger.close()
        paths = ("source.bam.bai", "source.bam.bai.partial", "regional.bam", "regional.bam.bai",
                 "regional.header.sam", "buffer.bed", "core.bed", "body_ledger.jsonl")
        manifest["artifacts"] = {name: {"size_bytes": (out / name).stat().st_size,
                                         "sha256": sha256_file(out / name)}
                                 for name in paths if (out / name).is_file()}
        write_json(manifest_path, manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samtools", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--prior-body-bytes", type=int, default=PRIOR_BYTES,
                        help="Cumulative body bytes from previous attempts, including header prefix")
    args = parser.parse_args()
    try:
        result = acquire(args.output, args.samtools, prior_body_bytes=args.prior_body_bytes)
    except Exception as exc:
        result = {"status": "INCOMPLETE", "error": f"{type(exc).__name__}: {exc}"}
    print(json.dumps({"status": result["status"], "output_dir": result.get("output_dir"),
                      "regional_bam": result.get("regional_bam"),
                      "regional_bai": result.get("regional_bai"),
                      "acquisition_json": str(Path(result.get("output_dir", args.output)) / "acquisition.json"),
                      "total_body_bytes": result.get("body_ledger", {}).get("total_body_bytes_including_prior"),
                      "error": result.get("error")}, sort_keys=True))
    return 0 if result["status"] == "COMPLETE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
