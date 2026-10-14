"""Synthetic-only contracts for the fixed regional BAM extraction sidecar."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


ANALYSIS_DIR = Path(__file__).resolve().parents[1] / "analysis"
if str(ANALYSIS_DIR) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_DIR))

import extract_inv_mapped_case_input as extract  # noqa: E402


REFERENCE = "A" * extract.REGION_LENGTH


class FakeAlignment:
    def __init__(
        self,
        *,
        qname="read-1",
        flag=0,
        sequence="A",
        quality="I",
        cigar=((7, 1),),
        reference_start=extract.REGION_START,
        mapq=0,
        tags=(),
        qalign_start=None,
        qalign_end=None,
    ):
        self.query_name = qname
        self.flag = flag
        self.query_sequence = sequence
        self.qual = quality
        self.query_qualities = None if quality is None else [ord(base) - 33 for base in quality]
        self.query_length = None if sequence is None else len(sequence)
        self.cigartuples = list(cigar)
        self.reference_start = reference_start
        self.reference_name = extract.CHROMOSOME
        self.mapping_quality = mapq
        self._tags = list(tags)
        self.cigarstring = "".join(f"{length}{extract.CIGAR_NAMES[code]}" for code, length in self.cigartuples)
        reference_consumed = sum(
            length for code, length in self.cigartuples if code in extract.REFERENCE_CONSUMING
        )
        self.reference_end = None if reference_start is None else reference_start + reference_consumed
        if qalign_start is None:
            qalign_start = 0
            for code, length in self.cigartuples:
                if code == 4:
                    qalign_start += length
                elif code in extract.QUERY_CONSUMING:
                    break
        if qalign_end is None:
            qalign_end = self.query_length
            if qalign_end is not None:
                for code, length in reversed(self.cigartuples):
                    if code == 4:
                        qalign_end -= length
                    elif code in extract.QUERY_CONSUMING:
                        break
        self.query_alignment_start = qalign_start
        self.query_alignment_end = qalign_end

    def get_tags(self, with_value_type=False):
        if with_value_type:
            return self._tags
        return [(name, value) for name, value, _value_type in self._tags]


def _reference_document(dna=REFERENCE):
    return {
        "genome": "hg38",
        "chrom": "chr2",
        "start": extract.REGION_START,
        "end": extract.REGION_END,
        "dna": dna,
    }


def _jsonl_line(value):
    return extract._json_bytes(value)


def _header_line():
    return _jsonl_line({
        "record_type": "header",
        "schema_version": 1,
        "region": {
            "chromosome": extract.CHROMOSOME,
            "start_zero_based_inclusive": extract.REGION_START,
            "end_zero_based_exclusive": extract.REGION_END,
            "length_bp": extract.REGION_LENGTH,
        },
        "coordinate_system": "zero-based half-open",
    })


def test_reference_json_requires_exact_fixed_window_and_dna():
    reference = extract.validate_reference_json(json.dumps(_reference_document()).encode())

    assert reference["genome"] == "hg38"
    assert reference["start"] == extract.REGION_START
    assert reference["end"] == extract.REGION_END
    assert reference["dna"] == REFERENCE
    assert reference["dna_sha256"] == hashlib.sha256(REFERENCE.encode()).hexdigest()

    wrong_start = _reference_document()
    wrong_start["start"] -= 1
    with pytest.raises(extract.ExtractionError, match="start differs"):
        extract.validate_reference_json(json.dumps(wrong_start).encode())
    wrong_dna = _reference_document(dna="N" + REFERENCE[1:])
    with pytest.raises(extract.ExtractionError, match="outside A/C/G/T"):
        extract.validate_reference_json(json.dumps(wrong_dna).encode())
    with pytest.raises(extract.ExtractionError, match="29,000"):
        extract.validate_reference_json(json.dumps(_reference_document(dna="A")).encode())


def test_forward_and_reverse_query_hashes_and_genomic_ordered_coordinates():
    forward_sequence = "AACGTA"
    forward_quality = "abcdef"
    reverse_stored_sequence = "TACGTT"
    reverse_stored_quality = "fedcba"
    cigar = ((4, 1), (7, 3), (4, 2))

    forward, _ = extract.alignment_record_and_witness(
        FakeAlignment(sequence=forward_sequence, quality=forward_quality, cigar=cigar),
        REFERENCE,
    )
    reverse, _ = extract.alignment_record_and_witness(
        FakeAlignment(
            flag=0x10,
            sequence=reverse_stored_sequence,
            quality=reverse_stored_quality,
            cigar=cigar,
        ),
        REFERENCE,
    )

    expected_sequence_hash = hashlib.sha256(forward_sequence.encode()).hexdigest()
    expected_quality_hash = hashlib.sha256(forward_quality.encode()).hexdigest()
    assert forward["sequence_reference_oriented_bam"] == forward_sequence
    assert reverse["sequence_reference_oriented_bam"] == reverse_stored_sequence
    assert forward["forward_query_sequence_sha256_uppercase"] == expected_sequence_hash
    assert reverse["forward_query_sequence_sha256_uppercase"] == expected_sequence_hash
    assert reverse["forward_query_quality_sha256"] == expected_quality_hash
    assert forward["query_alignment_interval_forward"] == [1, 4]
    assert reverse["query_alignment_interval_forward"] == [2, 5]
    assert reverse["cigar_walk_genomic_order"][1]["query_interval_reference_oriented_cigar"] == [1, 4]
    assert reverse["cigar_walk_genomic_order"][1]["query_interval_forward_cigar"] == [2, 5]


def test_equals_witness_compares_only_code7_and_cigar_consumption_bounds():
    cigar = (
        (4, 1),  # S consumes query only
        (7, 3),  # = consumes query and reference
        (0, 2),  # M is not an equality witness
        (8, 1),  # X is not an equality witness
        (2, 2),  # D consumes reference only
        (3, 3),  # N consumes reference only
        (1, 1),  # I consumes query only
        (5, 2),  # H does not advance stored query; full query is unknown
        (6, 1),  # P advances neither
        (4, 1),  # trailing S consumes query
    )
    alignment = FakeAlignment(
        sequence="GACCTTCGT",
        quality="I" * 9,
        cigar=cigar,
        qalign_start=1,
        qalign_end=8,
        reference_start=extract.REGION_START + 10,
        tags=[
            ("SA", "chr2,240675010,+,5M2S,60,1;", "Z"),
            ("RG", "rg-1", "Z"),
            ("HP", 2, "C"),
            ("PS", 12345, "i"),
            ("MD", "3A2", "Z"),
            ("NM", 1, "i"),
            ("AS", 42, "i"),
            ("ip", [1, 2, 3], "B"),
            ("MM", "C+m,0;", "Z"),
            ("ML", [200, 220], "B"),
        ],
    )
    record, observations = extract.alignment_record_and_witness(alignment, REFERENCE)

    assert record["reference_start_zero_based"] == extract.REGION_START + 10
    assert record["reference_end_zero_based_exclusive"] == extract.REGION_START + 21
    assert record["full_query_payload_status"] == "UNKNOWN_HARD_CLIPPED_QUERY_BASES_NOT_STORED"
    assert record["cigar_walk_genomic_order"][0]["query_interval_reference_oriented_cigar"] == [0, 1]
    assert record["cigar_walk_genomic_order"][6]["query_interval_reference_oriented_cigar"] == [7, 8]
    assert record["cigar_walk_genomic_order"][7]["query_interval_reference_oriented_cigar"] is None
    assert record["cigar_walk_genomic_order"][8]["reference_interval_zero_based_half_open"] is None
    assert record["equals_reference_witness"]["equals_reference_bases_compared"] == 3
    assert record["equals_reference_witness"]["equals_reference_base_conflicts"] == 2
    assert [item[2] for item in observations] == ["A", "C", "C"]
    assert record["essential_tags_typed"][0] == {
        "name": "SA", "type": "Z", "value": "chr2,240675010,+,5M2S,60,1;"
    }
    assert record["essential_tags_typed"][2] == {"name": "HP", "type": "C", "value": 2}
    assert record["omitted_tag_names_only"] == ["ip", "MM", "ML"]
    encoded_record = json.dumps(record)
    assert "[1, 2, 3]" not in encoded_record
    assert "[200, 220]" not in encoded_record


def test_missing_sequence_quality_and_hard_clipped_equals_are_unknown():
    record, observations = extract.alignment_record_and_witness(
        FakeAlignment(
            sequence=None,
            quality=None,
            cigar=((5, 2), (7, 3), (5, 1)),
            qalign_start=None,
            qalign_end=None,
        ),
        REFERENCE,
    )

    assert record["sequence_reference_oriented_bam"] is None
    assert record["quality_ascii_reference_oriented_bam"] is None
    assert record["forward_query_sequence_sha256_uppercase"] is None
    assert record["full_query_payload_status"] == "UNKNOWN_HARD_CLIPPED_QUERY_BASES_NOT_STORED"
    assert record["equals_reference_witness"]["equals_reference_bases_compared"] == 0
    assert record["equals_reference_witness"]["equals_query_bases_unknown"] == 3
    assert observations == []

    missing_quality, _ = extract.alignment_record_and_witness(
        FakeAlignment(sequence="AAA", quality=None, cigar=((7, 3),)),
        REFERENCE,
    )
    assert missing_quality["sequence_present"] is True
    assert missing_quality["quality_present"] is False
    assert missing_quality["forward_query_sequence_sha256_uppercase"] is not None
    assert missing_quality["forward_query_quality_sha256"] is None
    assert missing_quality["full_query_payload_status"] == "UNKNOWN_SEQUENCE_OR_QUALITY_MISSING"

    mismatched_quality, _ = extract.alignment_record_and_witness(
        FakeAlignment(sequence="AAA", quality="II", cigar=((7, 3),)),
        REFERENCE,
    )
    assert mismatched_quality["sequence_quality_lengths_match"] is False
    assert mismatched_quality["full_query_payload_status"] == "UNKNOWN_SEQUENCE_QUALITY_LENGTH_MISMATCH"


def test_equals_outside_window_and_short_sequence_do_not_create_false_witnesses():
    record, observations = extract.alignment_record_and_witness(
        FakeAlignment(
            sequence="A",
            quality="I",
            cigar=((7, 3),),
            reference_start=extract.REGION_END - 1,
        ),
        REFERENCE,
    )

    assert record["equals_reference_witness"]["equals_reference_bases_compared"] == 1
    assert record["equals_reference_witness"]["equals_query_bases_unknown"] == 0
    assert record["equals_reference_witness"]["equals_positions_outside_reference_context"] == 2
    assert len(observations) == 1

    outside, outside_observations = extract.alignment_record_and_witness(
        FakeAlignment(
            sequence="AA",
            quality="II",
            cigar=((7, 2),),
            reference_start=extract.REGION_END,
        ),
        REFERENCE,
    )
    assert outside["equals_reference_witness"]["equals_positions_outside_reference_context"] == 2
    assert outside["equals_reference_witness"]["equals_reference_bases_compared"] == 0
    assert outside_observations == []

    short_sequence, short_observations = extract.alignment_record_and_witness(
        FakeAlignment(sequence="A", quality="I", cigar=((7, 3),)),
        REFERENCE,
    )
    assert short_sequence["equals_reference_witness"]["equals_reference_bases_compared"] == 1
    assert short_sequence["equals_reference_witness"]["equals_query_bases_unknown"] == 2
    assert short_sequence["cigar_query_length_matches_stored_sequence"] is False
    assert short_sequence["full_query_payload_status"] == "UNKNOWN_CIGAR_QUERY_LENGTH_MISMATCH"
    assert len(short_observations) == 1


def test_collector_reaches_region_eof_and_keeps_duplicate_and_nonprimary_alignments():
    alignments = [
        FakeAlignment(qname="same", flag=0, mapq=0),
        FakeAlignment(qname="same", flag=0x800, mapq=0),
        FakeAlignment(qname="other", flag=0x100, mapq=60),
        FakeAlignment(qname="other", flag=0x900, mapq=60),
    ]
    output = []
    result = extract.collect_region_records(
        iter(alignments),
        REFERENCE,
        header_line=_header_line(),
        write_line=output.append,
    )

    assert result["status"] == "COMPLETE"
    assert result["region_iterator_eof_reached"] is True
    assert result["records_written"] == 4
    assert result["unique_qnames"] == 2
    assert result["duplicate_qname_alignment_records"] == 2
    assert result["alignment_class_counts"] == {
        "primary": 1,
        "supplementary": 2,
        "secondary": 2,
    }
    assert result["mapping_quality_counts_including_zero"] == {"0": 2, "60": 2}
    assert result["equals_reference_witness"]["equals_reference_bases_compared"] == 4
    assert result["equals_reference_witness"]["unique_reference_positions_observed"] == 1
    assert result["equals_reference_witness"]["observed_reference_position_offsets_zero_based"] == [0]
    assert result["equals_reference_witness"]["equals_reference_base_conflicts"] == 0
    assert len(output) == 5  # JSONL header plus all four alignments.
    rows = [json.loads(line) for line in output[1:]]
    assert [row["qname"] for row in rows] == ["same", "same", "other", "other"]
    assert rows[-1]["is_secondary_flag"] is True
    assert rows[-1]["is_supplementary_flag"] is True
    assert not any("independent_molecule" in key for row in rows for key in row)


def test_record_cap_stops_without_requesting_an_extra_alignment():
    requested = []

    def records():
        for index in range(5):
            requested.append(index)
            yield FakeAlignment(qname=f"r{index}")

    output = []
    result = extract.collect_region_records(
        records(), REFERENCE, header_line=_header_line(), write_line=output.append, record_limit=2
    )

    assert result["status"] == "INCOMPLETE"
    assert result["stop_reason"] == "record_cap_reached"
    assert result["region_iterator_eof_reached"] is False
    assert result["records_written"] == 2
    assert requested == [0, 1]
    assert len(output) == 3


def test_payload_cap_counts_header_and_rows_and_stops_without_more_outcomes():
    alignment = FakeAlignment(qname="at-cap")
    record, _ = extract.alignment_record_and_witness(alignment, REFERENCE)
    row = _jsonl_line({"record_type": "alignment", **record})
    cap = len(_header_line()) + len(row)
    requested = []

    def records():
        for index in range(4):
            requested.append(index)
            yield alignment

    output = []
    result = extract.collect_region_records(
        records(), REFERENCE,
        header_line=_header_line(), write_line=output.append,
        payload_limit_bytes=cap,
    )

    assert result["status"] == "INCOMPLETE"
    assert result["stop_reason"] == "case_payload_cap_reached"
    assert result["records_jsonl_bytes_including_header"] == cap
    assert result["records_written"] == 1
    assert result["region_iterator_eof_reached"] is False
    assert requested == [0]
    assert len(output) == 2


def test_payload_cap_refuses_oversize_row_before_writing_it():
    alignment = FakeAlignment(qname="too-large-row", sequence="A" * 100, quality="I" * 100,
                              cigar=((7, 100),))
    requested = []

    def records():
        requested.append("one candidate")
        yield alignment
        requested.append("must not be requested")
        yield alignment

    output = []
    result = extract.collect_region_records(
        records(), REFERENCE,
        header_line=_header_line(), write_line=output.append,
        payload_limit_bytes=len(_header_line()) + 5,
    )

    assert result["status"] == "INCOMPLETE"
    assert result["records_written"] == 0
    assert result["records_jsonl_bytes_including_header"] == len(_header_line())
    assert requested == ["one candidate"]
    assert output == [_header_line()]


def test_time_cap_stops_with_incomplete_status_and_no_second_fetch():
    class Clock:
        value = 0

        def __call__(self):
            return self.value

    clock = Clock()
    requested = []

    def records():
        requested.append("first")
        clock.value = 5
        yield FakeAlignment(qname="late")
        requested.append("second")
        yield FakeAlignment(qname="not-read")

    output = []
    result = extract.collect_region_records(
        records(), REFERENCE,
        header_line=_header_line(), write_line=output.append,
        clock=clock, time_limit_seconds=5,
    )

    assert result["status"] == "INCOMPLETE"
    assert result["stop_reason"] == "time_cap_reached"
    assert result["records_written"] == 0
    assert result["region_iterator_eof_reached"] is False
    assert requested == ["first"]
    assert len(output) == 1


def test_header_and_output_directory_guards():
    with pytest.raises(extract.ExtractionError, match="SO=coordinate"):
        extract.validate_bam_header({"HD": {"SO": "unsorted"}, "SQ": []})
    with pytest.raises(extract.ExtractionError, match="chr2 length"):
        extract.validate_bam_header({
            "HD": {"SO": "coordinate"},
            "SQ": [{"SN": "chr2", "LN": extract.CHR2_LENGTH - 1}],
        })

    with pytest.raises(extract.ExtractionError, match="existing"):
        extract.validate_output_directory(Path("/this/path/does/not/exist"))


class FakeHeader:
    def to_dict(self):
        return {
            "HD": {"VN": "1.6", "SO": "coordinate"},
            "SQ": [{"SN": "chr2", "LN": extract.CHR2_LENGTH}],
            "RG": [{"ID": "rg1", "SM": "HG002_WGS", "PL": "PACBIO"}],
        }


class FakeAlignmentFile:
    text = "@HD\tVN:1.6\tSO:coordinate\n@SQ\tSN:chr2\tLN:242193529\n@RG\tID:rg1\tSM:HG002_WGS\n"
    header = FakeHeader()

    def __init__(self, records, has_index=True):
        self.records = records
        self._has_index = has_index
        self.fetch_args = None

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def has_index(self):
        return self._has_index

    def fetch(self, chromosome, start, end):
        self.fetch_args = (chromosome, start, end)
        return iter(self.records)


def test_cli_fake_indexed_reader_writes_exclusive_complete_outputs(monkeypatch, tmp_path, capsys):
    bam = tmp_path / "input.bam"
    index = tmp_path / "input.bam.bai"
    reference_json = tmp_path / "reference.json"
    output_dir = tmp_path / "new-output"
    bam.write_bytes(b"fake BAM placeholder; no BAM parser reads this fixture")
    index.write_bytes(b"fake BAI placeholder")
    bam_before = bam.read_bytes()
    index_before = index.read_bytes()
    reference_bytes = json.dumps(_reference_document()).encode()
    reference_json.write_bytes(reference_bytes)
    output_dir.mkdir()
    fake_alignment_file = FakeAlignmentFile([FakeAlignment(qname="molecule-1", mapq=0)])

    class FakePysam:
        @staticmethod
        def AlignmentFile(path, mode, *, index_filename, require_index, threads):
            assert path == str(bam)
            assert mode == "rb"
            assert index_filename == str(index)
            assert require_index is True
            assert threads == 1
            return fake_alignment_file

    monkeypatch.setitem(sys.modules, "pysam", FakePysam)
    args = [
        "--bam", str(bam),
        "--reference-json", str(reference_json),
        "--output-dir", str(output_dir),
    ]
    exit_code = extract.main(args)
    capsys.readouterr()

    assert exit_code == 0
    assert fake_alignment_file.fetch_args == (
        extract.CHROMOSOME, extract.REGION_START, extract.REGION_END
    )
    records_path = output_dir / extract.RECORDS_FILENAME
    manifest_path = output_dir / extract.MANIFEST_FILENAME
    rows = [json.loads(line) for line in records_path.read_text().splitlines()]
    manifest = json.loads(manifest_path.read_text())
    assert [row["record_type"] for row in rows] == ["header", "alignment"]
    assert manifest["status"] == "COMPLETE"
    assert manifest["case_region_eof_reached"] is True
    assert manifest["region_iteration"]["records_written"] == 1
    assert manifest["region_iteration"]["mapping_quality_counts_including_zero"] == {"0": 1}
    assert manifest["reference_json"]["json_sha256"] == hashlib.sha256(reference_bytes).hexdigest()
    assert manifest["reference_json"]["dna_sha256"] == hashlib.sha256(REFERENCE.encode()).hexdigest()
    assert manifest["source_header"]["sort_order"] == "coordinate"
    assert "@RG\tID:rg1" in manifest["source_header"]["text"]
    assert manifest["source_bam"]["opened_successfully"] is True
    assert manifest["source_index"]["has_index_at_open"] is True
    assert manifest["region_fetch_started"] is True
    assert manifest["source_bam"]["whole_file_sha256_computed_this_run"] is False
    assert manifest["source_bam"]["stat_before"]["size_bytes"] == manifest["source_bam"]["stat_after"]["size_bytes"]
    assert manifest["source_index"]["stat_before"]["size_bytes"] == manifest["source_index"]["stat_after"]["size_bytes"]
    assert manifest["source_bam"]["historical_sha256"] is None
    assert manifest["biological_inv_classification_emitted"] is False
    assert manifest["biological_negative_claimed"] is False
    assert any("QNAME counts describe alignment labels only" in item for item in manifest["claim_limits"])
    assert manifest["records_file"]["bytes_including_jsonl_header"] == records_path.stat().st_size
    assert manifest["records_file"]["case_payload_cap_bytes"] == 9 * 1024 * 1024
    assert manifest["process_limits"]["max_total_retained_output_bytes"] == 10 * 1024 * 1024
    assert "combined retained output is at most 10 MiB" in manifest["records_file"]["case_payload_definition"]
    assert manifest_path.stat().st_size <= extract.MAX_MANIFEST_BYTES
    assert bam.read_bytes() == bam_before
    assert index.read_bytes() == index_before

    before_retry = {path.name: path.read_bytes() for path in output_dir.iterdir()}
    assert extract.main(args) == 2
    capsys.readouterr()
    assert {path.name: path.read_bytes() for path in output_dir.iterdir()} == before_retry


def test_cli_refuses_missing_bai_without_rebuilding_or_fetching(monkeypatch, tmp_path, capsys):
    bam = tmp_path / "input.bam"
    reference_json = tmp_path / "reference.json"
    output_dir = tmp_path / "new-output"
    bam.write_bytes(b"fake BAM placeholder")
    reference_json.write_text(json.dumps(_reference_document()), encoding="utf-8")
    output_dir.mkdir()

    class NeverOpenPysam:
        @staticmethod
        def AlignmentFile(*_args, **_kwargs):
            raise AssertionError("reader must not open when the required BAI is missing")

    monkeypatch.setitem(sys.modules, "pysam", NeverOpenPysam)
    exit_code = extract.main([
        "--bam", str(bam),
        "--reference-json", str(reference_json),
        "--output-dir", str(output_dir),
    ])
    capsys.readouterr()

    manifest = json.loads((output_dir / extract.MANIFEST_FILENAME).read_text())
    assert exit_code != 0
    assert manifest["status"] == "FAILED"
    assert "BAI index is required" in manifest["failure"]["message"]
    assert manifest["region_fetch_started"] is False
    assert manifest["source_index"]["stat_after"]["exists"] is False
    assert not Path(str(bam) + ".bai").exists()


def test_cli_record_cap_is_nonzero_and_never_claims_region_eof(monkeypatch, tmp_path, capsys):
    bam = tmp_path / "input.bam"
    index = tmp_path / "input.bam.bai"
    reference_json = tmp_path / "reference.json"
    output_dir = tmp_path / "new-output"
    bam.write_bytes(b"fake BAM placeholder")
    index.write_bytes(b"fake BAI placeholder")
    reference_json.write_text(json.dumps(_reference_document()), encoding="utf-8")
    output_dir.mkdir()
    requested = []

    def records():
        for index_value in range(extract.MAX_RECORDS + 1):
            requested.append(index_value)
            yield FakeAlignment(qname="same-qname", flag=0x100)

    fake_alignment_file = FakeAlignmentFile(records())

    class FakePysam:
        @staticmethod
        def AlignmentFile(_path, _mode, *, index_filename, require_index, threads):
            assert index_filename == str(index)
            assert require_index is True and threads == 1
            return fake_alignment_file

    monkeypatch.setitem(sys.modules, "pysam", FakePysam)
    exit_code = extract.main([
        "--bam", str(bam),
        "--reference-json", str(reference_json),
        "--output-dir", str(output_dir),
    ])
    capsys.readouterr()

    manifest = json.loads((output_dir / extract.MANIFEST_FILENAME).read_text())
    assert exit_code != 0
    assert manifest["status"] == "INCOMPLETE"
    assert manifest["region_iteration"]["stop_reason"] == "record_cap_reached"
    assert manifest["region_iteration"]["region_iterator_eof_reached"] is False
    assert manifest["region_iteration"]["records_written"] == extract.MAX_RECORDS
    assert len(requested) == extract.MAX_RECORDS
    assert manifest["region_iteration"]["unique_qnames"] == 1
    assert manifest["region_iteration"]["duplicate_qname_alignment_records"] == extract.MAX_RECORDS - 1
    assert manifest["biological_negative_claimed"] is False
