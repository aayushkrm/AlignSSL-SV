import hashlib
import json
from pathlib import Path

import pytest

pysam = pytest.importorskip("pysam")

from analysis import collect_tier2_geometry_screen as screen


def _truth_vcf(tmp_path):
    plain, compressed = tmp_path / "synthetic.vcf", tmp_path / "synthetic.vcf.gz"
    headers = [
        "##fileformat=VCFv4.2",
        "##contig=<ID=chr1,length=200000>",
        '##INFO=<ID=END,Number=1,Type=Integer,Description="End">',
        '##INFO=<ID=SOURCE,Number=1,Type=String,Description="Source">',
        '##INFO=<ID=ORIGINAL_LOCUS,Number=1,Type=String,Description="Original">',
        '##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">',
        "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSAMPLE",
    ]
    rows = []
    for i in range(1, 54):
        pos, end = (50_000, 105_000) if i == 2 else (35_000, 105_000)
        ident = "." if i == 1 else f"event{i}"
        info = f"END={end};SOURCE=synthetic;ORIGINAL_LOCUS=chr1:150000-160000"
        rows.append(f"chr1\t{pos}\t{ident}\tN\t<INV>\t.\tPASS\t{info}\tGT\t0|1")
    plain.write_text("\n".join(headers + rows) + "\n", encoding="ascii")
    pysam.tabix_compress(str(plain), str(compressed), force=True)
    return compressed


def _plan(tmp_path):
    vcf = _truth_vcf(tmp_path)
    raw = vcf.read_bytes()
    plan = screen.build_plan(vcf, expected_sha256=hashlib.sha256(raw).hexdigest(),
                             expected_bytes=len(raw), expected_rows=53)
    screen.validate_plan(plan, expected_sha256=hashlib.sha256(raw).hexdigest(),
                         expected_bytes=len(raw), expected_rows=53)
    return plan


def _record(header, name, start, cigar, seq, flag=0, mapq=60, tags=()):
    item = pysam.AlignedSegment(header)
    item.query_name = name
    item.flag = flag
    item.reference_id = 0
    item.reference_start = start
    item.mapping_quality = mapq
    item.cigarstring = cigar
    item.query_sequence = seq
    item.query_qualities = pysam.qualitystring_to_array("I" * len(seq))
    for key, value in tags:
        item.set_tag(key, value)
    return item


def _indexed_bam(path):
    header = {"HD": {"VN": "1.6", "SO": "coordinate"},
              "SQ": [{"SN": "chr1", "LN": 200_000}]}
    with pysam.AlignmentFile(str(path), "wb", header=header) as out:
        primary = _record(out.header, "z-split", 20_000, "50M50S", "A" * 100,
            tags=(("SA", "chr1,100001,+,50S50M,60,0;"), ("ZZ", "kept")))
        secondary = _record(out.header, "a-secondary", 50_000, "50M", "C" * 50,
            flag=0x100, mapq=0, tags=(("ZZ", "secondary-kept"),))
        spanning = _record(out.header, "wide", 50_000, "1M50000D49M", "G" * 50)
        supplementary = _record(out.header, "z-split", 100_000, "50S50M", "A" * 100,
            flag=0x800, tags=(("SA", "chr1,20001,+,50M50S,60,0;"),))
        for item in sorted((primary, secondary, spanning, supplementary),
                           key=lambda r: (r.reference_start, r.flag)):
            out.write(item)
    pysam.index(str(path))
    return Path(str(path) + ".bai")


def test_plan_preserves_printed_endpoints_rows_and_merges(tmp_path):
    plan = _plan(tmp_path)
    assert plan["row_count"] == 53
    assert plan["events"][0]["dot_id"] == "."
    assert plan["events"][0]["source_field"] == "synthetic"
    assert plan["events"][0]["genotypes"]["SAMPLE"] == {"GT": [0, 1], "phased": True}
    assert plan["events"][0]["info_fields"]["ORIGINAL_LOCUS"] == "chr1:150000-160000"
    assert [(w["start"], w["end"]) for w in plan["windows"]] == [
        (9_999, 74_999), (79_999, 129_999)]
    first = plan["events"][0]["endpoint_associations"]
    assert [(a["endpoint"], a["point0"]) for a in first] == [("END", 104_999), ("POS", 34_999)]
    assert all(w["end"] <= 129_999 for w in plan["windows"])
    assert len(plan["windows"][0]["endpoint_associations"]) == 53
    damaged = json.loads(json.dumps(plan))
    damaged["windows"][0]["start"] += 1
    with pytest.raises(screen.ScreenError, match="SHA-256"):
        screen.validate_plan(damaged, expected_sha256=plan["truth_sha256"],
                             expected_bytes=plan["truth_bytes"], expected_rows=53)


