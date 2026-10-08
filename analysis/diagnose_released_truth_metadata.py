#!/usr/bin/env python3
"""Bounded, literal metadata census for the pinned prepared HG002 VCF."""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import stat
import sys

try:
    from .released_truth_units import classify_truth_record
except ImportError:
    from released_truth_units import classify_truth_record

MAX_INPUT = 16 * 1024**2
MAX_REPORT = 1024**2
MAX_ROWS = 30_000
PURPOSE = "technical_metadata_census_not_REF_native_or_scoring"
SOURCE_SHA256 = "c908217f7ec8eba1efe93f51605675a8a8b9676d9c9ca443d1348ad0a00f68d2"
RESERVATION = 34_603_008
PROTOCOL_KEYS = {
    "diagnosis_approved", "purpose", "expected_records", "expected_sample",
    "expected_input_bytes", "eligible_truth_sha256", "source_script_sha256",
    "truth_units_script_sha256", "source_read_reservation_bytes",
}
FLAG_NAMES = (
    "eligibility_issue", "svtype_absent", "svtype_no_value", "svtype_dot",
    "svtype_duplicate_info", "svtype_multivalue", "svtype_unrecognized",
    "svtype_disagreement", "svlen_absent", "svlen_no_value", "svlen_dot",
    "svlen_duplicate_info", "svlen_multivalue", "svlen_noninteger",
    "svlen_sign_mismatch", "svlen_magnitude_mismatch",
)


class CensusError(ValueError):
    pass


def require(ok, message):
    if not ok:
        raise CensusError(message)


def _snapshot(info):
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def _open_regular(path):
    try:
        fd = os.open(os.fspath(path), os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
                     | getattr(os, "O_CLOEXEC", 0))
        info = os.fstat(fd)
        named = os.lstat(path)
        require(stat.S_ISREG(info.st_mode) and stat.S_ISREG(named.st_mode)
                and _snapshot(info) == _snapshot(named), "input must be a stable regular file")
        return fd, _snapshot(info)
    except CensusError:
        if "fd" in locals():
            os.close(fd)
        raise
    except OSError:
        if "fd" in locals():
            os.close(fd)
        raise CensusError("input could not be opened as a regular file") from None


def _read_pinned(path, cap):
    fd, before = _open_regular(path)
    try:
        require(before[2] <= cap, "bounded metadata file exceeds its byte cap")
        data = bytearray()
        while len(data) < cap:
            block = os.read(fd, min(1024**2, cap - len(data)))
            if not block:
                break
            data.extend(block)
        after = _snapshot(os.fstat(fd))
        require(len(data) <= cap and before == after == _snapshot(os.lstat(path)),
                "bounded metadata file changed while read")
        return bytes(data)
    finally:
        os.close(fd)


def _read_source(path):
    fd, before = _open_regular(path)
    try:
        require(before[2] <= MAX_INPUT, "truth input exceeds byte cap")
        data = bytearray()
        while len(data) < MAX_INPUT:
            block = os.read(fd, min(1024**2, MAX_INPUT - len(data)))
            if not block:
                break
            data.extend(block)
        require(len(data) <= MAX_INPUT and len(data) == before[2]
                and before == _snapshot(os.fstat(fd)) == _snapshot(os.lstat(path)),
                "truth input changed while read")
        return bytes(data), before
    finally:
        os.close(fd)


def _posthash(path, snapshot, digest, size):
    fd, opened = _open_regular(path)
    try:
        require(opened == snapshot, "truth snapshot changed before posthash")
        check, count = sha256(), 0
        while count < MAX_INPUT:
            block = os.read(fd, min(1024**2, MAX_INPUT - count))
            if not block:
                break
            count += len(block)
            require(count <= MAX_INPUT, "truth input exceeds byte cap")
            check.update(block)
        require(count == size and check.hexdigest() == digest
                and opened == _snapshot(os.fstat(fd)) == _snapshot(os.lstat(path)),
                "truth bytes or snapshot changed during census")
    finally:
        os.close(fd)


