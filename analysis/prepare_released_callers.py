"""Finite, standard-tool preparation of one approved released caller VCF.

Protocol v1 pins caller, source_basename/source_sha256/source_bytes, one exact
expected_sample_label, expected_source_records, max_source_bytes (<=4 GiB),
max_line_bytes, max_children, output_caps (keys in FILES plus sort_temp),
storage_cap_bytes, input_read_cap_bytes, opaque_io_reservation_bytes,
charged_prior_global_bytes, preparation_reservation_bytes, and runtime.
purpose must be PURPOSE; caller_preparation_approved must be true; an
independent_approval_ref is required. Outputs must be fresh and outside Git.
Named file-size passes are reservations, not physical I/O measurements.
Linux/Slurm CPU/RAM/wall limits and hard disk quotas remain external. Standard
tool output caps are checked at phase boundaries; spill peak is not measured.
No source/header repair, REF normalization, truth, BED, FASTA, or scoring.
Optional omit_info_rnames (strict boolean, default false) removes only the
INFO/RNAMES values from working copies, not its header declaration or source.
"""
from __future__ import annotations
import hashlib
import importlib.metadata
from itertools import zip_longest
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import quote

GIB, MIB = 1024**3, 1024**2
PURPOSE = "released_caller_preparation_v1"
CALLERS = ("cutesv", "debreak", "sawfish", "sniffles", "svim", "svpg")
RUNTIME = {"truvari": "5.4.0", "pysam": "0.24.0", "bcftools": "1.23.1",
           "htslib": "1.23.1", "python": "3.10.20"}
TAGS = ("CTRL_SRCORD", "CTRL_ALTIDX", "CTRL_ORIGID")
FILES = {"annotated": "annotated.vcf", "split": "split.vcf", "derived": "derived.vcf",
         "sorted": "sorted.vcf", "released": "released.vcf.gz",
         "released_index": "released.vcf.gz.tbi", "native": "native.vcf",
         "native_bgzf": "native.vcf.gz", "native_index": "native.vcf.gz.tbi"}
PASSES = {"annotated": 2, "split": 2, "derived": 2, "sorted": 7,
          "released": 5, "released_index": 4, "native": 5,
          "native_bgzf": 3, "native_index": 2}

class CallerPreparationError(ValueError):
    def __init__(self, message, report_path=None):
        super().__init__(message)
        self.report_path = report_path

class CallerPreparationGuardError(ValueError):
    """Internal bounded guard message; external ValueErrors may contain rows."""

def _need(ok, message):
    if not ok: raise CallerPreparationGuardError(message)

def _integer(value, minimum=1, maximum=64 * GIB):
    _need(type(value) is int and minimum <= value <= maximum, "invalid bounded integer")
    return value

