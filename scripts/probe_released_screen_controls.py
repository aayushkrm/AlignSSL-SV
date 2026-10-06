#!/usr/bin/env python3
"""Synthetic-only controls for the pinned released-screen stack."""
import hashlib
import importlib.metadata
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import traceback

NAMES = [str(n) for n in range(1, 23)] + ["X", "Y"]
LENGTHS = (249250621, 243199373, 198022430, 191154276, 180915260, 171115067,
           159138663, 146364022, 141213431, 135534747, 135006516, 133851895,
           115169878, 107349540, 102531392, 90354753, 81195210, 78077248,
           59128983, 63025520, 48129895, 51304566, 155270560, 59373566)
FILTERS = ("LowQual", "HET1", "HET2", "GAP1", "GAP2")
HEADER = ("##fileformat=VCFv4.2\n" + "".join(
    f"##contig=<ID={name},length={length}>\n" for name, length in zip(NAMES, LENGTHS)) +
    "##contig=<ID=chrSynthetic,length=20000>\n" + "".join(
    f'##FILTER=<ID={name},Description="Synthetic control">\n' for name in FILTERS) +
    '##INFO=<ID=HISTID,Number=1,Type=String,Description="Synthetic historical ID">\n'
    '##INFO=<ID=SVLEN,Number=1,Type=Integer,Description="Synthetic variant length">\n'
    '##INFO=<ID=SVTYPE,Number=1,Type=String,Description="Synthetic variant type">\n'
    '##INFO=<ID=CTRL_SRCORD,Number=1,Type=Integer,Description="Parent ordinal">\n'
    '##INFO=<ID=CTRL_ALTIDX,Number=A,Type=Integer,Description="Original ALT index">\n'
    '##INFO=<ID=CTRL_ORIGID,Number=1,Type=String,Description="Original ID">\n'
    '##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">\n'
    '##FORMAT=<ID=AD,Number=R,Type=Integer,Description="Synthetic allele depths">\n'
    "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSYNTH\n")


def _need(ok, message):
    if not ok: raise RuntimeError(message)

def _sha(path): return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def _index(path, pysam):
    gz = pathlib.Path(str(path) + ".gz")
    pysam.tabix_compress(str(path), str(gz), force=True); pysam.tabix_index(str(gz), preset="vcf", force=True)
    return gz

def _args(exe, base, comp, out, ref):
    return [str(exe), "bench", "-b", str(base), "-c", str(comp), "-o", str(out),
            "-f", str(ref), "-s", "50", "-S", "30", "--sizemax", "-1", "-r", "1000",
            "-p", "0", "-P", "0.5", "-O", "0", "--pick", "multi", "--dup-to-ins",
            "--bnddist", "-1", "--no-decompose"]


def _altidx(record):
    v = record.info["CTRL_ALTIDX"]
    return int(v[0] if isinstance(v, (tuple, list)) else v)

def _rows(path):
    return [s for s in pathlib.Path(path).read_text().splitlines() if s and not s.startswith("#")]


def _versions(pysam):
    from pysam.version import __bcftools_version__, __htslib_version__
    trv = importlib.metadata.version("truvari")
    _need(trv == "5.4.0" and pysam.__version__ == "0.24.0",
          "requires Truvari 5.4.0 and pysam 0.24.0")
    _need(__bcftools_version__ == __htslib_version__ == "1.23.1",
          "requires pysam-bundled bcftools/htslib 1.23.1")
    return {"python": sys.version.split()[0], "truvari": trv, "pysam": pysam.__version__,
            "bcftools": "1.23.1 (pysam)+htslib-1.23.1"}


