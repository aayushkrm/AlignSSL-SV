"""Freeze Tier2 endpoint windows or make a bounded, unfiltered BAM census."""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import itertools
import json
from pathlib import Path
import stat
import sys
import time

TRUTH_SHA256 = "3a4f950dbac34fda87a4994069e11b7530f5310cc19291a8d70838fe00c7ac89"
TRUTH_BYTES, TRUTH_ROWS, PADDING = 6215, 53, 25_000
MAX_RECORDS, MAX_BAM_BYTES = 50_000, 128 * 1024**2
BGZF_SLACK, MAX_STAGE_BYTES = 64 * 1024, 1024**3
MAX_METADATA_BYTES, SOFT_SECONDS = 32 * 1024**2, 300
RC = str.maketrans("ACGTRYMKBDHVNacgtrymkbdhvn", "TGCAYRKMVHDBNtgcayrkmvhdbn")


class ScreenError(ValueError):
    """The fixed input or collection contract was not met."""


def _json_bytes(value, pretty=False):
    options = {"sort_keys": True, "ensure_ascii": False, "allow_nan": False}
    if pretty:
        options["indent"] = 2
    else:
        options["separators"] = (",", ":")
    return (json.dumps(value, **options) + "\n").encode()


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _hash_file(path, limit):
    if not stat.S_ISREG(Path(path).stat().st_mode):
        raise ScreenError("truth input must be a regular file")
    digest, size = hashlib.sha256(), 0
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            size += len(chunk)
            if size > limit:
                raise ScreenError("truth input exceeds the frozen byte size")
            digest.update(chunk)
    return size, digest.hexdigest()


def _plain(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (tuple, list)):
        return [_plain(item) for item in value]
    if isinstance(value, bytes):
        return value.decode("utf-8")
    raise ScreenError(f"unsupported VCF metadata type: {type(value).__name__}")


def _make_windows(events, contigs, padding):
    if type(padding) is not int or padding != PADDING:
        raise ScreenError("endpoint padding must remain fixed at 25,000 bp")
    order = {name: i for i, name in enumerate(contigs)}
    points = []
    for event in events:
        chrom = event["chrom"]
        if chrom not in contigs:
            raise ScreenError(f"event contig {chrom} is absent from truth header")
        for label, printed in (("POS", event["pos_printed"]), ("END", event["end_printed"])):
            if type(printed) is not int or not 1 <= printed <= contigs[chrom]:
                raise ScreenError(f"row {event['row_index']} has invalid printed {label}")
            point = printed - 1
            points.append({"row_index": event["row_index"], "endpoint": label, "point0": point,
                "contig": chrom, "start": max(0, point-padding), "end": min(contigs[chrom], point+padding)})
    points.sort(key=lambda e: (order[e["contig"]], e["start"], e["end"], e["row_index"], e["endpoint"]))
    windows = []
    for point in points:
        if windows and windows[-1]["contig"] == point["contig"] and point["start"] <= windows[-1]["end"]:
            win = windows[-1]
            win["end"] = max(win["end"], point["end"])
            win["endpoint_associations"].append(point)
        else:
            windows.append({"contig": point["contig"], "start": point["start"],
                            "end": point["end"], "endpoint_associations": [point]})
    by_row = defaultdict(list)
    for i, win in enumerate(windows, 1):
        win["window_id"] = f"W{i:04d}"
        win["endpoint_associations"].sort(key=lambda e: (e["row_index"], e["endpoint"]))
        for ep in win["endpoint_associations"]:
            by_row[ep["row_index"]].append({"endpoint": ep["endpoint"], "point0": ep["point0"],
                "window_id": win["window_id"], "start": ep["start"], "end": ep["end"]})
    for event in events:
        event["endpoint_associations"] = sorted(by_row[event["row_index"]], key=lambda e: e["endpoint"])
    return windows


def _seal(plan):
    plan["plan_sha256"] = _sha(_json_bytes(plan))
    return plan


