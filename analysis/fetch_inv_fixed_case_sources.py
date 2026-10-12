"""Fetch one fixed, bounded INV benchmark panel and preserve raw case records."""

from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import urllib.parse
import urllib.request


REPOSITORY = "jamesc99/INV-Benchmark"
COMMIT = "ee77a2f336bf055e5234d7565389aafda56b85cd"
TREE_URL = f"https://api.github.com/repos/{REPOSITORY}/git/trees/{COMMIT}?recursive=1"
RAW_BASE = f"https://raw.githubusercontent.com/{REPOSITORY}/{COMMIT}/"
CASE_CHROMOSOME = "chr2"
CASE_START = 240_685_775
CASE_END = 240_688_980
WINDOW_BP = 1_000
WINDOW_LOW = CASE_START - WINDOW_BP
WINDOW_HIGH = CASE_END + WINDOW_BP

CALLSET_DIRECTORY = "data_zenodo/inv_call_5samples/30x/hg002/"
TRUTH_DIRECTORY = "data_zenodo/truvari_ref_vcf/HG002/"
CALLERS = ("cutesv2", "severus", "sniffles2", "svim", "svisionpro")
PLATFORMS = ("ont", "pb")
ALIGNERS = ("minimap2", "vacmap")
PRIMARY_PATHS = tuple(
    CALLSET_DIRECTORY + f"inv_{caller}_{platform}_{aligner}.vcf"
    for caller in CALLERS
    for platform in PLATFORMS
    for aligner in ALIGNERS
)
SUPPLEMENTAL_PATHS = tuple(
    CALLSET_DIRECTORY + basename for basename in ("gridss2_inv.vcf", "manta_inv.vcf")
)
TRUTH_BASE = "HG002_T2Tv1.1_asm_ref_2aligners.merged.vcf"
TRUTH_PATHS = (
    TRUTH_DIRECTORY + TRUTH_BASE + ".gz",
    TRUTH_DIRECTORY + TRUTH_BASE + "_Tier1.vcf.gz",
    TRUTH_DIRECTORY + TRUTH_BASE + "_Tier2.vcf.gz",
)
EXPECTED_PATHS = PRIMARY_PATHS + SUPPLEMENTAL_PATHS + TRUTH_PATHS

EXPECTED_TREE_ENTRIES = 603
EXPECTED_CALLER_BYTES = 6_065_007
EXPECTED_TRUTH_BYTES = 22_698
METADATA_CAP_BYTES = 1024**2
SOURCE_FILE_CAP_BYTES = 3 * 1024**2
SOURCE_TOTAL_CAP_BYTES = 7 * 1024**2
READ_CHUNK_BYTES = 64 * 1024
VCF_LINE_CAP_BYTES = 512 * 1024
VCF_EXPANDED_CAP_BYTES = 32 * 1024**2
DEFAULT_MANIFEST = (
    Path(__file__).resolve().parents[1] / "results" / "inv_fixed_case_20261013" / "sources.json"
)
RUNS_ROOT = Path(__file__).resolve().parents[2] / "runs"
RUNS_NAME_PREFIX = "inv-fixed-case-20261013."

HEADER_KINDS = {
    "fileformat": "fileformat",
    "reference": "reference",
    "contig": "contig",
    "sample": "sample",
    "source": "source",
    "version": "version",
    "bcftools_viewversion": "version",
    "filedate": "date",
    "command": "command",
    "commandline": "command",
    "cmdline": "command",
    "bcftools_viewcommand": "command",
}
HEADER_ALIAS_DISPLAY = {
    "commandline": "commandline",
    "cmdline": "cmdline",
    "bcftools_viewcommand": "bcftools_viewCommand",
    "bcftools_viewversion": "bcftools_viewVersion",
}
MATE_RE = re.compile(r"[\[\]](chr2|2):(\d+)[\[\]]")


class VCFFormatError(ValueError):
    def __init__(self, message, summary):
        super().__init__(message)
        self.summary = summary


def expected_sources():
    return [
        {
            "group": "long_read_caller_panel",
            "path": path,
        }
        for path in PRIMARY_PATHS
    ] + [
        {"group": "supplemental_short_read_controls", "path": path}
        for path in SUPPLEMENTAL_PATHS
    ] + [
        {"group": "truth_set", "path": path}
        for path in TRUTH_PATHS
    ]


