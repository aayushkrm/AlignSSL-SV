"""Synthetic adversarial checks for bounded INFO/RNAMES streaming."""

import hashlib
import io
import json
from pathlib import Path
import zipfile

import pytest

try:
    from analysis.stream_vcf_rnames import iter_stripped_vcf_lines
except ModuleNotFoundError as exc:
    if exc.name != "analysis.stream_vcf_rnames":
        raise
    pytest.skip("streaming VCF parser is not present yet", allow_module_level=True)

from analysis import stage_svpg_callsets as stage


HEADER = (
    b"##fileformat=VCFv4.2\r\n"
    b"##contig=<ID=chrSynthetic,length=100000>\n"
    b"#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSYNTHETIC\r\n"
)


def row(info=b"SVTYPE=DEL", *, alt=b"<DEL>", ending=b"\n", sample=b"0/1"):
    fields = (
        b"chrSynthetic", b"17", b"synthetic-17", b"N", alt, b".", b"PASS",
        info, b"GT", sample,
    )
    return b"\t".join(fields) + ending


def collect(raw, *, line_cap=4096, chunk_size=65536, initial=0, cap=None, stream=None):
    budget = [initial, initial + len(raw) if cap is None else cap]
    stats = {}
    source = io.BytesIO(raw) if stream is None else stream
    lines = list(iter_stripped_vcf_lines(source, budget, line_cap, stats,
                                         chunk_size=chunk_size))
    return lines, budget, stats


class StrictChunkStream(io.BytesIO):
    """Reject line reads and read requests larger than the parser contract."""

    def __init__(self, data, chunk_size):
        super().__init__(data)
        self.chunk_size = chunk_size
        self.requests = []

    def read(self, size=-1):
        assert 0 <= size <= self.chunk_size + 1
        self.requests.append(size)
        return super().read(size)

    def readline(self, size=-1):
        raise AssertionError("streaming parser must not call readline")


@pytest.mark.parametrize(
    "info,retained,removed",
    [
        (b"RNAMES=first;SVTYPE=DEL;END=17", b"SVTYPE=DEL;END=17", 1),
        (b"SVTYPE=DEL;RNAMES=middle;END=17", b"SVTYPE=DEL;END=17", 1),
        (b"SVTYPE=DEL;END=17;RNAMES=last", b"SVTYPE=DEL;END=17", 1),
        (b"RNAMES", b".", 1),
        (b"SVTYPE=DEL;RNAMES;END=17", b"SVTYPE=DEL;END=17", 1),
        (
            b"RNAMES=drop;MYRNAMES=keep;RNAMES2=keep2;XRNAMES=keep3",
            b"MYRNAMES=keep;RNAMES2=keep2;XRNAMES=keep3", 1,
        ),
        (
            b"MYRNAMES=keep;RNAMES2=keep2;XRNAMES=keep3",
            b"MYRNAMES=keep;RNAMES2=keep2;XRNAMES=keep3", 0,
        ),
    ],
)
def test_exact_rnames_key_is_removed_at_each_info_position(info, retained, removed):
    raw = HEADER + row(info, ending=b"\r\n")
    lines, budget, stats = collect(raw, chunk_size=1)
    assert b"".join(line for line, _ in lines) == HEADER + row(retained, ending=b"\r\n")
    assert [count for _, count in lines] == [0, 0, 0, removed]
    assert budget[0] == len(raw)
    assert stats["decoded_bytes"] == len(raw)


@pytest.mark.parametrize(
    "info",
    [
        b"RNAMES=one;RNAMES=two",
        b"SVTYPE=DEL;SVTYPE=DUP",
        b"RNAMES;RNAMES=two",
    ],
)
def test_duplicate_info_keys_are_rejected_even_when_rnames_is_discarded(info):
    with pytest.raises(ValueError, match="Duplicate or empty INFO key"):
        collect(HEADER + row(info), chunk_size=3)


def test_single_byte_chunks_split_every_delimiter_and_preserve_header_order():
    raw = (
        HEADER
        + row(b"SVTYPE=DEL;RNAMES=r1,r2;END=17;FLAG;MYRNAMES=keep", ending=b"\r\n")
        + row(b"RNAMES=only", ending=b"")
    )
    expected = (
        HEADER
        + row(b"SVTYPE=DEL;END=17;FLAG;MYRNAMES=keep", ending=b"\r\n")
        + row(b".", ending=b"")
    )
    lines, _, _ = collect(raw, chunk_size=1)
    assert b"".join(line for line, _ in lines) == expected
    assert [count for _, count in lines] == [0, 0, 0, 1, 1]


