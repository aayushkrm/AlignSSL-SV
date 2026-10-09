import json
from pathlib import Path

import pytest

from analysis import check_native_fixture_settings as validator


def _case(tmp_path, margin=10):
    bam = tmp_path / "reads.bam"
    reference = tmp_path / "reference.fa"
    bam.write_bytes(b"bam metadata fixture")
    reference.write_bytes(b"reference metadata fixture")
    output = tmp_path / "calls"
    settings = {
        **validator._FIXED_SETTINGS,
        "min_indel_size_noise_margin": margin,
        "bam_filename": str(bam.resolve()),
        "ref_filename": str(reference.resolve()),
        "output_dir": str(output),
        "future_flat_setting": "preserved",
    }
    path = tmp_path / "settings.json"
    path.write_text(json.dumps(settings), encoding="utf-8")
    return path, bam, reference, output, settings


def _check(case, margin=None):
    path, bam, reference, output, _ = case
    if margin is None:
        margin = case[4]["min_indel_size_noise_margin"]
    return validator.check_native_settings(
        path, expected_bam=bam, expected_reference=reference,
        expected_output_dir=output, expected_noise_margin=margin,
    )


@pytest.mark.parametrize("margin", [10, 30])
def test_accepts_default_and_rescue_settings_and_returns_every_field(tmp_path, margin):
    case = _case(tmp_path, margin)

    result = _check(case)

    assert result == case[4]
    assert result["future_flat_setting"] == "preserved"


@pytest.mark.parametrize(("field", "value"), [
    ("min_indel_size", 34),
    ("min_indel_size", 35.0),
    ("disable_cnv", 1),
    ("min_indel_size_noise_margin", 30),
    ("coverage_est_regex", "^chrOther$"),
])
def test_rejects_wrong_or_imprecisely_typed_required_values(tmp_path, field, value):
    case = _case(tmp_path, 10)
    case[4][field] = value
    case[0].write_text(json.dumps(case[4]), encoding="utf-8")

    with pytest.raises(ValueError):
        _check(case, 10)


def test_rejects_missing_and_nested_required_fields(tmp_path):
    case = _case(tmp_path)
    del case[4]["min_qual"]
    case[0].write_text(json.dumps(case[4]), encoding="utf-8")
    with pytest.raises(ValueError, match="missing top-level"):
        _check(case)

    case[0].write_text(json.dumps({"discover_settings": case[4]}), encoding="utf-8")
    with pytest.raises(ValueError, match="missing top-level"):
        _check(case)


@pytest.mark.parametrize("field", ["bam_filename", "ref_filename", "output_dir"])
def test_rejects_wrong_paths(tmp_path, field):
    case = _case(tmp_path)
    case[4][field] = str(tmp_path / "wrong-path")
    case[0].write_text(json.dumps(case[4]), encoding="utf-8")

    with pytest.raises(ValueError, match=field):
        _check(case)


@pytest.mark.parametrize(("tail", "message"), [
    (',"duplicate":1,"duplicate":2}', "duplicate key"),
    (',"extra":NaN}', "nonstandard number"),
])
def test_rejects_duplicate_keys_and_nonstandard_numbers(tmp_path, tail, message):
    case = _case(tmp_path)
    raw = json.dumps(case[4], separators=(",", ":"))[:-1]
    case[0].write_text(raw + tail, encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        _check(case)


def test_rejects_oversize_and_symlink_settings(tmp_path):
    case = _case(tmp_path)
    case[0].write_bytes(b" " * (validator.MAX_SETTINGS_BYTES + 1))
    with pytest.raises(ValueError, match="64-KiB"):
        _check(case)

    target = tmp_path / "target.json"
    target.write_text(json.dumps(case[4]), encoding="utf-8")
    link = tmp_path / "settings-link.json"
    link.symlink_to(target)
    linked_case = (link, *case[1:])
    with pytest.raises(ValueError, match="regular nonlink"):
        _check(linked_case)


def test_rejects_file_changed_between_read_and_posthash(tmp_path, monkeypatch):
    case = _case(tmp_path)
    read_stable = validator._read_stable
    reads = 0

    def change_after_first_read(path):
        nonlocal reads
        result = read_stable(path)
        reads += 1
        if reads == 1:
            changed = dict(case[4], min_sv_mapq=6)
            Path(path).write_text(json.dumps(changed), encoding="utf-8")
        return result

    monkeypatch.setattr(validator, "_read_stable", change_after_first_read)
    with pytest.raises(ValueError, match="changed after its initial read"):
        _check(case)
