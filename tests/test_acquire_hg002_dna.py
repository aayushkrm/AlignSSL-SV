"""Synthetic HTTP objects only: no sockets, jobs, or external inputs."""
import hashlib
import http.client
import json
import signal
import sys
import time
import urllib.error
from pathlib import Path
from types import SimpleNamespace

import pytest
from scripts import acquire_hg002_dna as dna


class Response:
    def __init__(self, meta, *, head=False, body=b"", changes=None, status=None):
        self.status = status or (200 if head else 206)
        self.headers = {"Content-Length": str(meta["size_bytes"]), "ETag": meta["etag"],
                        "Content-Encoding": "identity"}
        if not head:
            self.headers["Content-Range"] = f"bytes 0-{meta['size_bytes']-1}/{meta['size_bytes']}"
        self.headers.update(changes or {})
        self.body, self.reads = body, []

    def __enter__(self): return self
    def __exit__(self, *_): pass
    def close(self): self.closed = True

    def read(self, amount):
        assert 0 < amount <= dna.CHUNK
        self.reads.append(amount)
        block, self.body = self.body[:amount], self.body[amount:]
        return block


@pytest.fixture(autouse=True)
def forbid_network(monkeypatch):
    def forbidden(): raise AssertionError("network opener must be mocked")
    monkeypatch.setattr(dna.helper, "make_opener", forbidden)
    monkeypatch.setattr(dna, "_pending_signal", None)


@pytest.fixture
def small(monkeypatch):
    bodies = [b"bam-data", b"index"]
    sources = tuple({**meta, "size_bytes": len(body)} for meta, body in zip(dna.SOURCES, bodies))
    monkeypatch.setattr(dna, "SOURCES", sources)
    monkeypatch.setattr(dna.shutil, "disk_usage", lambda _: SimpleNamespace(free=dna.MIN_FREE))
    return sources, bodies


@pytest.fixture
def ledger(tmp_path):
    value = dna.Ledger(tmp_path/"ledger.jsonl", time.monotonic()+60)
    yield value
    value.close()


def fake_opener(sources, bodies, *, get_changes=None, head_changes=None, short=False):
    calls, responses = [], []
    def open_response(request, timeout):
        assert timeout == 30
        meta = next(m for m in sources if m["url"] == request.full_url)
        head = request.get_method() == "HEAD"
        body = bodies[sources.index(meta)]
        if not head and (short is True or short == meta["name"]): body = body[:3]
        changes = head_changes if head else get_changes
        response = Response(meta, head=head, body=body, changes=changes)
        calls.append(request); responses.append(response)
        return response
    return open_response, calls, responses


def test_exact_source_pins():
    assert [m["size_bytes"] for m in dna.SOURCES] == [48_727_325_910, 21_582_928]
    assert [m["etag"] for m in dna.SOURCES] == ['"8c384718d3e41cbe000453b6846a7451-5809"', '"b45b35aa8fd900989a2798ed22faec3c-3"']
    root = "https://stergachis-manuscript-data.s3.us-west-1.amazonaws.com/2023/Vollger_et_al_long-read_multi-ome/"
    assert all(m["url"] == root+m["name"] for m in dna.SOURCES)
    assert (dna.BODY_LIMIT, dna.PRIOR_BYTES, dna.WALL_SECONDS) == (52*1024**3, 196608, 14400)
    assert dna.helper.sha256_file(Path(dna.helper.__file__)) == dna.HELPER_SHA256