def _pairs_no_duplicates(pairs):
    out = {}
    for key, value in pairs:
        require(key not in out, "duplicate protocol JSON key")
        out[key] = value
    return out


def _split_attributes(value):
    parts, start, quoted, escaped = [], 0, False, False
    for index, char in enumerate(value):
        if escaped:
            escaped = False
        elif char == "\\" and quoted:
            escaped = True
        elif char == '"':
            quoted = not quoted
        elif char == "," and not quoted:
            parts.append(value[start:index]); start = index + 1
    require(not quoted and not escaped, "malformed INFO header declaration")
    parts.append(value[start:])
    attrs = {}
    for part in parts:
        key, sep, val = part.partition("=")
        require(sep and key and key not in attrs, "malformed INFO header declaration")
        attrs[key] = val
    return attrs


def _info_values(raw):
    values = {}
    if raw == ".":
        return values
    for field in raw.split(";"):
        key, sep, value = field.partition("=")
        require(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.]*", key) is not None,
                "malformed INFO field")
        values.setdefault(key, []).append(value if sep else None)
    return values


def _field_view(entries):
    if not entries:
        return "absent", None, False, False
    duplicate = len(entries) > 1
    multivalue = any(value is not None and "," in value for value in entries)
    if duplicate or multivalue:
        return "cardinality", None, duplicate, multivalue
    value = entries[0]
    if value is None:
        return "no_value", None, False, False
    if value == ".":
        return "dot", None, False, False
    return "value", value, False, False


def _header_and_rows(payload):
    try:
        lines = payload.decode("utf-8").splitlines()
    except UnicodeDecodeError:
        raise CensusError("truth VCF is not valid UTF-8") from None
    require(lines and re.fullmatch(r"##fileformat=VCFv[0-9]+\.[0-9]+", lines[0]),
            "malformed or missing VCF fileformat header")
    fileformat, declarations, header_bytes = lines[0], [], len(lines[0].encode("utf-8"))
    declared_info_ids = set()
    columns, rows, in_body = None, [], False
    for line in lines[1:]:
        if not in_body and line.startswith("##"):
            require(not line.startswith("##fileformat="), "duplicate VCF fileformat header")
            require(re.match(r"##[A-Za-z][A-Za-z0-9_]*=", line) is not None,
                    "malformed VCF metaheader")
            if line.startswith("##INFO="):
                require(line.startswith("##INFO=<") and line.endswith(">"),
                        "malformed INFO header declaration")
                attrs = _split_attributes(line[8:-1])
                if attrs.get("ID") in {"SVLEN", "SVTYPE"}:
                    require(attrs["ID"] not in declared_info_ids,
                            "duplicate SVLEN/SVTYPE header declaration")
                    declared_info_ids.add(attrs["ID"])
                    encoded = len(line.encode("utf-8"))
                    require(encoded <= 4096 and header_bytes + encoded <= 16_384,
                            "reported INFO headers exceed safe cap")
                    header_bytes += encoded
                    declarations.append({"id": attrs["ID"], "number": attrs.get("Number"),
                                         "type": attrs.get("Type"), "raw_line": line})
            continue
        if not in_body:
            require(columns is None and line.startswith("#CHROM\t"),
                    "malformed VCF column header")
            columns = line.split("\t")
            require(columns[:9] == ["#CHROM", "POS", "ID", "REF", "ALT", "QUAL",
                                    "FILTER", "INFO", "FORMAT"]
                    and len(columns) == 10 and columns[9] == "HG002",
                    "truth VCF must contain exactly the HG002 sample")
            in_body = True
            continue
        require(not line.startswith("#") and line, "malformed VCF body line")
        rows.append(line)
        require(len(rows) <= MAX_ROWS, "truth row cap exceeded")
    require(in_body, "missing VCF column header")
    return fileformat, declarations, rows


