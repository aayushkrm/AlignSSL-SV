#!/usr/bin/env python3
"""Observe the fixed synthetic native-caller fixture without running a caller."""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import contextmanager
from hashlib import sha256
import gzip
import io
import json
import os
from pathlib import Path
import re
import stat
import sys
import tempfile
import zlib


MAX_INPUT_PER_FILE = 8 * 1024**2
MAX_INPUT_TOTAL = 16 * 1024**2
MAX_REPORT = 64 * 1024
SYNTH_CONTIG = "chrSynthetic"
SYNTH_SAMPLE = "SYNTH"
REFERENCE_LENGTH = 4000
INSERTION_OFFSET = 1500
INSERTION_SEQUENCE = "A" * 60
EXPECTED_ALT_LENGTH = 4060
REPEAT_START = 1000
REPEAT_END = 3000
REFERENCE_SHA256_BASIS = "uppercase sequence ASCII bytes; FASTA header and wrapping excluded"
SYNTH_REFERENCE_SHA256 = "1e9e223b565b9f0847946d777a5c7fd4f2ba09f076174e4fab96f473156fe9ef"
INPUT_ROLES = (
    "reference_fasta",
    "truth_json",
    "assembly_bed",
    "candidate_vcf_bcf",
    "final_vcf_bcf",
    "contig_bam",
)
_DNA_RE = re.compile(r"[ACGTN]+\Z")


class FixtureError(ValueError):
    """Raised when an input is outside the fixed synthetic contract."""


def _snapshot(info):
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def _open_regular(path):
    fd = None
    try:
        fd = os.open(os.fspath(path), os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
                     | getattr(os, "O_CLOEXEC", 0))
        opened = os.fstat(fd)
        named = os.lstat(path)
        if (not stat.S_ISREG(opened.st_mode) or not stat.S_ISREG(named.st_mode)
                or _snapshot(opened) != _snapshot(named)):
            raise FixtureError("each input must be a stable regular nonlink file")
        return fd, _snapshot(opened)
    except FixtureError:
        if fd is not None:
            os.close(fd)
        raise
    except OSError:
        if fd is not None:
            os.close(fd)
        raise FixtureError("an input could not be opened as a regular nonlink file") from None


def _read_inputs(paths):
    opened = {}
    try:
        total_size = 0
        for role in INPUT_ROLES:
            fd, before = _open_regular(paths[role])
            opened[role] = (fd, before)
            if before[2] > MAX_INPUT_PER_FILE:
                raise FixtureError("an input exceeds the 8-MiB per-file cap")
            total_size += before[2]
            if total_size > MAX_INPUT_TOTAL:
                raise FixtureError("the combined inputs exceed the 16-MiB cap")

        payloads, snapshots, digests = {}, {}, {}
        for role in INPUT_ROLES:
            fd, before = opened[role]
            remaining = before[2]
            chunks = []
            while remaining:
                block = os.read(fd, min(1024**2, remaining))
                if not block:
                    raise FixtureError("an input changed or ended during its bounded read")
                chunks.append(block)
                remaining -= len(block)
            data = b"".join(chunks)
            try:
                after_fd = _snapshot(os.fstat(fd))
                after_name = _snapshot(os.lstat(paths[role]))
            except OSError:
                raise FixtureError("an input changed during its bounded read") from None
            if len(data) != before[2] or before != after_fd or before != after_name:
                raise FixtureError("an input changed during its bounded read")
            payloads[role] = data
            snapshots[role] = before
            digests[role] = sha256(data).hexdigest()
        return payloads, snapshots, digests, total_size
    finally:
        for fd, _ in opened.values():
            os.close(fd)


