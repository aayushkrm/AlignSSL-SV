#!/usr/bin/env python3
"""Small synthetic controls for the pinned reference-validation stack."""

import importlib.metadata
import hashlib
import json
import pathlib
import sys
import tempfile
import traceback


HEADER = (
    "##fileformat=VCFv4.2\n"
    "##contig=<ID=synthetic,length=256>\n"
    '##INFO=<ID=SVTYPE,Number=1,Type=String,Description="Synthetic type">\n'
    '##INFO=<ID=SVLEN,Number=1,Type=Integer,Description="Synthetic length">\n'
    '##INFO=<ID=KEEP,Number=1,Type=String,Description="Preservation marker">\n'
    '##FORMAT=<ID=GT,Number=1,Type=String,Description="Synthetic genotype">\n'
    '##FORMAT=<ID=DP,Number=1,Type=Integer,Description="Synthetic depth">\n'
    "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSYNTH\n"
)


def _need(ok, message):
    if not ok:
        raise RuntimeError(message)


def _versions(pysam):
    from pysam.version import __bcftools_version__, __htslib_version__

    truvari_version = importlib.metadata.version("truvari")
    versions = {
        "python": sys.version.split()[0],
        "pysam": pysam.__version__,
        "bcftools": __bcftools_version__,
        "htslib": __htslib_version__,
        "truvari": truvari_version,
    }
    _need(
        versions["pysam"] == "0.24.0"
        and versions["bcftools"] == "1.23.1"
        and versions["htslib"] == "1.23.1"
        and versions["truvari"] == "5.4.0",
        "requires cluster pins pysam 0.24.0, bundled bcftools/HTSlib 1.23.1, Truvari 5.4.0",
    )
    return versions


def _variant(sequence, record_id, pos, kind, *, svlen=None, svtype=None):
    offset = pos - 1
    if kind == "INS":
        ref, alt, canonical_len = sequence[offset], sequence[offset] + "TT", 2
    else:
        ref = sequence[offset : offset + 4]
        alt, canonical_len = ref[0], -3
    return {
        "id": record_id,
        "pos": pos,
        "ref": ref,
        "alt": alt,
        "svtype": kind if svtype is None else svtype,
        "svlen": canonical_len if svlen is None else svlen,
        "canonical_svtype": kind,
        "canonical_svlen": canonical_len,
    }


def _vcf_row(variant):
    return (
        f"synthetic\t{variant['pos']}\t{variant['id']}\t{variant['ref']}\t"
        f"{variant['alt']}\t.\tPASS\tSVTYPE={variant['svtype']};"
        f"SVLEN={variant['svlen']};KEEP={variant['id']}\tGT:DP\t./.:.\n"
    )


def _fixtures(root, pysam):
    sequence = "ACGT" * 64
    reference = root / "synthetic.fa"
    reference.write_text(f">synthetic\n{sequence}\n", encoding="ascii")
    pysam.faidx(str(reference))

    insertion = _variant(sequence, "matched_ins", 20, "INS")
    deletion = _variant(sequence, "matched_del", 60, "DEL")
    matched = root / "matched.vcf"
    matched.write_text(HEADER + _vcf_row(insertion) + _vcf_row(deletion), encoding="ascii")

    mismatch = _variant(sequence, "wrong_ref", 220, "INS")
    actual = mismatch["ref"]
    mismatch["ref"] = next(base for base in "ACGT" if base != actual)
    mismatch["alt"] = mismatch["ref"] + "TT"
    mismatch_vcf = root / "ref-mismatch.vcf"
    mismatch_vcf.write_text(HEADER + _vcf_row(mismatch), encoding="ascii")

    wrong_length = _variant(sequence, "wrong_svlen", 120, "DEL", svlen=-2)
    wrong_type = _variant(sequence, "wrong_svtype", 180, "DEL", svtype="INS")
    truth = root / "truth-metadata.vcf"
    truth.write_text(
        HEADER
        + "".join(_vcf_row(row) for row in (insertion, deletion, wrong_length, wrong_type)),
        encoding="ascii",
    )
    return reference, matched, mismatch_vcf, truth, sequence


def _norm(bcftools, reference, source, destination, *, disable_normalization=False):
    bcftools.norm(
        *(["-N"] if disable_normalization else []),
        "-c",
        "e",
        "-f",
        str(reference),
        "--no-version",
        "-Ov",
        "-o",
        str(destination),
        str(source),
        catch_stdout=False,
    )


