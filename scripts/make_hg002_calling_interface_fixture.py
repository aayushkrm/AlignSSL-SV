"""Whole synthetic caller/cohort interface control. No real-data inputs or P1."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import re
import signal
import subprocess
import time

VERSION = "synthetic-calling-interface-v1"
SAMPLE = "SYNTHETIC_CCS_V1"
RG = "toy_ccs_v1"
MAX_BYTES = 32 * 1024 * 1024
COHORT_SHA = "197a54c9dbf6dd3f7f9264a3eb090d0646f08d05fdb7dfe99ae2c337f0064f4e"
SOURCES = (
    "scripts/make_hg002_calling_interface_fixture.py",
    "scripts/run_hg002_calling_interface_fixture.sh",
    "tests/test_hg002_calling_interface_fixture.py",
    "docs/research/2026-10-11-hg002-calling-interface-fixture.md",
    "analysis/hg002_cds_overlap_cohort.py",
)
RECEIPTS = {
    "pbmm2.align-help.log": "71d53dcfbe5689d2e590e3548db38fdbaa83be7ebcb2865be83e5c5aefdf216c",
    "pbsv.discover-help.log": "f9af06a34ab582823efa8137f0e2641995cfc634ced3e9a7ab550ffa2b2c07f4",
    "pbsv.call-help.log": "fc3312869faa663e41889f1ff8a1f5bec6be171a68128d7841eef4548e970f90",
    "pbmm2.version.log": "8898afaf3479fb703bd547995ed2fdecf1c8be07ed65146dc7ac4039787407ed",
    "pbsv.version.log": "48793cf72e77de085e392831aa1fa41261d7b6d624151870348a5ee1ce70c12d",
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def rc(sequence):
    return sequence.translate(str.maketrans("ACGT", "TGCA"))[::-1]


def dna(seed, length):
    rng = random.Random(seed)
    return "".join(rng.choice("ACGT") for _ in range(length))


def publish(path, data):
    """Exclusive final publication; leave a partial if interrupted."""
    path = Path(path)
    if path.exists() or path.is_symlink():
        raise FileExistsError(path)
    part = path.with_name(path.name + ".partial")
    with part.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    os.link(part, path)
    part.unlink()


def json_bytes(value):
    return (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()


def leaf_bytes(root, transient_test_links=False):
    root = Path(root)
    files = list(Path(root).rglob("*"))
    size = 0
    for path in files:
        try:
            if path.is_symlink():
                test_root = root / "test-tmp"
                if not (transient_test_links and test_root in path.parents and test_root in path.resolve().parents):
                    raise ValueError("Packet contains a symlink")
                size += path.lstat().st_size  # Never read through test refusal fixtures.
                continue
            if path.is_file(): size += path.stat().st_size
        except FileNotFoundError:
            pass  # Exclusive publication/temp cleanup can remove a sampled path.
    return size


def guard(root, transient_test_links=False):
    size = leaf_bytes(root, transient_test_links)
    if size >= MAX_BYTES:
        raise ValueError("Packet reached its strict 32-MiB guard")
    return size


def make_fixture(output, source_root=None):
    output = Path(output)
    if not output.is_absolute() or output.parent.resolve() != output.parent:
        raise ValueError("Need an absolute path under a resolved existing parent")
    # Fixed seeds, fixed events, no native-output-dependent generation or retries.
    refs = {f"toy_{name}_v1": dna(seed, 30000)
            for name, seed in (("del", 11001), ("ins", 22002), ("ref", 33003))}
    insertion = dna(44004, 150)
    events = [dict(event_id="TOY_DEL.1", chrom="toy_del_v1", svtype="DEL",
                   start0=15000, end0=15120, size_bp=120, inserted_sequence=""),
              dict(event_id="TOY_INS.1", chrom="toy_ins_v1", svtype="INS",
                   start0=15000, end0=15000, size_bp=150, inserted_sequence=insertion)]
    alleles = {(chrom, "REF"): sequence for chrom, sequence in refs.items()}
    for e in events:
        ref = refs[e["chrom"]]
        alt = ref[:e["start0"]] + e["inserted_sequence"] + ref[e["end0"]:]
        alleles[e["chrom"], "ALT"] = alt
        e.update(reference_sha256=sha(ref.encode()), alternate_sha256=sha(alt.encode()),
                 gene_id=f"TOY_GENE_{e['svtype']}.1",
                 transcripts=[f"TOY_TX_{e['svtype']}_{i}.1" for i in (1, 2)],
                 expected_GT="0/1", expected_FILTER="PASS", expected_phase="UNPHASED")
    fasta = ""; fai = ""; offset = 0
    for chrom, seq in refs.items():
        head = f">{chrom}\n"
        body = "\n".join(seq[i:i+60] for i in range(0, len(seq), 60)) + "\n"
        fai += f"{chrom}\t{len(seq)}\t{offset + len(head)}\t60\t61\n"
        fasta += head + body
        offset += len(head) + len(body)
    fastq, identities, gtf = [], [], []
    zmw = 1000
    for chrom in refs:
        for allele in ("REF", "ALT") if chrom != "toy_ref_v1" else ("REF",):
            count = 10 if chrom != "toy_ref_v1" else 20
            seq = alleles[chrom, allele]
            for i in range(count):
                name = f"toyfixture_v1/{zmw}/ccs"; zmw += 1
                strand = "+" if i % 2 == 0 else "-"
                read = seq if strand == "+" else rc(seq)
                quality = "I" * len(read)  # FASTQ Phred+33, Q40 everywhere.
                fastq.append(f"@{name}\n{read}\n+\n{quality}\n")
                identities.append(dict(qname=name, chrom=chrom, allele=allele,
                    strand=strand, length=len(read), sequence_sha256=sha(read.encode()),
                    quality_sha256=sha(quality.encode()), sample=SAMPLE, rg=RG))
        kind = chrom.split("_")[1].upper()
        for iso in (1, 2):
            attrs = (f'gene_id "TOY_GENE_{kind}.1"; transcript_id "TOY_TX_{kind}_{iso}.1"; '
                     f'gene_name "TOY_{kind}"; gene_type "protein_coding"; transcript_type "protein_coding";')
            gtf.append(f"{chrom}\tsynthetic\tCDS\t9001\t21000\t.\t+\t0\t{attrs}\n")
    truth = dict(version=VERSION, sample=SAMPLE, rg=RG, quality="Phred+33 Q40",
        contigs={k: dict(length=len(v), sha256=sha(v.encode())) for k, v in refs.items()},
        events=events, negative_contig="toy_ref_v1", reads=identities,
        representation_contract="Whole alternate sequence exact equivalence; no breakpoint/size tolerance. "
            "Literal anchored DEL/INS or exact END/SVLEN symbolic DEL; symbolic INS unresolved. "
            "Exactly one nonref PASS heterozygous unphased call per truth event; no extras.",
        expected_cohort=dict(input_records=2, input_alt_observations=2, OVERLAPS_CDS=2,
                             UNKNOWN=0, index_rows=2, final_D=None, p1_state="NOT_ASSESSED",
                             candidate_state="UNKNOWN", unknown_reason="unphased_GT"))
    payload = {"reference.fa": fasta.encode(), "reference.fa.fai": fai.encode(),
               "reads.fastq": "".join(fastq).encode(), "cds.gtf": "".join(gtf).encode(),
               "alleles.fa": "".join(f">{c}|{a}\n{s}\n" for (c, a), s in alleles.items()).encode(),
               "truth.json": json_bytes(truth)}
    if source_root is not None:
        root = Path(source_root)
        for name in SOURCES:
            path = root / name
            if path.is_symlink() or path.stat().st_size > 1024 * 1024:
                raise ValueError("Unbounded/aliased source")
            payload["sources/" + name] = path.read_bytes()
        if sha(payload["sources/analysis/hg002_cds_overlap_cohort.py"]) != COHORT_SHA:
            raise ValueError("Unchanged cohort source pin mismatch")
        for name, expected in RECEIPTS.items():
            path = root / "results/hg002_caller_setup_20261011" / name
            if path.is_symlink() or path.stat().st_size > 65536:
                raise ValueError("Unbounded/aliased native receipt")
            data = path.read_bytes()
            if sha(data) != expected:
                raise ValueError("Captured help/version receipt changed")
            payload["sources/receipts/" + name] = data
    if sum(map(len, payload.values())) >= MAX_BYTES:
        raise ValueError("Fixture exceeds size guard")
    output.mkdir()  # Existing directory or dangling symlink fails, even when empty.
    for name, data in payload.items():
        path = output / name; path.parent.mkdir(parents=True, exist_ok=True)
        publish(path, data)
    manifest = dict(version=VERSION, synthetic_only=True,
        files={name: dict(bytes=len(data), sha256=sha(data)) for name, data in sorted(payload.items())})
    publish(output / "manifest.json", json_bytes(manifest))
    guard(output)
    return truth


def fasta(path):
    sequences, name = {}, None
    for line in Path(path).read_text().splitlines():
        if line.startswith(">"):
            name = line[1:]; sequences[name] = ""
        else:
            sequences[name] += line
    return sequences


def verify_inputs(root):
    root = Path(root)
    manifest = json.loads((root / "manifest.json").read_text())
    if manifest["version"] != VERSION or not manifest["synthetic_only"]:
        raise ValueError("Not this synthetic fixture")
    for name, entry in manifest["files"].items():
        path = root / name
        if Path(name).is_absolute() or ".." in Path(name).parts or path.is_symlink():
            raise ValueError("Invalid fixture manifest path")
        if path.stat().st_size != entry["bytes"] or sha(path.read_bytes()) != entry["sha256"]:
            raise ValueError("Fixture mutated: " + name)
    guard(root)


def compare(fixture, vcf, cohort, output):
    """Independent VCF truth check, then check unchanged cohort's JSONL accounting."""
    fixture = Path(fixture); verify_inputs(fixture)
    truth = json.loads((fixture / "truth.json").read_text()); refs = fasta(fixture / "reference.fa")
    observed, errors, samples = [], [], None
    for line in Path(vcf).read_text().splitlines():
        if line.startswith("#CHROM\t"):
            samples = line.split("\t")[9:]
            if samples != [SAMPLE]: errors.append("sample_columns_not_exact")
        elif line and not line.startswith("#"):
            f = line.split("\t")
            if len(f) != 10 or samples != [SAMPLE]:
                errors.append("malformed_record_or_sample"); observed.append(dict(raw=line)); continue
            info = {}; bad = []
            for entry in f[7].split(";"):
                key, _, value = entry.partition("=")
                if key in info: bad.append("duplicate_INFO_" + key)
                info[key] = value
            fields = dict(zip(f[8].split(":"), f[9].split(":")))
            gt = fields.get("GT", "")
            for i, alt in enumerate(f[4].split(","), 1):
                item = dict(raw=line, chrom=f[0], POS=f[1], REF=f[3], ALT=alt, FILTER=f[6],
                            FORMAT=fields, alt_index=i, reasons=list(bad), matched_truth=None)
                observed.append(item)
                try:
                    ref = refs[f[0]]; pos = int(f[1]) - 1
                    if pos < 0 or ref[pos:pos+len(f[3])] != f[3]:
                        raise ValueError("REF_mismatch")
                    tokens = gt.replace("|", "/").split("/")
                    valid_gt = all(t.isdigit() and int(t) <= len(f[4].split(",")) for t in tokens)
                    item["nonref"] = i in [int(t) for t in tokens if t.isdigit()]
                    if not valid_gt: item["reasons"].append("invalid_GT")
                    if not item["nonref"] and valid_gt: continue
                    if len(f[4].split(",")) != 1: raise ValueError("multiallelic_unexpected")
                    if alt == "<DEL>":
                        end = int(info["END"]); size = end - (pos+1)
                        if size <= 0 or int(info["SVLEN"]) != -size or end > len(ref):
                            raise ValueError("symbolic_DEL_geometry")
                        kind = "DEL"; alternate = ref[:pos+1] + ref[end:]
                    elif alt and all(c in "ACGT" for c in f[3] + alt):
                        alternate = ref[:pos] + alt + ref[pos+len(f[3]):]
                        delta = len(alt) - len(f[3]); size = abs(delta)
                        kind = "INS" if delta > 0 else "DEL" if delta < 0 else "OTHER"
                        if "SVLEN" in info and int(info["SVLEN"]) != delta:
                            raise ValueError("SVLEN_disagreement")
                    else:
                        raise ValueError("sequence_unresolved_or_other_type")
                    if info.get("SVTYPE", kind) != kind: raise ValueError("SVTYPE_disagreement")
                    item.update(svtype=kind, size_bp=size, alternate_sha256=sha(alternate.encode()))
                    matches = [e for e in truth["events"] if e["chrom"] == f[0] and e["svtype"] == kind
                               and e["size_bp"] == size and e["alternate_sha256"] == item["alternate_sha256"]]
                    if len(matches) == 1: item["matched_truth"] = matches[0]["event_id"]
                    if sorted(tokens) != ["0", "1"] or "|" in gt: item["reasons"].append("not_unphased_heterozygote")
                    if any(fields.get(k) not in (None, ".") for k in ("PS", "PID", "PGT", "HP")):
                        item["reasons"].append("unexpected_phase_tag")
                    if f[6] != "PASS": item["reasons"].append("FILTER_not_PASS")
                except (ValueError, KeyError) as exc:
                    item["reasons"].append(str(exc))
    if samples is None: errors.append("missing_VCF_header")
    missing = []; duplicates = []
    for event in truth["events"]:
        hits = [x for x in observed if x.get("matched_truth") == event["event_id"]]
        if not hits: missing.append(event["event_id"])
        if len(hits) > 1: duplicates.append(event["event_id"])
    extra = [i for i, x in enumerate(observed) if x.get("nonref", True) and x.get("matched_truth") is None]
    rows = [json.loads(line) for line in Path(cohort).read_text().splitlines()]
    if not rows or rows[0].get("final_D", "missing") is not None:
        errors.append("cohort_summary_or_final_D")
    summary = rows[0] if rows else {}; counters = summary.get("counters", {})
    for key in ("input_records", "input_alt_observations", "OVERLAPS_CDS", "UNKNOWN", "index_rows"):
        if counters.get(key) != truth["expected_cohort"][key]: errors.append("cohort_counter_" + key)
    if any(value for key, value in counters.items() if key.startswith("out_of_primary_")):
        errors.append("cohort_exclusion_counter")
    expected_keys = {(e["chrom"], e["gene_id"], tuple(e["transcripts"]), e["svtype"], e["size_bp"]) for e in truth["events"]}
    seen = []
    for row in rows[1:]:
        seen.append((row.get("chrom"), row.get("gene_id"), tuple(row.get("transcripts", [])), row.get("svtype"), row.get("size_bp")))
        if row.get("candidate_state") != "UNKNOWN" or "unphased_GT" not in row.get("unknown_reasons", []):
            errors.append("cohort_phase_unknown_not_retained")
        if row.get("p1_state") != "NOT_ASSESSED" or row.get("overlap_status") != "OVERLAPS_CDS":
            errors.append("cohort_role_or_overlap")
        for source in row.get("source_records", []):
            if source.get("phase_status") != "UNPHASED" or source.get("phase") or source.get("alt_copy_count") != 1:
                errors.append("cohort_source_phase_or_copy")
    # The cohort merges the two isoforms of each gene into one row, not two rows.
    if len(seen) != 2 or set(seen) != expected_keys: errors.append("cohort_rows_or_isoforms")
    report = dict(version=VERSION, observed=observed, missing=missing, duplicate_truth=duplicates,
        extra_observation_indices=extra, cohort_summary=summary, cohort_rows=rows[1:], errors=errors,
        complete=not (missing or duplicates or extra or errors or any(x.get("reasons") for x in observed)))
    publish(output, json_bytes(report))
    return report