def _posthash_inputs(paths, snapshots, digests):
    for role in INPUT_ROLES:
        fd, before = _open_regular(paths[role])
        try:
            if before != snapshots[role] or before[2] > MAX_INPUT_PER_FILE:
                raise FixtureError("an input snapshot changed before its posthash")
            check = sha256()
            remaining = before[2]
            while remaining:
                block = os.read(fd, min(1024**2, remaining))
                if not block:
                    raise FixtureError("an input changed during its posthash")
                check.update(block)
                remaining -= len(block)
            try:
                after_fd = _snapshot(os.fstat(fd))
                after_name = _snapshot(os.lstat(paths[role]))
            except OSError:
                raise FixtureError("an input changed during its posthash") from None
            if (before != after_fd or before != after_name
                    or check.hexdigest() != digests[role]):
                raise FixtureError("input bytes or snapshots changed during observation")
        finally:
            os.close(fd)


def _parse_fasta(payload):
    try:
        text = payload.decode("ascii")
    except UnicodeDecodeError:
        raise FixtureError("reference FASTA must contain ASCII sequence text") from None
    header = None
    sequence_parts = []
    for line in text.splitlines():
        if not line:
            continue
        if line.startswith(">"):
            if header is not None or line != f">{SYNTH_CONTIG}":
                raise FixtureError("reference FASTA must contain only chrSynthetic")
            header = line[1:]
        else:
            if header is None or _DNA_RE.fullmatch(line) is None:
                raise FixtureError("reference FASTA contains an invalid sequence line")
            sequence_parts.append(line.upper())
    sequence = "".join(sequence_parts)
    if (header != SYNTH_CONTIG or len(sequence) != REFERENCE_LENGTH
            or sequence[REPEAT_START:REPEAT_END] != "A" * (REPEAT_END - REPEAT_START)):
        raise FixtureError("reference FASTA does not match the fixed 4,000-base synthetic reference")
    sequence_sha256 = sha256(sequence.encode("ascii")).hexdigest()
    if sequence_sha256 != SYNTH_REFERENCE_SHA256:
        raise FixtureError("reference sequence hash does not match the frozen synthetic reference")
    return sequence, sequence_sha256


def _unique_json_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise FixtureError("truth JSON contains a duplicate key")
        result[key] = value
    return result


def _reject_json_constant(_value):
    raise FixtureError("truth JSON contains a nonstandard numeric value")


def _parse_truth(payload, reference, reference_sha256):
    try:
        truth = json.loads(payload.decode("utf-8"), object_pairs_hook=_unique_json_keys,
                           parse_constant=_reject_json_constant)
    except FixtureError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise FixtureError("truth JSON is not valid UTF-8 JSON") from None
    if (not isinstance(truth, dict)
            or set(truth) != {"version", "contig", "reference_sha256",
                              "reference_sha256_basis", "reference_length",
                              "insertion_offset", "inserted_sequence",
                              "expected_alt_length", "sample"}
            or type(truth.get("version")) is not int or truth["version"] != 1
            or truth.get("contig") != SYNTH_CONTIG
            or type(truth.get("reference_length")) is not int
            or truth["reference_length"] != REFERENCE_LENGTH
            or truth.get("reference_sha256") != reference_sha256
            or truth.get("reference_sha256") != SYNTH_REFERENCE_SHA256
            or truth.get("reference_sha256_basis") != REFERENCE_SHA256_BASIS
            or truth.get("sample") != SYNTH_SAMPLE
            or type(truth.get("insertion_offset")) is not int
            or truth["insertion_offset"] != INSERTION_OFFSET
            or truth.get("inserted_sequence") != INSERTION_SEQUENCE
            or type(truth.get("expected_alt_length")) is not int
            or truth["expected_alt_length"] != EXPECTED_ALT_LENGTH):
        raise FixtureError("truth JSON does not match the fixed version-1 synthetic scope")
    alternate = (reference[:INSERTION_OFFSET] + INSERTION_SEQUENCE
                 + reference[INSERTION_OFFSET:])
    if len(alternate) != EXPECTED_ALT_LENGTH:
        raise FixtureError("internal synthetic alternate length is inconsistent")
    return alternate


