"""Offline contract tests for bounded SVPG archive access and case selection."""

from __future__ import annotations

import hashlib
import io
import re
import struct
import sys
import zipfile
from pathlib import Path

import pytest


ANALYSIS_DIR = Path(__file__).resolve().parents[1] / "analysis"
if str(ANALYSIS_DIR) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_DIR))

import inspect_svpg_archive_index as archive_index  # noqa: E402
import fetch_svpg_case_sources as case_sources  # noqa: E402


LAST_MODIFIED = "Tue, 13 Oct 2026 00:00:00 GMT"


class MockResponse:
    def __init__(self, status=206, headers=None, body=b""):
        self.status = status
        self.headers = headers or {}
        self.body = body
        self.read_calls = 0

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self, size=-1):
        self.read_calls += 1
        return self.body if size is None or size < 0 else self.body[:size]


def _request_headers(request):
    return {key.lower(): value for key, value in request.header_items()}


def _install_payload_server(monkeypatch, payload):
    requests, responses = [], []

    def urlopen(request, timeout):
        match = re.fullmatch(r"bytes=(\d+)-(\d+)", _request_headers(request)["range"])
        assert match, "RangeReader must issue one explicit byte range"
        start, end = map(int, match.groups())
        headers = {
            "Content-Range": f"bytes {start}-{end}/{len(payload)}",
            "Last-Modified": LAST_MODIFIED,
        }
        response = MockResponse(headers=headers, body=payload[start : end + 1])
        requests.append((request, timeout, start, end))
        responses.append(response)
        return response

    monkeypatch.setattr(archive_index.urllib.request, "urlopen", urlopen)
    return requests, responses


def _install_static_response(monkeypatch, response):
    calls = []

    def urlopen(request, timeout):
        calls.append((request, timeout))
        return response

    monkeypatch.setattr(archive_index.urllib.request, "urlopen", urlopen)
    return calls


def _assert_receipts_match(payload, receipts):
    for receipt in receipts:
        start, end = receipt["start"], receipt["end"]
        assert set(receipt) == {"start", "end", "bytes", "sha256"}
        assert receipt["bytes"] == end - start + 1
        assert receipt["sha256"] == hashlib.sha256(payload[start : end + 1]).hexdigest()


@pytest.mark.parametrize(
    ("status", "headers"),
    [
        (200, {"Content-Range": "bytes 0-1/8"}),
        (206, {"Content-Range": "bytes 0-2/8"}),
        (206, {"Content-Range": "bytes 0-1/8", "Content-Encoding": "gzip"}),
    ],
    ids=["http-200", "wrong-content-range", "encoded-body"],
)
def test_range_reader_refuses_unbounded_or_encoded_response_before_read(
    monkeypatch, status, headers
):
    response = MockResponse(status=status, headers=headers, body=b"body")
    calls = _install_static_response(monkeypatch, response)
    reader = archive_index.RangeReader("https://offline.invalid/archive.zip", 8)

    with pytest.raises(ValueError):
        reader.read(2)

    assert len(calls) == 1
    assert response.read_calls == 0
    assert reader.position == 0
    assert reader.transferred == 0
    assert reader.receipts == []


def test_range_reader_records_exact_success_receipts(monkeypatch):
    payload = b"abcdefgh"
    requests, _ = _install_payload_server(monkeypatch, payload)
    reader = archive_index.RangeReader("https://offline.invalid/archive.zip", len(payload))

    assert reader.read(4) == b"abcd"
    assert reader.seek(6) == 6
    assert reader.read(2) == b"gh"

    assert reader.position == 8
    assert reader.transferred == 6
    _assert_receipts_match(payload, reader.receipts)
    assert reader.receipts == [
        {"start": 0, "end": 3, "bytes": 4, "sha256": hashlib.sha256(b"abcd").hexdigest()},
        {"start": 6, "end": 7, "bytes": 2, "sha256": hashlib.sha256(b"gh").hexdigest()},
    ]
    assert [(_request_headers(req)["range"], timeout) for req, timeout, _, _ in requests] == [
        ("bytes=0-3", 25),
        ("bytes=6-7", 25),
    ]
    assert all(_request_headers(req)["accept-encoding"] == "identity" for req, *_ in requests)