def _first_guard(unit, type_view, type_value, type_duplicate, type_multi,
                 len_view, len_value, len_duplicate, len_multi):
    if unit is None:
        return "eligibility"
    if type_duplicate or type_multi:
        return "SVTYPE cardinality"
    if type_view in {"absent", "no_value", "dot"}:
        return "SVTYPE missing"
    if type_value not in {"INS", "DEL"}:
        return "SVTYPE type"
    if type_value != unit.kind:
        return "SVTYPE disagreement"
    if len_duplicate or len_multi:
        return "SVLEN cardinality"
    if len_view in {"absent", "no_value", "dot"}:
        return "SVLEN missing"
    if len_view == "noninteger":
        return "SVLEN noninteger"
    expected = unit.length if unit.kind == "INS" else -unit.length
    if abs(len_value) != unit.length:
        return "SVLEN magnitude disagreement"
    if len_value != expected:
        return "SVLEN sign disagreement"
    return None


def _parse_payload(payload, source_sha):
    fileformat, declarations, rows = _header_and_rows(payload)
    ids, order = set(), sha256()
    flags = dict.fromkeys(FLAG_NAMES, 0)
    types = {key: 0 for key in ("INS", "DEL", "OTHER", "DOT", "NO_VALUE", "MULTIVALUE", "DUPLICATE", "ABSENT")}
    lengths = {key: 0 for key in ("ABSENT", "NO_VALUE", "DOT", "NONINTEGER", "MULTIVALUE", "DUPLICATE", "INTEGER")}
    presence = {key: 0 for key in ("svtype_present", "svtype_absent", "svlen_present", "svlen_absent")}
    comparisons = {key: 0 for key in ("comparable", "absolute_magnitude_agree", "signed_agree",
                                      "sign_mismatch", "sign_only_mismatch", "magnitude_mismatch")}
    canonical_kind_counts = {"INS": 0, "DEL": 0}
    eligibility_reasons, with_flags, first = {}, 0, None
    for ordinal, raw in enumerate(rows, 1):
        fields = raw.split("\t")
        require(len(fields) == 10, "malformed VCF record column count")
        chrom, pos_text, identity, ref, alt = fields[:5]
        require(re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", chrom) is not None
                and re.fullmatch(r"[0-9]+", pos_text) is not None and ref and alt,
                "malformed VCF coordinate")
        pos = int(pos_text)
        require(pos > 0, "malformed VCF coordinate")
        require(re.fullmatch(r"[0-9a-f]{64}", identity) is not None,
                "truth identity must be 64 lowercase hexadecimal characters")
        normalized_id = identity
        require(normalized_id not in ids, "duplicate truth identity")
        ids.add(normalized_id)
        order.update((normalized_id + "\n").encode("ascii"))

        fmt = fields[8].split(":") if fields[8] != "." else []
        sample = fields[9].split(":") if fmt else []
        require(fmt or fields[9] == ".", "malformed HG002 sample field")
        require(len(fmt) == len(set(fmt)) and (not fmt or all(fmt)), "malformed FORMAT field")
        require(len(sample) <= len(fmt), "malformed HG002 sample field")
        gt_index = fmt.index("GT") if "GT" in fmt else None
        gt = sample[gt_index] if gt_index is not None and gt_index < len(sample) else None
        try:
            classification = classify_truth_record("0" * 64, ordinal, chrom, pos, ref, alt, gt)
        except Exception:
            raise CensusError("truth eligibility classification failed") from None
        unit = classification.unit
        if unit is None:
            reason = classification.exclusion_reason or "unknown"
            eligibility_reasons[reason] = eligibility_reasons.get(reason, 0) + 1
        else:
            canonical_kind_counts[unit.kind] += 1

        info = _info_values(fields[7])
        type_entries, len_entries = info.get("SVTYPE", []), info.get("SVLEN", [])
        type_view, type_value, type_duplicate, type_multi = _field_view(type_entries)
        len_view, len_text, len_duplicate, len_multi = _field_view(len_entries)
        row_flags = set()
        for key, entries, view, duplicate, multi, prefix in (
            ("SVTYPE", type_entries, type_view, type_duplicate, type_multi, "svtype"),
            ("SVLEN", len_entries, len_view, len_duplicate, len_multi, "svlen"),
        ):
            presence[f"{prefix}_present" if entries else f"{prefix}_absent"] += 1
            if not entries:
                row_flags.add(f"{prefix}_absent")
            if any(value is None for value in entries):
                row_flags.add(f"{prefix}_no_value")
            if any(value == "." or (value is not None and "." in value.split(","))
                   for value in entries):
                row_flags.add(f"{prefix}_dot")
            if duplicate:
                row_flags.add(f"{prefix}_duplicate_info")
            if multi:
                row_flags.add(f"{prefix}_multivalue")

        if type_view == "absent":
            types["ABSENT"] += 1
        elif type_view == "no_value":
            types["NO_VALUE"] += 1
        elif type_view == "dot":
            types["DOT"] += 1
        elif type_duplicate:
            types["DUPLICATE"] += 1
        elif type_multi:
            types["MULTIVALUE"] += 1
        elif type_value in {"INS", "DEL"}:
            types[type_value] += 1
        else:
            types["OTHER"] += 1
            row_flags.add("svtype_unrecognized")
        type_tokens = [token for value in type_entries if value is not None for token in value.split(",")]
        if any(token not in {"", ".", "INS", "DEL"} for token in type_tokens):
            row_flags.add("svtype_unrecognized")
        if unit is not None and any(token in {"INS", "DEL"} and token != unit.kind
                                    for token in type_tokens):
            row_flags.add("svtype_disagreement")

        len_tokens = [token for value in len_entries if value is not None for token in value.split(",")]
        noninteger_present = any(
            token != "." and (re.fullmatch(r"[+-]?[0-9]+", token) is None or len(token) > 4300)
            for token in len_tokens
        )
        if noninteger_present:
            row_flags.add("svlen_noninteger")
        integer_value = None
        if len_view == "absent":
            lengths["ABSENT"] += 1
        elif len_view == "no_value":
            lengths["NO_VALUE"] += 1
        elif len_view == "dot":
            lengths["DOT"] += 1
        elif len_duplicate:
            lengths["DUPLICATE"] += 1
        elif len_multi:
            lengths["MULTIVALUE"] += 1
        elif re.fullmatch(r"[+-]?[0-9]+", len_text or ""):
            try:
                integer_value = int(len_text, 10)
            except ValueError:
                pass
            if integer_value is None:
                lengths["NONINTEGER"] += 1
            else:
                lengths["INTEGER"] += 1
        else:
            lengths["NONINTEGER"] += 1
        if unit is not None and integer_value is not None:
            comparisons["comparable"] += 1
            expected = unit.length if unit.kind == "INS" else -unit.length
            if abs(integer_value) == unit.length:
                comparisons["absolute_magnitude_agree"] += 1
                if integer_value == expected:
                    comparisons["signed_agree"] += 1
            else:
                comparisons["magnitude_mismatch"] += 1
                row_flags.add("svlen_magnitude_mismatch")
            wrong_sign = (integer_value == 0 or (unit.kind == "INS" and integer_value < 0)
                          or (unit.kind == "DEL" and integer_value > 0))
            if wrong_sign:
                comparisons["sign_mismatch"] += 1
                row_flags.add("svlen_sign_mismatch")
                if abs(integer_value) == unit.length:
                    comparisons["sign_only_mismatch"] += 1

        # The census follows the old guard's eligibility -> SVTYPE -> SVLEN order.
        # This is a literal candidate only; pysam/native parsing is not replayed.
        if first is None:
            guard = _first_guard(unit, type_view, type_value, type_duplicate, type_multi,
                                 len_view if integer_value is not None else
                                 ("noninteger" if len_view == "value" and not len_duplicate and not len_multi else len_view),
                                 integer_value, len_duplicate, len_multi)
            if guard is not None:
                first = {
                    "record_ordinal": ordinal, "id": identity,
                    "coordinate": {"contig": chrom, "position": pos},
                    "canonical_kind": unit.kind if unit else None,
                    "ref_length": len(ref), "alt_length": len(alt),
                    "raw_length_delta": len(alt) - len(ref),
                    "canonical_length": unit.length if unit else None,
                    "canonical_signed_delta": ((unit.length if unit.kind == "INS" else -unit.length)
                                                if unit else None),
                    "first_guard_contradiction": guard,
                    "info_states": {
                        "SVTYPE": {"presence": "present" if type_entries else "absent",
                                   "entry_count": len(type_entries), "state": type_view,
                                   "cardinality": ("duplicate_info" if type_duplicate else
                                                   "multiple_values" if type_multi else "single"),
                                   "value_class": type_value if type_value in {"INS", "DEL"} else
                                   ("other" if type_view == "value" else type_view)},
                        "SVLEN": {"presence": "present" if len_entries else "absent",
                                  "entry_count": len(len_entries),
                                  "cardinality": ("duplicate_info" if len_duplicate else
                                                  "multiple_values" if len_multi else "single"),
                                  "state": ("noninteger" if len_view == "value" and integer_value is None
                                            else "integer" if integer_value is not None else len_view)},
                    },
                }
                if integer_value is not None:
                    first["info_states"]["SVLEN"].update(
                        integer_value=integer_value,
                        sign="negative" if integer_value < 0 else "positive" if integer_value > 0 else "zero",
                        absolute_magnitude=abs(integer_value),
                    )
        if unit is None:
            row_flags.add("eligibility_issue")
        for flag in row_flags:
            flags[flag] += 1
        if row_flags:
            with_flags += 1

    require(len(rows) <= MAX_ROWS, "truth row cap exceeded")
    return {
        "status": "complete", "purpose": PURPOSE, "sample": "HG002", "records": len(rows),
        "unique_ids": len(ids), "identity_order_sha256": order.hexdigest(),
        "headers": {"fileformat_raw_line": fileformat, "info_declarations": declarations,
                    "normative_compliance_claim": False},
        "counts": {
            "eligible": len(rows) - flags["eligibility_issue"],
            "ineligible": flags["eligibility_issue"], "eligibility_reasons": eligibility_reasons,
            "svtype_presence": presence["svtype_present"], "svtype_absent": presence["svtype_absent"],
            "svtype_observed_classes": types,
            "canonical_kind_counts": canonical_kind_counts,
            "svlen_presence": presence["svlen_present"], "svlen_absent": presence["svlen_absent"],
            "svlen_observed_states": lengths, "svlen_comparisons": comparisons,
            "overlapping_flags": flags, "rows_with_any_contract_flag": with_flags,
            "rows_without_any_contract_flag": len(rows) - with_flags,
            "all_rows_retained_in_census": True,
        },
        "first_strict_guard_contradiction_not_replayed_old_guard": first,
        "native_validation": "UNASSESSED", "reference_validation": "UNASSESSED",
        "denominator_validation": "NOT_VALIDATED", "scoring_performed": False,
    }