def test_large_discarded_value_uses_bounded_reads_without_readline():
    chunk_size = 37
    line_cap = 512
    value = b"read-name," * 900
    source_record = row(b"SVTYPE=INS;RNAMES=" + value + b";END=17")
    raw = HEADER + source_record
    stream = StrictChunkStream(raw, chunk_size)
    lines, budget, stats = collect(raw, line_cap=line_cap, chunk_size=chunk_size,
                                   stream=stream)

    expected_record = row(b"SVTYPE=INS;END=17")
    assert b"".join(line for line, _ in lines) == HEADER + expected_record
    assert lines[-1][1] == 1
    assert len(source_record) > line_cap
    assert len(expected_record) <= line_cap
    assert stats["max_raw_line_bytes"] > line_cap
    assert stats["max_retained_line_bytes"] <= line_cap
    assert stats["max_read_chunk_bytes"] <= chunk_size + 1
    assert max(stream.requests) <= chunk_size + 1
    assert stream.requests
    assert budget[0] == len(raw)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"alt": b"A" * 700},
        {"info": b"NOTE=" + b"x" * 700},
    ],
)
def test_oversized_retained_alt_or_info_fails_closed(kwargs):
    with pytest.raises(ValueError, match="Retained VCF line exceeds"):
        collect(HEADER + row(**kwargs), line_cap=512, chunk_size=29)


@pytest.mark.parametrize(
    "ending",
    [b"\r\n", b""],
)
def test_crlf_and_complete_record_without_final_lf_are_preserved(ending):
    raw = HEADER + row(b"SVTYPE=DEL;RNAMES=discard;END=17", ending=ending)
    expected = HEADER + row(b"SVTYPE=DEL;END=17", ending=ending)
    lines, _, _ = collect(raw, chunk_size=5)
    assert b"".join(line for line, _ in lines) == expected
    assert lines[-1][1] == 1


def test_invalid_utf8_is_rejected_inside_a_discarded_rnames_value():
    raw = HEADER + row(b"SVTYPE=DEL;RNAMES=valid-prefix-\xff-invalid;END=17")
    with pytest.raises(UnicodeDecodeError):
        collect(raw, chunk_size=7)


def test_source_hash_and_byte_count_cover_raw_bytes_through_completion():
    raw = HEADER + row(b"SVTYPE=INS;RNAMES=" + b"q" * 2048 + b";END=17", ending=b"\r\n")
    initial = 123
    budget = [initial, initial + len(raw)]
    stats = {}
    iterator = iter_stripped_vcf_lines(io.BytesIO(raw), budget, 512, stats, chunk_size=23)

    first = next(iterator)
    assert first[0] == HEADER.splitlines(keepends=True)[0]
    assert "source_sha256" not in stats
    rest = list(iterator)

    assert [count for _, count in [first, *rest]][-1] == 1
    assert stats["source_sha256"] == hashlib.sha256(raw).hexdigest()
    assert stats["decoded_bytes"] == len(raw)
    assert budget == [initial + len(raw), initial + len(raw)]


def test_decoded_budget_charges_discarded_bytes_and_detects_chunk_overrun():
    raw = HEADER + row(b"RNAMES=" + b"z" * 2000)
    limit = len(raw) - 1
    budget = [0, limit]
    stats = {}
    with pytest.raises(ValueError, match="decoded body budget exceeded"):
        list(iter_stripped_vcf_lines(io.BytesIO(raw), budget, 512, stats, chunk_size=41))
    assert budget[0] > limit
    assert stats["decoded_bytes"] == budget[0]
    assert "source_sha256" not in stats


def _stage_stream(raw, *, line_cap=512, chunk_size=31):
    output = io.BytesIO()
    report = stage._stage_member(
        io.BytesIO(raw), output, [0, max(len(raw), 4096)], line_cap,
        stream_rnames=True, chunk_size=chunk_size,
    )
    return output.getvalue(), report


def test_stage_rejects_truncated_rnames_record_before_format_and_sample():
    truncated = (
        b"chrSynthetic\t17\tsynthetic-17\tN\t<DEL>\t.\tPASS\tSVTYPE=DEL;RNAMES="
        + b"read," * 300
        + b"\n"
    )
    with pytest.raises(ValueError, match="Truncated VCF record before all ten columns"):
        _stage_stream(HEADER + truncated)


