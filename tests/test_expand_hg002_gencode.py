import gzip
import hashlib
import json
import signal
from types import SimpleNamespace

import pytest
from scripts import expand_hg002_gencode as tool


def fixture(tmp_path, monkeypatch):
    source = tmp_path/"source"; source.mkdir()
    objects = []
    for name in sorted(tool.NAMES):
        body = gzip.compress(b"synthetic reference\n", mtime=0)
        (source/name).write_bytes(body)
        objects.append({"path": "/original/"+name, "size_bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()})
    (source/"manifest.json").write_text(json.dumps({"status": "STAGED_CHECKSUM_VERIFIED", "objects": objects}))
    monkeypatch.setattr(tool.shutil, "disk_usage", lambda _: SimpleNamespace(free=32*1024**3))
    return source


def test_whole_fixed_reference_expansion(tmp_path, monkeypatch):
    source = fixture(tmp_path, monkeypatch)
    result = tool.expand(source, tmp_path/"new")
    assert result["status"] == "EXPANDED_CRC_VERIFIED" and len(result["objects"]) == 5
    for obj in result["objects"]:
        body = (tmp_path/"new"/obj["name"]).read_bytes()
        assert hashlib.sha256(body).hexdigest() == obj["sha256"]
    with pytest.raises(ValueError): tool.expand(source, tmp_path/"new")


@pytest.mark.parametrize("fault", ["hash", "missing", "gzip", "space", "cap", "cancel"])
def test_faults_preserve_incomplete(tmp_path, monkeypatch, fault):
    source = fixture(tmp_path, monkeypatch)
    path = source/sorted(tool.NAMES)[0]
    if fault == "hash": path.write_bytes(b"wrong")
    if fault == "missing": path.unlink()
    if fault == "gzip":
        body = path.read_bytes()[:-8]; path.write_bytes(body)
        manifest = json.loads((source/"manifest.json").read_text())
        manifest["objects"][0].update(size_bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
        (source/"manifest.json").write_text(json.dumps(manifest))
    if fault == "space": monkeypatch.setattr(tool.shutil, "disk_usage", lambda _: SimpleNamespace(free=0))
    if fault == "cap": monkeypatch.setattr(tool, "PAYLOAD_CAP", 1)
    if fault == "cancel":
        original = tool.gzip.open
        def cancelled(*args, **kwargs):
            signal.raise_signal(signal.SIGTERM); return original(*args, **kwargs)
        monkeypatch.setattr(tool.gzip, "open", cancelled)
    result = tool.expand(source, tmp_path/"bad")
    assert result["status"] == "INCOMPLETE"
    assert json.loads((tmp_path/"bad/manifest.json").read_text()) == result