def build_plan(truth_gz, *, pysam_module=None, expected_sha256=TRUTH_SHA256,
               expected_bytes=TRUTH_BYTES, expected_rows=TRUTH_ROWS):
    """Hash the pinned VCF, then parse it to EOF so BGZF CRCs are checked."""
    size, digest = _hash_file(truth_gz, expected_bytes)
    if (size, digest) != (expected_bytes, expected_sha256):
        raise ScreenError("truth VCF size or SHA-256 differs from the frozen source")
    if pysam_module is None:
        import pysam as pysam_module
    events = []
    with pysam_module.VariantFile(str(truth_gz), "r") as vcf:
        contigs = {name: item.length for name, item in vcf.header.contigs.items()}
        if not contigs or any(type(n) is not int or n <= 0 for n in contigs.values()):
            raise ScreenError("truth header must give a positive length for every contig")
        for row, record in enumerate(vcf, 1):
            info_text = str(record).split("\t")[7]
            printed_end = next((f[4:] for f in info_text.split(";") if f.startswith("END=")), None)
            try:
                end = int(printed_end) if printed_end is not None else None
            except ValueError:
                end = None
            if end is None:
                raise ScreenError(f"row {row} has no scalar integer INFO/END")
            info = {key: _plain(value) for key, value in record.info.items()}
            info["END"] = end
            gt = {name: {"GT": _plain(s.get("GT")) if "GT" in record.format.keys() else None,
                         "phased": bool(s.phased) if "GT" in record.format.keys() else None}
                  for name, s in record.samples.items()}
            events.append({"row_index": row, "chrom": record.contig,
                "pos_printed": int(record.pos), "end_printed": end,
                "dot_id": record.id if record.id is not None else ".",
                "source_field": info.get("SOURCE"), "info_fields": info,
                "genotypes": gt})
    if len(events) != expected_rows:
        raise ScreenError(f"truth VCF has {len(events)} rows; expected {expected_rows}")
    windows = _make_windows(events, contigs, PADDING)
    return _seal({"schema": "tier2-geometry-plan-v1", "truth_bytes": size, "truth_sha256": digest,
        "row_count": len(events), "padding_bp": PADDING,
        "coordinate_rule": "printed POS/END; point=coordinate-1; zero-based half-open",
        "contigs": [{"name": k, "length": v} for k, v in contigs.items()],
        "events": events, "windows": windows})


def validate_plan(plan, *, expected_sha256=TRUTH_SHA256,
                  expected_bytes=TRUTH_BYTES, expected_rows=TRUTH_ROWS):
    if not isinstance(plan, dict) or plan.get("schema") != "tier2-geometry-plan-v1":
        raise ScreenError("unsupported plan schema")
    body = {k: v for k, v in plan.items() if k != "plan_sha256"}
    if plan.get("plan_sha256") != _sha(_json_bytes(body)):
        raise ScreenError("plan SHA-256 is invalid")
    if (plan.get("truth_sha256"), plan.get("truth_bytes"), plan.get("row_count"), plan.get("padding_bp")) != (
            expected_sha256, expected_bytes, expected_rows, PADDING):
        raise ScreenError("plan does not name the frozen 53-row truth source")
    contigs = {}
    for c in plan.get("contigs", []):
        if (not isinstance(c, dict) or not isinstance(c.get("name"), str)
                or type(c.get("length")) is not int or c["length"] <= 0
                or c["name"] in contigs):
            raise ScreenError("invalid or duplicate plan contig")
        contigs[c["name"]] = c["length"]
    events = plan.get("events")
    if not isinstance(events, list) or len(events) != expected_rows:
        raise ScreenError("plan event rows do not match the frozen count")
    if [e.get("row_index") for e in events] != list(range(1, expected_rows + 1)):
        raise ScreenError("plan rows are not in original VCF order")
    rebuilt = json.loads(json.dumps(events))
    wins = _make_windows(rebuilt, contigs, PADDING)
    if wins != plan.get("windows") or any(a.get("endpoint_associations") != b.get("endpoint_associations")
                                           for a, b in zip(events, rebuilt)):
        raise ScreenError("plan windows or event associations are inconsistent")
    return contigs