def _data_rows(path):
    return [line for line in pathlib.Path(path).read_text().splitlines() if line and not line.startswith("#")]


def _payload(path, pysam):
    payload = {}
    with pysam.VariantFile(str(path)) as vcf:
        for record in vcf:
            sample = record.samples["SYNTH"]
            payload[record.id] = {
                "info": {key: record.info[key] for key in ("SVTYPE", "SVLEN", "KEEP")},
                "gt": tuple(sample["GT"]),
                "dp": sample["DP"],
            }
    return payload


def _reference_controls(root, reference, matched, mismatch_vcf, pysam, bcftools):
    input_bytes = matched.read_bytes()
    normalized = root / "matched.norm.vcf"
    _norm(bcftools, reference, matched, normalized)
    same_rows = _data_rows(matched) == _data_rows(normalized)
    same_payload = _payload(matched, pysam) == _payload(normalized, pysam)
    _need(same_payload, "bcftools norm changed matched GT or INFO values")
    _need(len(_data_rows(normalized)) == 2, "matched control did not preserve both records")
    _need(matched.read_bytes() == input_bytes, "validation changed original source bytes")

    disabled_check = root / "mismatch.disabled-check.vcf"
    _norm(bcftools, reference, mismatch_vcf, disabled_check, disable_normalization=True)
    _need(_data_rows(disabled_check) == _data_rows(mismatch_vcf),
          "the observed -N unsafe REF-check counterexample changed")

    rejected = False
    diagnostic = ""
    try:
        _norm(bcftools, reference, mismatch_vcf, root / "mismatch.norm.vcf")
    except Exception as exc:
        rejected = True
        diagnostic = " ".join(
            str(value)
            for value in (exc, getattr(exc, "stderr", ""), getattr(exc, "stdout", ""))
            if value
        )
    lower = diagnostic.lower()
    diagnosed = "mismatch" in lower and ("reference" in lower or "ref" in lower)
    _need(rejected and diagnosed, "bcftools norm -c e -f did not reject a REF mismatch with a mismatch diagnostic")

    return {
        "command": "bcftools norm -c e -f <synthetic.fa>; transformed output is not an analysis input",
        "unsafe_disabled_normalization_control": {"command": "bcftools norm -N -c e -f",
                                                  "wrong_ref_accepted_unchanged": True},
        "ref_mismatch": {"rejected": rejected, "diagnostic_confirms_mismatch": diagnosed,
                         "diagnostic": diagnostic[:400]},
        "matched_rows": {"count": len(_data_rows(normalized)), "ids": sorted(_payload(normalized, pysam)),
                         "exact_validation_output_rows_preserved": same_rows,
                         "original_source_bytes_preserved": matched.read_bytes() == input_bytes,
                         "source_sha256": hashlib.sha256(input_bytes).hexdigest(),
                         "gt_and_info_unchanged": same_payload,
                         "validation_output_discarded_not_used_for_scoring": True},
    }


def _canonical(ref, alt):
    alphabet = set("ACGT")
    if not ref or not alt or set(ref) - alphabet or set(alt) - alphabet:
        raise RuntimeError("synthetic control expects nonempty sequence alleles")
    delta = len(alt) - len(ref)
    if delta == 0:
        raise RuntimeError("synthetic control expects a pure insertion or deletion")
    left, right = ref, alt
    while left and right and left[-1] == right[-1]:
        left, right = left[:-1], right[:-1]
    while left and right and left[0] == right[0]:
        left, right = left[1:], right[1:]
    if left and right:
        raise RuntimeError("synthetic control expects a pure insertion or deletion")
    return {"type": "INS" if delta > 0 else "DEL", "size": abs(delta), "svlen": delta}


def _type_label(value):
    return str(getattr(value, "name", str(value).rsplit(".", 1)[-1]))


