import io
import re
import zipfile

import pytest

from analysis.inventory_remote_zip import RemoteZip


class Response(io.BytesIO):
    def __init__(self, content, status, headers):
        super().__init__(content)
        self.status = status
        self.headers = headers


def fixture_archive():
    result = io.BytesIO()
    with zipfile.ZipFile(result, "w") as archive:
        archive.writestr("one.vcf.gz", b"synthetic-one")
        archive.writestr("two.vcf.gz", b"synthetic-two")
    return result.getvalue()


def mock_server(monkeypatch, content, bad_range=False):
    requests = []

    def open_request(request, timeout):
        requests.append(request)
        if request.get_method() == "HEAD":
            return Response(b"", 200, {"Content-Length": str(len(content))})
        match = re.fullmatch(r"bytes=(\d+)-(\d+)", request.get_header("Range"))
        assert match
        start, end = map(int, match.groups())
        if bad_range:
            return Response(content, 200, {"Content-Length": str(len(content))})
        return Response(content[start:end + 1], 206,
                        {"Content-Range": f"bytes {start}-{end}/{len(content)}"})

    monkeypatch.setattr("analysis.inventory_remote_zip.urllib.request.urlopen", open_request)
    return requests


def test_reads_only_bounded_central_directory(monkeypatch):
    archive = fixture_archive()
    requests = mock_server(monkeypatch, archive)
    remote = RemoteZip("https://example.invalid/archive.zip", 4096)
    with zipfile.ZipFile(remote) as zipped:
        assert zipped.namelist() == ["one.vcf.gz", "two.vcf.gz"]
    assert remote.used < 4096
    assert len(requests) > 1
    assert all(request.get_header("Range") for request in requests[1:])


def test_rejects_server_that_ignores_range(monkeypatch):
    mock_server(monkeypatch, fixture_archive(), bad_range=True)
    remote = RemoteZip("https://example.invalid/archive.zip", 4096)
    with pytest.raises(ValueError, match="expected partial range"):
        remote.read(4)


def test_transfer_cap_rejects_request_before_network(monkeypatch):
    requests = mock_server(monkeypatch, fixture_archive())
    remote = RemoteZip("https://example.invalid/archive.zip", 8)
    with pytest.raises(ValueError, match="transfer budget"):
        remote.read(9)
    assert len(requests) == 1
