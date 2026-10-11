"""Protocol-only synthetic checks; no real source or record bytes are read."""
import hashlib
import json

import pytest

from analysis import stage_svpg_callsets as stage


def protocol():
    return {
        "body_read_approved": True,
        "independent_outcome_approval": "synthetic-final-review",
        "header_protocol": {
            "members": list(stage.MEMBERS), "expected_archive_bytes": 1,
            "expected_archive_md5": "0" * 32, "verified_archive_sha256": "0" * 64,
        },
        "source_pass_amendment": "remaining-five-large-record-v1",
        "max_source_decoded_bytes": 4 * 1024**3,
        "max_line_bytes": 128 * 1024**2,
        "charged_prior_source_decoded_bytes": 3_087_320_050,
        "charged_prior_global_decoded_bytes": 3_116_730_525,
        "global_decoded_limit_bytes": 12 * 1024**3,
        "controller_traffic_account": "synthetic-final-reservation",
        "raw_line_policy": "stream_rnames",
        "execution_callers": list(stage.CALLERS[1:]),
        "reused_completed_callers": {"cutesv": {}},
    }


def parse(tmp_path, value):
    raw = json.dumps(value).encode()
    path = tmp_path / "synthetic-protocol.json"
    path.write_bytes(raw)
    return stage._protocol(path, hashlib.sha256(raw).hexdigest())


def test_final_amendment_accepts_only_explicit_larger_engineering_limits(tmp_path):
    _, budget, line_cap, _, _, value = parse(tmp_path, protocol())
    assert budget == [3_087_320_050, 4 * 1024**3]
    assert line_cap == 128 * 1024**2
    assert value["global_decoded_limit_bytes"] == 12 * 1024**3


@pytest.mark.parametrize("field,value,error", [
    ("max_line_bytes", 128 * 1024**2 + 1, "within 128 MiB"),
    ("max_source_decoded_bytes", 4 * 1024**3 + 1, "within 4 GiB"),
    ("global_decoded_limit_bytes", 12 * 1024**3 + 1, "within 12 GiB"),
    ("execution_callers", list(stage.CALLERS), "five unfinished callers"),
    ("raw_line_policy", "drop_large_records", "bounded streaming"),
])
def test_final_amendment_rejects_larger_limits_or_scientific_selection(tmp_path, field, value, error):
    data = protocol()
    data[field] = value
    with pytest.raises(ValueError, match=error):
        parse(tmp_path, data)


def test_prior_amendment_cannot_inherit_new_limits(tmp_path):
    data = protocol()
    data.update(source_pass_amendment="remaining-five-stream-rnames-v1",
                max_source_decoded_bytes=3 * 1024**3)
    with pytest.raises(ValueError, match="within 32 MiB"):
        parse(tmp_path, data)