def _protocol(path, expected):
    _need(isinstance(expected, str) and re.fullmatch(r"[0-9a-f]{64}", expected), "invalid protocol SHA-256")
    with Path(path).open("rb") as handle:
        raw = handle.read(MIB + 1)
    _need(len(raw) <= MIB and hashlib.sha256(raw).hexdigest() == expected, "protocol size or SHA-256 differs")
    p = json.loads(raw)
    _need(isinstance(p, dict) and p.get("purpose") == PURPOSE, "unsupported protocol")
    _need(p.get("caller_preparation_approved") is True, "explicit caller preparation approval required")
    ref = p.get("independent_approval_ref")
    _need(isinstance(ref, str) and 0 < len(ref.strip()) <= 512, "independent approval reference required")
    _need(p.get("runtime") == RUNTIME and p.get("caller") in CALLERS, "runtime metadata or caller differs")
    _need(type(p.get("omit_info_rnames", False)) is bool, "omit_info_rnames must be a boolean")
    _need(isinstance(p.get("source_sha256"), str) and re.fullmatch(r"[0-9a-f]{64}", p["source_sha256"]), "source SHA-256 required")
    for key in ("source_basename", "expected_sample_label"):
        _need(isinstance(p.get(key), str) and 0 < len(p[key]) <= 255
              and not any(c.isspace() or ord(c) < 32 for c in p[key]), f"invalid {key}")
    _need(Path(p["source_basename"]).name == p["source_basename"], "source basename must be a filename")
    source_cap = _integer(p.get("max_source_bytes"), maximum=4 * GIB)
    _integer(p.get("source_bytes"), maximum=source_cap)
    _integer(p.get("max_line_bytes"), maximum=min(128 * MIB, source_cap))
    _integer(p.get("expected_source_records"), maximum=100_000_000)
    _integer(p.get("max_children"), minimum=p["expected_source_records"], maximum=100_000_000)
    caps = p.get("output_caps")
    _need(isinstance(caps, dict) and set(caps) == set(FILES) | {"sort_temp"}, "incomplete output caps")
    for cap in caps.values(): _integer(cap, maximum=4 * GIB)
    _need(sum(caps.values()) + MIB <= _integer(p.get("storage_cap_bytes")), "storage reservation too small")
    opaque = _integer(p.get("opaque_io_reservation_bytes"))
    named = 3 * (source_cap + 1) + sum(caps[k] * n for k, n in PASSES.items())
    _need(named + opaque <= _integer(p.get("input_read_cap_bytes")), "input-read reservation too small")
    reserve = _integer(p.get("preparation_reservation_bytes"), minimum=p["input_read_cap_bytes"])
    prior = _integer(p.get("charged_prior_global_bytes"), minimum=4_124_617_258)
    _need(prior + reserve <= 64 * GIB, "prior charge plus reservation exceeds 64 GiB")
    return p

def _runtime():
    import pysam
    import pysam.bcftools as bcftools
    import truvari
    from pysam.version import __bcftools_version__, __htslib_version__
    versions = {"truvari": importlib.metadata.version("truvari"), "pysam": pysam.__version__,
                "bcftools": __bcftools_version__, "htslib": __htslib_version__,
                "python": sys.version.split()[0]}
    _need(versions == RUNTIME, f"requires pinned cluster stack; observed {versions}")
    return pysam, bcftools, truvari, versions

def _snapshot(path):
    s = Path(path).stat()
    return s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns

def _hash(path, cap, line_cap=None):
    """Bound byte hashing/framing only; all VCF parsing is done by pysam."""
    digest, size, tail = hashlib.sha256(), 0, 0
    before = _snapshot(path)
    _need(Path(path).is_file() and not Path(path).is_symlink() and before[2] <= cap, "input size or regular-file check failed")
    with Path(path).open("rb") as handle:
        while True:
            block = handle.read(min(MIB, cap + 1 - size))
            if not block: break
            if size == 0 and line_cap is not None:
                _need(not block.startswith((b"\x1f\x8b", b"BCF")), "source must be plaintext VCF")
            size += len(block)
            _need(size <= cap, "input byte cap exceeded")
            digest.update(block)
            if line_cap is not None:
                parts = block.split(b"\n")
                lengths = [tail + len(parts[0]), *(len(x) for x in parts[1:])]
                framed = [n + 1 for n in lengths[:-1]] + [lengths[-1]]
                _need(max(framed) <= line_cap, "source line cap exceeded")
                tail = lengths[0] if len(parts) == 1 else len(parts[-1])
    _need(_snapshot(path) == before and size == before[2], "input changed during hash pass")
    return digest.hexdigest(), size, before

def _fresh(path):
    path = Path(path)
    _need(not os.path.lexists(path), "output directory must be fresh")
    path = path.resolve()
    _need(path.parent.is_dir(), "output parent must exist")
    _need(not any((x / ".git").exists() for x in (path, *path.parents)), "output must be outside Git")
    path.mkdir(mode=0o700)
    return path

def child_identity(source_sha256, ordinal, alt_index):
    _need(isinstance(source_sha256, str) and re.fullmatch(r"[0-9a-f]{64}", source_sha256), "invalid source SHA-256")
    _integer(ordinal, maximum=100_000_000); _integer(alt_index, maximum=100_000_000)
    return hashlib.sha256(f"{source_sha256}|{ordinal}|{alt_index}".encode("ascii")).hexdigest()