def raw_url_for(path):
    return RAW_BASE + urllib.parse.quote(path, safe="/")


def _header(response, name):
    headers = response.headers
    value = headers.get(name)
    if value is not None:
        return value
    lowered = name.lower()
    for key, candidate in headers.items():
        if key.lower() == lowered:
            return candidate
    return None


def _check_response(response, expected_status=200):
    if response.status != expected_status:
        raise ValueError(f"Unexpected HTTP status {response.status}; expected {expected_status}")
    encoding = _header(response, "Content-Encoding")
    if encoding not in (None, "", "identity"):
        raise ValueError(f"Unexpected HTTP content encoding: {encoding}")


def _content_length(response):
    value = _header(response, "Content-Length")
    if value is None:
        return None
    try:
        length = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("Invalid Content-Length header") from exc
    if length < 0:
        raise ValueError("Negative Content-Length header")
    return length


def read_metadata_response(response, cap_bytes=METADATA_CAP_BYTES):
    """Read one metadata response without consuming more than its separate cap."""
    _check_response(response)
    declared_length = _content_length(response)
    if declared_length is not None and declared_length > cap_bytes:
        raise ValueError("Git tree metadata exceeds 1 MiB cap")
    chunks, total = [], 0
    while total < cap_bytes:
        chunk = response.read(min(READ_CHUNK_BYTES, cap_bytes - total))
        if not chunk:
            break
        total += len(chunk)
        if total > cap_bytes:
            raise ValueError("Git tree metadata exceeds 1 MiB cap")
        chunks.append(chunk)
    if declared_length is not None and total != declared_length:
        raise ValueError("Git tree metadata body size differs from Content-Length")
    if total == cap_bytes and declared_length != cap_bytes:
        raise ValueError("Metadata cap reached before EOF could be confirmed")
    return b"".join(chunks)


def _validate_tree_entries(tree_document):
    if tree_document.get("truncated") is not False:
        raise ValueError("Pinned Git tree is truncated or missing its truncation status")
    entries = tree_document.get("tree")
    if not isinstance(entries, list) or len(entries) != EXPECTED_TREE_ENTRIES:
        raise ValueError("Pinned Git tree must contain the complete 603-entry tree")
    by_path = {}
    duplicates = set()
    for entry in entries:
        path = entry.get("path")
        if path in by_path:
            duplicates.add(path)
        by_path[path] = entry
    if duplicates:
        raise ValueError("Git tree contains duplicate paths")

    selected = []
    for expected in expected_sources():
        entry = by_path.get(expected["path"])
        if entry is None or entry.get("type") != "blob":
            raise ValueError(f"Missing exact pinned source blob: {expected['path']}")
        size, sha = entry.get("size"), entry.get("sha")
        if not isinstance(size, int) or size < 0:
            raise ValueError(f"Invalid declared size for {expected['path']}")
        if size > SOURCE_FILE_CAP_BYTES:
            raise ValueError(f"Source exceeds 3 MiB individual cap: {expected['path']}")
        if not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{40}", sha):
            raise ValueError(f"Invalid Git blob SHA-1 for {expected['path']}")
        selected.append({
            **expected,
            "size": size,
            "git_blob_sha1": sha,
            "raw_url": raw_url_for(expected["path"]),
        })

    total = sum(item["size"] for item in selected)
    if total > SOURCE_TOTAL_CAP_BYTES:
        raise ValueError("Selected source files exceed 7 MiB cumulative cap")
    caller_total = sum(item["size"] for item in selected if item["group"] != "truth_set")
    truth_total = sum(item["size"] for item in selected if item["group"] == "truth_set")
    if caller_total != EXPECTED_CALLER_BYTES:
        raise ValueError("Pinned caller-panel byte total differs from the frozen 6,065,007 bytes")
    if truth_total != EXPECTED_TRUTH_BYTES:
        raise ValueError("Pinned truth-file byte total differs from the frozen 22,698 bytes")
    return selected


def _request(url, opener=None):
    request = urllib.request.Request(
        url,
        headers={
            "Accept-Encoding": "identity",
            "User-Agent": "inv-fixed-case-source-audit/1.0",
        },
    )
    open_url = urllib.request.urlopen if opener is None else opener
    return open_url(request, timeout=25)