def _fixture(root, pysam, bcftools):
    ref = root / "synthetic.fa"
    ref.write_text(">chrSynthetic\n" + "A" * 20000 + "\n", encoding="ascii")
    pysam.faidx(str(ref))
    truth = root / "truth.vcf"
    truth.write_text(HEADER + "".join(
        f"chrSynthetic\t{p}\t{i}\t{'A' * 61}\tA\t.\t{f}\tHISTID=sharedHistorical;SVLEN=-60;SVTYPE=DEL\tGT:AD\t0/1:{ad}\n"
        for p, i, f, ad in ((100, "truth_001", "PASS", "5,7"), (150, "truth_002", "HET1", "4,6"))),
        encoding="ascii")
    source = root / "caller-source.vcf"
    cases = ((1, 120, "PASS", "1/2"), (2, 5000, "LowQual", "0/0"),
             (3, 10000, ".", "./1"))
    source.write_text(HEADER + "".join(
        f"chrSynthetic\t{p}\tdupCallerID\t{'A' * 61}\tA,{'A' * 121}\t.\t{f}\tCTRL_SRCORD={i};CTRL_ALTIDX=1,2;CTRL_ORIGID=dupCallerID\tGT\t{gt}\n"
        for i, p, f, gt in cases), encoding="ascii")
    split, derived = root / "split.vcf", root / "derived.vcf"
    bcftools.norm("-m", "-any", "--multi-overlaps", ".", "-N", "--no-version",
                  "-Ov", "-o", str(split), str(source), catch_stdout=False)
    parent_pos, identities, projected = {1: 120, 2: 5000, 3: 10000}, [], {}
    with pysam.VariantFile(str(split)) as src, pysam.VariantFile(
            str(derived), "w", header=src.header) as dst:
        for rec in src:
            key = (int(rec.info["CTRL_SRCORD"]), _altidx(rec))
            _need(rec.id == "dupCallerID" and rec.info["CTRL_ORIGID"] == "dupCallerID",
                  "norm did not preserve original caller IDs")
            alt = "A" if key[1] == 1 else "A" * 121
            _need(rec.pos == parent_pos[key[0]] and rec.ref == "A" * 61 and rec.alts == (alt,),
                  "norm repaired caller coordinates or alleles")
            identities.append(key); projected[key] = tuple(rec.samples[0]["GT"])
            rec.id = f"child_{key[0]}_{key[1]}"
            dst.write(rec)
    expected = {(1, 1): (1, None), (1, 2): (None, 1), (2, 1): (0, 0),
                (2, 2): (0, 0), (3, 1): (None, 1), (3, 2): (None, None)}
    _need(len(identities) == 6 and set(identities) == set(expected) and projected == expected,
          "norm identity or dot-mode GT control failed")
    sorted_vcf = root / "caller-sorted.vcf"
    bcftools.sort("-Ov", "-o", str(sorted_vcf), str(derived), catch_stdout=False)
    coords, ids, records = [], [], {}
    with pysam.VariantFile(str(sorted_vcf)) as vcf:
        ranks = {name: i for i, name in enumerate(vcf.header.contigs)}
        for rec in vcf:
            key = (int(rec.info["CTRL_SRCORD"]), _altidx(rec))
            coords.append((ranks[rec.contig], rec.pos)); ids.append(rec.id)
            records[key] = (rec.pos, rec.ref, rec.alts[0])
    wanted = {(i, a): (parent_pos[i], "A" * 61, "A" if a == 1 else "A" * 121)
              for i in parent_pos for a in (1, 2)}
    _need(coords == sorted(coords) and records == wanted and len(set(ids)) == 6,
          "sort coordinate/identity control failed")
    return ref, _index(truth, pysam), source, _index(sorted_vcf, pysam), identities


def _native_view(source, destination, pysam, truvari):
    counts = dict(records=0, kept=0, filtered=0, not_present=0, both=0, dot_kept=0)
    kept = set()
    with pysam.VariantFile(str(source)) as raw, truvari.VariantFile(str(source)) as native, \
            pysam.VariantFile(str(destination), "w", header=raw.header) as out:
        for rec, trv in zip(raw, native):
            counts["records"] += 1
            filt, present = trv.is_filtered(), trv.is_present(0, allow_missing=True)
            counts["filtered"] += int(filt); counts["not_present"] += int(not present)
            counts["both"] += int(filt and not present)
            if not filt and present:
                out.write(rec)
                counts["kept"] += 1
                counts["dot_kept"] += int(not rec.filter.keys())
                kept.add((int(rec.info["CTRL_SRCORD"]), _altidx(rec)))
    wanted = {(1, 1), (1, 2), (3, 1)}
    _need(counts == dict(records=6, kept=3, filtered=2, not_present=3, both=2, dot_kept=1)
          and kept == wanted, "Truvari native caller-filter control failed")
    return counts