def audit_bam(fixture, bam, output):
    """Optional existing pysam is needed only during main's native run."""
    import pysam
    verify_inputs(fixture)
    truth = json.loads((Path(fixture) / "truth.json").read_text())
    reads = {x["qname"]: x for x in truth["reads"]}; seen = {}; errors = []; records = 0
    with pysam.AlignmentFile(str(bam), "rb") as stream:
        header = stream.header.to_dict()
        if not stream.has_index() or not stream.check_index():
            errors.append("BAM_index_missing_or_invalid")
        if dict(zip(stream.references, stream.lengths)) != {k: v["length"] for k, v in truth["contigs"].items()}:
            errors.append("BAM_dictionary_mismatch")
        groups = header.get("RG", [])
        if len(groups) != 1 or groups[0].get("ID") != RG or groups[0].get("SM") != SAMPLE:
            errors.append("BAM_sample_RG_mismatch")
        for rec in stream.fetch(until_eof=True):
            records += 1
            if rec.query_name not in reads: errors.append("unexpected_QNAME"); continue
            if rec.is_secondary or rec.is_supplementary: continue
            wanted = reads[rec.query_name]; seen[rec.query_name] = seen.get(rec.query_name, 0) + 1
            sequence = rec.get_forward_sequence(); qualities = rec.get_forward_qualities()
            if sequence is None or sha(sequence.encode()) != wanted["sequence_sha256"]:
                errors.append("source_sequence_mismatch:" + rec.query_name)
            if qualities is None or sha("".join(chr(q+33) for q in qualities).encode()) != wanted["quality_sha256"]:
                errors.append("source_quality_mismatch:" + rec.query_name)
            if rec.is_unmapped or rec.reference_name != wanted["chrom"] or rec.is_reverse != (wanted["strand"] == "-"):
                errors.append("source_alignment_orientation:" + rec.query_name)
            if not rec.has_tag("RG") or rec.get_tag("RG") != RG: errors.append("read_RG_mismatch")
            if rec.has_tag("HP") or rec.has_tag("PS"): errors.append("unexpected_read_phase")
    missing = sorted(set(reads) - set(seen)); duplicated = sorted(k for k, v in seen.items() if v != 1)
    report = dict(records=records, primary_identities=len(seen), missing=missing, duplicated=duplicated,
                  errors=errors, complete=not (missing or duplicated or errors), pysam_version=pysam.__version__)
    publish(output, json_bytes(report)); return report


