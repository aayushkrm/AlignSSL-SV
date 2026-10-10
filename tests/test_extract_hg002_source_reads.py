"""Small synthetic BAMs only; no real genomic inputs or external services."""
from array import array
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import signal
import sqlite3
from types import SimpleNamespace

import pysam
import pytest
from scripts import extract_hg002_source_reads as tool

HEADER = {"HD": {"VN": "1.6"}, "SQ": [{"SN": "synthetic", "LN": 1000}],
          "RG": [{"ID": "dna", "SM": "HG002_WGS"}]}
SEQ, QUAL = "ACGTACGA", list(range(10, 18))


def record(name="m/1/ccs", seq=SEQ, qual=QUAL, flag=0, cigar=None, tags=True):
    r = pysam.AlignedSegment()
    r.query_name, r.flag = name, flag
    stored = seq.translate(str.maketrans("ACGT", "TGCA"))[::-1] if seq and flag & 16 else seq
    r.query_sequence = stored
    r.query_qualities = array("B", qual[::-1] if flag & 16 else qual) if qual is not None else None
    r.reference_id, r.reference_start = (-1, -1) if flag & 4 else (0, 10)
    r.cigartuples = cigar if cigar is not None else None if flag & 4 else [(0, len(seq) if seq else 8)]
    if tags:
        r.set_tags([("RG", "dna"), ("HP", 1), ("PS", 100)])
    return r


def bam_file(tmp_path, records, name="input.bam"):
    path = tmp_path/name
    with pysam.AlignmentFile(path, "wb", header=HEADER) as out:
        for r in records: out.write(r)
    return path


def run(tmp_path, records, **kwargs):
    source = bam_file(tmp_path, records)
    before = source.read_bytes()
    result = tool.extract(source, tmp_path/"new", hashlib.sha256(before).hexdigest(),
                          remaining_s1_cpu_seconds=60, **kwargs)
    assert source.read_bytes() == before
    assert json.loads((tmp_path/"new/readiness.json").read_text()) == result
    return result


def fastq(tmp_path, partial=False):
    path = tmp_path/"new"/("source_reads.fastq.gz.partial" if partial else "source_reads.fastq.gz")
    return gzip.decompress(path.read_bytes()).decode().splitlines()


@pytest.mark.parametrize("full_reverse,fragment_reverse,late", [(a,b,c) for a in (False,True) for b in (False,True) for c in (False,True)])
def test_all_orientations_restore_fragment_and_later_full(tmp_path, full_reverse, fragment_reverse, late):
    full = record(flag=16 if full_reverse else 256)
    cigar = [(5,3),(0,3),(5,2)] if fragment_reverse else [(5,2),(0,3),(5,3)]
    fragment = record(seq=SEQ[2:5], qual=QUAL[2:5], flag=2048 | (16 if fragment_reverse else 0), cigar=cigar)
    result = run(tmp_path, [fragment, full] if late else [full, fragment])
    assert result["status"] == "READY_FOR_DNA_INPUT_REVIEW"
    assert result["census"]["restored_hardclip_ids"] == result["census"]["resolved_ids"] == 1
    assert fastq(tmp_path) == ["@m/1/ccs", SEQ, "+", "".join(chr(q+33) for q in QUAL)]
    db = sqlite3.connect(tmp_path/"new/identities.sqlite")
    assert db.execute("SELECT start,n,total FROM fragments").fetchone() == (2,3,8)
    assert all(len(x)==32 for x in db.execute("SELECT seqhash,qualhash FROM reads").fetchone())
    db.close()


def test_duplicate_unmapped_and_flags_are_not_filters(tmp_path):
    records = [record(flag=256), record(flag=2048|16), record("unmapped", flag=4|16, tags=False),
               record("qcfail", flag=512|1024), record("soft", cigar=[(4,2),(0,4),(4,2)])]
    result = run(tmp_path, records)
    assert result["census"]["original_ids"] == result["census"]["resolved_ids"] == 4
    assert result["census"]["resolved_bases"] == 32 and result["counts"]["duplicate_full_records"] == 1
    assert result["counts"]["HP_missing"] == 1 and result["tag_counts"]["HP"]["distinct_values"] == 1
    assert result["counts"]["unmapped_records"] == 1 and result["census"]["original_bases"] == 32
    assert result["archive_differences"]["observed_ids_minus_archive"] == 4-tool.ARCHIVE_IDS
    assert result["archive_differences"]["resolved_bases_minus_archive"] == 32-tool.ARCHIVE_BASES
    assert len(fastq(tmp_path)) == 16 and "SQ" not in result