def test_range_reader_enforces_request_and_cumulative_caps_before_request(monkeypatch):
    payload = b"abcdefgh"
    requests, _ = _install_payload_server(monkeypatch, payload)
    reader = archive_index.RangeReader(
        "https://offline.invalid/archive.zip", len(payload), request_cap=3, transfer_cap=4
    )

    with pytest.raises(ValueError, match="cap"):
        reader.read(4)
    assert requests == []

    assert reader.read(3) == b"abc"
    with pytest.raises(ValueError, match="cap"):
        reader.read(2)
    assert len(requests) == 1
    assert reader.transferred == 3


@pytest.mark.parametrize("body", [b"a", b"abc"], ids=["short", "long"])
def test_range_reader_rejects_wrong_body_size_without_success_receipt(monkeypatch, body):
    response = MockResponse(
        headers={"Content-Range": "bytes 0-1/8", "Last-Modified": LAST_MODIFIED},
        body=body,
    )
    _install_static_response(monkeypatch, response)
    reader = archive_index.RangeReader("https://offline.invalid/archive.zip", 8)

    with pytest.raises(ValueError, match="body size"):
        reader.read(2)

    assert response.read_calls == 1
    assert reader.position == 0
    assert reader.receipts == []
    assert reader.transferred == len(body)


def test_range_reader_does_not_exceed_cumulative_cap_on_overlong_body(monkeypatch):
    response = MockResponse(
        headers={"Content-Range": "bytes 0-1/8", "Last-Modified": LAST_MODIFIED},
        body=b"abc",
    )
    _install_static_response(monkeypatch, response)
    reader = archive_index.RangeReader(
        "https://offline.invalid/archive.zip", 8, request_cap=2, transfer_cap=2
    )

    with pytest.raises(ValueError, match="cap"):
        reader.read(2)

    assert reader.transferred <= reader.transfer_cap
    assert response.read_calls == 0


def test_range_reader_rejects_changed_last_modified_before_second_read(monkeypatch):
    payload = b"abcdefgh"
    responses = []

    def urlopen(request, timeout):
        headers = _request_headers(request)
        start, end = map(int, re.fullmatch(r"bytes=(\d+)-(\d+)", headers["range"]).groups())
        modified = LAST_MODIFIED if not responses else "Wed, 14 Oct 2026 00:00:00 GMT"
        response = MockResponse(
            headers={
                "Content-Range": f"bytes {start}-{end}/{len(payload)}",
                "Last-Modified": modified,
            },
            body=payload[start : end + 1],
        )
        responses.append(response)
        return response

    monkeypatch.setattr(archive_index.urllib.request, "urlopen", urlopen)
    reader = archive_index.RangeReader("https://offline.invalid/archive.zip", len(payload))

    assert reader.read(2) == b"ab"
    reader.seek(4)
    with pytest.raises(ValueError, match="Last-Modified"):
        reader.read(2)

    assert responses[0].read_calls == 1
    assert responses[1].read_calls == 0
    assert reader.position == 4
    assert reader.transferred == 2
    assert len(reader.receipts) == 1


def test_range_reader_seek_bounds_and_relative_origins():
    reader = archive_index.RangeReader("https://offline.invalid/archive.zip", 10)

    assert reader.seek(3) == 3
    assert reader.seek(2, 1) == 5
    assert reader.seek(-2, 2) == 8
    for offset, whence in [(-1, 0), (1, 2), (-11, 2)]:
        with pytest.raises(ValueError, match="Seek outside"):
            reader.seek(offset, whence)
    assert reader.tell() == 8