def test_acquire_full_hashes_runtime_and_prior(tmp_path, small):
    sources, bodies = small; opener, calls, responses = fake_opener(sources, bodies)
    result = dna.acquire(tmp_path/"new", opener=opener)
    assert result["status"] == "ACQUIRED" and result["full_S1_readiness"] == "NOT_ASSESSED"
    assert result["stage"] == "S1a" and result["scope"] == "ACQUISITION_ONLY"
    assert [r["sha256"] for r in result["objects"]] == [hashlib.sha256(b).hexdigest() for b in bodies]
    assert result["body_ledger"]["total_body_bytes_including_prior"] == dna.PRIOR_BYTES+sum(map(len, bodies))
    assert result["source_head"] and result["helper_current_sha256"] == dna.HELPER_SHA256
    assert result["code_sha256"] == dna.helper.sha256_file(Path(dna.__file__))
    assert result["cpu_seconds"] >= 0 and result["wall_seconds"] >= 0 and result["runtime"]["python"]
    assert len(calls) == 4 and all(not r.reads for r in responses[:2])
    for req, meta in zip(calls, [*sources, *sources]):
        assert req.get_header("If-match") == meta["etag"] and req.get_header("Accept-encoding") == "identity"
        if req.get_method() == "GET": assert req.get_header("Range") == f"bytes=0-{meta['size_bytes']-1}"
    assert json.loads((tmp_path/"new/manifest.json").read_text())["status"] == "ACQUIRED"


@pytest.mark.parametrize("status,changes", [(200, {}), (206, {"ETag":"wrong"}), (206, {"Content-Range":"bytes 1-4/5"}),
    (206, {"Content-Length":"9"}), (206, {"Content-Encoding":"gzip"}), (302, {}), (206, {"Content-Range":"bytes 0-4/*"})])
def test_rejected_before_body_read(tmp_path, small, ledger, status, changes):
    meta = small[0][1]; response = Response(meta, body=b"index", status=status, changes=changes)
    with pytest.raises(dna.AcquisitionError): dna.download(meta, tmp_path, ledger, lambda *a, **k: response)
    assert response.reads == [] and ledger.used == 0
    assert (tmp_path/(meta["name"]+".partial")).read_bytes() == b""


@pytest.mark.parametrize("failed_index", [0, 1])
def test_early_eof_preserves_partial_log_and_manifest(tmp_path, small, failed_index):
    sources, bodies = small
    opener, calls, _ = fake_opener(*small, short=sources[failed_index]["name"])
    prior = dna.PRIOR_BYTES + 4096
    result = dna.acquire(tmp_path/"new", opener=opener, prior_body_bytes=prior)
    assert result["status"] == "INCOMPLETE" and len(calls) == 3+failed_index
    assert (tmp_path/"new"/(sources[failed_index]["name"]+".partial")).read_bytes() == bodies[failed_index][:3]
    used = sum(len(body) for body in bodies[:failed_index]) + 3
    assert result["body_ledger"]["new_upstream_body_bytes"] == used
    assert result["body_ledger"]["total_body_bytes_including_prior"] == prior+used
    assert [r["sha256"] for r in result["objects"]] == [hashlib.sha256(b).hexdigest() for b in bodies[:failed_index]]
    events = [json.loads(s) for s in (tmp_path/"new/body_ledger.jsonl").read_text().splitlines()]
    assert [e["actual_body_bytes"] for e in events if e["event"]=="body_read"] == [len(b) for b in bodies[:failed_index]] + [3, 0]
    saved = json.loads((tmp_path/"new/manifest.json").read_text())
    assert saved["body_ledger"] == result["body_ledger"] and saved["status"] == "INCOMPLETE"
    assert (tmp_path/"new/manifest.initial.json").is_file() and (tmp_path/"new/manifest.json").is_file()


def test_chunk_bound_and_flushed_journal(tmp_path, small, ledger):
    meta = {**small[0][0], "size_bytes": dna.CHUNK+2}; body = b"x"*meta["size_bytes"]
    response = Response(meta, body=body)
    result = dna.download(meta, tmp_path, ledger, lambda *a, **k: response)
    assert response.reads == [dna.CHUNK, 2] and result["sha256"] == hashlib.sha256(body).hexdigest()
    assert '"event":"body_read"' in (tmp_path/"ledger.jsonl").read_text()


