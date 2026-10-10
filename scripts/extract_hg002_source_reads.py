#!/usr/bin/env python3
"""S1b: reconcile complete original DNA molecules; no alignment or phase qualification."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import shutil
import signal
import sqlite3
import sys
import time

import pysam

ARCHIVE_IDS, ARCHIVE_BASES = 5_359_077, 80_344_827_828
PYSAM_VERSION = "0.24.1"
INDEX_LIMIT = 5 * 1024**3
DISK_LIMIT, MEMORY_LIMIT = 160 * 1024**3, 16 * 1024**3
CHUNK, CHECKPOINT = 1024**2, 1000
MIN_FREE = 1024**3
PHRED33 = bytes(q+33 if q <= 93 else 255 for q in range(256))
QUERY_OPS = {0, 1, 4, 7, 8}


class ExtractionError(RuntimeError):
    pass


def digest(value):
    return hashlib.sha256(value).digest() if value is not None else b""


def fingerprint(path):
    stat = path.stat()
    return [stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns]


def sha256_file(path, guard):
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        while True:
            guard()
            block = stream.read(CHUNK)
            if not block:
                break
            hasher.update(block)
    guard()
    return hasher.hexdigest()


def write_json(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write("\n")


def open_bam(path):
    bam = pysam.AlignmentFile(str(path), "rb", check_sq=False, ignore_truncation=False, threads=1)
    if not bam.is_bam:
        bam.close()
        raise ExtractionError("input must be BAM, not SAM/CRAM")
    return bam


def payload(record):
    """Return forward data and hard-clip constraints; never infer clipped bases."""
    seq = record.get_forward_sequence() if record.query_sequence is not None else None
    quality = record.get_forward_qualities() if record.query_qualities is not None else None
    qual = bytes(quality) if quality is not None else None
    cigar = record.cigartuples or []
    if not cigar and not record.is_unmapped:
        raise ExtractionError("mapped record lacks CIGAR")
    if any(op not in range(9) or size <= 0 for op, size in cigar):
        raise ExtractionError("invalid CIGAR operation/length")
    left = cigar[0][1] if cigar and cigar[0][0] == 5 else 0
    right = cigar[-1][1] if cigar and cigar[-1][0] == 5 else 0
    core = cigar[(1 if left else 0):len(cigar)-(1 if right else 0)]
    if any(op == 5 or (op == 4 and i not in (0, len(core)-1)) for i, (op, _) in enumerate(core)):
        raise ExtractionError("internal hard/soft clipping")
    consumed = sum(size for op, size in cigar if op in QUERY_OPS)
    if cigar and consumed <= 0:
        raise ExtractionError("CIGAR has no query bases")
    if seq is not None and (not seq or not re.fullmatch("[ACMGRSVTWYHKDBN]+", seq)):
        raise ExtractionError("invalid or reference-dependent query sequence")
    if seq is not None and cigar and len(seq) != consumed:
        raise ExtractionError("query length differs from CIGAR")
    if qual is not None and (seq is None or len(qual) != len(seq) or max(qual, default=0) > 93):
        raise ExtractionError("query quality length/range invalid")
    n = len(seq) if seq is not None else consumed if cigar else -1
    total = n + left + right if n >= 0 else -1
    start = right if record.is_reverse else left
    return seq, qual, start, n, total, bool(left or right)


def make_index(path):
    path.touch(exist_ok=False)
    db = sqlite3.connect(path)
    try:
        db.execute("PRAGMA journal_mode=DELETE")
        db.execute("PRAGMA synchronous=FULL")
        db.execute("PRAGMA cache_size=-32768")
        db.execute("PRAGMA temp_store=FILE")
        # At most 2 GiB of pages; rollback journal plus page overhead stays below 5 GiB.
        db.execute(f"PRAGMA max_page_count={(INDEX_LIMIT * 2 // 5) // db.execute('PRAGMA page_size').fetchone()[0]}")
        db.executescript("""
            CREATE TABLE reads (
                name TEXT PRIMARY KEY, full_record INTEGER, length INTEGER,
                seqhash BLOB, qualhash BLOB, records INTEGER DEFAULT 0,
                partial INTEGER DEFAULT 0, missing INTEGER DEFAULT 0,
                bad INTEGER DEFAULT 0, conflict INTEGER DEFAULT 0,
                flags INTEGER DEFAULT 0, emitted INTEGER DEFAULT 0, constraint_bad INTEGER DEFAULT 0);
            CREATE UNIQUE INDEX canonical ON reads(full_record) WHERE full_record IS NOT NULL;
            CREATE TABLE fragments (name TEXT, start INTEGER, n INTEGER, total INTEGER,
                seqhash BLOB, qualhash BLOB, UNIQUE(name,start,n,total,seqhash,qualhash));
            CREATE TABLE tags (kind TEXT, value TEXT, n INTEGER, PRIMARY KEY(kind,value));
        """)
        return db
    except BaseException:
        db.close()
        raise


def observe(db, record, ordinal, counts):
    counts["records_pass1"] += 1
    counts[f"FLAG_{record.flag}"] += 1
    for mask, label in ((4, "unmapped"), (16, "reverse"), (256, "secondary"), (512, "qcfail"), (1024, "duplicate_flag"), (2048, "supplementary")):
        counts[label + "_records"] += int(bool(record.flag & mask))
    for tag in ("RG", "HP", "PS"):
        if record.has_tag(tag):
            value = str(record.get_tag(tag))
            # Bound tag storage without selecting molecules by metadata.
            if len(value) > 256:
                value = "LONG_VALUE_SHA256:" + hashlib.sha256(value.encode()).hexdigest()
            db.execute("INSERT INTO tags VALUES (?,?,1) ON CONFLICT(kind,value) DO UPDATE SET n=n+1", (tag, value))
            counts[tag + "_present"] += 1
        else:
            counts[tag + "_missing"] += 1
    name = record.query_name
    if not name or name == "*" or not re.fullmatch(r"[!-?A-~]{1,254}", name):
        counts["unidentified_records"] += 1
        return
    db.execute("INSERT OR IGNORE INTO reads(name) VALUES (?)", (name,))
    db.execute("UPDATE reads SET records=records+1,flags=flags|? WHERE name=?", (record.flag, name))
    try:
        seq, qual, start, n, total, hard = payload(record)
    except Exception:
        counts["malformed_records"] += 1
        db.execute("UPDATE reads SET bad=1 WHERE name=?", (name,))
        return
    missing = seq is None or qual is None
    counts["hard_clipped_records"] += int(hard)
    counts["missing_sequence_records"] += int(seq is None)
    counts["missing_quality_records"] += int(qual is None)
    db.execute("UPDATE reads SET partial=partial+?,missing=missing+? WHERE name=?", (int(hard), int(missing), name))
    seqhash, qualhash = digest(seq.encode() if seq is not None else None), digest(qual)
    if hard or missing:
        db.execute("INSERT OR IGNORE INTO fragments VALUES (?,?,?,?,?,?)", (name, start, n, total, seqhash, qualhash))
        return
    previous = db.execute("SELECT full_record,length,seqhash,qualhash FROM reads WHERE name=?", (name,)).fetchone()
    if previous[0] is None:
        db.execute("UPDATE reads SET full_record=?,length=?,seqhash=?,qualhash=? WHERE name=?",
                   (ordinal, n, seqhash, qualhash, name))
    elif previous[1:] != (n, seqhash, qualhash):
        db.execute("UPDATE reads SET conflict=1 WHERE name=?", (name,))
        counts["conflicting_full_records"] += 1
    else:
        counts["duplicate_full_records"] += 1


def matches_fragments(db, name, seq, qual):
    for start, n, total, seqhash, qualhash in db.execute(
            "SELECT start,n,total,seqhash,qualhash FROM fragments WHERE name=?", (name,)):
        if total >= 0 and total != len(seq):
            return False
        if n >= 0 and (start < 0 or start+n > len(seq)):
            return False
        if seqhash and digest(seq[start:start+n].encode()) != seqhash:
            return False
        if qualhash and digest(qual[start:start+n]) != qualhash:
            return False
    return True


def census(db):
    row = db.execute("""SELECT count(*),coalesce(sum(emitted),0),
        coalesce(sum(CASE WHEN emitted=1 THEN length ELSE 0 END),0),
        coalesce(sum(CASE WHEN emitted=1 AND partial>0 THEN 1 ELSE 0 END),0),
        coalesce(sum(CASE WHEN emitted=1 AND missing>0 THEN 1 ELSE 0 END),0),
        coalesce(sum(conflict),0),coalesce(sum(bad),0),coalesce(sum(constraint_bad),0)
        FROM reads""").fetchone()
    return dict(zip(("original_ids", "resolved_ids", "resolved_bases", "restored_hardclip_ids",
                     "restored_missing_ids", "conflicting_ids", "malformed_ids", "constraint_mismatch_ids"), row))


def extract(source, output, expected_sha256, *, remaining_s1_cpu_seconds, preexisting_s1_disk_bytes=0):
    """One CPU; wall allowance cannot exceed the caller's remaining S1 CPU account."""
    if not re.fullmatch("[0-9a-f]{64}", expected_sha256):
        raise ExtractionError("require the complete input SHA256 from acquisition")
    if type(remaining_s1_cpu_seconds) is not int or not 0 < remaining_s1_cpu_seconds <= 8*3600:
        raise ExtractionError("remaining S1 CPU allowance must be positive and at most 8 CPU hours")
    if type(preexisting_s1_disk_bytes) is not int or not 0 <= preexisting_s1_disk_bytes < DISK_LIMIT:
        raise ExtractionError("invalid preexisting S1 disk account, excluding source BAM and new output")
    source, output = Path(source).resolve(strict=True), Path(output)
    if not source.is_file() or output.exists() or output.is_symlink() or not output.parent.is_dir():
        raise ExtractionError("require local input and an exclusive new output directory")
    if signal.getitimer(signal.ITIMER_REAL)[0]:
        raise ExtractionError("existing wall timer prevents stage deadline control")
    output.mkdir(mode=0o700)
    out = output.resolve()
    started, cpu_start = time.monotonic(), time.process_time()
    allowance = remaining_s1_cpu_seconds  # One allocated CPU: wall seconds equal allocated CPU seconds.
    counts, cancelled, handlers = Counter(), [], {}
    deadline = started + allowance
    initial_stat = None
    manifest = {"stage": "S1b", "status": "INCOMPLETE", "scope": "FULL_SOURCE_READ_EXTRACTION_ONLY",
                "alignment_calling_phase_qualification": "NOT_ASSESSED", "source": str(source),
                "expected_input_sha256": expected_sha256, "pass1_complete": False, "pass2_complete": False,
                "limits": {"cpus": 1, "memory_bytes": MEMORY_LIMIT, "wall_seconds": allowance,
                           "remaining_s1_cpu_seconds": remaining_s1_cpu_seconds, "index_bytes": INDEX_LIMIT,
                           "s1_total_disk_bytes": DISK_LIMIT, "preexisting_s1_disk_bytes": preexisting_s1_disk_bytes,
                           "minimum_filesystem_free_bytes": MIN_FREE},
                "runtime": {"python": sys.version, "pysam": pysam.__version__, "sqlite": sqlite3.sqlite_version, "executable": sys.executable},
                "archive": {"ids": ARCHIVE_IDS, "bases": ARCHIVE_BASES}, "counts": {}, "objects": {}}
    manifest["count_scope"] = "Observed prefix until both passes finish; never infer unseen identities"
    manifest["index_peak_measurement"] = "Checkpoint/final file sizes; SQLite page cap also enforced"
    db, journal = None, None
    peak_index = 0
    peak_s1_disk = 0
    partial, complete = out/"source_reads.fastq.gz.partial", out/"source_reads.fastq.gz"

    def request_stop(signum, _):
        cancelled.append(signum)  # Defer exceptions until a safe checkpoint.

    def guard():
        if cancelled or time.monotonic() >= deadline:
            raise ExtractionError("cancelled or wall deadline reached")
        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if sys.platform == "darwin" else 1024)
        if rss > MEMORY_LIMIT:
            raise ExtractionError("16 GiB process RSS limit reached")

    def checkpoint():
        nonlocal peak_index, peak_s1_disk
        guard()
        sizes = sum(p.stat().st_size for p in out.glob("identities.sqlite*"))
        peak_index = max(peak_index, sizes)
        if sizes > INDEX_LIMIT:
            raise ExtractionError("identity index disk limit reached")
        own_bytes = sum(p.stat().st_size for p in out.iterdir() if p.is_file())
        aggregate = preexisting_s1_disk_bytes + initial_stat[2] + own_bytes
        peak_s1_disk = max(peak_s1_disk, aggregate)
        if aggregate > DISK_LIMIT:
            raise ExtractionError("summed source/custody/output exceed the S1 disk account")
        if shutil.disk_usage(out).free < MIN_FREE:
            raise ExtractionError("at least 1 GiB filesystem free space required")
        db.commit()
        journal.write(json.dumps({"counts": dict(counts), "pass1_complete": manifest["pass1_complete"],
                                  "index_bytes": sizes, "wall_seconds": time.monotonic()-started})+"\n")
        journal.flush()

    try:
        write_json(out/"manifest.initial.json", manifest)
        journal = (out/"stats.jsonl").open("x", encoding="utf-8")
        if pysam.__version__ != PYSAM_VERSION:
            raise ExtractionError("require the tested pysam 0.24.1 runtime")
        for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGALRM):
            handlers[sig] = signal.signal(sig, request_stop)
        signal.setitimer(signal.ITIMER_REAL, allowance)
        db = make_index(out/"identities.sqlite")
        initial_stat = fingerprint(source)
        manifest["input_stat"] = initial_stat
        checkpoint()  # Stop before reading the large source if the disk account cannot fit.
        manifest["code_sha256"] = sha256_file(Path(__file__), guard)
        manifest["input_sha256"] = sha256_file(source, guard)
        if manifest["input_sha256"] != expected_sha256 or fingerprint(source) != initial_stat:
            raise ExtractionError("input hash/stat differs from pinned source")
        with open_bam(source) as bam:
            manifest["read_groups"] = bam.header.to_dict().get("RG", [])  # No SQ dump.
            for ordinal, record in enumerate(bam.fetch(until_eof=True), 1):
                guard()
                observe(db, record, ordinal, counts)
                if ordinal % CHECKPOINT == 0:
                    checkpoint()
        checkpoint()
        manifest["pass1_complete"] = True
        if fingerprint(source) != initial_stat:
            raise ExtractionError("input changed during pass 1")
        with partial.open("xb") as raw, gzip.GzipFile(filename="", mode="wb", compresslevel=1, fileobj=raw, mtime=0) as fastq:
            with open_bam(source) as bam:
                for ordinal, record in enumerate(bam.fetch(until_eof=True), 1):
                    guard()
                    counts["records_pass2"] += 1
                    row = db.execute("SELECT name,length,seqhash,qualhash,bad,conflict FROM reads WHERE full_record=?", (ordinal,)).fetchone()
                    if row is not None:
                        name, n, seqhash, qualhash, bad, conflict = row
                        if record.query_name != name:
                            raise ExtractionError("canonical identity changed between passes")
                        if not bad and not conflict:
                            seq, qual, _, _, _, hard = payload(record)
                            if hard or seq is None or qual is None or len(seq) != n or digest(seq.encode()) != seqhash or digest(qual) != qualhash:
                                raise ExtractionError("canonical payload changed between passes")
                            if matches_fragments(db, name, seq, qual):
                                data = b"@"+name.encode()+b"\n"+seq.encode()+b"\n+\n"+qual.translate(PHRED33)+b"\n"
                                fastq.write(data)
                                db.execute("UPDATE reads SET emitted=1 WHERE name=?", (name,))
                                counts["emitted_ids"] += 1
                                counts["emitted_bases"] += n
                            else:
                                db.execute("UPDATE reads SET constraint_bad=1 WHERE name=?", (name,))
                    if ordinal % CHECKPOINT == 0:
                        fastq.flush()
                        raw.flush()
                        checkpoint()
        checkpoint()
        if counts["records_pass2"] != counts["records_pass1"] or fingerprint(source) != initial_stat:
            raise ExtractionError("input/record count changed between passes")
        manifest["pass2_complete"] = True
        manifest["objects"]["extracted_gzip_sha256"] = sha256_file(partial, guard)
        report = census(db)
        if report["original_ids"] == 0 or report["resolved_ids"] != report["original_ids"] or counts["unidentified_records"]:
            raise ExtractionError("empty source or unresolved original identities; no complete readset")
        guard()
        if fingerprint(source) != initial_stat:
            raise ExtractionError("input changed before publication")
        os.link(partial, complete)
        partial.unlink()
        checkpoint()
        manifest["status"] = "READY_FOR_DNA_INPUT_REVIEW"
    except BaseException as exc:
        manifest["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        if cancelled or time.monotonic() >= deadline:
            manifest.update(status="INCOMPLETE", error="cancelled or wall deadline reached")
        if db is not None:
            try:
                db.commit()
                manifest["census"] = census(db)
                manifest["census"]["unknown_ids"] = manifest["census"]["original_ids"]-manifest["census"]["resolved_ids"]
                manifest["tag_counts"] = {tag: {"distinct_values": db.execute("SELECT count(*) FROM tags WHERE kind=?", (tag,)).fetchone()[0],
                    "examples": [list(row) for row in db.execute("SELECT value,n FROM tags WHERE kind=? ORDER BY n DESC,value LIMIT 10", (tag,))]} for tag in ("RG", "HP", "PS")}
                manifest["unknown_examples"] = [row[0] for row in db.execute("SELECT name FROM reads WHERE emitted=0 ORDER BY name LIMIT 10")]
            except Exception as exc:
                manifest["status"] = "INCOMPLETE"
                manifest["index_error"] = str(exc)
            db.close()
        c = manifest.get("census", {})
        manifest.update(counts=dict(counts), wall_seconds=time.monotonic()-started, measured_cpu_seconds=time.process_time()-cpu_start,
                        peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if sys.platform == "darwin" else 1024),
                        allocated_cpu_seconds=time.monotonic()-started, peak_index_bytes=max(peak_index, sum(p.stat().st_size for p in out.glob("identities.sqlite*"))),
                        sampled_peak_s1_disk_bytes=peak_s1_disk,
                        index_bytes=sum(p.stat().st_size for p in out.glob("identities.sqlite*")),
                        gzip_bytes=next((p.stat().st_size for p in (complete, partial) if p.exists()), 0))
        # Accounting queries and file measurements also consume the deadline.
        # Keep handlers active until the final status has been recorded.
        try:
            if cancelled or time.monotonic() >= deadline:
                manifest.update(status="INCOMPLETE", error="cancelled or wall deadline reached")
            if journal is not None:
                journal.write(json.dumps({"final_status": manifest["status"], "counts": dict(counts)})+"\n")
                journal.close()
            if cancelled or time.monotonic() >= deadline:
                manifest.update(status="INCOMPLETE", error="cancelled or wall deadline reached")
            manifest["wall_seconds"] = time.monotonic()-started
            manifest["allocated_cpu_seconds"] = manifest["wall_seconds"]
            manifest["allocation_measurement"] = "process wall at one requested CPU; charge actual Slurm allocation separately"
            if c:
                c["original_bases"] = c["resolved_bases"] if manifest["status"] == "READY_FOR_DNA_INPUT_REVIEW" else None
            manifest["archive_differences"] = {"observed_ids_minus_archive": c.get("original_ids", 0)-ARCHIVE_IDS,
                "resolved_bases_minus_archive": c.get("resolved_bases", 0)-ARCHIVE_BASES,
                "complete_census": manifest["status"] == "READY_FOR_DNA_INPUT_REVIEW"}
            write_json(out/"readiness.json", manifest)
        finally:
            if handlers:
                signal.setitimer(signal.ITIMER_REAL, 0)
                for sig, handler in handlers.items():
                    signal.signal(sig, handler)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bam", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--input-sha256", required=True)
    parser.add_argument("--remaining-s1-cpu-seconds", type=int, required=True)
    parser.add_argument("--preexisting-s1-disk-bytes", type=int, required=True,
                        help="All retained S1 bytes except the source BAM and this new output; freeze during this stage")
    args = parser.parse_args()
    result = extract(args.bam, args.output, args.input_sha256,
                     remaining_s1_cpu_seconds=args.remaining_s1_cpu_seconds,
                     preexisting_s1_disk_bytes=args.preexisting_s1_disk_bytes)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "READY_FOR_DNA_INPUT_REVIEW" else 2


if __name__ == "__main__":
    raise SystemExit(main())