def step(root, label, seconds, command):
    """Bound a sequential process group; retain exact commands, logs and exits."""
    root = Path(root); guard(root)
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", label) or not 0 < seconds <= 120 or not command:
        raise ValueError("Invalid bounded step contract")
    log = root / (label + ".log")
    publish(root / (label + ".command.json"), json_bytes(command))
    started = time.monotonic(); stopped = None
    with log.open("xb") as stream:
        try:
            process = subprocess.Popen(command, stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
        except OSError as exc:
            publish(root / (label + ".exit.json"), json_bytes(dict(exit_code=127, stopped="launch_failure", error=str(exc))))
            return 127
        while process.poll() is None:
            try: guard(root, transient_test_links=label == "unit-tests")
            except (ValueError, OSError): stopped = "disk_guard"
            if time.monotonic() - started >= seconds: stopped = "timeout"
            if stopped:
                os.killpg(process.pid, signal.SIGTERM)
                try: process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL); process.wait()
                break
            time.sleep(0.05)
        code = process.wait()
        # Do not leave children running after the tracked parent has exited.
        try: os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError: pass
    publish(root / (label + ".exit.json"), json_bytes(dict(exit_code=code, stopped=stopped,
        elapsed_seconds=time.monotonic()-started)))
    guard(root)
    return code if code else 2 if stopped else 0