def _empty_dir(path):
    p = Path(path)
    if not p.is_dir() or p.is_symlink() or any(p.iterdir()):
        raise ScreenError("output must be an existing empty real directory")
    return p


def _exclusive(path, data):
    with open(path, "xb") as stream:
        stream.write(data)


def _bed(plan):
    lines = ["#contig\tstart0\tend0\twindow_id\trows\tendpoint_associations"]
    for win in plan["windows"]:
        eps = win["endpoint_associations"]
        rows = ",".join(str(x) for x in sorted({e["row_index"] for e in eps}))
        assoc = ",".join(f"{e['row_index']}:{e['endpoint']}:{e['point0']}" for e in eps)
        lines.append(f"{win['contig']}\t{win['start']}\t{win['end']}\t"
                     f"{win['window_id']}\t{rows}\t{assoc}")
    return ("\n".join(lines) + "\n").encode()


def write_plan(plan, output_dir):
    out = _empty_dir(output_dir)
    data = _json_bytes(plan, pretty=True)
    bed = _bed(plan)
    manifest = _json_bytes({"status": "COMPLETE", "plan_sha256": plan["plan_sha256"],
                            "truth_rows": len(plan["events"]),
                            "merged_windows": len(plan["windows"])}, pretty=True)
    if len(data) + len(bed) + len(manifest) > MAX_METADATA_BYTES:
        raise ScreenError("plan outputs exceed the 32 MiB metadata cap")
    _exclusive(out / "plan.json", data)
    _exclusive(out / "windows.bed", bed)
    _exclusive(out / "manifest.json", manifest)


def _snapshot(path):
    p = Path(path)
    s = p.stat()
    if not stat.S_ISREG(s.st_mode):
        raise ScreenError(f"source is not a regular file: {p}")
    return {"path": str(p), "size": s.st_size, "mtime_ns": s.st_mtime_ns,
            "ctime_ns": s.st_ctime_ns, "device": s.st_dev, "inode": s.st_ino}


def _bai_for(bam):
    candidates = [Path(str(bam) + ".bai"), Path(bam).with_suffix(".bai")]
    found = list(dict.fromkeys(p for p in candidates if p.exists()))
    if len(found) != 1:
        raise ScreenError("require exactly one existing BAI; index creation is disabled")
    return found[0]


def _sam_hash(aln):
    return _sha(aln.to_string().encode("utf-8"))


def _signature(aln):
    return (aln.reference_name, int(aln.reference_start),
            "-" if aln.is_reverse else "+", aln.cigarstring or "*",
            int(aln.mapping_quality))


def _sa_signatures(aln):
    if not aln.has_tag("SA"):
        return set()
    result = set()
    raw = aln.get_tag("SA")
    for item in str(raw).split(";"):
        if not item:
            continue
        fields = item.split(",")
        if len(fields) != 6 or fields[2] not in ("+", "-"):
            raise ValueError("malformed SA tag")
        pos, mapq = int(fields[1]), int(fields[4])
        if pos < 1:
            raise ValueError("invalid SA position")
        result.add((fields[0], pos - 1, fields[2], fields[3], mapq))
    return result


