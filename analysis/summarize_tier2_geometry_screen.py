"""Summarize a completed Tier2 geometry collection and native report offline."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import stat
import sys

from analysis import collect_tier2_geometry_screen as screen
from analysis.breakinator_native_controls import parse_native_report


EVENTS, WINDOWS, MAX_BYTES = 53, 59, 32 * 1024**2
ELIGIBLE, UNKNOWN = "ELIGIBLE_OBSERVED_SA_CONSISTENT", "UNKNOWN"
CLASSES = ("Pass", "Foldback", "Chimeric")


class SummaryError(ValueError):
    """An input does not meet the completed-screen summary contract."""


def _require(ok, message):
    if not ok:
        raise SummaryError(message)


def _read(path):
    try:
        before = path.lstat()
        _require(stat.S_ISREG(before.st_mode) and not path.is_symlink(),
                 f"input must be a regular non-link file: {path.name}")
        _require(before.st_size <= MAX_BYTES, f"input exceeds 32 MiB: {path.name}")
        data, after = path.read_bytes(), path.lstat()
    except OSError as exc:
        raise SummaryError(f"could not read input: {path.name}") from exc
    identity = lambda s: (s.st_dev, s.st_ino, s.st_mode, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    _require(identity(before) == identity(after) and len(data) == before.st_size,
             f"input changed while being read: {path.name}")
    return data, {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def _json_object(data, name):
    try:
        value = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SummaryError(f"{name} is not valid UTF-8 JSON") from exc
    _require(isinstance(value, dict), f"{name} must contain a JSON object")
    return value


def _groups(data):
    try:
        lines = data.decode("utf-8").splitlines()
    except UnicodeDecodeError as exc:
        raise SummaryError("groups.jsonl is not valid UTF-8") from exc
    rows, by_name = [], {}
    for number, line in enumerate(lines, 1):
        _require(bool(line.strip()), f"groups.jsonl has a blank line at {number}")
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise SummaryError(f"groups.jsonl has invalid JSON at line {number}") from exc
        _require(isinstance(row, dict), f"groups.jsonl line {number} must be an object")
        name = row.get("qname")
        _require(isinstance(name, str) and bool(name), f"groups.jsonl line {number} has invalid QNAME")
        _require(name not in by_name, f"duplicate group QNAME: {name}")
        _require(type(row.get("nrecords")) is int and row["nrecords"] > 0,
                 f"group {name} has invalid nrecords")
        _require(row.get("status") in (ELIGIBLE, UNKNOWN), f"group {name} has invalid status")
        _require(isinstance(row.get("event_associations"), list),
                 f"group {name} has invalid event associations")
        rows.append(row)
        by_name[name] = row
    return rows, by_name


def _validate(plan, manifest, groups, group_bytes):
    try:
        screen.validate_plan(plan)
    except (ValueError, KeyError, TypeError) as exc:
        raise SummaryError(f"plan validation failed: {exc}") from exc
    _require(len(plan["events"]) == EVENTS and len(plan["windows"]) == WINDOWS,
             "plan must contain all 53 events and 59 windows")
    _require(manifest.get("status") == "COMPLETE", "collection status is not COMPLETE")
    _require(manifest.get("fetch_complete") is True, "collection fetch is not complete")
    _require(manifest.get("groups_eof") is True and manifest.get("groups_complete") is True,
             "groups did not reach EOF and complete")
    _require(manifest.get("source_stats_stable") is True, "source statistics were not stable")
    _require(manifest.get("plan_sha256") == plan["plan_sha256"], "manifest names a different plan")
    _require(manifest.get("groups_file") == "groups.jsonl", "manifest does not name groups.jsonl")
    _require(manifest.get("groups_bytes") == group_bytes, "groups.jsonl byte count differs from manifest")

    mwindows = manifest.get("windows")
    _require(isinstance(mwindows, list) and len(mwindows) == WINDOWS, "manifest must contain 59 windows")
    for planned, seen in zip(plan["windows"], mwindows):
        _require(isinstance(seen, dict)
                 and all(seen.get(k) == planned[k] for k in ("window_id", "contig", "start", "end")),
                 "manifest window geometry differs from plan")
        _require(seen.get("fetch_eof") is True, f"window {planned['window_id']} did not reach EOF")

    census = manifest.get("events")
    _require(isinstance(census, list) and len(census) == EVENTS,
             "manifest must contain all 53 event census rows")
    for index, (planned, seen) in enumerate(zip(plan["events"], census), 1):
        _require(isinstance(seen, dict) and type(seen.get("row_index")) is int
                 and seen["row_index"] == index,
                 "event census is not in complete row order")
        _require((seen.get("dot_id"), seen.get("source_field")) ==
                 (planned["dot_id"], planned["source_field"]), f"event metadata differs at row {index}")
        _require(all(type(seen.get(k)) is int and seen[k] >= 0
                      for k in ("qname_groups", "eligible_groups", "unknown_groups")),
                 f"invalid event counts at row {index}")
        _require(seen["eligible_groups"] + seen["unknown_groups"] == seen["qname_groups"],
                 f"inconsistent event counts at row {index}")

    endpoints = {}
    for window in plan["windows"]:
        for endpoint in window["endpoint_associations"]:
            key = (endpoint["row_index"], endpoint["endpoint"], window["window_id"])
            endpoints[key] = {**endpoint, "window_id": window["window_id"], "contig": window["contig"]}
    counts = {i: Counter(qname_groups=0, eligible_groups=0, unknown_groups=0)
              for i in range(1, EVENTS + 1)}
    window_counts, record_total = Counter(), 0
    for group in groups:
        record_total += group["nrecords"]
        rows, wins, seen_keys = set(), set(), set()
        for association in group["event_associations"]:
            _require(isinstance(association, dict), f"group {group['qname']} has malformed association")
            row, endpoint_name, window_id = (association.get("row_index"),
                                             association.get("endpoint"),
                                             association.get("window_id"))
            _require(type(row) is int and 1 <= row <= EVENTS
                     and endpoint_name in ("POS", "END") and isinstance(window_id, str),
                     f"group {group['qname']} has malformed association key")
            key = (row, endpoint_name, window_id)
            endpoint = endpoints.get(key)
            _require(endpoint is not None and key not in seen_keys,
                     f"group {group['qname']} has invalid or duplicate association")
            event = plan["events"][key[0] - 1]
            _require((association.get("dot_id"), association.get("source_field")) ==
                     (event["dot_id"], event["source_field"]),
                     f"group {group['qname']} association metadata differs from plan")
            seen_keys.add(key)
            rows.add(key[0])
            wins.add(key[2])
        for row in rows:
            counts[row]["qname_groups"] += 1
            counts[row]["eligible_groups" if group["status"] == ELIGIBLE else "unknown_groups"] += 1
        for window_id in wins:
            window_counts[window_id] += 1
    _require(type(manifest.get("unique_records")) is int
             and record_total == manifest["unique_records"],
             "group nrecords sum differs from manifest unique_records")
    for index, row in enumerate(census, 1):
        _require(all(row[k] == counts[index][k]
                     for k in ("qname_groups", "eligible_groups", "unknown_groups")),
                 f"group counts differ from manifest at event row {index}")
    for window in mwindows:
        _require(type(window.get("qname_groups")) is int
                 and window["qname_groups"] == window_counts[window["window_id"]],
                 f"group counts differ from manifest at {window['window_id']}")
    return endpoints


def _matches(endpoints, events, contig, loc):
    return [{"row_index": ep["row_index"], "dot_id": events[ep["row_index"] - 1]["dot_id"],
             "source_field": events[ep["row_index"] - 1]["source_field"],
             "endpoint": ep["endpoint"], "window_id": ep["window_id"], "contig": ep["contig"],
             "point0": ep["point0"], "start": ep["start"], "end": ep["end"]}
            for ep in endpoints.values()
            if ep["contig"] == contig and ep["start"] <= loc < ep["end"]]


def summarize(input_dir):
    root = Path(input_dir)
    _require(root.is_dir() and not root.is_symlink(), "--input-dir must be a real directory")
    root = root.resolve()
    paths = {"plan.json": root / "plan.json",
             "collection/manifest.json": root / "collection/manifest.json",
             "collection/groups.jsonl": root / "collection/groups.jsonl",
             "native-report.txt": root / "native-report.txt"}
    raw, hashes = {}, {}
    for name, path in paths.items():
        raw[name], hashes[name] = _read(path)
    plan = _json_object(raw["plan.json"], "plan.json")
    manifest = _json_object(raw["collection/manifest.json"], "collection/manifest.json")
    groups, by_name = _groups(raw["collection/groups.jsonl"])
    endpoints = _validate(plan, manifest, groups, len(raw["collection/groups.jsonl"]))
    try:
        calls = parse_native_report(raw["native-report.txt"])
    except (ValueError, UnicodeDecodeError) as exc:
        raise SummaryError(f"native report parsing failed: {exc}") from exc
    for call in calls:
        _require(call.read_id in by_name, f"native breakpoint QNAME is absent from groups: {call.read_id}")

    class_counts = Counter({name: 0 for name in CLASSES})
    status_counts = Counter({ELIGIBLE: 0, UNKNOWN: 0})
    class_status = {name: Counter({ELIGIBLE: 0, UNKNOWN: 0}) for name in CLASSES}
    labels = {name: set() for name in CLASSES}
    flags = []
    for call in calls:
        status = by_name[call.read_id]["status"]
        class_counts[call.native_class] += 1
        status_counts[status] += 1
        class_status[call.native_class][status] += 1
        labels[call.native_class].add(call.read_id)
        if call.native_class not in ("Foldback", "Chimeric") or status != ELIGIBLE:
            continue
        selected = []
        for assoc in by_name[call.read_id]["event_associations"]:
            ep = endpoints[(assoc["row_index"], assoc["endpoint"], assoc["window_id"])]
            event = plan["events"][ep["row_index"] - 1]
            selected.append({"row_index": ep["row_index"], "dot_id": event["dot_id"],
                "source_field": event["source_field"], "endpoint": ep["endpoint"],
                "window_id": ep["window_id"], "contig": ep["contig"], "point0": ep["point0"],
                "start": ep["start"], "end": ep["end"]})
        breaks = {}
        for key, contig, loc in (("break1", call.break1_chr, call.break1_loc),
                                 ("break2", call.break2_chr, call.break2_loc)):
            matched = _matches(endpoints, plan["events"], contig, loc)
            breaks[key] = {"intersects_original_endpoint_window": bool(matched),
                           "matching_original_endpoints": matched}
        flags.append({"native_class": call.native_class, "qname": call.read_id,
            "group_status": status,
            "raw_native_coordinates": {"break1_chr": call.break1_chr,
                "break1_loc": call.break1_loc, "direction": call.direction,
                "break2_chr": call.break2_chr, "break2_loc": call.break2_loc,
                "mapq": call.mapq, "break1_read": call.break1_read,
                "break2_read": call.break2_read},
            "selected_event_associations": selected,
            "native_breakpoint_endpoint_intersections": breaks})

    fold, chim = labels["Foldback"], labels["Chimeric"]
    read_labels = {name: {"qnames": sorted(values), "distinct_qname_count": len(values)}
                   for name, values in labels.items()}
    event_census = [{k: row[k] for k in ("row_index", "dot_id", "source_field",
                    "qname_groups", "eligible_groups", "unknown_groups")}
                    for row in manifest["events"]]
    return {
        "schema": "tier2-geometry-result-summary-v1", "input_sources": hashes,
        "collection": {"status": manifest["status"], "plan_sha256": plan["plan_sha256"],
            "window_count": WINDOWS, "windows_reached_fetch_eof": True, "event_count": EVENTS,
            "group_qnames": len(groups), "group_records": manifest["unique_records"],
            "eligible_sa_consistent_group_qnames": sum(g["status"] == ELIGIBLE for g in groups),
            "unknown_group_qnames": sum(g["status"] == UNKNOWN for g in groups)},
        "event_census": event_census,
        "native_breakpoints": {"breakpoint_count": len(calls),
            "counts_by_native_class": {name: class_counts[name] for name in CLASSES},
            "counts_by_group_status": {ELIGIBLE: status_counts[ELIGIBLE],
                                        UNKNOWN: status_counts[UNKNOWN]},
            "counts_by_native_class_and_group_status": {name: {
                ELIGIBLE: class_status[name][ELIGIBLE], UNKNOWN: class_status[name][UNKNOWN]}
                for name in CLASSES},
            "read_labels_with_any_breakpoint_by_native_class": read_labels,
            "foldback_chimeric_qname_union": sorted(fold | chim),
            "foldback_chimeric_qname_overlap": sorted(fold & chim)},
        "eligible_native_flag_rows": flags,
        "coordinate_rule": ("Break1_loc and Break2_loc are compared as zero-based interbase positions "
            "against original plan endpoint windows [start, end); merged window bounds are not used."),
        "interpretation_limits": [
            "Native Pass, Foldback, and Chimeric labels are not biological truth.",
            "Eligible means observed records passed collector SA consistency checks; it does not prove "
            "all molecule placements or validate an allele.",
            "UNKNOWN is not a negative result.",
            "Foldback and Chimeric QNAME sets are any-breakpoint labels and can overlap; native final "
            "read-level dominance is not computed.",
            "Endpoint overlap is geometric context, not artifact or inversion support.",
            "No thresholds, sensitivity estimates, or genotype inferences are computed.",
        ],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", required=True, help="completed screen root")
    parser.add_argument("--output", required=True, help="new JSON summary path")
    args = parser.parse_args(argv)
    try:
        _require(Path(args.output).suffix.lower() == ".json", "--output must name a .json file")
        payload = json.dumps(summarize(args.input_dir), sort_keys=True, ensure_ascii=False,
                             allow_nan=False, indent=2) + "\n"
        with Path(args.output).open("x", encoding="utf-8", newline="\n") as output:
            output.write(payload)
    except FileExistsError:
        print("tier2 geometry summary: output already exists; choose a new JSON path", file=sys.stderr)
        return 2
    except (OSError, SummaryError) as exc:
        print(f"tier2 geometry summary: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
