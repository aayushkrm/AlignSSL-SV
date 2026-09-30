"""Synthetic tests for bounded, payload-free HTTP ZIP inventory."""

import hashlib
import io
import json
import re
import struct
import zipfile

import pytest

from scripts.audit_remote_zip_directory import (
    DEFAULT_MAX_NETWORK_BYTES,
    RemoteRangeReader,
    RemoteZipError,
    inventory_remote_zip,
    write_inventory,
)


URL = "https://example.test/archive.zip"
LAST_MODIFIED = "Tue, 09 Jun 2026 08:34:21 GMT"
FIRST_PAYLOAD = b"member-payload-one-" * 20


def zip_bytes(entries=(
    ("calls/a.vcf.gz", FIRST_PAYLOAD),
    ("README.txt", b"member-payload-two"),
), *, comment=b"") -> bytes:
    sink = io.BytesIO()
    with zipfile.ZipFile(sink, "w", allowZip64=True) as archive:
        for name, payload in entries:
            archive.writestr(name, payload, compress_type=zipfile.ZIP_DEFLATED)
        archive.comment = comment
    return sink.getvalue()


class FakeResponse:
    def __init__(self, *, status, url, headers, body=b""):
        self.status = status
        self.url = url
        self.headers = headers
        self.body = body
        self.read_sizes = []

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def geturl(self):
        return self.url

    def read(self, amount=-1):
        self.read_sizes.append(amount)
        return self.body if amount < 0 else self.body[:amount]


class FakeOpener:
    def __init__(
        self,
        data,
        *,
        etag='"fixed"',
        last_modified=LAST_MODIFIED,
        mutate=None,
        response_url=URL,
    ):
        self.data = data
        self.etag = etag
        self.last_modified = last_modified
        self.mutate = mutate
        self.response_url = response_url
        self.requests = []
        self.range_responses = []

    def __call__(self, request, timeout):
        assert timeout == 30
        method = request.get_method()
        self.requests.append(request)
        if method == "HEAD":
            headers = {"Content-Length": str(len(self.data)), "Content-Encoding": "identity"}
            if self.etag is not None:
                headers["ETag"] = self.etag
            if self.last_modified is not None:
                headers["Last-Modified"] = self.last_modified
            return FakeResponse(status=200, url=self.response_url, headers=headers)

        assert method == "GET"
        match = re.fullmatch(r"bytes=([0-9]+)-([0-9]+)", request.get_header("Range"))
        assert match
        start, end = map(int, match.groups())
        body = self.data[start:end + 1]
        headers = {
            "Content-Range": f"bytes {start}-{end}/{len(self.data)}",
            "Content-Length": str(len(body)),
            "Content-Encoding": "identity",
        }
        if self.etag is not None:
            headers["ETag"] = self.etag
        if self.last_modified is not None:
            headers["Last-Modified"] = self.last_modified
        status = 206
        index = len(self.range_responses)
        if self.mutate is not None:
            status, headers, body = self.mutate(index, start, end, status, headers, body)
        response = FakeResponse(status=status, url=self.response_url, headers=headers, body=body)
        self.range_responses.append(response)
        return response