def _parse_bed(payload):
    try:
        text = payload.decode("ascii")
    except UnicodeDecodeError:
        raise FixtureError("assembly BED must contain ASCII text") from None
    rows = synthetic_rows = other_contig_rows = 0
    insertion_covered = False
    non_data_lines = 0
    for line in text.splitlines():
        if not line or line.startswith("#") or line.startswith("track ") or line.startswith("browser "):
            non_data_lines += 1
            continue
        fields = line.split("\t")
        if (len(fields) < 3 or not fields[0]
                or not fields[1].isdigit() or not fields[2].isdigit()):
            raise FixtureError("assembly BED contains a malformed row")
        start, end = int(fields[1]), int(fields[2])
        if start >= end:
            raise FixtureError("assembly BED contains an empty or reversed interval")
        rows += 1
        if fields[0] == SYNTH_CONTIG:
            if end > REFERENCE_LENGTH:
                raise FixtureError("assembly BED interval exceeds chrSynthetic")
            synthetic_rows += 1
            insertion_covered |= start <= INSERTION_OFFSET < end
        else:
            other_contig_rows += 1
    return {
        "data_rows": rows,
        "chrSynthetic_rows": synthetic_rows,
        "other_contig_rows": other_contig_rows,
        "non_data_lines": non_data_lines,
        "insertion_offset_covered": insertion_covered,
    }


def _format_kind(payload):
    prefix = payload[:16]
    if prefix.startswith(b"BAM\x01"):
        return "bam"
    if prefix.startswith(b"BCF\x02"):
        return "bcf"
    if prefix.startswith(b"\x1f\x8b"):
        try:
            with gzip.GzipFile(fileobj=io.BytesIO(payload), mode="rb") as stream:
                inner = stream.read(16)
        except (OSError, EOFError, zlib.error):
            raise FixtureError("compressed VCF/BCF/BAM has an invalid header") from None
        if inner.startswith(b"BAM\x01"):
            return "bam"
        if inner.startswith(b"BCF\x02"):
            return "bcf"
        if inner.startswith(b"##fileformat="):
            return "vcf.gz"
    if prefix.startswith(b"##fileformat="):
        return "vcf"
    raise FixtureError("input is not a supported VCF, BCF, or BAM file")


@contextmanager
def _materialized_hts(payload, kind):
    suffix = {"bam": ".bam", "bcf": ".bcf", "vcf": ".vcf", "vcf.gz": ".vcf.gz"}[kind]
    with tempfile.TemporaryDirectory(prefix="observe-native-fixture-") as directory:
        path = Path(directory) / ("input" + suffix)
        try:
            with path.open("xb") as stream:
                stream.write(payload)
        except OSError:
            raise FixtureError("could not create a temporary frozen parser input") from None
        yield path


def _valid_ref_span(record, reference):
    ref = record.ref
    start = record.pos - 1
    if (not isinstance(ref, str) or _DNA_RE.fullmatch(ref.upper()) is None
            or start < 0 or start + len(ref) > len(reference)):
        return False
    return reference[start:start + len(ref)] == ref.upper()


def _is_symbolic(allele):
    return not isinstance(allele, str) or _DNA_RE.fullmatch(allele.upper()) is None


def _empty_call_counts():
    return {
        "total_records": 0,
        "exact_allele_records": 0,
        "non_equivalent_literal_records": 0,
        "invalid_ref_records": 0,
        "symbolic_records": 0,
        "multiallelic_unresolved_records": 0,
        "non_equivalent_literal_records_in_A_repeat": 0,
        "off_contig_records": 0,
        "other_unresolved_records": 0,
    }