def _check_report_path(path):
    path = Path(path)
    try:
        path.lstat()
    except FileNotFoundError:
        pass
    else:
        raise CensusError("report path already exists")
    require(path.parent.is_dir(), "report directory does not exist")
    parent = path.parent.resolve()
    require(not any((item / ".git").exists() for item in (parent, *parent.parents)),
            "report must be outside Git")
    return path


def _run_diagnosis(truth_path, protocol_path, protocol_sha256, report_path, expected):
    require(re.fullmatch(r"[0-9a-f]{64}", protocol_sha256 or "") is not None,
            "invalid protocol SHA-256")
    protocol_bytes = _read_pinned(protocol_path, MAX_REPORT)
    require(sha256(protocol_bytes).hexdigest() == protocol_sha256, "protocol hash mismatch")
    try:
        protocol = json.loads(protocol_bytes.decode("utf-8"), object_pairs_hook=_pairs_no_duplicates)
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise CensusError("protocol is not valid UTF-8 JSON") from None
    require(isinstance(protocol, dict) and set(protocol) == PROTOCOL_KEYS,
            "protocol schema keys do not match frozen schema")
    require(protocol.get("diagnosis_approved") is True, "diagnosis approval flag is not true")
    require(protocol.get("purpose") == PURPOSE, "protocol purpose mismatch")
    require(protocol.get("expected_records") == expected["expected_records"]
            and type(protocol.get("expected_records")) is int, "protocol record count mismatch")
    require(protocol.get("expected_sample") == "HG002", "protocol sample mismatch")
    require(protocol.get("expected_input_bytes") == expected["expected_input_bytes"]
            and type(protocol.get("expected_input_bytes")) is int, "protocol input size mismatch")
    require(protocol.get("eligible_truth_sha256") == expected["eligible_truth_sha256"],
            "protocol source SHA-256 mismatch")
    require(protocol.get("source_read_reservation_bytes") == RESERVATION
            and type(protocol.get("source_read_reservation_bytes")) is int,
            "protocol source-read reservation mismatch")

    script_path = Path(__file__)
    helper_path = script_path.with_name("released_truth_units.py")
    script_bytes = _read_pinned(script_path, MAX_REPORT)
    helper_bytes = _read_pinned(helper_path, MAX_REPORT)
    metadata_bytes = len(protocol_bytes) + len(script_bytes) + len(helper_bytes)
    require(metadata_bytes <= MAX_REPORT, "protocol and code pins exceed metadata cap")
    require(sha256(script_bytes).hexdigest() == protocol.get("source_script_sha256"),
            "diagnostic script pin mismatch")
    require(sha256(helper_bytes).hexdigest() == protocol.get("truth_units_script_sha256"),
            "truth helper pin mismatch")
    report_path = _check_report_path(report_path)

    payload, snapshot = _read_source(truth_path)
    source_sha, source_size = sha256(payload).hexdigest(), len(payload)
    require(source_sha == expected["eligible_truth_sha256"], "truth source SHA-256 mismatch")
    require(source_size == expected["expected_input_bytes"], "truth source size mismatch")
    result = _parse_payload(payload, source_sha)
    require(result["records"] == expected["expected_records"], "truth record count mismatch")
    _posthash(truth_path, snapshot, source_sha, source_size)
    result.update(eligible_truth_sha256=source_sha, input_bytes=source_size,
                  source_snapshot_stable=True, source_read_reservation_bytes=RESERVATION,
                  protocol_sha256=protocol_sha256,
                  source_script_sha256=sha256(script_bytes).hexdigest(),
                  truth_units_script_sha256=sha256(helper_bytes).hexdigest())
    output = (json.dumps(result, sort_keys=True, indent=2) + "\n").encode("utf-8")
    require(len(output) <= MAX_REPORT and metadata_bytes + len(output) <= MAX_REPORT,
            "report and pinned metadata exceed one-MiB cap")
    try:
        with report_path.open("xb") as stream:
            stream.write(output)
    except OSError:
        raise CensusError("exclusive report write failed") from None
    return result


FROZEN_EXPECTED = {
    "expected_records": 11_490, "expected_input_bytes": 11_853_747,
    "eligible_truth_sha256": SOURCE_SHA256,
}


def diagnose(truth_path, protocol_path, protocol_sha256, report_path):
    return _run_diagnosis(truth_path, protocol_path, protocol_sha256, report_path, FROZEN_EXPECTED)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("truth-path", "protocol-path", "protocol-sha256", "report-path"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args()
    try:
        result = diagnose(args.truth_path, args.protocol_path, args.protocol_sha256, args.report_path)
    except Exception as error:
        safe_error = str(error) if isinstance(error, CensusError) else "diagnostic operation failed"
        print(json.dumps({"status": "incomplete", "error_type": type(error).__name__,
                          "error": safe_error}), file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