def finalize(root, exit_code):
    root = Path(root)
    size = leaf_bytes(root)
    if exit_code == 0:
        for name in ("comparison.json", "bam-audit.json"):
            if not json.loads((root / name).read_text()).get("complete"):
                raise ValueError("Missing complete native audit/comparison")
    publish(root / "status.json", json_bytes(dict(exit_code=exit_code,
        state="SYNTHETIC_INTERFACE_COMPLETE" if exit_code == 0 and size < MAX_BYTES else "INCOMPLETE",
        sampled_bytes_before_manifest=size, disk_guard_bytes=MAX_BYTES)))
    try:
        files = {str(p.relative_to(root)): dict(bytes=p.stat().st_size, sha256=sha(p.read_bytes()))
                 for p in sorted(root.rglob("*")) if p.is_file()}
        publish(root / "artifact-manifest.json", json_bytes(dict(version=VERSION, files=files)))
        guard(root)
    except Exception as exc:
        publish(root / "finalization-failure.json", json_bytes(dict(error=str(exc), state="INCOMPLETE")))
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    p = sub.add_parser("make"); p.add_argument("--output", type=Path, required=True); p.add_argument("--source-root", type=Path)
    for action in ("compare", "audit-bam"):
        p = sub.add_parser(action); p.add_argument("--fixture", type=Path, required=True); p.add_argument("--output", type=Path, required=True)
        if action == "compare": p.add_argument("--vcf", type=Path, required=True); p.add_argument("--cohort", type=Path, required=True)
        else: p.add_argument("--bam", type=Path, required=True)
    p = sub.add_parser("step"); p.add_argument("--root", type=Path, required=True); p.add_argument("--label", required=True)
    p.add_argument("--seconds", type=float, required=True); p.add_argument("command", nargs=argparse.REMAINDER)
    p = sub.add_parser("finalize"); p.add_argument("--root", type=Path, required=True); p.add_argument("--exit-code", type=int, required=True)
    args = parser.parse_args()
    if args.action == "make": make_fixture(args.output, args.source_root)
    elif args.action == "compare":
        raise SystemExit(0 if compare(args.fixture, args.vcf, args.cohort, args.output)["complete"] else 2)
    elif args.action == "audit-bam":
        raise SystemExit(0 if audit_bam(args.fixture, args.bam, args.output)["complete"] else 2)
    elif args.action == "step":
        command = args.command[1:] if args.command[:1] == ["--"] else args.command
        raise SystemExit(step(args.root, args.label, args.seconds, command))
    else: finalize(args.root, args.exit_code)


if __name__ == "__main__":
    main()
