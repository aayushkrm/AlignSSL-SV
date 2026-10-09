"""Mocked range controls; loopback HTTP only, no external network or genomics."""

import hashlib
import json
import tempfile
import threading
import time
import unittest
import urllib.request
from pathlib import Path

from scripts.acquire_parent_sva_region import (
    AcquisitionError,
    BAI_ETAG,
    BAI_URL,
    BAM_ETAG,
    BAM_SIZE,
    BodyLedger,
    BudgetExceeded,
    copy_counted,
    download_bai,
    parse_range,
    running_proxy,
    validate_206,
)


class FakeResponse:
    def __init__(self, status, headers, body=b""):
        self.status, self.headers, self.body = status, headers, body
        self.read_calls, self.offset = [], 0

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def getcode(self):
        return self.status

    def read(self, size=-1):
        self.read_calls.append(size)
        if size < 0:
            size = len(self.body) - self.offset
        block = self.body[self.offset:self.offset + size]
        self.offset += len(block)
        return block


class FakeOpener:
    def __init__(self, response):
        self.response, self.requests = response, []

    def __call__(self, request, timeout):
        assert timeout == 30
        self.requests.append(request)
        return self.response


def range_headers(size, etag=BAI_ETAG):
    return {"Content-Length": str(size), "Content-Range": f"bytes 0-{size - 1}/{size}",
            "Content-Encoding": "identity", "ETag": etag}


class AcquisitionRangeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def ledger(self, name="ledger.jsonl", *, limit=1024, prior=0):
        return BodyLedger(self.root / name, time.monotonic() + 60, limit=limit, prior=prior)

    def test_parser_preserves_htslib_open_stream_and_caps_explicit_range(self):
        self.assertEqual(parse_range("bytes=10-", 100), (10, 99))
        self.assertEqual(parse_range("bytes=10-500", 100), (10, 99))
        for value in ("", "bytes=-10"):
            with self.subTest(value=value), self.assertRaisesRegex(AcquisitionError, "explicit-start"):
                parse_range(value, 100)
        self.assertEqual(parse_range("bytes=0-", BAM_SIZE), (0, BAM_SIZE - 1))
        with self.assertRaisesRegex(AcquisitionError, "64 MiB"):
            parse_range(f"bytes=0-{BAM_SIZE - 1}", BAM_SIZE)

    def test_bai_download_pins_range_etag_length_and_actual_bytes(self):
        body = b"bai-index"
        opener = FakeOpener(FakeResponse(206, range_headers(len(body)), body))
        ledger, output = self.ledger(), self.root / "source.bam.bai"
        result = download_bai({"url": BAI_URL, "size_bytes": len(body), "etag": BAI_ETAG},
                              output, ledger, opener)
        ledger.close()
        request = opener.requests[0]
        self.assertEqual(request.get_header("Range"), f"bytes=0-{len(body) - 1}")
        self.assertEqual(request.get_header("If-match"), BAI_ETAG)
        self.assertEqual(output.read_bytes(), body)
        self.assertEqual(result["sha256"], hashlib.sha256(body).hexdigest())
        self.assertEqual(ledger.snapshot()["new_upstream_body_bytes"], len(body))
        events = [json.loads(line) for line in (self.root / "ledger.jsonl").read_text().splitlines()]
        self.assertTrue(any(row.get("actual_body_bytes") == len(body) for row in events))

    def test_200_fallback_is_rejected_unread_and_partial_is_kept(self):
        body = b"do-not-read"
        response = FakeResponse(200, {"Content-Length": str(len(body)), "ETag": BAI_ETAG}, body)
        ledger, output = self.ledger(), self.root / "source.bam.bai"
        with self.assertRaisesRegex(AcquisitionError, "did not return 206"):
            download_bai({"url": BAI_URL, "size_bytes": len(body), "etag": BAI_ETAG},
                         output, ledger, FakeOpener(response))
        ledger.close()
        self.assertEqual(response.read_calls, [])
        self.assertEqual((self.root / "source.bam.bai.partial").read_bytes(), b"")
        attempt = ledger.snapshot()["attempts"][0]
        self.assertEqual((attempt["response_status"], attempt["actual_body_bytes"]), (200, 0))

    def test_short_body_records_actual_bytes_and_retains_partial(self):
        response = FakeResponse(206, range_headers(6), b"abc")
        ledger, output = self.ledger(), self.root / "source.bam.bai"
        with self.assertRaisesRegex(AcquisitionError, "ended before Content-Length"):
            download_bai({"url": BAI_URL, "size_bytes": 6, "etag": BAI_ETAG},
                         output, ledger, FakeOpener(response))
        ledger.close()
        self.assertEqual((self.root / "source.bam.bai.partial").read_bytes(), b"abc")
        self.assertEqual(ledger.snapshot()["new_upstream_body_bytes"], 3)

    def test_global_budget_reservations_are_atomic_and_never_overread(self):
        ledger = self.ledger("parallel.jsonl", limit=8)
        barrier, grants, denied = threading.Barrier(3), [], []

        def reserve():
            barrier.wait()
            try:
                grants.append(ledger.reserve(8))
            except BudgetExceeded:
                denied.append(True)

        workers = [threading.Thread(target=reserve) for _ in range(2)]
        for worker in workers:
            worker.start()
        barrier.wait()
        for worker in workers:
            worker.join()
        for grant in grants:
            ledger.release(grant)
        self.assertEqual((grants, len(denied)), ([8], 1))
        ledger.close()

        ledger = self.ledger("capped.jsonl", limit=4)
        key = ledger.begin("bam_range", "https://example.test/bam", {"Range": "bytes=0-5"})
        sink = bytearray()

        class Sink:
            def write(self, block):
                sink.extend(block)

        with self.assertRaises(BudgetExceeded):
            copy_counted(FakeResponse(206, {}, b"abcdef"), Sink(), ledger, key, 6)
        ledger.finish(key, "incomplete")
        ledger.close()
        self.assertEqual(bytes(sink), b"abcd")
        self.assertEqual(ledger.snapshot()["new_upstream_body_bytes"], 4)

    def test_range_requires_206_exact_length_range_and_etag(self):
        cases = [
            (200, range_headers(4), "did not return 206"),
            (206, {**range_headers(4), "Content-Length": "3"}, "Content-Length"),
            (206, {**range_headers(4), "Content-Range": "bytes 1-4/4"}, "Content-Range"),
            (206, range_headers(4, '"changed"'), "ETag"),
        ]
        for status, headers, message in cases:
            with self.subTest(message=message), self.assertRaisesRegex(AcquisitionError, message):
                validate_206(FakeResponse(status, headers), 0, 3, 4, BAI_ETAG)

    def test_proxy_supports_initial_get_and_open_ended_htslib_seek(self):
        body = b"synthetic-byte-stream" * 5
        requests = []

        def opener(req, timeout):
            requests.append(req)
            start, end = parse_range(req.get_header("Range"), len(body))
            return FakeResponse(206, {"Content-Length": str(end-start+1),
                "Content-Range": f"bytes {start}-{end}/{len(body)}", "ETag": BAM_ETAG},
                body[start:end+1])

        bai = self.root / "mock.bai"
        bai.write_bytes(b"mock")
        ledger = self.ledger(limit=1024)
        with running_proxy({"size_bytes": len(body), "etag": BAM_ETAG},
                           {"size_bytes": 4, "etag": BAI_ETAG}, bai, ledger, opener) as url:
            with urllib.request.urlopen(url, timeout=2) as response:
                self.assertEqual(response.status, 200)
                self.assertEqual(response.read(), body)
            req = urllib.request.Request(url, headers={"Range": "bytes=10-"})
            with urllib.request.urlopen(req, timeout=2) as response:
                self.assertEqual(response.status, 206)
                self.assertEqual(response.read(), body[10:])
        ledger.close()
        self.assertEqual(ledger.snapshot()["new_upstream_body_bytes"], 2*len(body)-10)
        self.assertEqual(len(requests), 2)


if __name__ == "__main__":
    unittest.main()