def read_source_response(response, expected_size, transferred_before=0):
    """Read exactly one tree-declared source body, with bounded chunk reads and EOF probe."""
    _check_response(response)
    if expected_size > SOURCE_FILE_CAP_BYTES:
        raise ValueError("Source exceeds 3 MiB individual cap")
    if transferred_before + expected_size + 1 > SOURCE_TOTAL_CAP_BYTES:
        raise ValueError("Source read plus overlong-body probe exceeds 7 MiB cumulative cap")
    declared_length = _content_length(response)
    if declared_length is not None and declared_length != expected_size:
        raise ValueError("HTTP Content-Length differs from pinned Git tree size")
    probe_needed = declared_length is None
    probe_reservation = 1 if probe_needed else 0

    chunks, total = [], 0
    while total < expected_size:
        amount = min(READ_CHUNK_BYTES, expected_size - total)
        if transferred_before + total + amount + probe_reservation > SOURCE_TOTAL_CAP_BYTES:
            raise ValueError("Source chunk plus overlong-body probe exceeds cumulative cap")
        if total + amount + probe_reservation > SOURCE_FILE_CAP_BYTES:
            raise ValueError("Source chunk plus overlong-body probe exceeds individual cap")
        chunk = response.read(amount)
        if not chunk:
            raise ValueError("Source body ended before the pinned Git tree size")
        if len(chunk) > amount:
            raise ValueError("HTTP response returned more bytes than requested")
        chunks.append(chunk)
        total += len(chunk)

    if transferred_before + total + probe_reservation > SOURCE_TOTAL_CAP_BYTES:
        raise ValueError("Source EOF probe exceeds cumulative cap")
    if total + probe_reservation > SOURCE_FILE_CAP_BYTES:
        raise ValueError("Source EOF probe exceeds individual cap")
    if probe_needed and response.read(1):
        raise ValueError("Source body exceeds the pinned Git tree size")
    if declared_length is not None and total != declared_length:
        raise ValueError("Source body size differs from Content-Length")
    return b"".join(chunks)


def verify_git_blob(path, body, declared_size, declared_sha1):
    if len(body) != declared_size:
        raise ValueError(f"Downloaded size differs from Git tree metadata: {path}")
    git_header = f"blob {len(body)}\0".encode("ascii")
    actual_sha1 = hashlib.sha1(git_header + body).hexdigest()
    if actual_sha1 != declared_sha1:
        raise ValueError(f"Git blob SHA-1 mismatch: {path}")
    return actual_sha1


def _header_key(line):
    match = re.match(r"^##([A-Za-z0-9_]+)(?:=|<|\b)", line)
    if match:
        return match.group(1).lower()
    return None


def _header_kind(line):
    key = _header_key(line)
    if key:
        return HEADER_KINDS.get(key)
    if line.startswith("#CHROM\t"):
        return "chrom_columns"
    return None


def _make_record(fields, line, line_number, source_path, summary):
    if len(fields) < 8:
        summary["malformed_records"].append({
            "line_number": line_number,
            "reason": f"expected at least 8 tab-separated fields; found {len(fields)}",
        })
        return
    chromosome = fields[0]
    try:
        position = int(fields[1])
        if position < 1:
            raise ValueError
    except ValueError:
        summary["malformed_records"].append({
            "line_number": line_number,
            "reason": "POS is not a positive integer",
        })
        return

    end_values = []
    malformed_end = False
    for item in fields[7].split(";"):
        if item.startswith("END="):
            value = item[4:]
            try:
                parsed = int(value)
                if parsed < 1:
                    raise ValueError
            except ValueError:
                malformed_end = True
                summary["malformed_records"].append({
                    "line_number": line_number,
                    "reason": "INFO/END is not a positive integer",
                })
            else:
                end_values.append(parsed)

    mates = [
        {"chromosome": chromosome_name, "position": int(position_text)}
        for chromosome_name, position_text in MATE_RE.findall(fields[4])
    ]
    record = {
        "line_number": line_number,
        "raw_record": line,
        "fields": fields,
        "chromosome": chromosome,
        "position": position,
        "id": fields[2],
        "ref": fields[3],
        "alt": fields[4],
        "qual": fields[5],
        "filter": fields[6],
        "info": fields[7],
        "end_field_values": [str(value) for value in end_values],
        "end_positions": end_values,
        "mate_endpoints": mates,
        "format_and_samples": fields[8:],
    }
    same_chromosome = chromosome in {"chr2", "2"}
    near = same_chromosome and (
        WINDOW_LOW <= position <= WINDOW_HIGH
        or any(WINDOW_LOW <= end <= WINDOW_HIGH for end in end_values)
    )
    near = near or any(
        endpoint["chromosome"] in {"chr2", "2"}
        and WINDOW_LOW <= endpoint["position"] <= WINDOW_HIGH
        for endpoint in mates
    )
    if near:
        summary["nearby_records"].append(record)

    if same_chromosome and not malformed_end:
        for end in end_values:
            low_endpoint, high_endpoint = sorted((position, end))
            spans_target = low_endpoint <= CASE_START and high_endpoint >= CASE_END
            both_outside_window = low_endpoint < WINDOW_LOW and high_endpoint > WINDOW_HIGH
            if spans_target and both_outside_window:
                summary["spanning_records"].append(record)
                break