class _Fingerprint:
    """O(1) memory, multiplicity-sensitive cryptographic multiset fingerprint."""
    def __init__(self): self.count = self.total = self.xor = 0
    def add(self, row):
        n = int.from_bytes(hashlib.sha256(row.encode()).digest(), "big")
        self.count += 1; self.total = (self.total + n) % (1 << 256); self.xor ^= n
    def result(self):
        return {"records": self.count, "sha256_sum": f"{self.total:064x}", "sha256_xor": f"{self.xor:064x}"}

def _row(record): return str(record).rstrip("\r\n")
def _one(value): return value[0] if isinstance(value, tuple) else value
def _items(value): return value if isinstance(value, tuple) else (value,)

def _paired_records(raw, native):
    sentinel = object()
    for record, trv in zip_longest(raw, native, fillvalue=sentinel):
        _need(record is not sentinel and trv is not sentinel, "paired reader lengths differ")
        _need(_row(record) == _row(trv), "paired reader whole rows differ")
        yield record, trv

def _fingerprint(path, pysam, indexed=False):
    result = _Fingerprint()
    if indexed:
        with pysam.TabixFile(str(path)) as reader:
            for contig in reader.contigs:
                for row in reader.fetch(contig): result.add(row)
    else:
        with pysam.VariantFile(str(path)) as reader:
            for record in reader: result.add(_row(record))
    return result.result()

def _check_file(path, cap):
    _need(path.is_file() and path.stat().st_size <= cap, f"file missing or storage cap exceeded: {path.name}")

