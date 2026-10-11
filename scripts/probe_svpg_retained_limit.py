"""Synthetic-only transient-memory probe; no real source files are accepted."""
from __future__ import annotations

from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from analysis.stage_svpg_callsets import _stage_member

LIMIT = 128 * 1024**2
HEADER = (b"##fileformat=VCFv4.2\n##contig=<ID=1,length=500000000>\n"
          b"#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSYNTHETIC\n")


class SyntheticStream:
    """Produce a repeated field in small reads, without storing the whole input."""
    def __init__(self, prefix, repeated_bytes, suffix):
        self.parts = [HEADER + prefix, repeated_bytes, suffix]
        self.offset = 0

    def read(self, size):
        if not 0 <= size <= 65_537:
            raise AssertionError("Unbounded synthetic read request")
        if size == 0:
            return b""
        result = bytearray()
        while self.parts and len(result) < size:
            part = self.parts[0]
            length = part if type(part) is int else len(part)
            take = min(size - len(result), length - self.offset)
            result.extend(b"A" * take if type(part) is int else part[self.offset:self.offset + take])
            self.offset += take
            if self.offset == length:
                self.parts.pop(0)
                self.offset = 0
        return bytes(result)


def run_probe():
    records = [
        (b"1\t100\t.\tA\t", b"\t.\tPASS\tSVTYPE=INS\tGT\t0/1\n"),
        (b"1\t100\t.\tA\tAC\t.\tPASS\tNOTE=", b"\tGT\t0/1\n"),
    ]
    for prefix, suffix in records:
        count = LIMIT - len(prefix) - len(suffix)
        with tempfile.TemporaryFile(mode="w+b") as output:
            report = _stage_member(SyntheticStream(prefix, count, suffix), output,
                                   [0, 3 * 1024**3], LIMIT, stream_rnames=True)
            assert report["records"] == 1
            assert report["streaming_buffers"]["max_retained_line_bytes"] == LIMIT
            assert report["streaming_buffers"]["max_read_chunk_bytes"] <= 65_537
            assert report["source_sha256"] == report["staged_sha256"]
            assert output.tell() == len(HEADER) + LIMIT
        # With just one extra retained byte the same route must fail, not truncate.
        with tempfile.TemporaryFile(mode="w+b") as output:
            try:
                _stage_member(SyntheticStream(prefix, count + 1, suffix), output,
                              [0, 3 * 1024**3], LIMIT, stream_rnames=True)
            except ValueError as exc:
                assert "Retained VCF line exceeds" in str(exc)
            else:
                raise AssertionError("Over-limit record was accepted")
    print("PASS: two exact 128-MiB synthetic retained-field cases and two overflow cases")


if __name__ == "__main__":
    run_probe()