def test_stage_member_propagates_synthetic_zip_crc_failure():
    raw = HEADER + row(b"SVTYPE=DEL;RNAMES=discard;END=17")
    archive_buffer = io.BytesIO()
    with zipfile.ZipFile(archive_buffer, "w", compression=zipfile.ZIP_STORED) as archive:
        archive.writestr("synthetic.vcf", raw)

    damaged = bytearray(archive_buffer.getvalue())
    data_offset = damaged.find(raw)
    sample_offset = raw.find(b"\t0/1\n")
    assert data_offset >= 0 and sample_offset >= 0
    damaged[data_offset + sample_offset + 3] = ord("0")

    with zipfile.ZipFile(io.BytesIO(damaged)) as archive:
        with archive.open("synthetic.vcf") as member:
            output = io.BytesIO()
            with io.BufferedReader(member) as stream:
                with pytest.raises(zipfile.BadZipFile, match="CRC"):
                    stage._stage_member(
                        stream, output, [0, len(raw) + 10], 512,
                        stream_rnames=True, chunk_size=19,
                    )


def _write_protocol(tmp_path, protocol, name="synthetic-protocol.json"):
    raw = json.dumps(protocol, sort_keys=True).encode("utf-8")
    path = tmp_path / name
    path.write_bytes(raw)
    return path, hashlib.sha256(raw).hexdigest()


def _amendment_protocol():
    prior = stage.DECODED_CAP + 1
    return {
        "body_read_approved": True,
        "independent_outcome_approval": "synthetic-review-only",
        "header_protocol": {
            "members": list(stage.MEMBERS),
            "expected_archive_bytes": 1,
            "expected_archive_md5": "0" * 32,
            "verified_archive_sha256": "0" * 64,
        },
        "max_source_decoded_bytes": stage.AMENDED_DECODED_CAP,
        "charged_prior_source_decoded_bytes": prior,
        "max_line_bytes": 512,
        "controller_traffic_account": "synthetic-ledger",
        "source_pass_amendment": "remaining-five-stream-rnames-v1",
        "raw_line_policy": "stream_rnames",
        "execution_callers": list(stage.CALLERS[1:]),
        "reused_completed_callers": {"cutesv": {"synthetic_pin": True}},
        "global_decoded_limit_bytes": 6 * 1024**3,
        "charged_prior_global_decoded_bytes": prior,
    }


def test_three_gib_source_cap_requires_exact_remaining_five_amendment(tmp_path):
    protocol = _amendment_protocol()
    path, digest = _write_protocol(tmp_path, protocol)
    header, budget, line_cap, account, order_policy, parsed = stage._protocol(path, digest)
    assert budget == [stage.DECODED_CAP + 1, stage.AMENDED_DECODED_CAP]
    assert line_cap == 512
    assert account == "synthetic-ledger"
    assert header["members"] == list(stage.MEMBERS)
    assert parsed["execution_callers"] == list(stage.CALLERS[1:])

    legacy = dict(protocol)
    legacy.pop("source_pass_amendment")
    legacy["max_source_decoded_bytes"] = stage.DECODED_CAP + 1
    path, digest = _write_protocol(tmp_path, legacy, "synthetic-legacy.json")
    with pytest.raises(ValueError, match="within 2 GiB"):
        stage._protocol(path, digest)


@pytest.mark.parametrize(
    "field,value,message",
    [
        ("source_pass_amendment", "remaining-four-stream-rnames-v1", "Unsupported source-pass amendment"),
        ("execution_callers", list(stage.CALLERS), "exactly five unfinished callers"),
        ("reused_completed_callers", {"debreak": {"synthetic_pin": True}}, "cuteSV reuse"),
        ("raw_line_policy", "whole_line", "bounded streaming"),
    ],
)
def test_amendment_rejects_changed_selection_or_stream_policy(tmp_path, field, value, message):
    protocol = _amendment_protocol()
    protocol[field] = value
    path, digest = _write_protocol(tmp_path, protocol, f"bad-{field}.json")
    with pytest.raises(ValueError, match=message):
        stage._protocol(path, digest)