def test_inventory_uses_bounded_ranges_and_writes_checksums(tmp_path):
    data = zip_bytes()
    opener = FakeOpener(data)
    official_md5 = "cef8268e5dc77d9881b35f90875151c0"

    inventory = inventory_remote_zip(
        URL,
        len(data),
        official_md5=official_md5,
        opener=opener,
    )

    assert [member["name"] for member in inventory["members"]] == [
        "calls/a.vcf.gz", "README.txt"
    ]
    first = inventory["members"][0]
    assert first["compressed_size"] < first["uncompressed_size"]
    assert first["uncompressed_size"] == len(FIRST_PAYLOAD)
    assert first["crc32"] == f"{zipfile.crc32(FIRST_PAYLOAD):08x}"
    assert first["compression"] == "deflate"
    assert first["header_offset"] == 0

    summary = inventory["summary"]
    assert summary["source_manifest_size_bytes"] == len(data)
    assert summary["source_manifest_md5"] == official_md5
    assert summary["whole_archive_md5_verification"] == "UNVERIFIED_NOT_DOWNLOADED"
    assert summary["validator"]["kind"] == "strong_etag"
    assert summary["member_payloads_requested"] is False
    assert summary["member_payload_bytes_requested"] == 0
    assert summary["range_response_body_bytes_read"] <= DEFAULT_MAX_NETWORK_BYTES
    assert summary["range_request_count"] == len(summary["range_requests"])
    for record in summary["range_requests"]:
        offset, length = record["offset"], record["length"]
        assert record["sha256"] == hashlib.sha256(data[offset:offset + length]).hexdigest()
        assert length > 0
    assert all(request.get_header("Range") for request in opener.requests if request.get_method() == "GET")
    assert all(response.read_sizes == [int(response.headers["Content-Length"]) + 1]
               for response in opener.range_responses)

    with zipfile.ZipFile(io.BytesIO(data)) as local_archive:
        member_body_ranges = []
        for info in local_archive.infolist():
            name_length, extra_length = struct.unpack_from(
                "<HH", data, info.header_offset + 26
            )
            body_start = info.header_offset + 30 + name_length + extra_length
            member_body_ranges.append((body_start, body_start + info.compress_size))
    for request in summary["range_requests"]:
        request_start = request["offset"]
        request_end = request_start + request["length"]
        assert all(
            request_end <= body_start or request_start >= body_end
            for body_start, body_end in member_body_ranges
        )

    out_dir = tmp_path / "inventory"
    write_inventory(out_dir, inventory)
    sums = {
        name: digest
        for digest, name in (
            line.split("  ", 1)
            for line in (out_dir / "SHA256SUMS").read_text().splitlines()
        )
    }
    for name in ("members.jsonl", "range_requests.jsonl", "summary.json"):
        assert sums[name] == hashlib.sha256((out_dir / name).read_bytes()).hexdigest()
    assert json.loads((out_dir / "summary.json").read_text())["whole_archive_md5_verification"] == (
        "UNVERIFIED_NOT_DOWNLOADED"
    )


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (
            lambda i, s, e, status, headers, body: (
                200, {**headers, "Content-Length": str(len(body))}, body
            ),
            "did not honor Range",
        ),
        (
            lambda i, s, e, status, headers, body: (
                status, {**headers, "Content-Length": str(len(body) + 1)}, body
            ),
            "Incorrect Content-Length",
        ),
        (
            lambda i, s, e, status, headers, body: (
                status, headers, body[:-1]
            ),
            "Short Range response body",
        ),
        (
            lambda i, s, e, status, headers, body: (
                status, {**headers, "Content-Range": f"bytes {s + 1}-{e + 1}/{headers['Content-Range'].split('/')[-1]}"}, body
            ),
            "Incorrect Content-Range",
        ),
        (
            lambda i, s, e, status, headers, body: (
                status, headers, body + b"x"
            ),
            "Oversized Range response body",
        ),
    ],
)
def test_rejects_range_protocol_and_body_mismatches(mutation, message):
    data = zip_bytes()
    opener = FakeOpener(data, mutate=mutation)
    with pytest.raises(RemoteZipError, match=message):
        inventory_remote_zip(URL, len(data), opener=opener)


def test_head_size_must_match_manifest_before_ranges():
    opener = FakeOpener(zip_bytes())
    with pytest.raises(RemoteZipError, match="differs from source-manifest size"):
        RemoteRangeReader(URL, len(opener.data) + 1, opener=opener)
    assert not opener.range_responses


def test_ignored_range_full_body_is_not_read_or_retried():
    data = zip_bytes()

    def ignore_range(index, start, end, status, headers, body):
        return 200, {**headers, "Content-Length": str(len(data))}, data

    opener = FakeOpener(data, mutate=ignore_range)
    with pytest.raises(RemoteZipError, match="did not honor Range"):
        inventory_remote_zip(URL, len(data), opener=opener)

    assert len(opener.range_responses) == 1
    assert opener.range_responses[0].read_sizes == []


@pytest.mark.parametrize("archive_kind", ["comment", "trailing"])
def test_commented_or_trailing_archive_is_rejected_after_terminal_probe(archive_kind):
    data = zip_bytes(comment=b"archive comment") if archive_kind == "comment" else zip_bytes() + b"trailer"
    opener = FakeOpener(data)

    with pytest.raises(RemoteZipError, match="comment-free ZIP with EOCD exactly at EOF"):
        inventory_remote_zip(URL, len(data), opener=opener)

    assert len(opener.range_responses) == 1
    response = opener.range_responses[0]
    assert response.read_sizes == [23]
    request = next(request for request in opener.requests if request.get_method() == "GET")
    assert request.get_header("Range") == f"bytes={len(data) - 22}-{len(data) - 1}"


def test_eocd_multidisk_fields_are_rejected_before_central_directory():
    data = bytearray(zip_bytes())
    struct.pack_into("<H", data, len(data) - 22 + 4, 1)
    opener = FakeOpener(bytes(data))

    with pytest.raises(RemoteZipError, match="Multi-disk ZIP archives"):
        inventory_remote_zip(URL, len(data), opener=opener)
    assert len(opener.range_responses) == 1


def test_central_directory_multidisk_member_is_rejected():
    data = bytearray(zip_bytes((("one.txt", b"body"),)))
    central = data.index(b"PK\x01\x02")
    struct.pack_into("<H", data, central + 34, 1)
    opener = FakeOpener(bytes(data))

    with pytest.raises(RemoteZipError, match="Multi-disk ZIP member"):
        inventory_remote_zip(URL, len(data), opener=opener)