def _member_body_spans(payload):
    spans = []
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        for entry in archive.infolist():
            if not entry.compress_size:
                continue
            name_size, extra_size = struct.unpack_from("<HH", payload, entry.header_offset + 26)
            start = entry.header_offset + 30 + name_size + extra_size
            spans.append((start, start + entry.compress_size - 1))
    return spans


def test_archive_index_excludes_directories_without_reading_member_bodies(monkeypatch):
    body = b"synthetic member payload; directory indexing must not read this.\n" * 512
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_STORED) as archive:
        archive.writestr("synthetic/", b"")
        archive.writestr("synthetic/payload.bin", body)
        archive.writestr("other.txt", b"also not read")
    payload = stream.getvalue()
    requests, _ = _install_payload_server(monkeypatch, payload)

    result = archive_index.inspect_index("https://offline.invalid/archive.zip", len(payload))

    assert result["scope"] == "ZIP_DIRECTORY_ONLY"
    assert result["file_entries"] == 2
    assert [entry["name"] for entry in result["entries"]] == [
        "synthetic/payload.bin",
        "other.txt",
    ]
    assert result["member_bodies_read"] == 0
    assert result["whole_archive_checksum_verified"] is False
    _assert_receipts_match(payload, result["range_receipts"])
    for receipt in result["range_receipts"]:
        for body_start, body_end in _member_body_spans(payload):
            assert receipt["end"] < body_start or receipt["start"] > body_end
    assert requests


def _synthetic_vcf():
    rows = [
        "##fileformat=VCFv4.2",
        "##source=synthetic-contract-test",
        "##reference=synthetic-reference",
        "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSAMPLE",
        f"chr7\t{case_sources.LOW}\tpos-low\tN\t<DEL>\t.\tPASS\tSVTYPE=DEL;END={case_sources.LOW + 419};SVLEN=-419\tGT:DP\t0/1:9",
        "chr1\t10\tother-chromosome\tN\t<DEL>\t.\tPASS\tSVTYPE=DEL;END=20\tGT:DP\t0/1:2",
    ]
    return ("\n".join(rows) + "\n").encode("utf-8")


def _synthetic_case_zip(overrides=None, compression=zipfile.ZIP_DEFLATED):
    overrides = overrides or {}
    vcf = _synthetic_vcf()
    bodies = {}
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=compression) as archive:
        archive.writestr(case_sources.PREFIX, b"")
        for basename in case_sources.FILES:
            if basename in overrides:
                body = overrides[basename]
            elif basename.endswith(".vcf"):
                body = vcf
            else:
                body = b"synthetic non-VCF source row\n"
            bodies[basename] = body
            archive.writestr(case_sources.PREFIX + basename, body)
    return stream.getvalue(), bodies


def _patch_case_source(monkeypatch, payload):
    monkeypatch.setattr(case_sources, "URL", "https://offline.invalid/archive.zip")
    monkeypatch.setattr(case_sources, "TOTAL_BYTES", len(payload))
    return _install_payload_server(monkeypatch, payload)


def test_fetch_case_panel_uses_synthetic_zip_and_returns_exact_receipts(monkeypatch, tmp_path):
    payload, bodies = _synthetic_case_zip()
    _patch_case_source(monkeypatch, payload)

    manifest = case_sources.fetch(tmp_path)

    assert [record["local_basename"] for record in manifest["files"]] == case_sources.FILES
    assert manifest["whole_archive_checksum_verified"] is False
    assert manifest["last_modified"] == LAST_MODIFIED
    _assert_receipts_match(payload, manifest["range_receipts"])
    assert manifest["transferred_range_bytes"] == sum(
        receipt["bytes"] for receipt in manifest["range_receipts"]
    )
    for record in manifest["files"]:
        basename = record["local_basename"]
        assert record["bytes"] == len(bodies[basename])
        assert record["member_crc_verified"] is True
        assert (tmp_path / basename).read_bytes() == bodies[basename]
        if basename.endswith(".vcf"):
            assert record["total_records_read"] == 2
            assert [row["id"] for row in record["nearby_records"]] == ["pos-low"]
            assert record["nearby_records"][0]["raw_record"] in bodies[basename].decode()