def _summarize_callset(payload, reference, alternate, *, role, final=False):
    try:
        import pysam
    except ImportError:
        raise FixtureError("pysam is required to parse synthetic VCF/BCF/BAM inputs") from None
    kind = _format_kind(payload)
    if kind == "bam":
        raise FixtureError(f"{role} input has the wrong file type")
    counts = _empty_call_counts()
    filter_counts = Counter()
    heterozygous = phased_heterozygous = unphased_heterozygous = 0
    pass_exact = pass_heterozygous = 0
    try:
        with _materialized_hts(payload, kind) as path:
            mode = "rb" if kind == "bcf" else "r"
            with pysam.VariantFile(str(path), mode=mode, threads=1) as variants:
                samples = tuple(variants.header.samples)
                for record in variants:
                    counts["total_records"] += 1
                    filter_names = tuple(record.filter.keys())
                    if not filter_names:
                        filter_counts["."] += 1
                    else:
                        for name in filter_names:
                            filter_counts[name] += 1

                    alts = tuple(record.alts or ())
                    if any(_is_symbolic(alt) for alt in alts):
                        counts["symbolic_records"] += 1
                    if len(alts) > 1:
                        counts["multiallelic_unresolved_records"] += 1

                    if record.contig != SYNTH_CONTIG:
                        counts["off_contig_records"] += 1
                        continue
                    if not _valid_ref_span(record, reference):
                        counts["invalid_ref_records"] += 1
                        continue
                    if len(alts) > 1:
                        continue
                    if not alts:
                        counts["other_unresolved_records"] += 1
                        continue
                    if _is_symbolic(alts[0]):
                        counts["other_unresolved_records"] += 1
                        continue

                    start = record.pos - 1
                    # The replacement uses the full REF span, so equivalent left shifts
                    # pass only when the complete alternate haplotype is byte-for-byte equal.
                    ref_end = start + len(record.ref)
                    literal_haplotype = (reference[:start] + alts[0].upper()
                                         + reference[ref_end:])
                    if literal_haplotype != alternate:
                        counts["non_equivalent_literal_records"] += 1
                        if REPEAT_START - 1 <= start and ref_end <= REPEAT_END:
                            counts["non_equivalent_literal_records_in_A_repeat"] += 1
                        continue
                    counts["exact_allele_records"] += 1
                    if final:
                        is_pass = filter_names == ("PASS",)
                        pass_exact += int(is_pass)
                        if SYNTH_SAMPLE in samples:
                            sample = record.samples[SYNTH_SAMPLE]
                            genotype = sample.get("GT")
                            if genotype in ((0, 1), (1, 0)):
                                heterozygous += 1
                                pass_heterozygous += int(is_pass)
                                if sample.phased:
                                    phased_heterozygous += 1
                                else:
                                    unphased_heterozygous += 1

                if final and samples != (SYNTH_SAMPLE,):
                    raise FixtureError("final VCF/BCF must contain exactly the SYNTH sample")
                if not final and samples not in ((), (SYNTH_SAMPLE,)):
                    raise FixtureError("candidate VCF/BCF must be sites-only or contain only SYNTH")
    except FixtureError:
        raise
    except Exception:
        raise FixtureError(f"{role} VCF/BCF could not be parsed completely") from None

    counts["unresolved_records"] = (
        counts["total_records"] - counts["exact_allele_records"]
        - counts["non_equivalent_literal_records"]
    )
    if not final:
        counts["sample_columns"] = len(samples)
    else:
        counts.update({
            "pass_exact_allele_records": pass_exact,
            "heterozygous_gt_0_1_or_1_0_exact_records": heterozygous,
            "pass_heterozygous_exact_allele_records": pass_heterozygous,
            "phased_heterozygous_exact_records": phased_heterozygous,
            "unphased_heterozygous_exact_records": unphased_heterozygous,
            "filter_counts": dict(sorted(filter_counts.items())),
        })
    unresolved_reasons = {}
    for count_key in (
        "invalid_ref_records", "symbolic_records", "multiallelic_unresolved_records",
        "off_contig_records", "other_unresolved_records",
    ):
        if counts[count_key]:
            unresolved_reasons[count_key] = counts[count_key]
    # REF padding may extend beyond the repeat while the edit remains inside it.
    # Do not infer full-allele absence from a boundary-dependent edit heuristic.
    literal_count = counts["non_equivalent_literal_records"]
    if literal_count >= 2:
        unresolved_reasons["multiple_non_equivalent_literal_records_on_chrSynthetic"] = literal_count
    if counts["exact_allele_records"]:
        output_state = "PRESENT"
    elif unresolved_reasons:
        output_state = "UNRESOLVED"
    else:
        output_state = "ABSENT_FROM_OUTPUT"
    counts.update({
        "exact_single_record_presence": counts["exact_allele_records"] > 0,
        "single_record_output_state": output_state,
        "single_record_representation_unit": "one literal REF-to-ALT record applied to the full reference",
        "full_haplotype_absence_claim": False,
        "negative_inference_unresolved_reasons": unresolved_reasons,
    })
    if final:
        if pass_heterozygous:
            recovery_state = "RECOVERED"
        elif output_state == "PRESENT":
            recovery_state = "EXACT_ALLELE_PRESENT_ENDPOINT_NOT_MET"
        else:
            recovery_state = output_state
        counts["exact_pass_heterozygous_recovery_state"] = recovery_state
    return counts