def _synthetic_amended_stage_inputs(tmp_path):
    raw_info = b"SVTYPE=DEL;RNAMES=" + b"synthetic-read," * 180 + b";END=17"
    raw_source = HEADER + row(raw_info)
    staged_source = HEADER + row(b"SVTYPE=DEL;END=17")
    archive_path = tmp_path / "synthetic-six-member.zip"
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_STORED) as archive:
        for member_name in stage.MEMBERS:
            archive.writestr(member_name, raw_source)
    archive_bytes = archive_path.read_bytes()

    with zipfile.ZipFile(archive_path) as archive:
        item = archive.getinfo(stage.MEMBERS[0])
    staged_path = tmp_path / "synthetic-completed-cutesv.vcf"
    staged_path.write_bytes(staged_source)
    completed = {
        "member": item.filename,
        "selected_member_crc_verified": True,
        "crc32": f"{item.CRC:08x}",
        "decoded_bytes": item.file_size,
        "records": 1,
        "source_sha256": hashlib.sha256(raw_source).hexdigest(),
        "staged_sha256": hashlib.sha256(staged_source).hexdigest(),
    }
    report_bytes = json.dumps({"completed_callers": {"cutesv": completed}},
                              sort_keys=True).encode("utf-8")
    report_path = tmp_path / "synthetic-completed-report.json"
    report_path.write_bytes(report_bytes)
    reuse_spec = {
        "report_path": str(report_path),
        "report_sha256": hashlib.sha256(report_bytes).hexdigest(),
        "staged_path": str(staged_path),
        "staged_bytes": len(staged_source),
        "source_sha256": completed["source_sha256"],
        "staged_sha256": completed["staged_sha256"],
    }

    selected_bytes = len(raw_source) * (len(stage.CALLERS) - 1)
    prior = stage.DECODED_CAP + 101
    protocol = {
        "body_read_approved": True,
        "independent_outcome_approval": "synthetic-review-only",
        "header_protocol": {
            "members": list(stage.MEMBERS),
            "expected_archive_bytes": len(archive_bytes),
            "expected_archive_md5": hashlib.md5(archive_bytes).hexdigest(),
            "verified_archive_sha256": hashlib.sha256(archive_bytes).hexdigest(),
        },
        "max_source_decoded_bytes": prior + selected_bytes,
        "charged_prior_source_decoded_bytes": prior,
        "max_line_bytes": 512,
        "controller_traffic_account": "synthetic-ledger",
        "source_pass_amendment": "remaining-five-stream-rnames-v1",
        "raw_line_policy": "stream_rnames",
        "execution_callers": list(stage.CALLERS[1:]),
        "reused_completed_callers": {"cutesv": reuse_spec},
        "global_decoded_limit_bytes": 6 * 1024**3,
        "charged_prior_global_decoded_bytes": prior,
    }
    return archive_path, protocol, raw_source, staged_source, reuse_spec


def test_remaining_five_amendment_reuses_pinned_cutesv_and_streams_only_five(tmp_path):
    archive_path, protocol, raw_source, staged_source, reuse_spec = _synthetic_amended_stage_inputs(tmp_path)
    protocol_path, digest = _write_protocol(tmp_path, protocol)
    report = stage.stage_zip(archive_path, tmp_path / "synthetic-amended-stage",
                             protocol_path, digest)

    assert report["source_decoded_cap"] > stage.DECODED_CAP
    assert report["execution_callers"] == list(stage.CALLERS[1:])
    assert report["reused_completed_callers"] == ["cutesv"]
    assert report["callers"]["cutesv"]["reused_completed_derivative"] is True
    assert report["callers"]["cutesv"]["source_sha256"] == hashlib.sha256(raw_source).hexdigest()
    assert report["callers"]["cutesv"]["staged_sha256"] == hashlib.sha256(staged_source).hexdigest()
    assert report["callers"]["cutesv"]["reuse_verification_bytes"] == reuse_spec["staged_bytes"]
    assert list(report["callers"]) == ["cutesv", *stage.CALLERS[1:]]

    for caller in stage.CALLERS[1:]:
        staged = (tmp_path / "synthetic-amended-stage" / f"{caller}.vcf").read_bytes()
        assert staged == staged_source
        caller_report = report["callers"][caller]
        assert caller_report["raw_line_policy"] == "stream_rnames"
        assert caller_report["omitted_RNAMES"] == 1
        assert caller_report["decoded_bytes"] == len(raw_source)
        assert caller_report["source_sha256"] == hashlib.sha256(raw_source).hexdigest()
        assert caller_report["streaming_buffers"]["max_raw_line_bytes"] > 512
        assert caller_report["streaming_buffers"]["max_retained_line_bytes"] <= 512

    assert report["unique_source_decoded_bytes"] == len(raw_source) * 5
    assert report["reuse_verification_bytes"] == reuse_spec["staged_bytes"]