def scan_vcf_stream(stream, source_path):
    summary = {
        "source_path": source_path,
        "total_records_read": 0,
        "expanded_bytes_read": 0,
        "relevant_headers": [],
        "header_counts": {kind: 0 for kind in (*HEADER_KINDS.values(), "chrom_columns")},
        "nearby_records": [],
        "spanning_records": [],
        "malformed_records": [],
    }
    line_number = 0
    while True:
        raw_line = stream.readline(VCF_LINE_CAP_BYTES + 1)
        if not raw_line:
            break
        line_number += 1
        summary["expanded_bytes_read"] += len(raw_line)
        if summary["expanded_bytes_read"] > VCF_EXPANDED_CAP_BYTES:
            raise ValueError(f"Expanded VCF exceeds 32 MiB cap: {source_path}")
        if len(raw_line) > VCF_LINE_CAP_BYTES:
            summary["malformed_records"].append({
                "line_number": line_number,
                "reason": "line exceeds 512 KiB bounded line cap",
            })
            while raw_line and not raw_line.endswith(b"\n"):
                raw_line = stream.readline(VCF_LINE_CAP_BYTES + 1)
                summary["expanded_bytes_read"] += len(raw_line)
                if summary["expanded_bytes_read"] > VCF_EXPANDED_CAP_BYTES:
                    raise ValueError(f"Expanded VCF exceeds 32 MiB cap: {source_path}")
            continue
        try:
            line = raw_line.decode("utf-8").rstrip("\r\n")
        except UnicodeDecodeError:
            summary["malformed_records"].append({
                "line_number": line_number,
                "reason": "line is not valid UTF-8",
            })
            continue
        if not line:
            continue
        if line.startswith("#"):
            kind = _header_kind(line)
            if kind:
                summary["relevant_headers"].append(line)
                summary["header_counts"][kind] += 1
            continue
        summary["total_records_read"] += 1
        _make_record(line.split("\t"), line, line_number, source_path, summary)

    if summary["malformed_records"]:
        first = summary["malformed_records"][0]
        raise VCFFormatError(
            f"Malformed VCF in {source_path}, line {first['line_number']}: {first['reason']}",
            summary,
        )
    return summary


def summarize_vcf_body(body, source_path):
    if source_path.endswith(".gz"):
        with gzip.GzipFile(fileobj=io.BytesIO(body), mode="rb") as stream:
            summary = scan_vcf_stream(stream, source_path)
        summary["gzip_crc_verified"] = True
    else:
        with io.BytesIO(body) as stream:
            summary = scan_vcf_stream(stream, source_path)
        summary["gzip_crc_verified"] = None
    return summary


def _write_exclusive(path, body):
    with path.open("xb") as handle:
        handle.write(body)