def test_plan_outputs_are_exclusive_and_bed_keeps_endpoint_links(tmp_path):
    plan = _plan(tmp_path)
    out = tmp_path / "plan-out"
    out.mkdir()
    screen.write_plan(plan, out)
    bed = (out / "windows.bed").read_text()
    assert "W0001\t1,2,3" in bed
    assert "1:POS:34999" in bed and "1:END:104999" in bed
    assert json.loads((out / "manifest.json").read_text())["status"] == "COMPLETE"
    with pytest.raises(screen.ScreenError, match="empty"):
        screen.write_plan(plan, out)


def test_collection_deduplicates_full_sam_and_keeps_unknowns(tmp_path):
    plan = _plan(tmp_path)
    plan_file = tmp_path / "fixed-plan.json"
    plan_file.write_text(screen._json_bytes(plan, pretty=True).decode())
    bam = tmp_path / "synthetic.bam"
    bai = _indexed_bam(bam)
    before = (bam.stat(), bai.stat())
    out = tmp_path / "collection"
    out.mkdir()
    args = {"expected_sha256": plan["truth_sha256"], "expected_bytes": plan["truth_bytes"],
            "expected_rows": 53}
    assert screen.collect_bam(bam, plan_file, out, **args) == "COMPLETE"
    manifest = json.loads((out / "manifest.json").read_text())
    assert manifest["fetch_complete"] and manifest["groups_complete"]
    assert manifest["fetched_records"] == 5
    assert manifest["unique_records"] == 4
    assert sum(w["globally_duplicate_records"] for w in manifest["windows"]) == 1
    assert manifest["source_stats_stable"]
    assert (bam.stat(), bai.stat()) == before
    with pysam.AlignmentFile(str(out / "raw_subset.bam"), "rb") as raw:
        records = list(raw.fetch(until_eof=True))
    assert len(records) == 4
    retained = next(r for r in records if r.query_name == "z-split" and not r.is_supplementary)
    assert retained.get_tag("ZZ") == "kept"
    assert retained.query_sequence == "A" * 100
    summaries = [json.loads(line) for line in (out / "groups.jsonl").read_text().splitlines()]
    by_name = {item["qname"]: item for item in summaries}
    assert by_name["z-split"]["status"] == "ELIGIBLE_OBSERVED_SA_CONSISTENT"
    assert by_name["wide"]["status"] == "ELIGIBLE_OBSERVED_SA_CONSISTENT"
    assert by_name["a-secondary"]["status"] == "UNKNOWN"
    assert all("sequence" not in item and "query_sequence" not in item for item in summaries)
    assert len(manifest["events"]) == 53
    assert all(event["qname_groups"] == 3 for event in manifest["events"])


def test_record_cap_is_strict_incomplete_and_does_not_create_index(tmp_path):
    plan = _plan(tmp_path)
    plan_file = tmp_path / "fixed-plan.json"
    plan_file.write_text(screen._json_bytes(plan, pretty=True).decode())
    bam = tmp_path / "synthetic.bam"
    bai = _indexed_bam(bam)
    out = tmp_path / "limited"
    out.mkdir()
    args = {"expected_sha256": plan["truth_sha256"], "expected_bytes": plan["truth_bytes"],
            "expected_rows": 53}
    status = screen.collect_bam(bam, plan_file, out, max_records=2, **args)
    assert status == "INCOMPLETE"
    manifest = json.loads((out / "manifest.json").read_text())
    assert manifest["fetched_records"] == 2
    assert manifest["incomplete_reason"] == "record_cap_reached_without_fetching_next_record"
    assert not manifest["fetch_complete"]
    assert bai.exists()

    no_index = tmp_path / "no-index.bam"
    with pysam.AlignmentFile(str(no_index), "wb", header={
            "HD": {"VN": "1.6"}, "SQ": [{"SN": "chr1", "LN": 200_000}]}) as sink:
        pass
    no_index_out = tmp_path / "no-index-out"
    no_index_out.mkdir()
    assert screen.collect_bam(no_index, plan_file, no_index_out, **args) == "FAILED"
    assert not Path(str(no_index) + ".bai").exists()


def test_sa_missing_or_contradictory_is_unknown_not_reconstructed():
    header = pysam.AlignmentHeader.from_dict({"SQ": [{"SN": "chr1", "LN": 10_000}]})
    primary = _record(header, "q", 100, "5M5S", "A" * 10)
    supplementary = _record(header, "q", 500, "5S5M", "A" * 10, flag=0x800)
    eligible, reasons = screen.classify_group([primary, supplementary])
    assert not eligible
    assert "SA_not_mutually_consistent_with_observed_alignments" in reasons