def test_deadline_cap_and_reservation_underflow(ledger):
    key = ledger.begin("test", "mock", {})
    with pytest.raises(dna.AcquisitionError, match="underflow"): ledger.charge(key, 1, 0)
    ledger.deadline = time.monotonic()-1
    with pytest.raises(dna.BudgetExceeded, match="wall deadline"): ledger.reserve(1)
    ledger.deadline = time.monotonic()+60; ledger.used = ledger.limit-ledger.prior
    with pytest.raises(dna.BudgetExceeded, match="body-byte"): ledger.reserve(1)
    dna.wall_alarm()
    with pytest.raises(dna.BudgetExceeded, match="cancellation"): dna.check_deadline(time.monotonic()+60)


@pytest.mark.parametrize("prior", [0, 196607, dna.BODY_LIMIT, -1, True])
def test_prior_underflow_rejected(tmp_path, prior):
    with pytest.raises(dna.AcquisitionError): dna.acquire(tmp_path/"new", prior_body_bytes=prior)
    assert not (tmp_path/"new").exists()


def test_free_space_and_whole_transfer_budget_preflight(tmp_path, small, monkeypatch):
    opener, calls, _ = fake_opener(*small)
    monkeypatch.setattr(dna.shutil, "disk_usage", lambda _: SimpleNamespace(free=dna.MIN_FREE-1))
    assert "160 GiB" in dna.acquire(tmp_path/"disk", opener=opener)["error"] and not calls
    monkeypatch.setattr(dna.shutil, "disk_usage", lambda _: SimpleNamespace(free=dna.MIN_FREE))
    result = dna.acquire(tmp_path/"budget", opener=opener, prior_body_bytes=dna.BODY_LIMIT-1)
    assert "body-byte budget" in result["error"] and not calls


@pytest.mark.parametrize("changes", [{"ETag":"changed"}, {"Content-Length":"9"}, {"Content-Encoding":"gzip"}])
def test_source_head_failure_and_existing_output(tmp_path, small, changes):
    opener, calls, responses = fake_opener(*small, head_changes=changes)
    result = dna.acquire(tmp_path/"new", opener=opener)
    assert result["status"] == "INCOMPLETE" and len(calls) == 1 and not responses[0].reads
    saved = (tmp_path/"new/manifest.json").read_bytes()
    with pytest.raises(dna.AcquisitionError): dna.acquire(tmp_path/"new", opener=opener)
    assert (tmp_path/"new/manifest.json").read_bytes() == saved


def test_changed_helper_hash_stops_before_requests(tmp_path, small, monkeypatch):
    opener, calls, _ = fake_opener(*small)
    monkeypatch.setattr(dna, "HELPER_SHA256", "0"*64)
    result = dna.acquire(tmp_path/"new", opener=opener)
    assert result["status"] == "INCOMPLETE" and "helper hash" in result["error"] and not calls
    assert result["body_ledger"]["total_body_bytes_including_prior"] == dna.PRIOR_BYTES
    assert json.loads((tmp_path/"new/manifest.json").read_text())["helper_current_sha256"] != "0"*64


def test_cli_scratch_containment(tmp_path, monkeypatch):
    monkeypatch.setattr(dna, "SCRATCH_EXPERIMENTS", tmp_path)
    assert dna.cli_output(tmp_path/"hg002_dna_s1a_future") == tmp_path/"hg002_dna_s1a_future"
    for path in [tmp_path/"other", tmp_path.parent/"hg002_dna_s1a_escape", Path("hg002_dna_s1a_relative")]:
        with pytest.raises(dna.AcquisitionError): dna.cli_output(path)
    (tmp_path/"hg002_dna_s1a_link").symlink_to(tmp_path/"absent")
    with pytest.raises(dna.AcquisitionError): dna.cli_output(tmp_path/"hg002_dna_s1a_link")
    monkeypatch.setattr(dna.os, "access", lambda *_: False)
    with pytest.raises(dna.AcquisitionError, match="writable"): dna.cli_output(tmp_path/"hg002_dna_s1a_future")