def _audit_record(record, truvari):
    canonical = _canonical(record.ref, record.alts[0])
    native_type = record.var_type()
    native_size = int(record.var_size())
    info_svlen = int(record.info["SVLEN"])
    info_svtype = str(record.info["SVTYPE"])
    checks = {
        "native_size_matches_canonical": native_size == canonical["size"],
        "native_type_matches_canonical": native_type == getattr(truvari.SV, canonical["type"]),
        "info_svlen_matches_canonical": info_svlen == canonical["svlen"],
        "info_svtype_matches_canonical": info_svtype == canonical["type"],
    }
    return {
        "id": record.id,
        "canonical": canonical,
        "native": {"size": native_size, "type": _type_label(native_type)},
        "info": {"SVLEN": info_svlen, "SVTYPE": info_svtype},
        "checks": checks,
        "valid": all(checks.values()),
    }


def _truth_metadata_control(path, truvari):
    with truvari.VariantFile(str(path)) as vcf:
        audits = [_audit_record(record, truvari) for record in vcf]
    by_id = {audit["id"]: audit for audit in audits}
    _need(len(audits) == 4 and len(by_id) == 4, "truth metadata fixture did not contain four unique records")

    for record_id in ("matched_ins", "matched_del"):
        _need(all(by_id[record_id]["checks"].values()), f"native Truvari/canonical check failed for {record_id}")
    _need(not by_id["wrong_svlen"]["valid"]
          and not by_id["wrong_svlen"]["checks"]["info_svlen_matches_canonical"]
          and by_id["wrong_svlen"]["checks"]["info_svtype_matches_canonical"],
          "wrong truth SVLEN was not rejected independently")
    _need(not by_id["wrong_svtype"]["valid"]
          and not by_id["wrong_svtype"]["checks"]["info_svtype_matches_canonical"]
          and by_id["wrong_svtype"]["checks"]["info_svlen_matches_canonical"],
          "wrong truth SVTYPE was not rejected independently")
    return {
        "native_checks": [by_id[key] for key in ("matched_ins", "matched_del")],
        "contradictions": {
            "wrong_svlen": {"rejected": not by_id["wrong_svlen"]["valid"],
                             "mutated_info_field": "SVLEN",
                             "checks": by_id["wrong_svlen"]["checks"]},
            "wrong_svtype": {"rejected": not by_id["wrong_svtype"]["valid"],
                             "mutated_info_field": "SVTYPE",
                             "checks": by_id["wrong_svtype"]["checks"]},
        },
    }


def run_probe():
    import pysam
    import pysam.bcftools as bcftools
    import truvari

    versions = _versions(pysam)
    with tempfile.TemporaryDirectory(prefix="released-reference-control-") as temp_dir:
        root = pathlib.Path(temp_dir)
        reference, matched, mismatch_vcf, truth, sequence = _fixtures(root, pysam)
        ref_control = _reference_controls(root, reference, matched, mismatch_vcf, pysam, bcftools)
        metadata_control = _truth_metadata_control(truth, truvari)
    assertions = {
        "bcftools_rejects_ref_mismatch": ref_control["ref_mismatch"]["rejected"],
        "bcftools_reports_ref_mismatch": ref_control["ref_mismatch"]["diagnostic_confirms_mismatch"],
        "original_insertion_and_deletion_source_preserved": ref_control["matched_rows"]["original_source_bytes_preserved"],
        "matched_gt_and_info_unchanged": ref_control["matched_rows"]["gt_and_info_unchanged"],
        "native_truvari_matches_canonical_alleles": all(
            all(row["checks"].values()) for row in metadata_control["native_checks"]
        ),
        "wrong_truth_svlen_rejected_independently": metadata_control["contradictions"]["wrong_svlen"]["rejected"],
        "wrong_truth_svtype_rejected_independently": metadata_control["contradictions"]["wrong_svtype"]["rejected"],
    }
    _need(all(assertions.values()), "one or more reported synthetic assertions failed")
    return {
        "status": "pass",
        "scope": "synthetic_only",
        "fixture": {"reference_bases": len(sequence), "matched_records": 2, "metadata_records": 4,
                    "real_genomic_inputs_read": False},
        "versions": versions,
        "reference_validation": ref_control,
        "truth_metadata": metadata_control,
        "assertions": assertions,
    }


def main():
    try:
        result, code = run_probe(), 0
    except Exception as exc:
        traceback.print_exc(file=sys.stderr)
        result, code = {"status": "error", "error_type": type(exc).__name__, "error": str(exc)[:500]}, 1
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return code


if __name__ == "__main__":
    sys.exit(main())