def _summarize_bam(payload):
    try:
        import pysam
    except ImportError:
        raise FixtureError("pysam is required to parse the synthetic contig BAM") from None
    if _format_kind(payload) != "bam":
        raise FixtureError("contig BAM input is not a BAM file")
    total = mapped = unmapped = 0
    query_lengths = Counter()
    contig_names = set()
    try:
        with _materialized_hts(payload, "bam") as path:
            with pysam.AlignmentFile(str(path), mode="rb") as bam:
                references = tuple(bam.references)
                lengths = tuple(bam.lengths)
                if len(references) != len(lengths):
                    raise FixtureError("contig BAM header has inconsistent reference metadata")
                counts_by_reference = {name: 0 for name in references}
                for record in bam.fetch(until_eof=True):
                    total += 1
                    query_lengths[str(record.query_length)] += 1
                    if record.query_name is not None:
                        contig_names.add(record.query_name)
                    if record.is_unmapped:
                        unmapped += 1
                    else:
                        mapped += 1
                        reference_id = record.reference_id
                        if reference_id < 0 or reference_id >= len(references):
                            raise FixtureError("contig BAM record has an invalid reference id")
                        counts_by_reference[references[reference_id]] += 1
    except FixtureError:
        raise
    except Exception:
        raise FixtureError("contig BAM could not be parsed completely") from None
    return {
        "alignment_records": total,
        "mapped_alignment_records": mapped,
        "unmapped_alignment_records": unmapped,
        "reference_count": len(references),
        "reference_lengths": [
            {"name": name, "length": int(length)} for name, length in zip(references, lengths)
        ],
        "alignment_counts_by_reference": counts_by_reference,
        "unique_contig_names": len(contig_names),
        "query_length_counts_by_alignment": dict(sorted(query_lengths.items())),
        "evidence_scope": "counts_and_lengths_only_not_sequence_recovery",
    }


def _write_exclusive_report(report_path, payload):
    if len(payload) > MAX_REPORT:
        raise FixtureError("report exceeds the 64-KiB cap")
    flags = (os.O_WRONLY | os.O_CREAT | os.O_EXCL
             | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0))
    try:
        fd = os.open(os.fspath(report_path), flags, 0o600)
    except OSError:
        raise FixtureError("report path must be new and support exclusive creation") from None
    identity = os.fstat(fd)
    try:
        view = memoryview(payload)
        while view:
            written = os.write(fd, view)
            if written <= 0:
                raise FixtureError("report write ended before all bytes were written")
            view = view[written:]
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size != len(payload):
            raise FixtureError("exclusive report is not a complete regular file")
        os.close(fd)
        fd = None
    except Exception as error:
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass
        try:
            named = os.lstat(report_path)
            if (stat.S_ISREG(named.st_mode) and named.st_dev == identity.st_dev
                    and named.st_ino == identity.st_ino):
                os.unlink(report_path)
        except OSError:
            pass
        if isinstance(error, FixtureError):
            raise
        raise FixtureError("exclusive report write failed") from None