@pytest.mark.parametrize("changed", ["sequence", "quality", "length"])
def test_conflicting_full_records_never_emit(tmp_path, changed):
    other = record(seq="TCGTACGA" if changed=="sequence" else SEQ+"A" if changed=="length" else SEQ,
                   qual=QUAL+[18] if changed=="length" else [20]*8 if changed=="quality" else QUAL)
    result = run(tmp_path, [record(), other])
    assert result["status"] == "INCOMPLETE" and result["census"]["conflicting_ids"] == 1
    assert result["census"]["unknown_ids"] == 1 and fastq(tmp_path, True) == []
    assert result["census"]["original_bases"] is None
    assert not (tmp_path/"new/source_reads.fastq.gz").exists()


@pytest.mark.parametrize("changed", ["sequence", "quality", "length"])
def test_fragment_constraint_conflicts(tmp_path, changed):
    fragment = record(seq="AAAA" if changed=="sequence" else SEQ[2:6],
                      qual=[40]*4 if changed=="quality" else QUAL[2:6],
                      cigar=[(5,2),(0,4),(5,3 if changed=="length" else 2)])
    result = run(tmp_path, [fragment, record()])
    assert result["status"] == "INCOMPLETE" and result["census"]["constraint_mismatch_ids"] == 1


@pytest.mark.parametrize("missing", ["sequence", "quality"])
@pytest.mark.parametrize("restored", [False, True])
def test_missing_payload_needs_later_complete_record(tmp_path, missing, restored):
    absent = record(seq=None if missing=="sequence" else SEQ, qual=None)
    result = run(tmp_path, [absent]+([record()] if restored else []))
    assert result["status"] == ("READY_FOR_DNA_INPUT_REVIEW" if restored else "INCOMPLETE")
    assert result["census"]["restored_missing_ids"] == int(restored)
    assert result["census"]["unknown_ids"] == int(not restored)


def test_unrecoverable_hardclip_identity_is_unknown(tmp_path):
    fragment = record(seq=SEQ[2:6], qual=QUAL[2:6], cigar=[(5,2),(0,4),(5,2)])
    result = run(tmp_path, [fragment, fragment])
    assert result["status"] == "INCOMPLETE" and result["census"]["original_ids"] == 1
    assert result["census"]["unknown_ids"] == 1 and result["census"]["resolved_bases"] == 0


@pytest.mark.parametrize("cigar", [[(0,7)], [(0,4),(5,1),(0,4)], [(0,3),(4,2),(0,3)], [(0,0)]])
def test_malformed_query_cigar_is_not_canonical(tmp_path, cigar):
    db = tool.make_index(tmp_path/"ids.sqlite"); counts = Counter()
    tool.observe(db, record(cigar=cigar), 1, counts)
    assert db.execute("SELECT bad,full_record FROM reads").fetchone() == (1, None)
    assert counts["malformed_records"] == 1
    db.commit(); db.close()


def test_missing_original_identity_is_not_a_molecule(tmp_path):
    db = tool.make_index(tmp_path/"ids.sqlite"); counts = Counter()
    tool.observe(db, record(name="*"), 1, counts)
    assert counts["unidentified_records"] == 1 and tool.census(db)["original_ids"] == 0
    db.close()