def test_cigar_query_disagreement_is_unknown():
    header = pysam.AlignmentHeader.from_dict({"SQ": [{"SN": "chr1", "LN": 10_000}]})
    record = _record(header, "q", 100, "5M4S", "A" * 10)
    eligible, reasons = screen.classify_group([record])
    assert not eligible
    assert "nonsecondary_CIGAR_query_length_mismatch" in reasons


def test_merged_window_does_not_assign_distant_endpoint_to_group():
    header = pysam.AlignmentHeader.from_dict({"SQ": [{"SN": "chr1", "LN": 10_000}]})
    record = _record(header, "q", 150, "100M", "A" * 100)
    plan = {
        "events": [{"dot_id": ".", "source_field": None} for _ in range(2)],
        "windows": [{"window_id": "W0001", "endpoint_associations": [
            {"row_index": 1, "endpoint": "POS", "contig": "chr1", "start": 100, "end": 500},
            {"row_index": 2, "endpoint": "POS", "contig": "chr1", "start": 400, "end": 800},
        ]}],
    }
    result = screen._group_summary("q", [record], {screen._sam_hash(record): {"W0001"}}, plan)
    assert [a["row_index"] for a in result["event_associations"]] == [1]


def test_identical_distinct_source_records_are_not_collapsed(tmp_path):
    plan = _plan(tmp_path)
    plan_file = tmp_path / "fixed-plan.json"
    plan_file.write_bytes(screen._json_bytes(plan, pretty=True))
    bam_path = tmp_path / "duplicate-physical.bam"
    with pysam.AlignmentFile(str(bam_path), "wb", header={
            "HD": {"VN": "1.6", "SO": "coordinate"},
            "SQ": [{"SN": "chr1", "LN": 200_000}]}) as handle:
        record = _record(handle.header, "same-qname", 20_000, "100M", "A" * 100)
        handle.write(record)
        handle.write(record)
    pysam.index(str(bam_path))
    out = tmp_path / "physical-records"
    out.mkdir()
    status = screen.collect_bam(bam_path, plan_file, out,
        expected_sha256=plan["truth_sha256"], expected_bytes=plan["truth_bytes"], expected_rows=53)
    assert status == "COMPLETE"
    manifest = json.loads((out / "manifest.json").read_text())
    assert manifest["unique_records"] == 2
    groups = [json.loads(line) for line in (out / "groups.jsonl").read_text().splitlines()]
    assert groups[0]["nrecords"] == 2 and groups[0]["status"] == "UNKNOWN"


def test_capacity_override_is_explicit_and_does_not_change_records(tmp_path):
    plan = _plan(tmp_path)
    plan_file = tmp_path / "fixed-plan.json"
    plan_file.write_bytes(screen._json_bytes(plan, pretty=True))
    bam = tmp_path / "synthetic.bam"
    _indexed_bam(bam)
    outputs = []
    for label, capacity in (("original", {}), ("run02", {
            "max_bam_bytes": 512 * 1024**2, "max_stage_bytes": 2 * 1024**3})):
        out = tmp_path / label
        out.mkdir()
        assert screen.collect_bam(bam, plan_file, out,
            expected_sha256=plan["truth_sha256"], expected_bytes=plan["truth_bytes"],
            expected_rows=53, **capacity) == "COMPLETE"
        manifest = json.loads((out / "manifest.json").read_text())
        with pysam.AlignmentFile(str(out / "namesorted.bam"), "rb") as handle:
            records = [r.to_string() for r in handle]
        outputs.append((manifest, records, (out / "groups.jsonl").read_bytes()))
    assert outputs[0][1:] == outputs[1][1:]
    assert outputs[0][0]["events"] == outputs[1][0]["events"]
    assert outputs[0][0]["windows"] == outputs[1][0]["windows"]
    assert outputs[0][0]["bounds"]["bam_nominal_bytes_each"] == 128 * 1024**2
    assert outputs[1][0]["bounds"]["bam_nominal_bytes_each"] == 512 * 1024**2
    assert outputs[1][0]["bounds"]["stage_bytes_check"] == 2 * 1024**3
    for key in ("max_fetched_records", "soft_runtime_seconds"):
        assert outputs[0][0]["bounds"][key] == outputs[1][0]["bounds"][key]


def test_cli_rejects_mixed_or_selection_capacity_settings(tmp_path):
    out = tmp_path / "empty"
    out.mkdir()
    assert screen.main(["--bam", "unused", "--plan", "unused",
                        "--bam-cap-mib", "512", "--output-dir", str(out)]) == 2
    assert screen.main(["--plan-only", "--truth-gz", "unused",
                        "--bam-cap-mib", "512", "--stage-cap-mib", "2048",
                        "--output-dir", str(out)]) == 2
    assert not any(out.iterdir())