def test_fetch_rejects_member_over_8_mib_before_reading_its_body(monkeypatch, tmp_path):
    oversized = b"x" * (8 * 1024**2 + 1)
    payload, _ = _synthetic_case_zip(
        overrides={case_sources.FILES[0]: oversized}, compression=zipfile.ZIP_STORED
    )
    requests, _ = _patch_case_source(monkeypatch, payload)

    with pytest.raises(ValueError, match="Member size"):
        case_sources.fetch(tmp_path)

    assert list(tmp_path.iterdir()) == []
    for _, _, start, end in requests:
        for body_start, body_end in _member_body_spans(payload):
            assert end < body_start or start > body_end


def test_fetch_accepts_member_within_8_mib_even_if_above_single_range_cap(monkeypatch, tmp_path):
    permitted_size = 4 * 1024**2 + 1
    large_bed = bytes(range(256)) * (permitted_size // 256) + bytes(range(permitted_size % 256))
    assert len(large_bed) == permitted_size
    payload, _ = _synthetic_case_zip(
        overrides={case_sources.FILES[0]: large_bed}, compression=zipfile.ZIP_STORED
    )
    _patch_case_source(monkeypatch, payload)

    manifest = case_sources.fetch(tmp_path)

    assert manifest["files"][0]["bytes"] == permitted_size


def _vcf_record(chromosome, position, identifier, alt="N", info=".", sample="0/1:3"):
    return "\t".join(
        [chromosome, str(position), identifier, "N", alt, ".", "PASS", info, "GT:DP", sample]
    )


def test_case_rows_counts_all_chromosomes_and_selects_inclusive_frozen_boundaries():
    low, high = case_sources.LOW, case_sources.HIGH
    records = [
        _vcf_record("chr7", low, "pos-low"),
        _vcf_record("7", high, "pos-high"),
        _vcf_record("chr7", 1, "end-low", "<DEL>", f"SVTYPE=DEL;END={low}"),
        _vcf_record("chr7", 2, "end-high", "<DEL>", f"SVTYPE=DEL;END={high}"),
        _vcf_record("chr2", 99, "mate-low", "N]chr7:{}]".format(low), "SVTYPE=BND"),
        _vcf_record("chr2", 100, "mate-high", "N[7:{}[".format(high), "SVTYPE=BND"),
        _vcf_record("chr7", low - 1, "spans-window", "<DEL>", f"SVTYPE=DEL;END={high + 1}"),
        _vcf_record("chr7", low - 1, "both-ends-outside", "<DEL>", f"SVTYPE=DEL;END={low - 2}"),
        _vcf_record("chr1", low, "other-chromosome"),
    ]
    text = "\n".join(
        ["##fileformat=VCFv4.2", "##source=synthetic", "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO"]
        + records
    )

    result = case_sources.case_rows(text)

    assert result["total_records_read"] == len(records)
    selected = result["nearby_records"]
    assert [row["id"] for row in selected] == [
        "pos-low",
        "pos-high",
        "end-low",
        "end-high",
        "mate-low",
        "mate-high",
    ]
    assert all(row["raw_record"] in records for row in selected)
    assert selected[2]["alt"] == "<DEL>"
    assert selected[2]["format_and_samples"] == ["GT:DP", "0/1:3"]
    assert selected[4]["alt"] == f"N]chr7:{low}]"
    assert any(line.startswith("#CHROM\t") for line in result["selected_headers"])
    assert "##fileformat=VCFv4.2" in result["selected_headers"]


@pytest.mark.parametrize(
    "record",
    [
        "chr7\t1\ttoo-few-columns",
        "chr7\tnot-an-integer\tid\tN\t<DEL>\t.\tPASS\tEND=10",
    ],
    ids=["too-few-columns", "invalid-position"],
)
def test_case_rows_rejects_malformed_vcf_records(record):
    with pytest.raises(ValueError):
        case_sources.case_rows("#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n" + record)