@pytest.mark.parametrize("damage", ["empty", "missing_eof", "bad_record", "corrupt_block"])
def test_empty_or_decode_errors_never_pass(tmp_path, damage):
    if damage == "bad_record":
        source = bam_file(tmp_path, [record(cigar=[(0,7)])])
    else:
        source = bam_file(tmp_path, [] if damage=="empty" else [record()])
    body = source.read_bytes()
    if damage == "missing_eof": source.write_bytes(body[:-28])
    if damage == "corrupt_block":
        altered = bytearray(body); altered[-40] ^= 127; source.write_bytes(altered)
    result = tool.extract(source, tmp_path/"new", hashlib.sha256(source.read_bytes()).hexdigest(), remaining_s1_cpu_seconds=60)
    assert result["status"] == "INCOMPLETE" and not result["archive_differences"]["complete_census"]
    assert (tmp_path/"new/readiness.json").is_file() and (tmp_path/"new/stats.jsonl").is_file()


def test_input_and_output_hashes_once_and_existing_refusal(tmp_path, monkeypatch):
    calls = []; original = tool.sha256_file
    def counted(path, guard):
        calls.append(path)
        return original(path, guard)
    monkeypatch.setattr(tool, "sha256_file", counted)
    result = run(tmp_path, [record()])
    source = tmp_path/"input.bam"; output = tmp_path/"new"
    assert calls.count(source) == 1 and calls.count(output/"source_reads.fastq.gz.partial") == 1
    assert result["objects"]["extracted_gzip_sha256"] == hashlib.sha256((output/"source_reads.fastq.gz").read_bytes()).hexdigest()
    saved = (output/"readiness.json").read_bytes()
    with pytest.raises(tool.ExtractionError):
        tool.extract(source, output, hashlib.sha256(source.read_bytes()).hexdigest(), remaining_s1_cpu_seconds=60)
    assert (output/"readiness.json").read_bytes() == saved


def test_cancel_deferred_until_record_is_persisted(tmp_path, monkeypatch):
    original = tool.observe; old = signal.getsignal(signal.SIGTERM)
    def cancelled(*args):
        signal.raise_signal(signal.SIGTERM)
        original(*args)
    monkeypatch.setattr(tool, "observe", cancelled)
    result = run(tmp_path, [record(), record("later")])
    assert result["status"] == "INCOMPLETE" and result["counts"]["records_pass1"] == 1
    assert result["census"]["original_ids"] == 1 and result["census"]["unknown_ids"] == 1
    assert not result["pass1_complete"] and signal.getsignal(signal.SIGTERM) == old


def test_budget_expiry_preserves_manifest(tmp_path, monkeypatch):
    source = bam_file(tmp_path, [record()]); clock = [0]
    original = tool.sha256_file
    def expired(path, guard):
        if path == source: clock[0] = 61
        return original(path, guard)
    monkeypatch.setattr(tool, "time", type("Clock", (), {"monotonic": lambda: clock[0], "process_time": lambda: 0}))
    monkeypatch.setattr(tool, "sha256_file", expired)
    result = tool.extract(source, tmp_path/"new", hashlib.sha256(source.read_bytes()).hexdigest(), remaining_s1_cpu_seconds=60)
    assert result["status"] == "INCOMPLETE" and "deadline" in result["error"]
    assert (tmp_path/"new/readiness.json").exists()


def test_index_limit_is_enforced_and_input_hash_mismatch_stops(tmp_path, monkeypatch):
    source = bam_file(tmp_path, [record()])
    mismatch = tool.extract(source, tmp_path/"mismatch", "0"*64, remaining_s1_cpu_seconds=60)
    assert mismatch["status"] == "INCOMPLETE" and "hash/stat" in mismatch["error"]
    monkeypatch.setattr(tool, "INDEX_LIMIT", 16384)
    result = tool.extract(source, tmp_path/"limit", hashlib.sha256(source.read_bytes()).hexdigest(), remaining_s1_cpu_seconds=60)
    assert result["status"] == "INCOMPLETE" and not result["pass1_complete"]
    assert (tmp_path/"limit/identities.sqlite").is_file()