def classify_group(records):
    """Classify only observed records; SA never creates a missing alignment."""
    reasons, primary = [], []
    mapped = [r for r in records if not r.is_unmapped]
    nonsecondary = [r for r in records if not r.is_secondary]
    primary = [r for r in nonsecondary if not r.is_supplementary]
    if len(primary) != 1:
        reasons.append("observed_primary_count_not_one")
    elif primary[0].is_unmapped:
        reasons.append("observed_primary_is_unmapped")
    qlengths, seqhashes, signatures = set(), set(), []
    for r in nonsecondary:
        cigar = r.cigartuples or []
        if any(code == 5 for code, _ in cigar):
            reasons.append("nonsecondary_hard_clipped")
        seq, qual, qlen = r.query_sequence, r.qual, r.query_length
        if seq is None or qual is None:
            reasons.append("nonsecondary_sequence_or_quality_missing")
            continue
        if len(seq) != len(qual) or qlen != len(seq):
            reasons.append("nonsecondary_query_length_mismatch")
        consumed = sum(length for code, length in cigar if code in {0, 1, 4, 7, 8})
        if consumed != len(seq):
            reasons.append("nonsecondary_CIGAR_query_length_mismatch")
        qlengths.add(qlen)
        forward = seq.translate(RC)[::-1] if r.is_reverse else seq
        seqhashes.add(_sha(forward.upper().encode("ascii")))
        if not r.is_unmapped:
            signatures.append(_signature(r))
    if len(qlengths) != 1:
        reasons.append("query_length_not_consistent")
    if len(seqhashes) != 1:
        reasons.append("forward_sequence_not_consistent")
    if len(set(signatures)) != len(signatures):
        reasons.append("ambiguous_duplicate_nonsecondary_signature")
    sigset = set(signatures)
    if len(signatures) > 1:
        for r in nonsecondary:
            if r.is_unmapped:
                continue
            try:
                declared = _sa_signatures(r)
                if declared != sigset - {_signature(r)}:
                    reasons.append("SA_not_mutually_consistent_with_observed_alignments")
            except (ValueError, TypeError):
                reasons.append("SA_malformed")
    elif nonsecondary and nonsecondary[0].has_tag("SA"):
        try:
            if _sa_signatures(nonsecondary[0]):
                reasons.append("SA_describes_unobserved_alignment")
        except (ValueError, TypeError):
            reasons.append("SA_malformed")
    return (not reasons), sorted(set(reasons))


def _group_summary(qname, records, record_windows, plan):
    eligible, reasons = classify_group(records)
    window_ids = sorted({w for r in records for w in record_windows.get(_sam_hash(r), ())})
    win_by_id = {w["window_id"]: w for w in plan["windows"]}
    associations = {}
    for wid in window_ids:
        for ep in win_by_id[wid]["endpoint_associations"]:
            if not any(not r.is_unmapped and r.reference_name == ep["contig"]
                       and r.reference_end is not None
                       and r.reference_start < ep["end"] and r.reference_end > ep["start"]
                       for r in records):
                continue
            row = ep["row_index"]
            associations[(row, wid, ep["endpoint"])] = {
                "row_index": row, "dot_id": plan["events"][row - 1]["dot_id"],
                "source_field": plan["events"][row - 1]["source_field"],
                "window_id": wid, "endpoint": ep["endpoint"]}
    intervals = []
    for r in records:
        if not r.is_unmapped:
            intervals.append({"reference": r.reference_name, "start0": r.reference_start,
                              "end0": r.reference_end, "flag": r.flag})
    return {"qname": qname, "nrecords": len(records),
            "status": "ELIGIBLE_OBSERVED_SA_CONSISTENT" if eligible else "UNKNOWN",
            "reasons": reasons, "reference_intervals": intervals,
            "event_associations": list(associations.values())}


