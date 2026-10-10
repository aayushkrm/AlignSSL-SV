"""Bounded byte-stream removal of the exact INFO/RNAMES field.

The raw record may be large. Only retained bytes and INFO keys are buffered.
All decoded source bytes (including discarded values) are hashed, validated
as UTF-8 and charged. Record ordering and all other bytes remain unchanged.
This is staging, not allele normalization or scientific filtering.
"""
from __future__ import annotations

import codecs
import hashlib
import re

CHUNK_BYTES = 65_536
_OUTSIDE = re.compile(br"[\t\n]")
_KEY = re.compile(br"[=;\t\n]")
_VALUE = re.compile(br"[;\t\n]")


def iter_stripped_vcf_lines(stream, budget, line_cap, stats, *, chunk_size=CHUNK_BYTES):
    """Yield ``(retained_line, omitted_count)`` using bounded ``read`` calls.

    ``budget`` is the shared mutable [charged bytes, source limit]. ``stats``
    reports actual delivered bytes, raw source SHA and parser-buffer maxima.
    A final record without LF is valid only with all ten VCF columns present.
    The caller still validates VCF headers, INFO/FORMAT syntax and coordinates.
    """
    if type(chunk_size) is not int or not 1 <= chunk_size <= CHUNK_BYTES:
        raise ValueError("Chunk size must be within 1..65536 bytes")
    if type(line_cap) is not int or line_cap < 1:
        raise ValueError("Positive retained line budget required")
    digest = hashlib.sha256()
    decoder = codecs.getincrementaldecoder("utf-8")("strict")
    stats.update(decoded_bytes=0, max_retained_line_bytes=0,
                 max_info_key_bytes=0, max_read_chunk_bytes=0, max_raw_line_bytes=0)
    retained = bytearray()
    key = bytearray()
    seen = set()
    key_memory = 0
    started = header = False
    col, mode, removed, kept, discard, raw_line_bytes = 0, "key", 0, 0, False, 0

    def append(piece):
        if len(retained) + len(piece) > line_cap:
            raise ValueError(f"Retained VCF line exceeds approved {line_cap}-byte bound")
        retained.extend(piece)
        stats["max_retained_line_bytes"] = max(stats["max_retained_line_bytes"], len(retained))

    def begin_token(has_value):
        nonlocal key_memory, kept, removed, discard
        token = bytes(key)
        if not token or token in seen:
            raise ValueError("Duplicate or empty INFO key")
        key_memory += len(token) + 128
        if key_memory > 4 * 1024**2:
            raise ValueError("INFO key metadata exceeds 4 MiB bound")
        seen.add(token)
        discard = token == b"RNAMES"
        if discard:
            removed += 1
        else:
            if kept:
                append(b";")
            append(token)
            if has_value:
                append(b"=")
            kept += 1
        key.clear()

    def reset():
        nonlocal started, header, col, mode, removed, kept, discard, key_memory, raw_line_bytes
        retained.clear()
        key.clear()
        seen.clear()
        started = header = False
        col, mode, removed, kept, discard, key_memory = 0, "key", 0, 0, False, 0
        raw_line_bytes = 0

    while True:
        remaining = budget[1] - budget[0]
        if remaining < 0:
            raise ValueError("Selected-source decoded body budget exceeded")
        chunk = stream.read(min(chunk_size, remaining) + 1)
        budget[0] += len(chunk)
        stats["decoded_bytes"] += len(chunk)
        stats["max_read_chunk_bytes"] = max(stats["max_read_chunk_bytes"], len(chunk))
        if budget[0] > budget[1]:
            raise ValueError("Selected-source decoded body budget exceeded")
        if not chunk:
            decoder.decode(b"", final=True)
            if started:
                if not header and col != 9:
                    raise ValueError("Truncated VCF record before all ten columns")
                yield bytes(retained), removed
            stats["source_sha256"] = digest.hexdigest()
            return
        digest.update(chunk)
        decoder.decode(chunk, final=False)
        offset = 0
        while offset < len(chunk):
            if not started:
                started, header = True, chunk[offset:offset + 1] == b"#"
            pattern = _OUTSIDE if header or col != 7 else _KEY if mode == "key" else _VALUE
            match = pattern.search(chunk, offset)
            end = match.start() if match else len(chunk)
            piece = chunk[offset:end]
            raw_line_bytes += len(piece) + int(match is not None)
            stats["max_raw_line_bytes"] = max(stats["max_raw_line_bytes"], raw_line_bytes)
            if not header and col == 7:
                if mode == "key":
                    if len(key) + len(piece) > line_cap:
                        raise ValueError("INFO key exceeds retained line budget")
                    key.extend(piece)
                    stats["max_info_key_bytes"] = max(stats["max_info_key_bytes"], len(key))
                elif not discard:
                    append(piece)
            else:
                append(piece)
            if match is None:
                break
            delimiter = match.group()
            offset = end + 1
            if header:
                append(delimiter)
                if delimiter == b"\n":
                    yield bytes(retained), removed
                    reset()
                continue
            if col == 7:
                if mode == "key":
                    begin_token(delimiter == b"=")
                    if delimiter == b"=":
                        mode = "value"
                        continue
                if delimiter == b";":
                    mode = "key"
                    continue
                if delimiter == b"\n":
                    raise ValueError("Truncated VCF record before all ten columns")
                if kept == 0:
                    append(b".")
                append(b"\t")
                col = 8
            else:
                append(delimiter)
                if delimiter == b"\t":
                    col += 1
                    if col > 9:
                        raise ValueError("Expected a single-sample VCF record")
                else:
                    if col != 9:
                        raise ValueError("Truncated VCF record before all ten columns")
                    yield bytes(retained), removed
                    reset()
