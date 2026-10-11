import hashlib
import json
import signal
from types import SimpleNamespace

import pytest

from scripts import stage_hg002_gencode as reference
from tests.test_acquire_hg002_dna import Response


@pytest.fixture
def setup(monkeypatch):
    bodies = [b"reference", b"annotation"]
    files = tuple((f"file{i}.gz", len(b), hashlib.md5(b).hexdigest()) for i, b in enumerate(bodies))
    monkeypatch.setattr(reference, "FILES", files)
    monkeypatch.setattr(reference.shutil, "disk_usage", lambda _: SimpleNamespace(free=reference.MIN_FREE))
    monkeypatch.setattr(reference.helper, "make_opener", lambda: pytest.fail("no external network"))
    calls, responses = [], []
    def opener(req, timeout):
        index = next(i for i, x in enumerate(files) if req.full_url.endswith(x[0]))
        name, size, _ = files[index]
        obj = Response({"size_bytes": size, "etag": '"pin"'}, head=req.get_method()=="HEAD", body=bodies[index])
        calls.append(req); responses.append(obj)
        return obj
    return files, bodies, opener, calls, responses


def test_verified_reference_only_stage(tmp_path, setup):
    files, bodies, opener, calls, _ = setup
    result = reference.stage(tmp_path/"new", opener=opener)
    assert result["status"] == "STAGED_CHECKSUM_VERIFIED"
    assert result["body_ledger"]["new_upstream_body_bytes"] == sum(map(len, bodies))
    assert result["body_ledger"]["prior_body_bytes"] == 0
    assert [a["actual_md5"] for a in result["objects"]] == [x[2] for x in files]
    assert len(calls) == 4 and all(reference.ROOT in r.full_url for r in calls)
    assert json.loads((tmp_path/"new/manifest.json").read_text())["status"] == result["status"]
    with pytest.raises(reference.helper.AcquisitionError): reference.stage(tmp_path/"new", opener=opener)


@pytest.mark.parametrize("fault", ["checksum", "size", "encoding", "low_space"])
def test_failures_never_qualify(tmp_path, setup, monkeypatch, fault):
    files, _, opener, calls, responses = setup
    if fault == "checksum": monkeypatch.setattr(reference, "FILES", ((files[0][0], files[0][1], "0"*32), files[1]))
    if fault == "low_space": monkeypatch.setattr(reference.shutil, "disk_usage", lambda _: SimpleNamespace(free=0))
    def bad(req, timeout):
        response = opener(req, timeout)
        if req.get_method() == "HEAD":
            if fault == "size": response.headers["Content-Length"] = "0"
            if fault == "encoding": response.headers["Content-Encoding"] = "gzip"
        return response
    result = reference.stage(tmp_path/"bad", opener=bad)
    assert result["status"] == "INCOMPLETE"
    if fault in ("size", "encoding", "low_space"):
        assert not any(r.reads for r in responses)
    assert (tmp_path/"bad/manifest.json").is_file()


def test_cancellation_retains_returned_reference_bytes(tmp_path, setup):
    _, bodies, opener, _, _ = setup
    def cancelled(req, timeout):
        response = opener(req, timeout)
        if req.get_method() == "GET":
            original = response.read
            def read(amount):
                block = original(amount)
                signal.raise_signal(signal.SIGTERM)
                return block
            response.read = read
        return response
    result = reference.stage(tmp_path/"cancel", opener=cancelled)
    assert result["status"] == "INCOMPLETE"
    assert result["body_ledger"]["new_upstream_body_bytes"] == len(bodies[0])


def test_full_published_asset_pins():
    assert sum(x[1] for x in reference.FILES) == 1_152_186_383
    assert len(reference.FILES) == 5
    assert reference.FILES[0][2] == "da1a11258be075cfa7af718162c894e7"
    assert reference.LIMIT == 2 * 1024**3
