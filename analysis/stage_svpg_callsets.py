"""Stage the six frozen caller VCFs after explicit independent body approval.

--protocol-sha256 pins the exact --protocol JSON bytes. Required protocol keys:
body_read_approved=true, independent_outcome_approval (review reference),
header_protocol (the complete frozen header protocol),
max_source_decoded_bytes (<=2 GiB default, <=3/4 GiB with explicit amendments),
max_line_bytes (<=32 MiB default, <=128 MiB only with final large-record amendment),
charged_prior_source_decoded_bytes (prior source-body passes, including failures),
controller_traffic_account (external controller ledger/reservation reference).
The source budget includes prior source passes, headers and discarded RNAMES.
The controller must reserve
and charge all decoded traffic, including truth, repeats and failed attempts,
against the reviewed global limit; this function only enforces its own pass.
Failures preserve partial VCFs and failure.json; no automatic removal or retry.
Failure accounting includes a conservative full-selection traffic charge because
ZIP CRC failures can occur before decoded bytes are delivered to this function.
All FORMAT fields and INFO except RNAMES are preserved; no allele/GT changes.
Unsorted input fails by default; an explicitly reviewed preserve_and_report
policy retains every source record and flags sorting required before matching.
Inventory keys and contig names have a separate 4 MiB memory budget.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import io
import json
import os
from pathlib import Path
import re
import zipfile

if __package__:
    from .stream_vcf_rnames import iter_stripped_vcf_lines
else:
    from stream_vcf_rnames import iter_stripped_vcf_lines

CALLERS = ("cutesv", "debreak", "sawfish", "sniffles", "svim", "svpg")
MEMBERS = tuple(f"SV_callsets/HG002_benchmark/{caller}/hifi.vcf" for caller in CALLERS)
DECODED_CAP = 2 * 1024**3
AMENDED_DECODED_CAP = 3 * 1024**3
FINAL_DECODED_CAP = 4 * 1024**3
LINE_CAP = 32 * 1024**2
FINAL_LINE_CAP = 128 * 1024**2
REPO = Path(__file__).resolve().parents[1]
COLUMNS = "#CHROM POS ID REF ALT QUAL FILTER INFO FORMAT".split()


def _snapshot(path, source):
    def signature(stat):
        return (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns)
    file_signature = signature(os.fstat(source.fileno()))
    if signature(path.stat()) != file_signature:
        raise ValueError("Archive path and open source differ")
    return file_signature


def _protocol(path, digest):
    if not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise ValueError("An explicit protocol SHA256 is required")
    with path.open("rb") as source:
        raw = source.read(1024**2 + 1)
    if len(raw) > 1024**2:
        raise ValueError("Protocol exceeds 1 MiB")
    if hashlib.sha256(raw).hexdigest() != digest:
        raise ValueError("Protocol SHA256 mismatch")
    protocol = json.loads(raw)
    if protocol.get("body_read_approved") is not True or not isinstance(
        protocol.get("independent_outcome_approval"), str
    ) or not protocol["independent_outcome_approval"].strip():
        raise ValueError("Independent outcome approval for body reads is required")
    header = protocol["header_protocol"]
    if header["members"] != list(MEMBERS):
        raise ValueError("Frozen six-member selection differs or contains duplicates")
    amendment = protocol.get("source_pass_amendment")
    if amendment not in (None, "remaining-five-stream-rnames-v1", "remaining-five-large-record-v1"):
        raise ValueError("Unsupported source-pass amendment")
    final_amendment = amendment == "remaining-five-large-record-v1"
    cap_limit = FINAL_DECODED_CAP if final_amendment else AMENDED_DECODED_CAP if amendment else DECODED_CAP
    line_limit = FINAL_LINE_CAP if final_amendment else LINE_CAP
    cap, line_cap = protocol["max_source_decoded_bytes"], protocol["max_line_bytes"]
    prior = protocol["charged_prior_source_decoded_bytes"]
    if type(cap) is not int or type(prior) is not int or not 0 <= prior <= cap <= cap_limit or cap == 0:
        raise ValueError(f"Selected-source decoded budget must be within {cap_limit // 1024**3} GiB")
    if type(line_cap) is not int or not 0 < line_cap <= line_limit:
        raise ValueError(f"Explicit line budget must be within {line_limit // 1024**2} MiB")
    account = protocol.get("controller_traffic_account")
    if not isinstance(account, str) or not account.strip():
        raise ValueError("External controller traffic account is required")
    for key, length in (("expected_archive_md5", 32), ("verified_archive_sha256", 64)):
        if not re.fullmatch(rf"[0-9a-f]{{{length}}}", header[key]):
            raise ValueError(f"Invalid archive pin: {key}")
    if type(header["expected_archive_bytes"]) is not int or header["expected_archive_bytes"] <= 0:
        raise ValueError("Positive archive byte pin required")
    order_policy = protocol.get("input_order_policy", "require_header_order")
    if order_policy not in ("require_header_order", "preserve_and_report"):
        raise ValueError("Unsupported input-order policy")
    if amendment:
        if protocol.get("raw_line_policy") != "stream_rnames":
            raise ValueError("Remaining-five amendment requires bounded streaming")
        if protocol.get("execution_callers") != list(CALLERS[1:]):
            raise ValueError("Remaining-five amendment requires exactly five unfinished callers")
        if set(protocol.get("reused_completed_callers", {})) != {"cutesv"}:
            raise ValueError("Remaining-five amendment requires verified cuteSV reuse")
        global_cap = protocol.get("global_decoded_limit_bytes")
        global_prior = protocol.get("charged_prior_global_decoded_bytes")
        global_limit = (12 if final_amendment else 6) * 1024**3
        if (type(global_cap) is not int or type(global_prior) is not int
                or not prior <= global_prior <= global_cap <= global_limit):
            raise ValueError(f"Explicit aggregate traffic budget within {global_limit // 1024**3} GiB required")
    elif any(key in protocol for key in ("execution_callers", "reused_completed_callers", "raw_line_policy")):
        raise ValueError("Partial reuse or streaming requires explicit source-pass amendment")
    return header, [prior, cap], line_cap, account, order_policy, protocol


def _record(fields):
    if len(fields) != 10 or not fields[0] or not fields[2] or not fields[3] or not fields[4]:
        raise ValueError("Expected a single-sample VCF record")
    if not fields[1].isascii() or not fields[1].isdigit() or int(fields[1]) < 1:
        raise ValueError("Invalid VCF position")
    info, kept = {}, []
    for token in fields[7].split(";") if fields[7] != "." else []:
        key = token.partition("=")[0]
        if not key or key in info:
            raise ValueError("Duplicate or empty INFO key")
        info[key] = token.partition("=")[2]
        if key != "RNAMES":
            kept.append(token)
    fields[7] = ";".join(kept) or "."
    formats = fields[8].split(":") if fields[8] != "." else []
    values = fields[9].split(":")
    if len(formats) != len(set(formats)) or len(values) > max(1, len(formats)):
        raise ValueError("Invalid or duplicate FORMAT fields")
    gt = None
    if "GT" in formats:
        index = formats.index("GT")
        gt = values[index] if index < len(values) else "."
        if not re.fullmatch(r"(?:\d+|\.)(?:[/|](?:\d+|\.))*", gt):
            raise ValueError("Invalid genotype")
    alt = fields[4]
    representation = ("multiallelic" if "," in alt else "breakend" if "[" in alt or "]" in alt
                      else "symbolic" if alt.startswith("<") or alt == "*" else "sequence")
    svtype = info.get("SVTYPE")
    if not svtype:
        svtype = ("MULTIALLELIC" if representation == "multiallelic" else "BND"
                  if representation == "breakend" else alt.strip("<>")
                  if representation == "symbolic" else "INS" if len(alt) > len(fields[3])
                  else "DEL" if len(alt) < len(fields[3]) else "SUB")
    return gt, svtype, representation, int("RNAMES" in info)


def _stage_member(stream, output, budget, line_cap=LINE_CAP,
                  order_policy="require_header_order", *, stream_rnames=False, chunk_size=65_536):
    input_sha, output_sha, header_sha = hashlib.sha256(), hashlib.sha256(), hashlib.sha256()
    filters, types, genotypes, representations = (Counter() for _ in range(4))
    counts = dict(records=0, gt_absent=0, gt_missing=0, gt_phased=0, gt_reference=0,
                  omitted_RNAMES=0, decoded_bytes=0, contig_order_violations=0,
                  position_order_violations=0)
    ranks, closed, current, previous_pos, previous_rank = {}, set(), None, 0, -1
    metadata_bytes = 0
    def bounded_key(mapping, key):
        nonlocal metadata_bytes
        if key not in mapping:
            metadata_bytes += len(key.encode()) + 128
            if metadata_bytes > 4 * 1024**2:
                raise ValueError("Inventory metadata exceeds 4 MiB bound")
    columns = False
    stream_stats = {}
    def legacy_lines():
        while True:
            raw = stream.readline(min(line_cap, budget[1] - budget[0]) + 1)
            budget[0] += len(raw)
            counts["decoded_bytes"] += len(raw)
            if budget[0] > budget[1]:
                raise ValueError("Selected-source decoded body budget exceeded")
            if len(raw) > line_cap:
                raise ValueError(f"VCF line exceeds approved {line_cap}-byte bound")
            if not raw:
                return
            yield raw, 0
    lines = (iter_stripped_vcf_lines(stream, budget, line_cap, stream_stats, chunk_size=chunk_size)
             if stream_rnames else legacy_lines())
    for raw, streamed_omitted in lines:
        input_sha.update(raw)
        text = raw.decode("utf-8").rstrip("\r\n")
        if not columns:
            if text.startswith("##"):
                if text.startswith("##contig=<"):
                    identifier = re.search(r"(?:<|,)ID=([^,>]+)", text)
                    if identifier is None:
                        raise ValueError("Contig declaration lacks an ID")
                    chrom = identifier.group(1)
                    if chrom in ranks:
                        raise ValueError("Duplicate contig declaration")
                    bounded_key(ranks, chrom)
                    ranks[chrom] = len(ranks)
            elif text.startswith("#CHROM\t"):
                fields = text.split("\t")
                if len(fields) != 10 or fields[:9] != COLUMNS or not fields[9]:
                    raise ValueError("Expected exactly one sample in VCF header")
                columns = True
            else:
                raise ValueError("Missing single-sample VCF column header")
            header_sha.update(raw)
            staged = raw
        else:
            if text.startswith("#"):
                raise ValueError("Header line in VCF body")
            fields = text.split("\t")
            gt, svtype, representation, omitted = _record(fields)
            chrom, pos = fields[0], int(fields[1])
            if chrom not in ranks:
                raise ValueError("VCF body contig is not declared in its header")
            rank = ranks[chrom]
            if chrom != current:
                if chrom in closed or rank < previous_rank:
                    counts["contig_order_violations"] += 1
                    if order_policy == "require_header_order":
                        raise ValueError("Unsorted VCF contig order")
                if current is not None:
                    closed.add(current)
                current, previous_pos = chrom, 0
            if pos < previous_pos:
                counts["position_order_violations"] += 1
                if order_policy == "require_header_order":
                    raise ValueError("Unsorted VCF coordinates")
            previous_pos, previous_rank = pos, rank
            for mapping, key in ((filters, fields[6]), (types, svtype),
                                 (genotypes, "<absent>" if gt is None else gt), (representations, representation)):
                bounded_key(mapping, key)
            filters[fields[6]] += 1
            types[svtype] += 1
            genotypes["<absent>" if gt is None else gt] += 1
            representations[representation] += 1
            counts["records"] += 1
            counts["gt_absent"] += int(gt is None)
            counts["gt_missing"] += int(gt is None or "." in gt)
            counts["gt_phased"] += int(gt is not None and "|" in gt)
            counts["gt_reference"] += int(gt is not None and all(a == "0" for a in re.split(r"[/|]", gt)))
            counts["omitted_RNAMES"] += omitted + streamed_omitted
            ending = b"\r\n" if raw.endswith(b"\r\n") else b"\n" if raw.endswith(b"\n") else b""
            staged = "\t".join(fields).encode() + ending
        output.write(staged)
        output_sha.update(staged)
    if not columns:
        raise ValueError("Missing VCF column header")
    if stream_rnames:
        counts["decoded_bytes"] = stream_stats["decoded_bytes"]
    source_digest = stream_stats["source_sha256"] if stream_rnames else input_sha.hexdigest()
    return {**counts, "requires_sorting": bool(counts["contig_order_violations"] or
                                             counts["position_order_violations"]),
            "input_order_policy": order_policy,
            "by_filter": dict(filters), "by_type": dict(types), "by_gt": dict(genotypes),
            "by_alt_representation": dict(representations), "source_sha256": source_digest,
            "staged_sha256": output_sha.hexdigest(), "header_sha256": header_sha.hexdigest(),
            "raw_line_policy": "stream_rnames" if stream_rnames else "bounded_whole_line",
            "streaming_buffers": stream_stats if stream_rnames else None}


def _reuse_completed(spec, caller, item):
    """Verify a previously completed derivative without decompressing its source."""
    report_path = Path(spec["report_path"])
    with report_path.open("rb") as source:
        raw = source.read(1024**2 + 1)
    if len(raw) > 1024**2 or hashlib.sha256(raw).hexdigest() != spec["report_sha256"]:
        raise ValueError("Completed-caller report pin mismatch or oversized report")
    record = json.loads(raw)["completed_callers"][caller]
    if (record["member"] != item.filename or not record["selected_member_crc_verified"]
            or record["crc32"] != f"{item.CRC:08x}" or record["decoded_bytes"] != item.file_size
            or record["source_sha256"] != spec["source_sha256"]
            or record["staged_sha256"] != spec["staged_sha256"]):
        raise ValueError("Completed-caller source/derivative metadata differs")
    path = Path(spec["staged_path"]).resolve()
    if path == REPO or REPO in path.parents:
        raise ValueError("Reused caller must remain outside Git")
    digest, read_bytes = hashlib.sha256(), 0
    with path.open("rb") as source:
        before = _snapshot(path, source)
        if before[2] != spec["staged_bytes"]:
            raise ValueError("Reused caller size mismatch")
        while read_bytes < spec["staged_bytes"]:
            chunk = source.read(min(1024**2, spec["staged_bytes"] - read_bytes))
            if not chunk:
                raise ValueError("Reused caller ended before its reserved length")
            digest.update(chunk)
            read_bytes += len(chunk)
        if _snapshot(path, source) != before or digest.hexdigest() != spec["staged_sha256"]:
            raise ValueError("Reused caller SHA256 mismatch or source changed")
    return {**record, "staged_path": str(path), "reused_completed_derivative": True,
            "reuse_verification_bytes": read_bytes}


def stage_zip(archive_path: Path, outdir: Path, protocol_path: Path, protocol_sha256: str) -> dict:
    header, budget, line_cap, account, order_policy, protocol = _protocol(protocol_path, protocol_sha256)
    prior = budget[0]
    amended = protocol.get("source_pass_amendment") is not None
    execution_callers = protocol["execution_callers"] if amended else list(CALLERS)
    reuse_specs = protocol.get("reused_completed_callers", {})
    outdir = outdir.resolve() if not outdir.is_symlink() else outdir
    if outdir.exists() or outdir.is_symlink():
        raise FileExistsError("Refusing to overwrite staging directory")
    if outdir == REPO or REPO in outdir.parents or any((p / ".git").exists() for p in outdir.parents):
        raise ValueError("Staging outputs must be outside Git")
    md5, sha = hashlib.md5(), hashlib.sha256()
    with archive_path.open("rb") as source:
        before = _snapshot(archive_path, source)
        if before[2] != header["expected_archive_bytes"]:
            raise ValueError("Archive byte size mismatch")
        while block := source.read(1024**2):
            md5.update(block)
            sha.update(block)
        if md5.hexdigest() != header["expected_archive_md5"] or sha.hexdigest() != header["verified_archive_sha256"]:
            raise ValueError("Archive MD5/SHA256 mismatch")
        if _snapshot(archive_path, source) != before:
            raise ValueError("Archive metadata changed during preflight")
        source.seek(0)
        with zipfile.ZipFile(source) as archive:
            names = [item.filename for item in archive.infolist()]
            if len(names) != len(set(names)):
                raise ValueError("Duplicate ZIP member names")
            all_selected = {caller: archive.getinfo(name) for caller, name in zip(CALLERS, MEMBERS)}
            selected = [all_selected[caller] for caller in execution_callers]
            if any(item.flag_bits & 0x41 or item.volume != 0 for item in selected):
                raise ValueError("Encrypted or multi-disk selected member")
            selected_bytes = sum(item.file_size for item in selected)
            if selected_bytes + prior > budget[1]:
                raise ValueError("Selected source bodies plus prior passes exceed decoded budget")
            reuse_bytes = sum(spec["staged_bytes"] for spec in reuse_specs.values())
            if amended and (any(type(s["staged_bytes"]) is not int or s["staged_bytes"] < 0
                                for s in reuse_specs.values())
                            or protocol["charged_prior_global_decoded_bytes"] + selected_bytes + reuse_bytes
                            > protocol["global_decoded_limit_bytes"]):
                raise ValueError("Selected source and reuse verification exceed aggregate budget")
            outdir.mkdir(mode=0o700)
            failed_caller = None
            try:
                ledger = {"protocol_sha256": protocol_sha256, "archive_bytes": before[2],
                          "archive_md5": md5.hexdigest(), "archive_sha256": sha.hexdigest(),
                          "members": list(MEMBERS), "callers": {}, "scoring_performed": False,
                          "source_decoded_cap": budget[1], "max_line_bytes": line_cap,
                          "charged_prior_source_decoded_bytes": prior,
                          "input_order_policy": order_policy,
                          "controller_traffic_account": account, "global_traffic_limit_enforced": amended,
                          "execution_callers": execution_callers,
                          "reused_completed_callers": list(reuse_specs),
                          "archive_hash_bytes_read": before[2], "truth_comparison_performed": False,
                          "transformation": "Remove INFO/RNAMES only; preserve header and all FORMAT fields"}
                for caller, spec in reuse_specs.items():
                    failed_caller = caller
                    ledger["callers"][caller] = _reuse_completed(spec, caller, all_selected[caller])
                    failed_caller = None
                for caller, item in zip(execution_callers, selected):
                    failed_caller = caller
                    with archive.open(item) as member, io.BufferedReader(member) as stream:
                        with (outdir / f"{caller}.vcf").open("xb") as output:
                            record = _stage_member(stream, output, budget, line_cap, order_policy,
                                                   stream_rnames=amended)
                    ledger["callers"][caller] = {"member": item.filename, **record,
                                                "selected_member_crc_verified": True, "crc32": f"{item.CRC:08x}",
                                                "staged_path": str(outdir / f"{caller}.vcf")}
                    failed_caller = None
                if _snapshot(archive_path, source) != before:
                    raise ValueError("Archive metadata changed during staging")
                ledger["unique_source_decoded_bytes"] = budget[0] - prior
                ledger["staging_decoded_traffic_bytes"] = budget[0] - prior
                ledger["source_decoded_budget_used_including_prior"] = budget[0]
                if amended:
                    ledger["reuse_verification_bytes"] = reuse_bytes
                    ledger["global_traffic_reserved_including_prior"] = (
                        protocol["charged_prior_global_decoded_bytes"] + selected_bytes + reuse_bytes)
                    ledger["conservative_source_charge_including_prior"] = prior + selected_bytes
                ledger["biological_records_parsed"] = any(r["records"] for r in ledger["callers"].values())
                for name, value in (("header_protocol.json", header), ("caller_inventory.incomplete.json", ledger)):
                    with (outdir / name).open("x") as output:
                        json.dump(value, output, indent=2, sort_keys=True)
                        output.write("\n")
                if _snapshot(archive_path, source) != before:
                    raise ValueError("Archive metadata changed before completion")
                (outdir / "caller_inventory.incomplete.json").rename(outdir / "caller_inventory.json")
            except BaseException as exc:
                exc.staging_decoded_bytes_read = budget[0] - prior
                exc.archive_hash_bytes_read = before[2]
                failure = {"status": "incomplete", "protocol_sha256": protocol_sha256,
                           "members": list(MEMBERS),
                           "completed_callers": ledger["callers"], "failed_caller": failed_caller,
                           "exception_type": type(exc).__name__,
                           "exception_message": str(exc) if type(exc) is ValueError else
                           "Selected ZIP member verification failed" if isinstance(exc, zipfile.BadZipFile) else
                           "VCF UTF-8 decoding failed" if isinstance(exc, UnicodeError) else
                           "Input, I/O or interruption failure; raw fields omitted",
                           "staging_decoded_bytes_read": budget[0] - prior,
                           "source_decoded_budget_used_including_prior": budget[0],
                           "charged_prior_source_decoded_bytes": prior,
                           "conservative_staging_traffic_charge_bytes": max(budget[0] - prior, selected_bytes),
                           "reuse_verification_reservation_bytes": reuse_bytes,
                           "source_decoded_cap": budget[1], "max_line_bytes": line_cap,
                           "controller_traffic_account": account, "global_traffic_limit_enforced": amended}
                with (outdir / "failure.json").open("x") as output:
                    json.dump(failure, output, indent=2, sort_keys=True)
                    output.write("\n")
                raise
    return ledger


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--protocol-sha256", required=True)
    args = parser.parse_args()
    try:
        stage_zip(args.archive, args.outdir, args.protocol, args.protocol_sha256)
    except (ValueError, OSError, KeyError, zipfile.BadZipFile) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