def test_sigterm_preserves_manifest_and_restores_handler(tmp_path, small):
    previous = signal.getsignal(signal.SIGTERM)
    opener, _, _ = fake_opener(*small)
    def terminating(request, timeout):
        if request.get_method() == "GET":
            signal.raise_signal(signal.SIGTERM)
        return opener(request, timeout)
    result = dna.acquire(tmp_path/"term", opener=terminating)
    assert result["status"] == "INCOMPLETE"
    assert "cancellation" in result["error"]
    assert result["body_ledger"]["new_upstream_body_bytes"] == 0
    assert (tmp_path/"term/manifest.json").is_file()
    assert signal.getsignal(signal.SIGTERM) == previous


@pytest.mark.parametrize("signum", [signal.SIGTERM, signal.SIGALRM])
def test_cancel_between_read_return_and_charge_is_accounted(tmp_path, small, signum):
    target = next(i for i, line in enumerate(Path(dna.__file__).read_text().splitlines(), 1)
                  if 'ledger.charge(key, grant, len(block))' in line)
    fired = []
    def trace(frame, event, arg):
        if frame.f_code is dna.download.__code__ and event == "line" and frame.f_lineno == target and not fired:
            fired.append(True)
            signal.raise_signal(signum)
        return trace
    prior_trace = sys.gettrace()
    try:
        sys.settrace(trace)
        opener, _, _ = fake_opener(*small)
        result = dna.acquire(tmp_path/"boundary", opener=opener)
    finally:
        sys.settrace(prior_trace)
    assert fired and result["status"] == "INCOMPLETE"
    assert result["body_ledger"]["new_upstream_body_bytes"] == len(small[1][0])
    assert (tmp_path/"boundary"/(small[0][0]["name"]+".partial")).read_bytes() == small[1][0]
    events = [json.loads(s) for s in (tmp_path/"boundary/body_ledger.jsonl").read_text().splitlines()]
    assert sum(e["actual_body_bytes"] for e in events if e["event"] == "body_read") == len(small[1][0])


@pytest.mark.parametrize("failure", ["deadline", "partial", "http"])
def test_failed_reads_and_error_bodies_are_accounted(tmp_path, small, ledger, failure):
    meta = small[0][0]
    error_body = Response(meta, body=b"error")
    def failed_read(amount):
        if failure == "deadline":
            dna.wall_alarm()
            return b"bam"
        raise http.client.IncompleteRead(b"bam", meta["size_bytes"]-3)
    response = Response(meta); response.read = failed_read
    def opener(*a, **k):
        if failure == "http":
            raise urllib.error.HTTPError(meta["url"], 302, "redirect", response.headers, error_body)
        return response
    with pytest.raises((dna.AcquisitionError, http.client.IncompleteRead)): dna.download(meta, tmp_path, ledger, opener)
    assert ledger.used == (3 if failure in ("partial", "deadline") else 0) and not error_body.reads
    if failure == "http": assert error_body.closed
    assert (tmp_path/(meta["name"]+".partial")).read_bytes() == (b"bam" if failure in ("partial", "deadline") else b"")


def test_cancellation_in_partial_exception_preserves_bytes(tmp_path, small, ledger):
    def read(amount):
        dna.wall_alarm(signal.SIGTERM)
        raise http.client.IncompleteRead(b"bam", 5)
    response = Response(small[0][0]); response.read = read
    with pytest.raises(dna.BudgetExceeded, match="cancellation"):
        dna.download(small[0][0], tmp_path, ledger, lambda *a, **k: response)
    assert ledger.used == 3
    assert (tmp_path/(small[0][0]["name"]+".partial")).read_bytes() == b"bam"


def test_hash_honors_deferred_cancellation(tmp_path):
    path = tmp_path/"bytes"; path.write_bytes(b"data")
    dna.wall_alarm(signal.SIGTERM)
    with pytest.raises(dna.BudgetExceeded, match="cancellation"):
        dna.bounded_hash(path, time.monotonic()+60)