def new_manifest(sources_dir):
    return {
        "schema_version": 1,
        "status": "IN_PROGRESS",
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "case": {
            "source_order": "First HG002 row of Supplementary Table S10, fixed before caller VCF body inspection",
            "chromosome": CASE_CHROMOSOME,
            "start": CASE_START,
            "end": CASE_END,
            "reported_length_bp": CASE_END - CASE_START,
            "window_bp_each_side": WINDOW_BP,
            "window_low_inclusive": WINDOW_LOW,
            "window_high_inclusive": WINDOW_HIGH,
            "supplement_label": "GRCh38/hg38",
            "coordinate_build_status": "UNKNOWN_PENDING_INDEPENDENT_HEADER_AND_RECORD_REVIEW",
            "coordinate_convention_status": "UNKNOWN; coordinates are used verbatim without conversion",
            "T2Tv1.1_filename_token_is_not_build_proof": True,
        },
        "provenance": {
            "repository": REPOSITORY,
            "commit": COMMIT,
            "tree_url": TREE_URL,
            "tree_entry_count_expected": EXPECTED_TREE_ENTRIES,
            "source_directory": str(Path(sources_dir).resolve()),
            "raw_file_base": RAW_BASE,
        },
        "limits": {
            "tree_metadata_max_bytes": METADATA_CAP_BYTES,
            "source_file_max_bytes": SOURCE_FILE_CAP_BYTES,
            "source_total_max_bytes": SOURCE_TOTAL_CAP_BYTES,
            "vcf_expanded_file_max_bytes": VCF_EXPANDED_CAP_BYTES,
            "vcf_line_max_bytes": VCF_LINE_CAP_BYTES,
            "source_request_chunk_bytes": READ_CHUNK_BYTES,
        },
        "retrieval": {
            "tree_metadata_bytes": 0,
            "source_bytes_transferred": 0,
            "tree_truncated": None,
            "tree_entries": None,
            "declared_source_bytes": None,
            "whole_source_set_sha256": None,
        },
        "sources": [],
        "scientific_recovery_claim": "NOT_ASSESSED",
    }


def validate_sources_directory(sources_dir, require_task_path=False):
    directory = Path(sources_dir)
    if not directory.is_dir():
        raise ValueError("Existing task-specific source directory required")
    if any(directory.iterdir()):
        raise ValueError("Source directory must be empty; source files are never overwritten")
    if require_task_path:
        resolved = directory.resolve()
        if resolved.parent != RUNS_ROOT.resolve() or not resolved.name.startswith(RUNS_NAME_PREFIX):
            raise ValueError("Source directory must be the mktemp task directory under runs/")
    return directory


def fetch_sources(sources_dir, opener=None, manifest=None):
    directory = validate_sources_directory(sources_dir)
    manifest = new_manifest(directory) if manifest is None else manifest

    with _request(TREE_URL, opener) as response:
        tree_bytes = read_metadata_response(response)
    manifest["retrieval"]["tree_metadata_bytes"] = len(tree_bytes)
    try:
        tree_document = json.loads(tree_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("Pinned Git tree response is not valid UTF-8 JSON") from exc
    manifest["retrieval"]["tree_truncated"] = tree_document.get("truncated")
    manifest["retrieval"]["tree_entries"] = len(tree_document.get("tree", []))

    # Validate the complete path set and every cap before making a source-body request.
    selected = _validate_tree_entries(tree_document)
    declared_total = sum(item["size"] for item in selected)
    manifest["retrieval"]["declared_source_bytes"] = declared_total
    manifest["sources"] = [
        {
            **item,
            "local_filename": Path(item["path"]).name,
            "download_status": "PENDING",
        }
        for item in selected
    ]

    for source in manifest["sources"]:
        output_path = directory / source["local_filename"]
        if output_path.exists():
            raise FileExistsError(f"Refusing to overwrite source body: {output_path}")
        try:
            with _request(source["raw_url"], opener) as response:
                source["http_status"] = response.status
                _check_response(response)
                content_length = _content_length(response)
                if content_length is not None and content_length != source["size"]:
                    raise ValueError(f"HTTP Content-Length differs from tree size: {source['path']}")
                body = read_source_response(
                    response,
                    source["size"],
                    transferred_before=manifest["retrieval"]["source_bytes_transferred"],
                )
        except Exception as exc:
            source["download_status"] = "FAILED"
            source["failure"] = {"type": type(exc).__name__, "message": str(exc)}
            raise

        _write_exclusive(output_path, body)
        source["download_status"] = "BODY_SAVED"
        source["downloaded_bytes"] = len(body)
        source["sha256"] = hashlib.sha256(body).hexdigest()
        manifest["retrieval"]["source_bytes_transferred"] += len(body)
        try:
            verified_sha1 = verify_git_blob(
                source["path"], body, source["size"], source["git_blob_sha1"]
            )
        except Exception as exc:
            source["download_status"] = "INTEGRITY_FAILED"
            source["failure"] = {"type": type(exc).__name__, "message": str(exc)}
            raise
        source["git_blob_sha1_verified"] = True
        source["git_blob_sha1_computed"] = verified_sha1
        if source["path"].endswith((".vcf", ".vcf.gz")):
            try:
                source["vcf_summary"] = summarize_vcf_body(body, source["path"])
            except VCFFormatError as exc:
                source["vcf_summary"] = exc.summary
                source["download_status"] = "VCF_MALFORMED"
                source["failure"] = {"type": type(exc).__name__, "message": str(exc)}
                raise
            except Exception as exc:
                source["download_status"] = "VCF_VALIDATION_FAILED"
                source["failure"] = {"type": type(exc).__name__, "message": str(exc)}
                raise
        else:
            source["vcf_summary"] = None
        source["download_status"] = "VALIDATED"

    manifest["retrieval"]["whole_source_set_sha256"] = hashlib.sha256(
        "".join(source["sha256"] for source in manifest["sources"]).encode("ascii")
    ).hexdigest()
    manifest["status"] = "COMPLETE"
    return manifest


def write_manifest_exclusive(path, manifest):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, ensure_ascii=False, allow_nan=False)
        handle.write("\n")


