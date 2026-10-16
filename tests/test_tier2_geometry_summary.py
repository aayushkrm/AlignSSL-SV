import hashlib
import json

import pytest

from analysis import collect_tier2_geometry_screen as screen
from analysis import summarize_tier2_geometry_screen as summary
from analysis.breakinator_native_controls import REPORT_HEADER


def _synthetic_plan():
    points = [None] * (53 * 2)
    points[0], points[2] = 500_000, 530_000
    remaining = [i for i, value in enumerate(points) if value is None]
    for pair in range(46):
        point = 1_000_000 + pair * 200_000
        points[remaining[2 * pair]] = point
        points[remaining[2 * pair + 1]] = point
    for offset, slot in enumerate(remaining[92:]):
        points[slot] = 10_500_000 + offset * 200_000

    events = []
    for row in range(1, 54):
        events.append({"row_index": row, "chrom": "chr1",
            "pos_printed": points[2 * (row - 1)] + 1,
            "end_printed": points[2 * (row - 1) + 1] + 1,
            "dot_id": "." if row == 1 else f"event{row}",
            "source_field": "synthetic"})
    contigs = {"chr1": 30_000_000}
    plan = {
        "schema": "tier2-geometry-plan-v1", "truth_bytes": screen.TRUTH_BYTES,
        "truth_sha256": screen.TRUTH_SHA256, "row_count": 53,
        "padding_bp": screen.PADDING,
        "coordinate_rule": "printed POS/END; point=coordinate-1; zero-based half-open",
        "contigs": [{"name": name, "length": length} for name, length in contigs.items()],
        "events": events,
    }
    plan["windows"] = screen._make_windows(plan["events"], contigs, screen.PADDING)
    assert len(plan["windows"]) == 59
    return screen._seal(plan)


def _group(qname, nrecords, status, associations=()):
    return {"qname": qname, "nrecords": nrecords, "status": status,
            "reasons": [], "reference_intervals": [],
            "event_associations": list(associations)}


def _association(plan, row, endpoint="POS"):
    event = plan["events"][row - 1]
    selected = next(item for item in event["endpoint_associations"]
                    if item["endpoint"] == endpoint)
    return {"row_index": row, "dot_id": event["dot_id"],
            "source_field": event["source_field"], "window_id": selected["window_id"],
            "endpoint": endpoint}


def _report(rows):
    return "\t".join(REPORT_HEADER) + "\n" + "".join(
        "\t".join(map(str, row)) + "\n" for row in rows
    )


def _call(qname, native_class, break1_loc=540_000, break2_chr="chr1", break2_loc=4_000_000):
    return ("chr1", break1_loc, "><", break2_chr, break2_loc, 60,
            qname, native_class, 40, 40)


