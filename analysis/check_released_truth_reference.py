"""Single sequential FASTA check, without normalization or random BGZF fetches.

This utility is not an approved real-data driver. Call only after exact
input/resource/protocol review. It checks original anchored REF alleles,
not event equivalence, phase, alternate haplotypes or caller performance.
"""
from __future__ import annotations

import gzip
from pathlib import Path

try:
    from .check_released_truth_metadata import require
except ImportError:
    from check_released_truth_metadata import require

MAX_FASTA_DECODED = 4 * 1024**3
MAX_CONTIG_BYTES = 256 * 1024**2
MAX_LINE = 1024**2
MAX_QUERY_RECORDS = 30_000
MAX_QUERY_REF_BYTES = 16 * 1024**2


def check_reference_stream(reference_gzip, lengths, queries, *,
                           max_decoded=MAX_FASTA_DECODED, max_contig=MAX_CONTIG_BYTES):
    """Check (identity, zero-based start, original REF bytes) queries by contig.

    ``lengths`` is the independently pinned FAI name/length dictionary. Read
    all FASTA members to EOF and verify every declared length, even contigs
    without queries. Retain at most one reference contig plus bounded queries.
    No genomic output is written. Exceptions fail the whole check.
    """
    require(type(max_decoded) is int and 0 < max_decoded <= MAX_FASTA_DECODED,
            "invalid decoded-byte limit")
    require(type(max_contig) is int and 0 < max_contig <= MAX_CONTIG_BYTES,
            "invalid contig-byte limit")
    require(isinstance(lengths, dict) and bool(lengths), "reference dictionary empty")
    require(all(isinstance(k, str) and k and type(v) is int and 0 < v <= max_contig
                for k, v in lengths.items()), "invalid reference dictionary")
    require(set(queries) <= set(lengths), "query contig absent from reference")
    seen_ids, ref_bytes = set(), 0
    for name, rows in queries.items():
        for identity, start, ref in rows:
            require(identity not in seen_ids, "duplicate query identity")
            require(len(seen_ids) < MAX_QUERY_RECORDS, "query count limit exceeded")
            seen_ids.add(identity)
            require(type(start) is int and start >= 0 and isinstance(ref, bytes) and bool(ref)
                    and start + len(ref) <= lengths[name], "invalid REF query bounds")
            require(all(c in b"ACGTacgt" for c in ref), "ambiguous query REF")
            ref_bytes += len(ref)
            require(ref_bytes <= MAX_QUERY_REF_BYTES, "query REF-byte limit exceeded")
    seen, name, sequence = set(), None, bytearray()
    decoded, checked = 0, 0

    def finish_contig():
        nonlocal checked
        require(name is not None, "FASTA sequence precedes first header")
        require(len(sequence) == lengths[name], "reference contig length mismatch")
        for identity, start, ref in queries.get(name, ()):
            require(sequence[start:start + len(ref)].upper() == ref.upper(),
                    f"original anchored REF mismatch for truth identity {identity}")
            checked += 1

    with Path(reference_gzip).open("rb") as compressed, gzip.GzipFile(fileobj=compressed) as stream:
        while True:
            raw = stream.readline(min(MAX_LINE + 1, max_decoded - decoded + 1))
            if not raw:
                break
            decoded += len(raw)
            require(decoded <= max_decoded, "FASTA decoded-byte cap exceeded")
            require(len(raw) <= MAX_LINE, "FASTA line cap exceeded")
            line = raw.rstrip(b"\r\n")
            if line.startswith(b">"):
                if name is not None:
                    finish_contig()
                parts = line[1:].split()
                require(bool(parts), "empty FASTA header")
                name = parts[0].decode("ascii")
                require(name in lengths and name not in seen, "unknown or duplicate FASTA contig")
                seen.add(name)
                sequence = bytearray()
            else:
                require(name is not None and bool(line)
                        and not line.translate(None, b"ACGTRYSWKMBDHVNacgtryswkmbdhvn"),
                        "invalid FASTA sequence line")
                require(len(sequence) + len(line) <= lengths[name], "reference exceeds declared length")
                sequence.extend(line)
    require(name is not None, "empty FASTA")
    finish_contig()
    require(seen == set(lengths), "missing reference contig")
    require(checked == len(seen_ids), "REF query cardinality mismatch")
    return dict(status="complete", reference_contigs=len(seen), checked_REF_records=checked,
                reference_delivered_decoded_bytes=decoded, query_REF_bytes=ref_bytes,
                whole_gzip_eof_crc_verified=True,
                normalization_performed=False, genomic_output_written=False)