def _local_attempt_notes(alias_counts):
    observed = ", ".join(
        f"{HEADER_ALIAS_DISPLAY[key]}={alias_counts[key]}"
        for key in HEADER_ALIAS_DISPLAY
        if alias_counts.get(key, 0)
    ) or "none"
    return (
        "Local revision attempt notes (transcribed; no raw terminal log):\n"
        "\n"
        "1. The first header parser omitted four VCF metadata aliases. The retained-source audit found "
        "##commandline, ##cmdline, and ##bcftools_viewCommand command headers, plus "
        "##bcftools_viewVersion version headers. The local corrected-parser pass counted: "
        f"{observed}. The original sources.json remains unchanged.\n"
        "\n"
        "2. The first local Git-blob verifier attempt encoded the Git header terminator as the two "
        "characters backslash and zero, not one NUL byte. That verifier attempt failed. The corrected "
        "local verifier used b'blob ' + decimal_size + bytes([0]) + source_body; all 25 retained "
        "source files then matched their recorded size, SHA-256, and Git blob SHA-1. This was a "
        "verifier-command error. It did not change any source file and caused no network request.\n"
        "\n"
        "This revision reuses the original 25 retained source bodies. Historical source_bytes_transferred "
        "is preserved from sources.json; new_operation_network_bytes is 0. No biological interpretation "
        "is made.\n"
    )