def observe_native_fixture(reference_fasta, truth_json, assembly_bed,
                           candidate_vcf_bcf, final_vcf_bcf, contig_bam,
                           report_path):
    """Validate and summarize the fixed synthetic fixture, then create one report.

    All six input paths must be regular, nonlink files. The function parses
    immutable in-memory copies and verifies each original file again before it
    creates the report. It never starts a caller or stores record-level traces.
    """
    paths = {
        "reference_fasta": reference_fasta,
        "truth_json": truth_json,
        "assembly_bed": assembly_bed,
        "candidate_vcf_bcf": candidate_vcf_bcf,
        "final_vcf_bcf": final_vcf_bcf,
        "contig_bam": contig_bam,
    }
    payloads, snapshots, digests, total_size = _read_inputs(paths)
    try:
        reference, reference_sha = _parse_fasta(payloads["reference_fasta"])
        alternate = _parse_truth(payloads["truth_json"], reference, reference_sha)
        bed = _parse_bed(payloads["assembly_bed"])
        candidate = _summarize_callset(payloads["candidate_vcf_bcf"], reference,
                                       alternate, role="candidate", final=False)
        final = _summarize_callset(payloads["final_vcf_bcf"], reference,
                                   alternate, role="final", final=True)
        bam = _summarize_bam(payloads["contig_bam"])
    finally:
        _posthash_inputs(paths, snapshots, digests)

    report = {
        "schema_version": 1,
        "status": "complete",
        "synthetic_only": True,
        "complete_parse": True,
        "sample": SYNTH_SAMPLE,
        "reference": {
            "contig": SYNTH_CONTIG,
            "length": REFERENCE_LENGTH,
            "sequence_sha256": reference_sha,
            "sequence_sha256_basis": REFERENCE_SHA256_BASIS,
        },
        "truth": {
            "version": 1,
            "validated_exact_scope": True,
            "insertion_offset": INSERTION_OFFSET,
            "inserted_length": len(INSERTION_SEQUENCE),
            "expected_alternate_length": EXPECTED_ALT_LENGTH,
        },
        "input_integrity": {
            "total_input_bytes": total_size,
            "all_before_after_hashes_and_snapshots_match": True,
            "files": {
                role: {"bytes": len(payloads[role]), "sha256": digests[role]}
                for role in INPUT_ROLES
            },
        },
        "comparison": {
            "method": "apply_each_single_literal_REF_to_ALT_to_the_full_4000_base_reference",
            "equivalence": "exact_4060_base_haplotype_equality",
            "left_shift_tolerance": "none; identical haplotypes compare equal",
        },
        "assembly_bed": bed,
        "candidate": candidate,
        "final": final,
        "contig_bam": bam,
        "limits": {
            "read_trace": "not_collected",
            "rejected_trace_completeness": "not_assessed",
            "causal_attribution": "not_assessed",
            "caller_execution": False,
            "scoring": False,
        },
    }
    encoded = (json.dumps(report, sort_keys=True, indent=2) + "\n").encode("utf-8")
    _write_exclusive_report(report_path, encoded)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-fasta", required=True)
    parser.add_argument("--truth-json", required=True)
    parser.add_argument("--assembly-bed", required=True)
    parser.add_argument("--candidate-vcf-bcf", required=True)
    parser.add_argument("--final-vcf-bcf", required=True)
    parser.add_argument("--contig-bam", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args(argv)
    try:
        result = observe_native_fixture(
            args.reference_fasta, args.truth_json, args.assembly_bed,
            args.candidate_vcf_bcf, args.final_vcf_bcf,
            args.contig_bam, args.report,
        )
    except FixtureError as error:
        print(json.dumps({"status": "incomplete", "error": str(error)}), file=sys.stderr)
        return 2
    print(json.dumps({"status": result["status"], "report": args.report,
                      "candidate": result["candidate"], "final": result["final"]},
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