def collect_bam(bam_path, plan_path, output_dir, *, pysam_module=None,
                max_records=MAX_RECORDS, soft_seconds=SOFT_SECONDS,
                max_bam_bytes=MAX_BAM_BYTES, max_stage_bytes=MAX_STAGE_BYTES,
                expected_sha256=TRUTH_SHA256, expected_bytes=TRUTH_BYTES,
                expected_rows=TRUTH_ROWS):
    """Collect only the frozen windows. A cap produces INCOMPLETE, never a prefix claim."""
    out = _empty_dir(output_dir)
    if any(type(value) is not int or value <= 0
           for value in (max_bam_bytes, max_stage_bytes)):
        raise ScreenError("storage bounds must be positive integer byte counts")
    if pysam_module is None:
        import pysam as pysam_module
    started = time.monotonic()
    manifest = {"status": "INCOMPLETE", "plan_path": str(plan_path),
        "bam_path": str(bam_path), "windows": [], "events": [],
        "groups_file": "groups.jsonl", "raw_bam": "raw_subset.bam",
        "name_sorted_bam": "namesorted.bam",
        "interpretation_limit": "SA consistency is not proof of complete molecule or all placements.",
        "historical_source_fingerprint": {
            "bam_bytes": 48_727_325_910,
            "bam_sha256": "b7edeb4bbc2589039c6148a912857f26924ca8fd5971cd3141337d0ce24bbde4",
            "bai_bytes": 21_582_928,
            "bai_sha256": "5106ac6339847460842a528a312471785d9348f59cc65cca02b55b15e157e546",
            "verification": "historical metadata only; this screen does not rehash the 48 GB source"},
        "bounds": {"max_fetched_records": max_records,
            "bam_nominal_bytes_each": max_bam_bytes,
            "bgzf_block_overshoot_allowance_bytes": BGZF_SLACK,
            "stage_bytes_check": max_stage_bytes,
            "stage_limit_is_hard_quota": False,
            "soft_runtime_seconds": soft_seconds}}
    raw_path, name_path = out / "raw_subset.bam", out / "namesorted.bam"
    groups_path = out / "groups.jsonl"
    before = after = bai_before = bai_after = None
    try:
        if Path(plan_path).stat().st_size > MAX_METADATA_BYTES:
            raise ScreenError("plan exceeds the 32 MiB metadata cap")
        plan = json.loads(Path(plan_path).read_text(encoding="utf-8"))
        contigs = validate_plan(plan, expected_sha256=expected_sha256,
                                expected_bytes=expected_bytes, expected_rows=expected_rows)
        manifest["plan_sha256"] = plan["plan_sha256"]
        before = _snapshot(bam_path)
        bai = _bai_for(bam_path)
        bai_before = _snapshot(bai)
        manifest["source_stat_before"], manifest["bai_stat_before"] = before, bai_before
        windows = [{**w, "fetch_eof": False, "fetched_records": 0,
                    "unique_records": 0, "duplicate_records": 0,
                    "globally_duplicate_records": 0, "qname_groups": 0}
                   for w in plan["windows"]]
        manifest["windows"] = windows
        event_counts = {e["row_index"]: {"qname_groups": 0, "eligible_groups": 0,
                                           "unknown_groups": 0} for e in plan["events"]}
        seen, record_windows, total = set(), defaultdict(set), 0
        why_incomplete = None
        with pysam_module.AlignmentFile(str(bam_path), "rb") as bam:
            if not bam.has_index():
                raise ScreenError("existing BAI is not usable; index building is disabled")
            lengths = dict(zip(bam.references, bam.lengths))
            for name, length in contigs.items():
                if lengths.get(name) != length:
                    raise ScreenError(f"BAM header length mismatch for truth contig {name}")
            with pysam_module.AlignmentFile(str(raw_path), "wb", template=bam) as raw:
                for census, win in zip(windows, plan["windows"]):
                    if time.monotonic() - started >= soft_seconds:
                        why_incomplete = "soft_runtime_limit"
                        break
                    local = set()
                    iterator = bam.fetch(win["contig"], win["start"], win["end"])
                    while True:
                        if total >= max_records:
                            why_incomplete = "record_cap_reached_without_fetching_next_record"
                            break
                        if time.monotonic() - started >= soft_seconds:
                            why_incomplete = "soft_runtime_limit"
                            break
                        try:
                            aln = next(iterator)
                        except StopIteration:
                            census["fetch_eof"] = True
                            break
                        total += 1
                        census["fetched_records"] += 1
                        digest = _sam_hash(aln)
                        # One physical source record can be fetched by two windows.
                        # Distinct records with identical SAM text must still survive.
                        source_record = (bam.tell(), digest)
                        record_windows[digest].add(census["window_id"])
                        if source_record in local:
                            census["duplicate_records"] += 1
                            continue
                        local.add(source_record)
                        census["unique_records"] += 1
                        if source_record in seen:
                            census["globally_duplicate_records"] += 1
                            continue
                        seen.add(source_record)
                        raw.write(aln)
                        if raw_path.stat().st_size > max_bam_bytes + BGZF_SLACK:
                            why_incomplete = "raw_bam_size_cap"
                            break
                    if why_incomplete:
                        break
                manifest["fetched_records"] = total
                manifest["unique_records"] = len(seen)
                manifest["fetch_complete"] = why_incomplete is None and all(
                    w["fetch_eof"] for w in windows)
        manifest["incomplete_reason"] = why_incomplete
        if raw_path.exists():
            if raw_path.stat().st_size > max_bam_bytes + BGZF_SLACK:
                why_incomplete = why_incomplete or "raw_bam_size_cap"
            if time.monotonic() - started >= soft_seconds:
                why_incomplete = why_incomplete or "soft_runtime_limit_before_sort"
            else:
                pysam_module.sort("-n", "-m", "128M", "-@", "0", "-T",
                    str(out / "sort_tmp"), "-o", str(name_path), str(raw_path))
                if name_path.stat().st_size > max_bam_bytes + BGZF_SLACK:
                    why_incomplete = why_incomplete or "name_sorted_bam_size_cap"
                if _stage_bytes(out) > max_stage_bytes:
                    why_incomplete = why_incomplete or "retained_stage_size_cap"
                if time.monotonic() - started >= soft_seconds:
                    why_incomplete = why_incomplete or "soft_runtime_limit_after_sort"
            if name_path.exists() and time.monotonic() - started < soft_seconds:
                used, groups_eof = 0, False
                with open(groups_path, "xb") as groups, pysam_module.AlignmentFile(
                        str(name_path), "rb") as sorted_bam:
                    for qname, items in itertools.groupby(
                            sorted_bam, key=lambda r: r.query_name):
                        if time.monotonic() - started >= soft_seconds:
                            why_incomplete = why_incomplete or "soft_runtime_limit_grouping"
                            break
                        records = list(items)
                        summary = _group_summary(qname, records, record_windows, plan)
                        line = _json_bytes(summary)
                        if used + len(line) > MAX_METADATA_BYTES - 256 * 1024:
                            why_incomplete = why_incomplete or "metadata_size_cap"
                            break
                        groups.write(line)
                        used += len(line)
                        row_ids = {a["row_index"] for a in summary["event_associations"]}
                        win_ids = {a["window_id"] for a in summary["event_associations"]}
                        for census in windows:
                            if census["window_id"] in win_ids:
                                census["qname_groups"] += 1
                        for row in row_ids:
                            count = event_counts[row]
                            count["qname_groups"] += 1
                            count["eligible_groups" if summary["status"].startswith("ELIGIBLE")
                                  else "unknown_groups"] += 1
                    else:
                        groups_eof = True
                manifest["groups_bytes"] = used
                manifest["groups_eof"] = groups_eof
                manifest["groups_complete"] = groups_eof
                manifest["events"] = [{"row_index": e["row_index"], "dot_id": e["dot_id"],
                    "source_field": e["source_field"], "genotypes": e["genotypes"],
                    **event_counts[e["row_index"]]} for e in plan["events"]]
        if _stage_bytes(out) > max_stage_bytes:
            why_incomplete = why_incomplete or "retained_stage_size_cap_after_grouping"
        after = _snapshot(bam_path)
        bai_after = _snapshot(bai)
        stable = before == after and bai_before == bai_after
        manifest["source_stat_after"], manifest["bai_stat_after"] = after, bai_after
        manifest["source_stats_stable"] = stable
        manifest["raw_bam_bytes"] = raw_path.stat().st_size if raw_path.exists() else 0
        manifest["name_sorted_bam_bytes"] = name_path.stat().st_size if name_path.exists() else 0
        manifest["retained_stage_bytes_at_check"] = _stage_bytes(out)
        if not stable:
            why_incomplete = "source_or_index_stat_changed"
        if time.monotonic() - started >= soft_seconds:
            why_incomplete = why_incomplete or "soft_runtime_limit_during_finalization"
        manifest["incomplete_reason"] = why_incomplete
        manifest["elapsed_seconds"] = round(time.monotonic() - started, 3)
        if why_incomplete is None and manifest.get("fetch_complete") and manifest.get("groups_complete"):
            manifest["status"] = "COMPLETE"
        else:
            manifest["status"] = "INCOMPLETE"
    except Exception as exc:
        manifest["status"] = "FAILED"
        manifest["error"] = f"{type(exc).__name__}: {exc}"
        manifest["incomplete_reason"] = manifest.get("incomplete_reason") or "collection_error"
        manifest["elapsed_seconds"] = round(time.monotonic() - started, 3)
        try:
            if before is not None:
                manifest["source_stat_after"] = _snapshot(bam_path)
            if bai_before is not None:
                manifest["bai_stat_after"] = _snapshot(bai_before["path"])
        except Exception as stat_exc:
            manifest["stat_check_error"] = str(stat_exc)
    payload = _json_bytes(manifest, pretty=True)
    if len(payload) + (groups_path.stat().st_size if groups_path.exists() else 0) > MAX_METADATA_BYTES:
        manifest["status"] = "INCOMPLETE"
        manifest["incomplete_reason"] = "metadata_size_cap"
        manifest["events"] = []
        payload = _json_bytes(manifest, pretty=True)
    try:
        _exclusive(out / "manifest.json", payload)
    except OSError as exc:
        print(f"could not finalize manifest: {exc}", file=sys.stderr)
        return "FAILED"
    return manifest["status"]