@pytest.mark.parametrize("boundary", ["gzip_write", "publication"])
def test_cancel_cannot_become_ready_after_emission(tmp_path, monkeypatch, boundary):
    if boundary == "gzip_write":
        original = tool.gzip.GzipFile.write
        def cancelled_write(self, data):
            result = original(self, data)
            signal.raise_signal(signal.SIGTERM)
            return result
        monkeypatch.setattr(tool.gzip.GzipFile, "write", cancelled_write)
    else:
        original = tool.os.link
        def cancelled_link(*args):
            original(*args)
            signal.raise_signal(signal.SIGTERM)
        monkeypatch.setattr(tool.os, "link", cancelled_link)
    result = run(tmp_path, [record()])
    assert result["status"] == "INCOMPLETE" and result["census"]["resolved_ids"] == 1
    assert not result["archive_differences"]["complete_census"]


@pytest.mark.parametrize("reverse", [False, True])
def test_phred33_translation_all_valid_scores(tmp_path, reverse):
    qualities = list(range(94))
    result = run(tmp_path, [record(seq="A"*94, qual=qualities, flag=16 if reverse else 0)])
    assert result["status"] == "READY_FOR_DNA_INPUT_REVIEW"
    assert fastq(tmp_path)[3] == "".join(chr(q+33) for q in qualities)


@pytest.mark.parametrize("invalid", [94, 255])
def test_out_of_range_quality_never_becomes_canonical(tmp_path, invalid):
    db = tool.make_index(tmp_path/"ids.sqlite"); counts = Counter()
    tool.observe(db, record(qual=[20, invalid]+QUAL[2:]), 1, counts)
    assert db.execute("SELECT bad,full_record FROM reads").fetchone() == (1, None)
    db.close()


def test_preexisting_custody_cost_stops_before_source_hash(tmp_path):
    result = run(tmp_path, [record()], preexisting_s1_disk_bytes=tool.DISK_LIMIT-1)
    assert result["status"] == "INCOMPLETE" and "summed" in result["error"]
    assert "input_sha256" not in result and not result["pass1_complete"]
    assert result["sampled_peak_s1_disk_bytes"] > tool.DISK_LIMIT


def test_physical_free_space_stop_preserves_state(tmp_path, monkeypatch):
    monkeypatch.setattr(tool.shutil, "disk_usage", lambda _: SimpleNamespace(free=0))
    result = run(tmp_path, [record()])
    assert result["status"] == "INCOMPLETE" and "filesystem free" in result["error"]
    assert not result["pass1_complete"] and "input_sha256" not in result


@pytest.mark.parametrize("kind", ["quality", "fragment_quality", "sequence"])
@pytest.mark.parametrize("late", [False, True])
def test_reverse_missing_payload_is_restored(tmp_path, kind, late):
    absent = record(seq=None if kind=="sequence" else SEQ[2:6] if kind=="fragment_quality" else SEQ,
                    qual=None, flag=16|2048,
                    cigar=[(5,2),(0,4),(5,2)] if kind=="fragment_quality" else [(0,8)])
    result = run(tmp_path, [absent, record()] if late else [record(), absent])
    assert result["status"] == "READY_FOR_DNA_INPUT_REVIEW"
    assert result["census"]["restored_missing_ids"] == 1 and result["census"]["malformed_ids"] == 0


def test_reverse_missing_quality_fragment_disagreement(tmp_path):
    fragment = record(seq="AAAA", qual=None, flag=16|2048, cigar=[(5,2),(0,4),(5,2)])
    result = run(tmp_path, [fragment, record()])
    assert result["status"] == "INCOMPLETE" and result["census"]["constraint_mismatch_ids"] == 1


@pytest.mark.parametrize("fault", ["deadline", "cancel"])
def test_final_accounting_never_masks_expiry(tmp_path, monkeypatch, fault):
    clock = [0]
    real_census = tool.census
    visits = [0]
    def delayed(db):
        visits[0] += 1
        report = real_census(db)
        if visits[0] == 2:  # Final census, after the successful prepublication census.
            if fault == "deadline": clock[0] = 61
            else: signal.raise_signal(signal.SIGTERM)
        return report
    monkeypatch.setattr(tool, "time", type("Clock", (), {"monotonic": lambda: clock[0], "process_time": lambda: 0}))
    monkeypatch.setattr(tool, "census", delayed)
    result = run(tmp_path, [record()])
    assert result["status"] == "INCOMPLETE" and not result["archive_differences"]["complete_census"]
    assert result["census"]["original_bases"] is None
