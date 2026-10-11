import hashlib
import json

import pytest

from scripts.check_hg002_intake_custody import verify


def fixture(tmp_path):
    objects = []
    for name, body in (("dna.bam", b"synthetic"), ("dna.bai", b"index")):
        (tmp_path/name).write_bytes(body)
        objects.append({"path": "/original/"+name, "size_bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()})
    manifest = {"stage": "S1a", "status": "ACQUIRED", "objects": objects}
    (tmp_path/"manifest.json").write_text(json.dumps(manifest))
    return manifest


def test_retained_copy_hashes(tmp_path):
    manifest = fixture(tmp_path)
    assert verify(tmp_path)["objects"][0]["sha256"] == manifest["objects"][0]["sha256"]


@pytest.mark.parametrize("fault", ["status", "size", "hash", "duplicate", "missing"])
def test_custody_failure_stops(tmp_path, fault):
    manifest = fixture(tmp_path)
    if fault == "status": manifest["status"] = "INCOMPLETE"
    if fault == "size": manifest["objects"][0]["size_bytes"] += 1
    if fault == "hash": (tmp_path/"dna.bam").write_bytes(b"different")
    if fault == "duplicate": manifest["objects"][1] = manifest["objects"][0]
    if fault == "missing": (tmp_path/"dna.bai").unlink()
    (tmp_path/"manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError): verify(tmp_path)
