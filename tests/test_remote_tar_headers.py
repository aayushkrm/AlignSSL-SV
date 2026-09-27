"""Synthetic TAR tests for bounded, header-only remote inventory."""

import io
import tarfile

import pytest

from scripts.scan_remote_tar_headers import BLOCK, _range, parse_header, walk_headers


def tar_bytes(names: list[str]) -> bytes:
    sink = io.BytesIO()
    with tarfile.open(fileobj=sink, mode="w", format=tarfile.USTAR_FORMAT) as archive:
        for name in names:
            payload = b"payload" * 23
            item = tarfile.TarInfo(name)
            item.size = len(payload)
            archive.addfile(item, io.BytesIO(payload))
    return sink.getvalue()


def test_walk_skips_payload_and_finds_bed() -> None:
    data = tar_bytes(["calls/a.vcf.gz", "results/callable_regions_h1_500.bed.gz"])
    requested = []

    def fetch(offset: int) -> bytes:
        requested.append(offset)
        return data[offset:offset + BLOCK]

    members, n_requests = walk_headers(fetch, len(data))
    assert n_requests == 4
    assert requested == [0, 1024, 2048, 2560]
    assert [member["is_bed"] for member in members] == [False, True]
    assert [member["contains_callable"] for member in members] == [False, True]


def test_corrupt_checksum_fails() -> None:
    data = bytearray(tar_bytes(["calls/a.vcf.gz"]))
    data[1] ^= 1
    with pytest.raises(ValueError, match="checksum mismatch"):
        parse_header(bytes(data[:BLOCK]), 0)


def test_missing_second_zero_block_fails() -> None:
    data = bytearray(tar_bytes(["calls/a.vcf.gz"]))
    data[1536] = 1
    with pytest.raises(ValueError, match="second zero end marker"):
        walk_headers(lambda offset: bytes(data[offset:offset + BLOCK]), len(data))


def test_payload_size_past_archive_boundary_fails() -> None:
    data = tar_bytes(["calls/a.vcf.gz"])
    with pytest.raises(ValueError, match="archive boundary"):
        walk_headers(lambda offset: data[offset:offset + BLOCK], BLOCK)


def test_extended_name_requires_payload_and_fails_closed() -> None:
    sink = io.BytesIO()
    with tarfile.open(fileobj=sink, mode="w", format=tarfile.GNU_FORMAT) as archive:
        item = tarfile.TarInfo("very_long_directory/" + "x" * 110 + ".vcf.gz")
        item.size = 0
        archive.addfile(item, io.BytesIO())
    data = sink.getvalue()
    with pytest.raises(ValueError, match="Extended-name metadata"):
        walk_headers(lambda offset: data[offset:offset + BLOCK], len(data))


class FakeResponse:
    def __init__(self, *, status=206, url="https://example.test/archive.tar", headers=None):
        self.status = status
        self.url = url
        self.headers = headers or {
            "ETag": '"fixed"',
            "Content-Range": "bytes 512-1023/4096",
            "Content-Length": "512",
        }

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def geturl(self):
        return self.url

    def read(self, amount):
        assert amount == BLOCK + 1
        return bytes(BLOCK)


@pytest.mark.parametrize(
    ("response", "message"),
    [
        (FakeResponse(status=200), "did not honor Range"),
        (FakeResponse(url="https://other.test/archive.tar"), "did not honor Range"),
        (FakeResponse(headers={"ETag": '"changed"', "Content-Range": "bytes 512-1023/4096", "Content-Length": "512"}), "ETag changed"),
        (FakeResponse(headers={"ETag": '"fixed"', "Content-Range": "bytes 512-1023/0", "Content-Length": "512"}), "Incorrect Content-Range"),
    ],
)
def test_http_range_protocol_failures(monkeypatch, response, message) -> None:
    def fake_urlopen(request, timeout):
        assert request.get_header("Range") == "bytes=512-1023"
        assert request.get_header("If-range") == '"fixed"'
        assert timeout == 30
        return response

    monkeypatch.setattr("scripts.scan_remote_tar_headers.urllib.request.urlopen", fake_urlopen)
    with pytest.raises(ValueError, match=message):
        _range("https://example.test/archive.tar", 512, 4096, '"fixed"')


def test_http_range_success(monkeypatch) -> None:
    monkeypatch.setattr(
        "scripts.scan_remote_tar_headers.urllib.request.urlopen",
        lambda *_args, **_kwargs: FakeResponse(),
    )
    assert _range("https://example.test/archive.tar", 512, 4096, '"fixed"') == bytes(BLOCK)