def _coordinate_control(root, name, rows, pysam, bcftools):
    src = root / f"{name}.vcf"
    header = ("##fileformat=VCFv4.2\n##contig=<ID=chrSynthetic,length=20000>\n"
              "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n")
    src.write_text(header + "".join(row + "\n" for row in rows), encoding="ascii")
    pos0 = any(row.split("\t")[1] == "0" for row in rows)
    suffix = "pos0" if pos0 else "nplus1"
    out = dict(status="limited", source_records=len(rows), source_sha256=_sha(src))
    stage = "norm"
    try:
        norm = root / f"{name}.norm.vcf"
        bcftools.norm("-m", "-any", "--multi-overlaps", ".", "-N", "--no-version",
                      "-Ov", "-o", str(norm), str(src), catch_stdout=False)
        expected = _rows(src)
        if sorted(_rows(norm)) != sorted(expected):
            out.update(stage=stage, limitation=f"standard_norm_did_not_preserve_{suffix}"); return out
        stage, sorted_vcf = "sort", root / f"{name}.sorted.vcf"
        bcftools.sort("-Ov", "-o", str(sorted_vcf), str(norm), catch_stdout=False)
        sorted_rows = _rows(sorted_vcf)
        positions = [int(row.split("\t")[1]) for row in sorted_rows]
        if sorted(sorted_rows) != sorted(expected) or positions != sorted(positions):
            out.update(stage=stage, limitation=f"standard_sort_did_not_preserve_{suffix}"); return out
        out["sorted_records"] = len(sorted_rows)
        stage = "index"
        gz = _index(sorted_vcf, pysam)
        with pysam.TabixFile(str(gz)) as tabix:
            indexed = list(tabix.fetch("chrSynthetic"))
        out["indexed_records"] = len(indexed)
        if sorted(indexed) != sorted(expected):
            out.update(stage=stage, limitation="standard_index_did_not_represent_pos0" if pos0
                       else "standard_index_did_not_represent_all_rows"); return out
        out.update(status="pass", stage="complete", limitation=None)
    except Exception as exc:
        out.update(stage=stage, error_type=type(exc).__name__)
        out["limitation"] = ("standard_index_could_not_represent_pos0" if pos0 and stage == "index"
                             else f"standard_{stage}_rejected_{suffix}_fixture")
    return out