def _projected(value, number, index, ploidy=2):
    if _items(value) == (None,): return (None,)
    if number == "A": return (_items(value)[index - 1],)
    if number == "R": return (_items(value)[0], _items(value)[index])
    if number == "G":
        _need(ploidy in (1, 2), "Number=G requires a declared haploid/diploid GT")
        offsets = (0, index) if ploidy == 1 else (0, index * (index + 1) // 2, index * (index + 3) // 2)
        return tuple(_items(value)[i] for i in offsets)
    return _items(value)

def _semantic_child(rec, index=None, omitted_info=()):
    """Expectation only; END tokens use parser serialization, not raw source text."""
    sample, info, values = rec.samples[0], {}, {}
    explicit_end = [t for t in _row(rec).split("\t", 8)[7].split(";") if t.partition("=")[0] == "END"]
    _need(len(explicit_end) <= 1 and all(re.fullmatch(r"END=(?:[+-]?[0-9]+|\.)", t) for t in explicit_end), "duplicate or malformed serialized INFO/END")
    for key in rec.info:
        if key in omitted_info: continue
        info[key] = _items(rec.info[key]) if index is None else _projected(rec.info[key], rec.header.info[key].number, index, len(sample.get("GT", ())))
    for key in sample:
        value = sample[key]
        if index is None: values[key] = _items(value)
        elif key == "GT":
            values[key] = tuple(None if x is None else 0 if x == 0 else 1 if x == index else None for x in value)
        else: values[key] = _projected(value, rec.header.formats[key].number, index, len(sample.get("GT", ())))
    fields = (rec.contig, rec.pos, rec.stop, explicit_end, rec.id, rec.ref, rec.alts[0 if index is None else index - 1],
              rec.qual, list(rec.filter), info, list(rec.format), list(rec.header.samples), values, sample.phased)
    return json.dumps(fields, sort_keys=True, separators=(",", ":"))

def _annotate(source, dest, p, pysam, counts):
    expected, projected = _Fingerprint(), _Fingerprint()
    omitted_info = ("RNAMES",) if p.get("omit_info_rnames", False) else ()
    counts["info_rnames_rows_removed"] = 0
    with pysam.VariantFile(str(source)) as reader:
        _need(list(reader.header.samples) == [p["expected_sample_label"]], "source sample label/count differs")
        header = reader.header.copy()
        original_info = set(header.info)
        _need(not any(k in header.info for k in TAGS), "reserved identity INFO tag already exists")
        for key, number, kind in zip(TAGS, (1, "A", 1), ("Integer", "Integer", "String")):
            header.info.add(key, number, kind, "Caller source identity (original ID is percent encoded)")
        with pysam.VariantFile(str(dest), "w", header=header) as out:
            for ordinal, rec in enumerate(reader, 1):
                counts["source_records"] = ordinal
                _need(ordinal <= p["expected_source_records"] and rec.alts, "source record count/ALT schema differs")
                _need(rec.contig in header.contigs and rec.pos >= 0, "undeclared contig or unsupported POS")
                gt = rec.samples[0].get("GT")
                _need(gt is None or all(x is None or 0 <= x <= len(rec.alts) for x in gt), "GT allele out of range")
                _need(set(reader.header.info) == original_info and set(reader.header.formats) == set(header.formats)
                      and set(reader.header.filters) == set(header.filters), "undeclared INFO/FORMAT/FILTER schema")
                counts["children"] += len(rec.alts)
                _need(counts["children"] <= p["max_children"], "derived child count cap exceeded")
                rec.translate(out.header)
                original = quote(rec.id or ".", safe="")
                rec.info[TAGS[0]] = ordinal; rec.info[TAGS[1]] = tuple(range(1, len(rec.alts) + 1))
                rec.info[TAGS[2]] = "%2E" if original == "." else original
                counts["pos_zero"] += rec.pos == 0
                length = header.contigs[rec.contig].length
                _need(length is None or length > 0 and rec.pos <= length + 1, "POS exceeds declared contig length plus one")
                counts["pos_length_plus_one"] += length is not None and rec.pos == length + 1
                for index in range(1, len(rec.alts) + 1):
                    expected.add(child_identity(p["source_sha256"], ordinal, index))
                    # Freeze every other field BEFORE the optional deletion.
                    # Downstream checks have no exclusion: any restored RNAMES
                    # or changed scientific field makes the projection differ.
                    projected.add(_semantic_child(rec, index, omitted_info))
                if omitted_info and "RNAMES" in rec.info:
                    del rec.info["RNAMES"]
                    counts["info_rnames_rows_removed"] += 1
                counts["source_alt_identity_fingerprint"] = expected.result()
                out.write(rec)
    _need(counts["source_records"] == p["expected_source_records"], "source record census differs")
    return expected.result(), projected.result()

def _derive(split, dest, p, pysam, counts):
    identities, projected, rows = _Fingerprint(), _Fingerprint(), _Fingerprint()
    with pysam.VariantFile(str(split)) as children, pysam.VariantFile(str(dest), "w", header=children.header) as out:
        _need(list(children.header.samples) == [p["expected_sample_label"]], "norm changed sample column")
        for child in children:
            _need(child.alts and len(child.alts) == 1 and rows.count < p["max_children"], "norm ALT/count schema differs")
            ordinal, index = child.info[TAGS[0]], _one(child.info[TAGS[1]])
            _integer(ordinal, maximum=p["expected_source_records"]); _integer(index, maximum=p["max_children"])
            projected.add(_semantic_child(child))
            child.id = child_identity(p["source_sha256"], ordinal, index)
            identities.add(child.id); rows.add(_row(child)); out.write(child)
            counts["derived_identity_fingerprint"] = identities.result()
    return identities.result(), projected.result(), rows.result()

def _native(source, dest, pysam, truvari, sample, report):
    counts = dict(records=0, kept=0, filtered=0, not_present=0, both=0, dot_kept=0)
    report["native_counts"] = counts
    retained = _Fingerprint()
    with pysam.VariantFile(str(source)) as raw, truvari.VariantFile(str(source)) as native, \
            pysam.VariantFile(str(dest), "w", header=raw.header) as out:
        _need(list(raw.header.samples) == [sample], "native input sample column differs")
        for rec, trv in _paired_records(raw, native):
            filt, present = trv.is_filtered(), trv.is_present(0, allow_missing=True)
            counts["records"] += 1; counts["filtered"] += int(filt)
            counts["not_present"] += int(not present); counts["both"] += int(filt and not present)
            if not filt and present:
                out.write(rec); retained.add(_row(rec)); counts["kept"] += 1
                counts["dot_kept"] += int(not rec.filter.keys())
    _need(counts["kept"] == counts["records"] - counts["filtered"] - counts["not_present"] + counts["both"], "native counts do not partition input")
    return counts, retained.result()

def _save_report(path, report):
    raw = (json.dumps(report, indent=2, sort_keys=True) + "\n").encode()
    _need(len(raw) <= MIB, "report exceeds metadata cap")
    with path.open("xb") as handle: handle.write(raw)

def prepare_released_caller(source_path, outdir, protocol_path, protocol_sha256):
    """Prepare exactly one protocol-named source, without retry or partial reuse."""
    p = _protocol(protocol_path, protocol_sha256)
    source = Path(source_path)
    _need(source.name == p["source_basename"], "actual source filename differs from protocol")
    output = _fresh(outdir)
    paths = {key: output / name for key, name in FILES.items()}
    counts = dict(source_records=0, children=0, pos_zero=0, pos_length_plus_one=0)
    report = dict(status="incomplete", caller=p["caller"], protocol_sha256=protocol_sha256,
                  source_sha256=p["source_sha256"], counts=counts, output_caps=p["output_caps"],
                  reserved_charge_bytes=p["preparation_reservation_bytes"],
                  prior_global_charge_bytes=p["charged_prior_global_bytes"],
                  named_maximum_pass_reservations={"source": 3 * (p["max_source_bytes"] + 1), **{k: p["output_caps"][k] * n for k, n in PASSES.items()}},
                  opaque_io_reservation_bytes=p["opaque_io_reservation_bytes"],
                  info_rnames_policy="omit_values_only" if p.get("omit_info_rnames", False) else "preserve",
                  norm_end_validation="Explicit INFO/END presence/value checked from standard-parser serialization independently of stop; raw lexical normalization by the parser is not checked.",
                  accounting_limitation="Named file-size passes are reservations; HTSlib read-ahead, BGZF decoded traffic, sort spill/peak and OS caching are not measured. Hard resource/disk enforcement is external.")
    phase = "preflight"
    try:
        pysam, bcftools, truvari, versions = _runtime(); report["runtime"] = versions
        sha, size, snapshot = _hash(source, p["max_source_bytes"], p["max_line_bytes"])
        report.update(source_observed_sha256=sha, source_hash_bytes=size)
        _need(sha == p["source_sha256"] and size == p["source_bytes"], "actual source SHA-256/size differs")
        report["source_verified_sha256"] = sha
        phase = "annotate"
        identities, expected_projection = _annotate(source, paths["annotated"], p, pysam, counts)
        _need(_snapshot(source) == snapshot, "source changed during standard parser pass")
        _check_file(paths["annotated"], p["output_caps"]["annotated"])
        phase = "norm"
        bcftools.norm("-m", "-any", "--multi-overlaps", ".", "-N", "--no-version", "-Ov",
                      "-o", str(paths["split"]), str(paths["annotated"]), catch_stdout=False)
        _check_file(paths["split"], p["output_caps"]["split"])
        observed, actual_projection, rows = _derive(paths["split"], paths["derived"], p, pysam, counts)
        _need(observed == identities and actual_projection == expected_projection, "norm source ALT identity/projected whole-field multiset differs")
        report["identity_fingerprint"] = observed
        _check_file(paths["derived"], p["output_caps"]["derived"])
        phase = "sort"
        temp = output / "sort-tmp"; temp.mkdir()
        bcftools.sort("-Ov", "-o", str(paths["sorted"]), "-T", str(temp / "sort"),
                      str(paths["derived"]), catch_stdout=False)
        _check_file(paths["sorted"], p["output_caps"]["sorted"])
        _need(_fingerprint(paths["sorted"], pysam) == rows, "sort changed whole-row multiset")
        phase = "released_bgzip_tabix"
        pysam.tabix_compress(str(paths["sorted"]), str(paths["released"]), force=False)
        _check_file(paths["released"], p["output_caps"]["released"])
        pysam.tabix_index(str(paths["released"]), preset="vcf", force=False)
        _check_file(paths["released_index"], p["output_caps"]["released_index"])
        _need(_fingerprint(paths["released"], pysam, indexed=True) == rows, "tabix changed indexed row multiset (including POS=0/N+1)")
        phase = "native_view"
        native_counts, retained = _native(paths["released"], paths["native"], pysam, truvari, p["expected_sample_label"], report)
        report["native_counts"] = native_counts
        _check_file(paths["native"], p["output_caps"]["native"])
        _need(native_counts["records"] == counts["children"] and _fingerprint(paths["native"], pysam) == retained, "native view changed complete retained rows")
        phase = "native_bgzip_tabix"
        pysam.tabix_compress(str(paths["native"]), str(paths["native_bgzf"]), force=False)
        _check_file(paths["native_bgzf"], p["output_caps"]["native_bgzf"])
        pysam.tabix_index(str(paths["native_bgzf"]), preset="vcf", force=False)
        _check_file(paths["native_index"], p["output_caps"]["native_index"])
        _need(_fingerprint(paths["native_bgzf"], pysam, indexed=True) == retained, "native index changed retained whole rows")
        phase = "final_hashes"
        outputs = {k: {"path": str(path), "sha256": _hash(path, p["output_caps"][k])[0], "bytes": path.stat().st_size} for k, path in paths.items()}
        _need(_hash(source, p["max_source_bytes"], p["max_line_bytes"]) == (sha, size, snapshot), "source changed after preparation")
        named = {"source_hash_parse_rehash": 3 * size, **{k: outputs[k]["bytes"] * n for k, n in PASSES.items()}}
        _need(sum(named.values()) + p["opaque_io_reservation_bytes"] <= p["input_read_cap_bytes"], "named read reservation cap exceeded")
        temp_size = sum(x.stat().st_size for x in temp.rglob("*") if x.is_file())
        _need(temp_size <= p["output_caps"]["sort_temp"], "remaining sort temporary storage cap exceeded")
        _need(sum(x["bytes"] for x in outputs.values()) + temp_size + MIB <= p["storage_cap_bytes"], "storage cap exceeded")
        report.update(status="complete", outputs=outputs, named_phase_byte_reservations=named,
                      opaque_io_reservation_bytes=p["opaque_io_reservation_bytes"],
                      derived_rows=rows, retained_rows=retained,
                      fingerprint_method="count plus modular sum and XOR of per-whole-row SHA-256; cryptographic collision risk remains")
        report_file = output / "caller_preparation_report.json"
        _save_report(report_file, report)
    except Exception as exc:
        partials = []
        for x in output.rglob("*"):
            if x.is_file():
                if len(partials) == 512: break
                partials.append({"path": str(x.relative_to(output)), "bytes": x.stat().st_size, "sha256": None, "hash_status": "not_reread_after_failure"})
        # External parser/tool errors can embed a complete variant or read names.
        # Keep their category here; raw diagnostics stay in cluster stderr.
        failure = str(exc)[:1000] if type(exc) is CallerPreparationGuardError else "External parser/tool error; inspect retained cluster diagnostics before archival."
        report.update(status="incomplete", failed_phase=phase, failure_type=type(exc).__name__, failure=failure,
                      partial_files_preserved=partials, partial_inventory_may_be_truncated=len(partials) == 512)
        report_file = output / "caller_preparation_failure.json"
        _save_report(report_file, report)
        raise CallerPreparationError(str(exc), report_file) from exc
    return report


def main():
    """Small CLI for the fixed, externally limited one-source invocation."""
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-path", required=True)
    parser.add_argument("--outdir", required=True)
    parser.add_argument("--protocol-path", required=True)
    parser.add_argument("--protocol-sha256", required=True)
    args = parser.parse_args()
    try:
        report = prepare_released_caller(args.source_path, args.outdir,
                                         args.protocol_path, args.protocol_sha256)
    except (ValueError, OSError) as exc:
        # No source row or parser error context in the launcher output.
        print(json.dumps({"status": "incomplete", "error_type": type(exc).__name__,
                          "report_path": str(getattr(exc, "report_path", ""))}))
        return 2
    print(json.dumps({"status": report["status"], "caller": report["caller"],
                      "source_records": report["counts"]["source_records"],
                      "children": report["counts"]["children"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
