"""Validate the serialized settings for the synthetic Sawfish native fixture."""
from __future__ import annotations

import json
import os
import stat
from hashlib import sha256


MAX_SETTINGS_BYTES = 64 * 1024
_FIXED_SETTINGS = {
    "min_indel_size": 35,
    "disable_cnv": True,
    "fast_cnv_mode": False,
    "min_gap_compressed_identity": 0.97,
    "min_sv_mapq": 5,
    "reduce_overlapping_sv_alleles": False,
    "disable_path_canonicalization": False,
    "disable_large_insertions": False,
    "debug_gc_correction": False,
    "min_qual": 10,
    "target_cluster_index": None,
    "expected_copy_number_filename": None,
    "cnv_excluded_regions_filename": None,
    "maf_filename": None,
    "maf_sample_name": None,
    "coverage_est_regex": "^chrSynthetic$",
}


def _snapshot(info):
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def _read_stable(path):
    fd = None
    try:
        fd = os.open(os.fspath(path), os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
                     | getattr(os, "O_CLOEXEC", 0))
        before = os.fstat(fd)
        named = os.lstat(path)
        snapshot = _snapshot(before)
        if (not stat.S_ISREG(before.st_mode) or not stat.S_ISREG(named.st_mode)
                or snapshot != _snapshot(named)):
            raise ValueError("settings JSON must be a stable regular nonlink file")
        if before.st_size > MAX_SETTINGS_BYTES:
            raise ValueError("settings JSON exceeds the 64-KiB limit")
        chunks, remaining = [], before.st_size
        while remaining:
            block = os.read(fd, min(8192, remaining))
            if not block:
                raise ValueError("settings JSON changed during read")
            chunks.append(block)
            remaining -= len(block)
        payload = b"".join(chunks)
        if (snapshot != _snapshot(os.fstat(fd))
                or snapshot != _snapshot(os.lstat(path))):
            raise ValueError("settings JSON snapshot changed during read")
        return payload, snapshot, sha256(payload).digest()
    except ValueError:
        raise
    except OSError:
        raise ValueError("settings JSON is not a readable regular nonlink file") from None
    finally:
        if fd is not None:
            os.close(fd)


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("settings JSON contains a duplicate key")
        result[key] = value
    return result


def _reject_constant(value):
    raise ValueError(f"settings JSON contains nonstandard number {value}")


def check_native_settings(path, *, expected_bam, expected_reference,
                          expected_output_dir, expected_noise_margin):
    """Return the complete flat settings object after checking its pinned values."""
    if type(expected_noise_margin) is not int or expected_noise_margin not in (10, 30):
        raise ValueError("expected noise margin must be integer 10 or 30")
    output_dir = str(expected_output_dir)
    if not os.path.isabs(output_dir):
        raise ValueError("expected output directory must be absolute")

    payload, snapshot, digest = _read_stable(path)
    try:
        settings = json.loads(payload.decode("utf-8"), object_pairs_hook=_unique_pairs,
                              parse_constant=_reject_constant)
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ValueError("settings JSON is not strict UTF-8 JSON") from None
    if type(settings) is not dict:
        raise ValueError("settings JSON must be a top-level object")

    expected = dict(_FIXED_SETTINGS)
    expected.update(
        min_indel_size_noise_margin=expected_noise_margin,
        bam_filename=os.path.realpath(expected_bam),
        ref_filename=os.path.realpath(expected_reference),
        output_dir=output_dir,
    )
    for key, value in expected.items():
        if key not in settings:
            raise ValueError(f"settings JSON is missing top-level field {key}")
        if type(settings[key]) is not type(value) or settings[key] != value:
            raise ValueError(f"settings JSON field {key} does not match its required value")

    post_payload, post_snapshot, post_digest = _read_stable(path)
    if (snapshot != post_snapshot or digest != post_digest
            or payload != post_payload):
        raise ValueError("settings JSON changed after its initial read")
    return dict(settings)