def _bench(root, exe, base, comp, ref, nbase, ncomp, pysam):
    with tempfile.TemporaryDirectory(prefix="bench-", dir=str(root)) as td:
        out = pathlib.Path(td) / "result"
        subprocess.run(_args(exe, base, comp, out, ref), check=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        summary = json.loads((out / "summary.json").read_text())
        base_ids = [rec.id for name in ("tp-base.vcf.gz", "fn.vcf.gz")
                    for rec in pysam.VariantFile(str(out / name))]
    stats = dict(base_count=int(summary["base cnt"]), caller_count=int(summary["comp cnt"]),
                 tp_base=int(summary["TP-base"]), tp_caller=int(summary["TP-comp"]),
                 fn=int(summary["FN"]), truth_ids_sha256=hashlib.sha256(
                     json.dumps(sorted(base_ids)).encode()).hexdigest())
    _need(stats["base_count"] == nbase and stats["tp_base"] + stats["fn"] == nbase
          and len(base_ids) == nbase and None not in base_ids,
          "bench changed the truth denominator or identity multiset")
    _need(stats["caller_count"] == ncomp, "bench caller count differs from its frozen view")
    return stats


def run_probe():
    import pysam
    import pysam.bcftools as bcftools
    import truvari

    versions = _versions(pysam)
    exe = shutil.which("truvari")
    _need(exe is not None, "truvari executable is not on PATH")
    cli = subprocess.run([exe, "version"], check=True, capture_output=True, text=True).stdout
    _need("5.4.0" in cli, "truvari CLI version differs from imported package")
    with tempfile.TemporaryDirectory(prefix="released-screen-control-") as td:
        root = pathlib.Path(td)
        ref, truth, source, caller, identities = _fixture(root, pysam, bcftools)
        pos0 = _coordinate_control(root, "pos0-nplus1", [
            "chrSynthetic\t0\tpos0_nplus1\tN\tNA\t.\tPASS\t.",
            "chrSynthetic\t20001\tnplus1\tN\tNA\t.\tPASS\t."], pysam, bcftools)
        nplus1 = _coordinate_control(root, "nplus1-only", [
            "chrSynthetic\t20001\tnplus1\tN\tNA\t.\tPASS\t."], pysam, bcftools)
        native_vcf = root / "caller-native.vcf"
        native_counts = _native_view(caller, native_vcf, pysam, truvari)
        native = _index(native_vcf, pysam)
        with pysam.VariantFile(str(truth)) as vcf:
            truth_rows = list(vcf)
            ids = [r.id for r in truth_rows]; hist = [r.info["HISTID"] for r in truth_rows]
            nonpass = sum(list(r.filter.keys()) != ["PASS"] for r in truth_rows)
        _need(len(set(ids)) == 2 and hist == ["sharedHistorical"] * 2 and nonpass == 1,
              "synthetic truth ID/FILTER control failed")
        with truvari.VariantFile(str(truth)) as vcf:
            sizes, types = zip(*((r.var_size(), r.var_type()) for r in vcf))
        _need(sizes == (60, 60) and types == (truvari.SV.DEL,) * 2,
              "truth SVLEN/SVTYPE disagree with native Truvari size/type")
        a, b = (_bench(root, exe, truth, caller, ref, 2, 6, pysam),
                _bench(root, exe, truth, native, ref, 2, 3, pysam))
        input_hash = hashlib.sha256(json.dumps(sorted(ids)).encode()).hexdigest()
        _need(a["truth_ids_sha256"] == b["truth_ids_sha256"] == input_hash,
              "truth ID multiset differs between arms")
        _need((a["tp_base"], a["tp_caller"], a["fn"]) == (2, 1, 0),
              "fixed lenient pick=multi control failed")
        return {
            "status": "pass" if pos0["status"] == nplus1["status"] == "pass" else "pass_with_limitations",
            "versions": versions,
            "coordinate_controls": {"pos0_and_nplus1": pos0, "nplus1_only": nplus1,
                                     "truth_scored": False, "scope": "synthetic_caller_preservation_only"},
            "fixture_counts": {"truth_records": 2, "truth_nonpass": nonpass, "caller_source_records": 3,
                "decomposed_children": 6, "native_filtered_children": native_counts["kept"],
                "native_rejected_filter": native_counts["filtered"], "native_rejected_presence": native_counts["not_present"],
                "native_rejected_both": native_counts["both"], "native_kept_dot_filter": native_counts["dot_kept"],
                "source_parent_alt_pairs": len(identities)},
            "identity_sha256": {"truth_ids": hashlib.sha256("\n".join(sorted(ids)).encode()).hexdigest(),
                "parent_alt_pairs": hashlib.sha256(json.dumps(sorted(map(list, identities))).encode()).hexdigest(),
                "truth_vcf": _sha(truth), "caller_source_vcf": _sha(source), "caller_sorted_vcf": _sha(caller),
                "reference": _sha(ref)},
            "bench": {"as_released": a, "native_filtered": b,
                "truth_denominator_unchanged": a["base_count"] == b["base_count"] == 2,
                "lenient_one_to_many": a["tp_base"] == 2 and a["tp_caller"] == 1}}


def main():
    try:
        result, code = run_probe(), 0
    except Exception as exc:
        traceback.print_exc()
        result, code = {"status": "error", "error_type": type(exc).__name__,
                        "error_message": str(exc)[:500]}, 1
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return code


if __name__ == "__main__":
    sys.exit(main())