def test_query_values_are_not_persisted_in_inventory():
    data = zip_bytes()
    url = URL + "?token=secret-value"
    opener = FakeOpener(data, response_url=url)
    inventory = inventory_remote_zip(url, len(data), opener=opener)

    encoded_summary = json.dumps(inventory["summary"])
    assert "secret-value" not in encoded_summary
    assert inventory["summary"]["archive_url"] == URL
    assert inventory["summary"]["resolved_archive_url"] == URL
    assert inventory["summary"]["archive_url_query_redacted"] is True
    assert inventory["summary"]["resolved_archive_url_query_redacted"] is True


def test_strong_etag_change_fails_before_body_read():
    data = zip_bytes()

    def change_etag(index, start, end, status, headers, body):
        return status, {**headers, "ETag": '"changed"'}, body

    opener = FakeOpener(data, mutate=change_etag)
    with pytest.raises(RemoteZipError, match="Strong ETag changed"):
        inventory_remote_zip(URL, len(data), opener=opener)
    assert opener.range_responses[0].read_sizes == []
    request = next(request for request in opener.requests if request.get_method() == "GET")
    assert request.get_header("If-range") == '"fixed"'


def test_last_modified_fallback_is_conditional_and_labeled_weaker():
    data = zip_bytes()
    opener = FakeOpener(data, etag=None)
    inventory = inventory_remote_zip(URL, len(data), opener=opener)

    assert inventory["summary"]["validator"] == {
        "kind": "last_modified_and_size_weaker",
        "etag": None,
        "last_modified": LAST_MODIFIED,
    }
    assert all(
        request.get_header("If-unmodified-since") == LAST_MODIFIED
        for request in opener.requests if request.get_method() == "GET"
    )


def test_last_modified_change_fails():
    data = zip_bytes()

    def change_date(index, start, end, status, headers, body):
        return status, {**headers, "Last-Modified": "Wed, 10 Jun 2026 08:34:21 GMT"}, body

    opener = FakeOpener(data, etag=None, mutate=change_date)
    with pytest.raises(RemoteZipError, match="Last-Modified changed"):
        inventory_remote_zip(URL, len(data), opener=opener)
    request = next(request for request in opener.requests if request.get_method() == "GET")
    assert request.get_header("If-unmodified-since") == LAST_MODIFIED


def test_missing_stable_validator_fails_closed():
    opener = FakeOpener(zip_bytes(), etag=None, last_modified=None)
    with pytest.raises(RemoteZipError, match="No strong ETag or usable Last-Modified"):
        RemoteRangeReader(URL, len(opener.data), opener=opener)
    assert not opener.range_responses


def test_read_caps_are_checked_before_issuing_get():
    opener = FakeOpener(bytes(512))
    reader = RemoteRangeReader(URL, 512, max_network_bytes=64, opener=opener)
    with pytest.raises(RemoteZipError, match="exceeds per-read network cap"):
        reader.read(65)
    assert not opener.range_responses

    reader.read(49)
    reader.seek(100)
    with pytest.raises(RemoteZipError, match="exceeds remaining network budget"):
        reader.read(15)
    assert len(opener.range_responses) == 1


def test_existing_output_directory_is_never_overwritten(tmp_path):
    out_dir = tmp_path / "already-there"
    out_dir.mkdir()
    marker = out_dir / "keep.txt"
    marker.write_text("preserve me")

    with pytest.raises(FileExistsError, match="Refusing to overwrite"):
        write_inventory(out_dir, {})
    assert marker.read_text() == "preserve me"


def test_duplicate_member_names_are_rejected():
    sink = io.BytesIO()
    with zipfile.ZipFile(sink, "w") as archive:
        with pytest.warns(UserWarning, match="Duplicate name"):
            archive.writestr("duplicate.txt", b"one")
            archive.writestr("duplicate.txt", b"two")
    data = sink.getvalue()
    with pytest.raises(RemoteZipError, match="Duplicate ZIP member name"):
        inventory_remote_zip(URL, len(data), opener=FakeOpener(data))


def test_encrypted_member_flag_is_rejected_without_reading_payload():
    data = bytearray(zip_bytes((("secret.txt", b"do not read"),)))
    central = data.index(b"PK\x01\x02")
    flags = struct.unpack_from("<H", data, central + 8)[0]
    struct.pack_into("<H", data, central + 8, flags | 0x1)
    opener = FakeOpener(bytes(data))

    with pytest.raises(RemoteZipError, match="Encrypted ZIP member"):
        inventory_remote_zip(URL, len(data), opener=opener)


def test_zip64_end_records_are_supported_by_stdlib(monkeypatch):
    sink = io.BytesIO()
    with monkeypatch.context() as patch:
        patch.setattr(zipfile, "ZIP64_LIMIT", 0)
        with zipfile.ZipFile(sink, "w", allowZip64=True) as archive:
            archive.writestr("zip64.txt", b"small payload")
    data = sink.getvalue()
    assert b"PK\x06\x06" in data

    inventory = inventory_remote_zip(URL, len(data), opener=FakeOpener(data))
    assert [member["name"] for member in inventory["members"]] == ["zip64.txt"]