def regenerate_local_revision(original_manifest_path, output_manifest_path, first_attempts_path):
    """Rebuild header metadata from the 25 retained bodies without any network access."""
    original_path = Path(original_manifest_path)
    output_path = Path(output_manifest_path)
    attempts_path = Path(first_attempts_path)
    if not original_path.is_file():
        raise FileNotFoundError(f"Original source manifest not found: {original_path}")
    if output_path.resolve() == original_path.resolve() or attempts_path.resolve() == original_path.resolve():
        raise ValueError("Local revision outputs must not overwrite the original manifest")
    if output_path.resolve() == attempts_path.resolve():
        raise ValueError("Corrected manifest and attempt notes must use separate output paths")
    if output_path.exists() or attempts_path.exists():
        raise FileExistsError("Refusing to overwrite local revision output")

    original_bytes = original_path.read_bytes()
    try:
        original = json.loads(original_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("Original source manifest is not valid UTF-8 JSON") from exc
    if original.get("status") != "COMPLETE" or "revision" in original:
        raise ValueError("Expected the complete, unrevised original source manifest")

    sources = original.get("sources")
    expected_paths = [item["path"] for item in expected_sources()]
    if not isinstance(sources, list) or [source.get("path") for source in sources] != expected_paths:
        raise ValueError("Original manifest does not contain the exact frozen 25-source panel")
    source_directory = Path(original.get("provenance", {}).get("source_directory", ""))
    if not source_directory.is_dir():
        raise ValueError("Original manifest's retained source directory is unavailable")
    for output in (output_path, attempts_path):
        try:
            output.resolve().relative_to(source_directory.resolve())
        except ValueError:
            continue
        raise ValueError("Revision outputs must not be written into the retained source directory")

    existing_names = {path.name for path in source_directory.iterdir()}
    expected_names = {Path(path).name for path in expected_paths}
    if existing_names != expected_names:
        raise ValueError("Retained source directory must contain exactly the frozen 25 source files")

    revised = deepcopy(original)
    alias_counts = Counter()
    actual_source_bytes = 0
    source_hashes = []
    for source, revised_source in zip(sources, revised["sources"]):
        filename = source.get("local_filename")
        expected_filename = Path(source["path"]).name
        if filename != expected_filename or Path(filename).name != filename:
            raise ValueError(f"Unsafe or unexpected retained filename for {source['path']}")
        body = (source_directory / filename).read_bytes()
        body_size = len(body)
        if body_size != source.get("size") or body_size != source.get("downloaded_bytes"):
            raise ValueError(f"Retained source size differs from original manifest: {source['path']}")
        sha256 = hashlib.sha256(body).hexdigest()
        if sha256 != source.get("sha256"):
            raise ValueError(f"Retained source SHA-256 differs from original manifest: {source['path']}")
        git_sha1 = verify_git_blob(
            source["path"], body, body_size, source.get("git_blob_sha1")
        )
        if source.get("git_blob_sha1_verified") is not True:
            raise ValueError(f"Original manifest lacks Git-blob verification: {source['path']}")
        if source.get("git_blob_sha1_computed") not in (None, git_sha1):
            raise ValueError(f"Retained source Git blob SHA-1 differs from original manifest: {source['path']}")

        actual_source_bytes += body_size
        source_hashes.append(sha256)
        old_summary = source.get("vcf_summary")
        if not isinstance(old_summary, dict):
            raise ValueError(f"Original VCF summary is missing: {source['path']}")
        try:
            new_summary = summarize_vcf_body(body, source["path"])
        except Exception as exc:
            raise ValueError(f"Retained source failed local VCF revalidation: {source['path']}: {exc}") from exc
        if set(old_summary) != set(new_summary):
            raise ValueError(f"VCF summary schema changed for {source['path']}")
        for key in old_summary:
            if key not in {"relevant_headers", "header_counts"} and old_summary[key] != new_summary[key]:
                raise ValueError(f"Non-header VCF summary changed for {source['path']}: {key}")

        old_headers = Counter(old_summary["relevant_headers"])
        new_headers = Counter(new_summary["relevant_headers"])
        if old_headers - new_headers:
            raise ValueError(f"A previously recorded header disappeared for {source['path']}")
        added_headers = new_headers - old_headers
        for line, count in added_headers.items():
            key = _header_key(line)
            if key not in HEADER_ALIAS_DISPLAY:
                raise ValueError(f"Unexpected non-alias header addition for {source['path']}: {line}")
            alias_counts[key] += count

        if set(old_summary["header_counts"]) != set(new_summary["header_counts"]):
            raise ValueError(f"VCF header-count schema changed for {source['path']}")
        per_source_aliases = Counter()
        for line, count in added_headers.items():
            per_source_aliases[_header_kind(line)] += count
        for kind, count in new_summary["header_counts"].items():
            if count - old_summary["header_counts"].get(kind, 0) != per_source_aliases[kind]:
                raise ValueError(f"Header-count delta does not match added aliases for {source['path']}")

        revised_source_summary = revised_source["vcf_summary"]
        revised_source_summary["relevant_headers"] = new_summary["relevant_headers"]
        revised_source_summary["header_counts"] = new_summary["header_counts"]

    retrieval = original.get("retrieval", {})
    if retrieval.get("source_bytes_transferred") != actual_source_bytes:
        raise ValueError("Historical source_bytes_transferred does not match retained source sizes")
    if retrieval.get("declared_source_bytes") != actual_source_bytes:
        raise ValueError("Declared source bytes do not match retained source sizes")
    whole_set_hash = hashlib.sha256("".join(source_hashes).encode("ascii")).hexdigest()
    if retrieval.get("whole_source_set_sha256") != whole_set_hash:
        raise ValueError("Retained source-set SHA-256 differs from original manifest")

    display_counts = {
        HEADER_ALIAS_DISPLAY[key]: alias_counts[key]
        for key in HEADER_ALIAS_DISPLAY
        if alias_counts.get(key, 0)
    }
    revised["retrieval"]["new_operation_network_bytes"] = 0
    revised["revision"] = {
        "kind": "LOCAL_ONLY_HEADER_METADATA_CORRECTION",
        "original_manifest_sha256": hashlib.sha256(original_bytes).hexdigest(),
        "source_bodies_reused_without_modification": True,
        "selection_coordinates_hashes_and_records_unchanged": True,
        "header_aliases_added": display_counts,
        "explanation": (
            "The parser now recognizes ##commandline, ##cmdline, and ##bcftools_viewCommand as "
            "command metadata, and ##bcftools_viewVersion as version metadata. All retained source "
            "bodies were re-hashed and re-parsed locally."
        ),
        "new_operation_network_bytes": 0,
    }

    # Normalize only the approved metadata fields. Every other original manifest field must match.
    normalized = deepcopy(revised)
    normalized.pop("revision")
    normalized["retrieval"].pop("new_operation_network_bytes")
    for original_source, normalized_source in zip(sources, normalized["sources"]):
        normalized_source["vcf_summary"]["relevant_headers"] = original_source["vcf_summary"]["relevant_headers"]
        normalized_source["vcf_summary"]["header_counts"] = original_source["vcf_summary"]["header_counts"]
    if normalized != original:
        raise ValueError("Local revision changed a field outside approved header metadata and revision notes")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    attempts_path.parent.mkdir(parents=True, exist_ok=True)
    write_manifest_exclusive(output_path, revised)
    with attempts_path.open("xb") as handle:
        handle.write(_local_attempt_notes(alias_counts).encode("utf-8"))
    return revised


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources-dir", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument(
        "--from-manifest",
        type=Path,
        help="Rebuild headers from retained local source bodies; this mode makes no network requests",
    )
    parser.add_argument("--first-attempts", type=Path)
    args = parser.parse_args()

    if args.from_manifest is not None:
        if args.sources_dir is not None or args.manifest is None or args.first_attempts is None:
            parser.error("--from-manifest requires --manifest and --first-attempts, and forbids --sources-dir")
        revised = regenerate_local_revision(args.from_manifest, args.manifest, args.first_attempts)
        print(json.dumps({
            "status": revised["status"],
            "revision": revised["revision"]["kind"],
            "source_count": len(revised["sources"]),
            "historical_source_bytes_transferred": revised["retrieval"]["source_bytes_transferred"],
            "new_operation_network_bytes": revised["retrieval"]["new_operation_network_bytes"],
            "manifest": str(args.manifest),
            "first_attempts": str(args.first_attempts),
        }, indent=2))
        return

    if args.first_attempts is not None:
        parser.error("--first-attempts is only valid with --from-manifest")
    if args.sources_dir is None:
        parser.error("online source acquisition requires --sources-dir")
    sources_dir = validate_sources_directory(args.sources_dir, require_task_path=True)
    manifest_path = DEFAULT_MANIFEST if args.manifest is None else args.manifest
    if manifest_path.exists():
        raise FileExistsError(f"Refusing to overwrite provenance manifest: {manifest_path}")
    manifest = new_manifest(sources_dir)
    try:
        fetch_sources(sources_dir, manifest=manifest)
    except Exception as exc:
        manifest["status"] = "FAILED"
        manifest["first_failure"] = {"type": type(exc).__name__, "message": str(exc)}
        write_manifest_exclusive(manifest_path, manifest)
        raise
    write_manifest_exclusive(manifest_path, manifest)
    print(json.dumps({
        "status": manifest["status"],
        "source_count": len(manifest["sources"]),
        "source_bytes": manifest["retrieval"]["source_bytes_transferred"],
        "manifest": str(manifest_path),
    }, indent=2))


if __name__ == "__main__":
    main()