def _stage_bytes(path):
    total = 0
    for item in Path(path).rglob("*"):
        mode = item.lstat().st_mode
        if stat.S_ISREG(mode):
            total += item.stat().st_size
        elif not stat.S_ISDIR(mode):
            raise ScreenError("output contains a symlink or special file")
    return total


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--plan-only", action="store_true")
    mode.add_argument("--bam")
    parser.add_argument("--truth-gz")
    parser.add_argument("--plan")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--bam-cap-mib", type=int, choices=(128, 512), default=128)
    parser.add_argument("--stage-cap-mib", type=int, choices=(1024, 2048), default=1024)
    args = parser.parse_args(argv)
    try:
        if (args.bam_cap_mib, args.stage_cap_mib) not in {(128, 1024), (512, 2048)}:
            raise ScreenError("use the original 128/1024 or explicit run02 512/2048 storage pair")
        if args.plan_only:
            if (args.bam_cap_mib, args.stage_cap_mib) != (128, 1024):
                raise ScreenError("storage overrides apply to collection, not selection")
            if not args.truth_gz or args.plan:
                raise ScreenError("plan-only requires --truth-gz and does not accept --plan")
            plan = build_plan(args.truth_gz)
            write_plan(plan, args.output_dir)
            print(f"plan COMPLETE: {args.output_dir} (sha256 {plan['plan_sha256']})")
            return 0
        if not args.plan or args.truth_gz:
            raise ScreenError("run mode requires --bam and --plan; omit --truth-gz")
        status = collect_bam(args.bam, args.plan, args.output_dir,
                             max_bam_bytes=args.bam_cap_mib * 1024**2,
                             max_stage_bytes=args.stage_cap_mib * 1024**2)
        print(f"collection {status}: {args.output_dir}")
        return 0 if status == "COMPLETE" else 2
    except Exception as exc:
        print(f"tier2 geometry screen: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