def test_remaining_five_amendment_rejects_reused_source_hash_mismatch(tmp_path):
    archive_path, protocol, _, _, reuse_spec = _synthetic_amended_stage_inputs(tmp_path)
    protocol["reused_completed_callers"]["cutesv"]["source_sha256"] = "f" * 64
    protocol_path, digest = _write_protocol(tmp_path, protocol, "bad-reuse-pin.json")
    outdir = tmp_path / "synthetic-bad-reuse"

    with pytest.raises(ValueError, match="source/derivative metadata differs"):
        stage.stage_zip(archive_path, outdir, protocol_path, digest)

    failure = json.loads((outdir / "failure.json").read_text())
    assert failure["failed_caller"] == "cutesv"
    assert failure["completed_callers"] == {}
    assert failure["reuse_verification_reservation_bytes"] == reuse_spec["staged_bytes"]


class MeteredReader:
    def __init__(self, wrapped, before_first_read):
        self.wrapped = wrapped
        self.before_first_read = before_first_read
        self.did_mutate = False
        self.read_requests = []
        self.bytes_read = 0

    def __enter__(self):
        self.wrapped.__enter__()
        return self

    def __exit__(self, *args):
        return self.wrapped.__exit__(*args)

    def __getattr__(self, name):
        return getattr(self.wrapped, name)

    def read(self, size=-1):
        if not self.did_mutate:
            self.did_mutate = True
            self.before_first_read()
        self.read_requests.append(size)
        data = self.wrapped.read(size)
        self.bytes_read += len(data)
        return data


def _meter_reuse_reads(monkeypatch, staged_path, before_first_read):
    target = Path(staged_path).resolve()
    path_type = type(target)
    original_open = path_type.open
    readers = []

    def open_instrumented(path, *args, **kwargs):
        source = original_open(path, *args, **kwargs)
        mode = args[0] if args else kwargs.get("mode", "r")
        if Path(path).resolve() == target and mode == "rb":
            reader = MeteredReader(source, before_first_read)
            readers.append(reader)
            return reader
        return source

    monkeypatch.setattr(path_type, "open", open_instrumented)
    return readers, original_open


def _synthetic_cutesv_item(archive_path):
    with zipfile.ZipFile(archive_path) as archive:
        return archive.getinfo(stage.MEMBERS[0])


def test_reuse_growth_after_preflight_never_reads_beyond_reserved_bytes(tmp_path, monkeypatch):
    archive_path, _, _, _, spec = _synthetic_amended_stage_inputs(tmp_path)
    staged_path = Path(spec["staged_path"])

    def grow_after_preflight():
        with original_open(staged_path, "ab") as target:
            target.write(b"synthetic-growth-after-preflight")

    readers, original_open = _meter_reuse_reads(
        monkeypatch, staged_path, grow_after_preflight,
    )
    with pytest.raises(ValueError, match="SHA256 mismatch or source changed"):
        stage._reuse_completed(spec, "cutesv", _synthetic_cutesv_item(archive_path))

    assert len(readers) == 1
    assert readers[0].bytes_read == spec["staged_bytes"]
    assert readers[0].bytes_read <= spec["staged_bytes"]
    assert all(0 < request <= spec["staged_bytes"] for request in readers[0].read_requests)


def test_reuse_premature_eof_fails_before_reserved_length_is_consumed(tmp_path, monkeypatch):
    archive_path, _, _, _, spec = _synthetic_amended_stage_inputs(tmp_path)
    staged_path = Path(spec["staged_path"])
    shortened_length = max(1, spec["staged_bytes"] // 2)

    def truncate_after_preflight():
        with original_open(staged_path, "r+b") as target:
            target.truncate(shortened_length)

    readers, original_open = _meter_reuse_reads(
        monkeypatch, staged_path, truncate_after_preflight,
    )
    with pytest.raises(ValueError, match="ended before its reserved length"):
        stage._reuse_completed(spec, "cutesv", _synthetic_cutesv_item(archive_path))

    assert len(readers) == 1
    assert readers[0].bytes_read == shortened_length
    assert readers[0].bytes_read < spec["staged_bytes"]
    assert all(0 < request <= spec["staged_bytes"] for request in readers[0].read_requests)