def _fixture(tmp_path):
    plan = _synthetic_plan()
    groups = [
        _group("q1", 2, summary.ELIGIBLE, [_association(plan, 1)]),
        _group("q2", 1, summary.UNKNOWN, [_association(plan, 2)]),
        _group("q3", 3, summary.UNKNOWN),
    ]
    event_counts = {row: {"qname_groups": 0, "eligible_groups": 0, "unknown_groups": 0}
                    for row in range(1, 54)}
    window_counts = {window["window_id"]: 0 for window in plan["windows"]}
    for group in groups:
        rows, windows = set(), set()
        for association in group["event_associations"]:
            rows.add(association["row_index"])
            windows.add(association["window_id"])
        for row in rows:
            event_counts[row]["qname_groups"] += 1
            event_counts[row]["eligible_groups" if group["status"] == summary.ELIGIBLE
                              else "unknown_groups"] += 1
        for window in windows:
            window_counts[window] += 1
    events = [{"row_index": row, "dot_id": event["dot_id"],
        "source_field": event["source_field"], **event_counts[row]}
        for row, event in enumerate(plan["events"], 1)]
    windows = [{**window, "fetch_eof": True,
                "qname_groups": window_counts[window["window_id"]]}
               for window in plan["windows"]]
    groups_bytes = b"".join(
        json.dumps(group, sort_keys=True, separators=(",", ":")).encode() + b"\n"
        for group in groups
    )
    manifest = {
        "status": "COMPLETE", "plan_sha256": plan["plan_sha256"],
        "fetch_complete": True, "groups_eof": True, "groups_complete": True,
        "source_stats_stable": True, "groups_file": "groups.jsonl",
        "groups_bytes": len(groups_bytes), "unique_records": 6,
        "windows": windows, "events": events,
    }
    report = _report([
        _call("q1", "Foldback"),
        _call("q1", "Chimeric", break2_chr="chr2", break2_loc=900_000),
        _call("q2", "Pass"),
        _call("q3", "Foldback"),
        _call("q3", "Chimeric", break2_chr="chr2", break2_loc=900_000),
    ])
    root = tmp_path
    collection = root / "collection"
    collection.mkdir()
    (root / "plan.json").write_text(json.dumps(plan), encoding="utf-8")
    (collection / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (collection / "groups.jsonl").write_bytes(groups_bytes)
    (root / "native-report.txt").write_text(report, encoding="utf-8")
    return plan, manifest, groups, report


def test_summary_counts_breakpoints_labels_event_census_and_direct_endpoints(tmp_path):
    plan, _, _, _ = _fixture(tmp_path)
    result = summary.summarize(tmp_path)

    assert result["collection"]["window_count"] == 59
    assert result["collection"]["event_count"] == 53
    assert result["native_breakpoints"]["counts_by_native_class"] == {
        "Pass": 1, "Foldback": 2, "Chimeric": 2,
    }
    assert result["native_breakpoints"]["counts_by_native_class_and_group_status"] == {
        "Pass": {summary.ELIGIBLE: 0, summary.UNKNOWN: 1},
        "Foldback": {summary.ELIGIBLE: 1, summary.UNKNOWN: 1},
        "Chimeric": {summary.ELIGIBLE: 1, summary.UNKNOWN: 1},
    }
    assert result["native_breakpoints"]["read_labels_with_any_breakpoint_by_native_class"][
        "Foldback"]["qnames"] == ["q1", "q3"]
    assert result["native_breakpoints"]["read_labels_with_any_breakpoint_by_native_class"][
        "Chimeric"]["qnames"] == ["q1", "q3"]
    assert result["native_breakpoints"]["foldback_chimeric_qname_union"] == ["q1", "q3"]
    assert result["native_breakpoints"]["foldback_chimeric_qname_overlap"] == ["q1", "q3"]
    assert len(result["event_census"]) == 53
    assert result["event_census"][0]["qname_groups"] == 1
    assert result["event_census"][2]["qname_groups"] == 0
    assert result["input_sources"]["plan.json"]["sha256"] == hashlib.sha256(
        (tmp_path / "plan.json").read_bytes()).hexdigest()

    eligible_rows = result["eligible_native_flag_rows"]
    assert [row["native_class"] for row in eligible_rows] == ["Foldback", "Chimeric"]
    assert eligible_rows[0]["raw_native_coordinates"]["break1_loc"] == 540_000
    assert eligible_rows[0]["selected_event_associations"][0]["row_index"] == 1
    direct = eligible_rows[0]["native_breakpoint_endpoint_intersections"]["break1"]
    assert direct["intersects_original_endpoint_window"]
    assert [(item["row_index"], item["endpoint"]) for item in direct[
        "matching_original_endpoints"]] == [(2, "POS")]
    row2_pos_window = next(item["window_id"] for item in
                           plan["events"][1]["endpoint_associations"]
                           if item["endpoint"] == "POS")
    row1_pos_window = next(item["window_id"] for item in
                           plan["events"][0]["endpoint_associations"]
                           if item["endpoint"] == "POS")
    assert eligible_rows[0]["selected_event_associations"][0]["window_id"] == row2_pos_window
    assert row1_pos_window == row2_pos_window
    assert direct["matching_original_endpoints"][0]["window_id"] == \
        row2_pos_window
    assert all(item["row_index"] != 1 for item in direct["matching_original_endpoints"])
    assert all("sequence" not in row and "qualities" not in row for row in eligible_rows)
    serialized = json.dumps(result).lower()
    assert "sequence" not in serialized and "qualities" not in serialized
    assert "not a negative result" in " ".join(result["interpretation_limits"])


def test_incomplete_collection_is_rejected(tmp_path):
    _fixture(tmp_path)
    path = tmp_path / "collection" / "manifest.json"
    manifest = json.loads(path.read_text())
    manifest["fetch_complete"] = False
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(summary.SummaryError, match="fetch is not complete"):
        summary.summarize(tmp_path)


def test_native_unknown_qname_is_rejected(tmp_path):
    _fixture(tmp_path)
    path = tmp_path / "native-report.txt"
    path.write_text(_report([_call("not-in-groups", "Pass")]), encoding="utf-8")
    with pytest.raises(summary.SummaryError, match="absent from groups"):
        summary.summarize(tmp_path)


def test_duplicate_group_qname_is_rejected(tmp_path):
    _fixture(tmp_path)
    path = tmp_path / "collection" / "groups.jsonl"
    lines = path.read_bytes()
    path.write_bytes(lines + lines.splitlines(keepends=True)[0])
    manifest_path = tmp_path / "collection" / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["groups_bytes"] = path.stat().st_size
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(summary.SummaryError, match="duplicate group QNAME"):
        summary.summarize(tmp_path)


def test_group_record_sum_must_match_manifest(tmp_path):
    _fixture(tmp_path)
    path = tmp_path / "collection" / "groups.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    rows[0]["nrecords"] += 1
    payload = "".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n"
                      for row in rows)
    path.write_text(payload, encoding="utf-8")
    manifest_path = tmp_path / "collection" / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["groups_bytes"] = len(payload.encode())
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(summary.SummaryError, match="nrecords sum"):
        summary.summarize(tmp_path)


def test_cli_writes_only_a_new_json_file(tmp_path):
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    _fixture(inputs)
    output = tmp_path / "new-summary.json"
    assert summary.main(["--input-dir", str(inputs),
                         "--output", str(output)]) == 0
    saved = output.read_bytes()
    assert json.loads(saved)["schema"] == "tier2-geometry-result-summary-v1"
    assert summary.main(["--input-dir", str(inputs),
                         "--output", str(output)]) == 2
    assert output.read_bytes() == saved
