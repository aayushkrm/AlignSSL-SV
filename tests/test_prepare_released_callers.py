"""Synthetic controls only; the pinned Truvari integration is labelled separately."""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from analysis import prepare_released_callers as prep

HEADER = (
    "##fileformat=VCFv4.2\n##contig=<ID=chrSynthetic,length=10000>\n"
    '##FILTER=<ID=LowQual,Description="Synthetic">\n'
    '##INFO=<ID=AF,Number=A,Type=Float,Description="Synthetic">\n'
    '##INFO=<ID=DP,Number=1,Type=Integer,Description="Synthetic">\n'
    '##INFO=<ID=SVLEN,Number=A,Type=Integer,Description="Synthetic">\n'
    '##INFO=<ID=SVTYPE,Number=A,Type=String,Description="Synthetic">\n'
    '##FORMAT=<ID=GT,Number=1,Type=String,Description="Synthetic">\n'
    '##FORMAT=<ID=AD,Number=R,Type=Integer,Description="Synthetic">\n'
    '##FORMAT=<ID=PL,Number=G,Type=Integer,Description="Synthetic">\n'
    "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSYNTH\n"
)
ROWS = (
    "chrSynthetic\t5000\tduplicate\tA\tAA,AA\t60\tPASS\tAF=0.1,0.2;DP=10;SVLEN=1,1;SVTYPE=INS,INS\tGT:AD:PL\t1|2:5,6,7:0,10,20,30,40,50\n"
    "chrSynthetic\t0\tduplicate\tN\tNA\t.\t.\tAF=.;DP=2;SVLEN=1;SVTYPE=INS\tGT:AD:PL\t./1:.,8:0,1,2\n"
    "chrSynthetic\t10001\t.\tN\tNA\t.\tLowQual\tAF=.;DP=5;SVLEN=1;SVTYPE=INS\tGT:AD:PL\t0/0:5,0:0,2,4\n"
)

def case(tmp_path, raw=HEADER + ROWS, **updates):
    source = tmp_path / "synthetic-caller.vcf"
    source.write_text(raw)
    caps = {k: prep.MIB for k in (*prep.FILES, "sort_temp")}
    p = dict(purpose=prep.PURPOSE, caller="cutesv", caller_preparation_approved=True,
             independent_approval_ref="synthetic-only-review", runtime=prep.RUNTIME,
             source_basename=source.name, source_sha256=hashlib.sha256(raw.encode()).hexdigest(),
             source_bytes=len(raw.encode()), expected_sample_label="SYNTH", expected_source_records=3,
             max_source_bytes=prep.MIB, max_line_bytes=16384, max_children=32,
             output_caps=caps, storage_cap_bytes=12 * prep.MIB,
             input_read_cap_bytes=40 * prep.MIB, opaque_io_reservation_bytes=prep.MIB,
             preparation_reservation_bytes=40 * prep.MIB,
             charged_prior_global_bytes=4_124_617_258)
    p.update(updates)
    return source, p, tmp_path / "prepared"

def pin(tmp_path, p):
    path = tmp_path / "synthetic-protocol.json"
    path.write_text(json.dumps(p, sort_keys=True))
    return path, hashlib.sha256(path.read_bytes()).hexdigest()

def run_case(tmp_path, source, p, out):
    path, digest = pin(tmp_path, p)
    return prep.prepare_released_caller(source, out, path, digest)

@pytest.fixture
def local_tools(monkeypatch):
    """Actual local HTS tools; native decisions are an explicit synthetic API stub."""
    pysam = pytest.importorskip("pysam")
    import pysam.bcftools as bcftools
    calls = []
    class NativeRow:
        def __init__(self, record): self.record = record
        def __str__(self): return str(self.record)
        def is_filtered(self): return self.record.info[prep.TAGS[0]] == 3
        def is_present(self, sample, allow_missing=False):
            calls.append((sample, allow_missing))
            return self.record.info[prep.TAGS[0]] != 3
    class NativeReader:
        def __init__(self, path): self.reader = pysam.VariantFile(path)
        def __enter__(self): return self
        def __exit__(self, *args): self.reader.close()
        def __iter__(self): return (NativeRow(rec) for rec in self.reader)
    truvari_stub = SimpleNamespace(VariantFile=NativeReader)
    versions = {"test_only": "local HTS tools with synthetic native API; not pinned end-to-end"}
    monkeypatch.setattr(prep, "_runtime", lambda: (pysam, bcftools, truvari_stub, versions))
    return pysam, bcftools, calls

def test_full_local_standard_tool_control_with_synthetic_native_api(tmp_path, local_tools):
    source, p, out = case(tmp_path)
    report = run_case(tmp_path, source, p, out)
    pysam, _, calls = local_tools
    assert report["status"] == "complete" and report["runtime"]["test_only"]
    assert report["counts"]["source_records"] == 3 and report["counts"]["children"] == 4
    assert (report["counts"]["pos_zero"], report["counts"]["pos_length_plus_one"]) == (1, 1)
    assert report["native_counts"] == dict(records=4, kept=3, filtered=1, not_present=1, both=1, dot_kept=1)
    assert calls == [(0, True)] * 4
    with pysam.VariantFile(str(out / "released.vcf.gz")) as reader:
        assert list(reader.header.samples) == ["SYNTH"]
        rows = list(reader)
    pairs = [(r.info[prep.TAGS[0]], prep._one(r.info[prep.TAGS[1]])) for r in rows]
    assert set(pairs) == {(1, 1), (1, 2), (2, 1), (3, 1)}
    assert len({r.id for r in rows}) == 4
    assert all(r.id == prep.child_identity(p["source_sha256"], *pair) for r, pair in zip(rows, pairs))
    assert [r.pos for r in rows] == [0, 5000, 5000, 10001]
    at = {pair: row for pair, row in zip(pairs, rows)}
    assert at[(1, 1)].alts == at[(1, 2)].alts == ("AA",)
    assert (at[(1, 1)].samples[0]["GT"], at[(1, 2)].samples[0]["GT"]) == ((1, None), (None, 1))
    assert (at[(1, 1)].samples[0]["PL"], at[(1, 2)].samples[0]["PL"]) == ((0, 10, 20), (0, 30, 50))
    assert at[(1, 1)].info[prep.TAGS[2]] == at[(2, 1)].info[prep.TAGS[2]] == "duplicate"
    assert at[(3, 1)].info[prep.TAGS[2]] == "%2E"
    assert report["identity_fingerprint"] == report["counts"]["source_alt_identity_fingerprint"]
    assert report["retained_rows"]["records"] == 3
    assert "not measured" in report["accounting_limitation"]
    for item in report["outputs"].values():
        assert hashlib.sha256(Path(item["path"]).read_bytes()).hexdigest() == item["sha256"]

@pytest.mark.parametrize("update,match", [
    ({"caller_preparation_approved": 1}, "approval"),
    ({"expected_sample_label": ""}, "sample"),
    ({"source_sha256": "a" * 63}, "SHA"),
    ({"runtime": {}}, "runtime"),
    ({"max_source_bytes": 4 * prep.GIB + 1}, "integer"),
    ({"preparation_reservation_bytes": prep.GIB, "charged_prior_global_bytes": 64 * prep.GIB}, "64 GiB"),
])
def test_protocol_gates_before_runtime_or_parse(tmp_path, monkeypatch, update, match):
    source, p, out = case(tmp_path, **update)
    monkeypatch.setattr(prep, "_runtime", lambda: pytest.fail("runtime reached after rejected protocol"))
    with pytest.raises(ValueError, match=match): run_case(tmp_path, source, p, out)
    assert not out.exists()

def test_exact_protocol_hash_and_per_file_caps(tmp_path):
    _, p, _ = case(tmp_path)
    path, digest = pin(tmp_path, p)
    with pytest.raises(ValueError, match="protocol size or SHA"):
        prep._protocol(path, "0" * 64)
    p["output_caps"]["split"] = 4 * prep.GIB + 1
    path, digest = pin(tmp_path, p)
    with pytest.raises(ValueError, match="integer"): prep._protocol(path, digest)

@pytest.mark.parametrize("kind", ["hash", "size", "sample"])
def test_actual_input_pins_fail_without_output_acceptance(tmp_path, local_tools, kind):
    source, p, out = case(tmp_path)
    if kind == "hash": p["source_sha256"] = "f" * 64
    if kind == "size": p["source_bytes"] += 1
    if kind == "sample": p["expected_sample_label"] = "OTHER"
    with pytest.raises(prep.CallerPreparationError) as exc: run_case(tmp_path, source, p, out)
    report = json.loads(exc.value.report_path.read_text())
    assert report["status"] == "incomplete" and report["counts"]["source_records"] == 0
    assert not (out / "caller_preparation_report.json").exists()

def test_fresh_output_and_git_exclusion(tmp_path):
    existing = tmp_path / "existing"; existing.mkdir()
    with pytest.raises(ValueError, match="fresh"): prep._fresh(existing)
    git = tmp_path / "repo"; git.mkdir(); (git / ".git").write_text("gitdir: synthetic")
    with pytest.raises(ValueError, match="outside Git"): prep._fresh(git / "out")
    target = tmp_path / "target"; target.mkdir()
    link = tmp_path / "link"; link.symlink_to(target)
    with pytest.raises(ValueError, match="fresh"): prep._fresh(link)

def test_streaming_byte_hash_line_and_plaintext_limits(tmp_path):
    path = tmp_path / "synthetic.bytes"
    path.write_bytes(b"abcd\n")
    assert prep._hash(path, 5, 5)[:2] == (hashlib.sha256(b"abcd\n").hexdigest(), 5)
    with pytest.raises(ValueError, match="line cap"): prep._hash(path, 5, 4)
    with pytest.raises(ValueError, match="input size"): prep._hash(path, 4)
    path.write_bytes(b"\x1f\x8bsynthetic")
    with pytest.raises(ValueError, match="plaintext"): prep._hash(path, 100, 100)

def test_identity_uses_source_sha_ordinal_and_alt_not_duplicate_id():
    values = {prep.child_identity(sha, ordinal, alt) for sha in ("a" * 64, "b" * 64)
              for ordinal in (1, 2) for alt in (1, 2)}
    assert len(values) == 8 and all(len(v) == 64 for v in values)
    assert prep.child_identity("a" * 64, 2, 1) == hashlib.sha256(("a" * 64 + "|2|1").encode()).hexdigest()

def test_whole_row_fingerprint_checks_all_columns_order_and_multiplicity():
    rows = [ROWS.splitlines()[0], ROWS.splitlines()[1]]
    def fingerprint(values):
        fp = prep._Fingerprint()
        for value in values: fp.add(value)
        return fp.result()
    assert fingerprint(rows) == fingerprint(reversed(rows))
    assert fingerprint(rows + rows[:1]) != fingerprint(rows)
    for column in range(10):
        fields = rows[0].split("\t"); fields[column] += "changed"
        assert fingerprint(["\t".join(fields), rows[1]]) != fingerprint(rows)

@pytest.mark.parametrize("left,right", [( ["a"], []), ([], ["a"]), (["a"], ["a", "b"]), (["sameID\tGT01"], ["sameID\tGT11"])])
def test_paired_reader_rejects_tail_or_any_whole_row_change(left, right):
    with pytest.raises(ValueError, match="paired reader"): list(prep._paired_records(left, right))
    assert list(prep._paired_records(["a"], ["a"])) == [("a", "a")]

@pytest.mark.parametrize("mode", ["drop", "duplicate_alt_identity", "info", "gt"])
def test_production_norm_invariants_reject_corruption(tmp_path, local_tools, monkeypatch, mode):
    source, p, out = case(tmp_path)
    pysam, bcftools, _ = local_tools
    def corrupt_norm(*args, **kwargs):
        bcftools.norm(*args, **kwargs)
        path = Path(args[args.index("-o") + 1])
        lines = path.read_text().splitlines(True)
        body = [i for i, line in enumerate(lines) if not line.startswith("#")]
        if mode == "drop": del lines[body[-1]]
        if mode == "duplicate_alt_identity": lines = [row.replace("CTRL_ALTIDX=2", "CTRL_ALTIDX=1") for row in lines]
        if mode == "info": lines = [row.replace("DP=10", "DP=999") for row in lines]
        if mode == "gt": lines = [row.replace("1|.", "1|0") for row in lines]
        path.write_text("".join(lines))
    runtime = prep._runtime()
    monkeypatch.setattr(prep, "_runtime", lambda: (pysam, SimpleNamespace(norm=corrupt_norm), runtime[2], runtime[3]))
    with pytest.raises(prep.CallerPreparationError, match="norm"): run_case(tmp_path, source, p, out)
    report = json.loads((out / "caller_preparation_failure.json").read_text())
    assert report["failed_phase"] == "norm" and report["partial_files_preserved"]

@pytest.mark.parametrize("phase", ["sort", "native"])
def test_production_retained_full_row_checks(tmp_path, local_tools, monkeypatch, phase):
    source, p, out = case(tmp_path)
    pysam, bcftools, _ = local_tools
    def change_qual(path):
        lines = path.read_text().splitlines(True)
        index = next(i for i, row in enumerate(lines) if not row.startswith("#"))
        fields = lines[index].rstrip("\n").split("\t"); fields[5] = "17"
        lines[index] = "\t".join(fields) + "\n"; path.write_text("".join(lines))
    if phase == "sort":
        runtime = prep._runtime()
        def bad_sort(*args, **kwargs):
            bcftools.sort(*args, **kwargs); change_qual(Path(args[args.index("-o") + 1]))
        monkeypatch.setattr(prep, "_runtime", lambda: (pysam, SimpleNamespace(norm=bcftools.norm, sort=bad_sort), runtime[2], runtime[3]))
    else:
        native = prep._native
        def bad_native(*args):
            result = native(*args); change_qual(args[1]); return result
        monkeypatch.setattr(prep, "_native", bad_native)
    with pytest.raises(prep.CallerPreparationError, match="rows|multiset"): run_case(tmp_path, source, p, out)

def test_failed_output_cap_preserves_partial_hash_and_identity_census(tmp_path, local_tools):
    source, p, out = case(tmp_path)
    p["output_caps"]["annotated"] = 16
    with pytest.raises(prep.CallerPreparationError, match="storage cap") as exc: run_case(tmp_path, source, p, out)
    report = json.loads(exc.value.report_path.read_text())
    assert report["counts"]["source_records"] == 3
    assert report["counts"]["source_alt_identity_fingerprint"]["records"] == 4
    assert report["source_verified_sha256"] == p["source_sha256"]
    assert (out / "annotated.vcf").exists() and report["partial_files_preserved"]
    assert report["reserved_charge_bytes"] == p["preparation_reservation_bytes"]

@pytest.mark.parametrize("tag", ["DP", "END"])
def test_missing_header_declaration_fails_without_repair(tmp_path, local_tools, tag):
    raw = (HEADER + ROWS).replace('##INFO=<ID=DP,Number=1,Type=Integer,Description="Synthetic">\n', "") if tag == "DP" else (HEADER + ROWS).replace("DP=10;", "DP=10;END=5020;")
    source, p, out = case(tmp_path, raw)
    with pytest.raises(prep.CallerPreparationError, match="undeclared"): run_case(tmp_path, source, p, out)

@pytest.mark.parametrize("endpoint,corruption", [(5020, "change"), (5000, "remove")])
def test_reserved_end_and_flag_are_preserved_and_checked(tmp_path, local_tools, monkeypatch, endpoint, corruption):
    extra = ('##INFO=<ID=END,Number=1,Type=Integer,Description="Synthetic">\n'
             '##INFO=<ID=IMPRECISE,Number=0,Type=Flag,Description="Synthetic">\n')
    raw = (HEADER.replace("#CHROM", extra + "#CHROM") + ROWS).replace("DP=10;", f"DP=10;END={endpoint};IMPRECISE;")
    if endpoint == 5000: raw = raw.replace("AA,AA", "<INS>,<INS>")
    source, p, out = case(tmp_path, raw)
    report = run_case(tmp_path, source, p, out)
    assert report["status"] == "complete"
    pysam, bcftools, _ = local_tools
    with pysam.VariantFile(str(out / "released.vcf.gz")) as reader:
        rows = [r for r in reader if r.info[prep.TAGS[0]] == 1]
        assert [r.stop for r in rows] == [endpoint, endpoint]
        assert all(f"END={endpoint}" in str(r).split("\t")[7].split(";") for r in rows)
        assert all(r.info["IMPRECISE"] is True for r in rows)
    assert "independently of stop" in report["norm_end_validation"]
    runtime = prep._runtime()
    def corrupt_end(*args, **kwargs):
        bcftools.norm(*args, **kwargs)
        path = Path(args[args.index("-o") + 1])
        with pysam.VariantFile(str(path)) as reader:
            before = [r.stop for r in reader]
        old, new = (f"END={endpoint};", "") if corruption == "remove" else (f"END={endpoint}", f"END={endpoint + 1}")
        path.write_text(path.read_text().replace(old, new))
        if corruption == "remove":
            with pysam.VariantFile(str(path)) as reader:
                assert [r.stop for r in reader] == before
    monkeypatch.setattr(prep, "_runtime", lambda: (pysam, SimpleNamespace(norm=corrupt_end), runtime[2], runtime[3]))
    with pytest.raises(prep.CallerPreparationError, match="whole-field"): run_case(tmp_path, source, p, tmp_path / "corrupted")

def test_nonsymbolic_redundant_end_fingerprinted_before_writer_normalization(tmp_path, local_tools):
    extra = '##INFO=<ID=END,Number=1,Type=Integer,Description="Synthetic">\n'
    raw = (HEADER.replace("#CHROM", extra + "#CHROM") + ROWS).replace("DP=10;", "DP=10;END=5000;")
    source, p, out = case(tmp_path, raw)
    pysam, _, _ = local_tools
    without = tmp_path / "synthetic-without-end.vcf"
    without.write_text(raw.replace("END=5000;", ""))
    with pysam.VariantFile(str(source)) as reader, pysam.VariantFile(str(without)) as no_end:
        before, after = next(reader), next(no_end)
        assert before.stop == after.stop == 5000
        assert prep._semantic_child(before, 1) != prep._semantic_child(after, 1)
    # Local standard writing removes this redundant nonsymbolic END: fail closed.
    with pytest.raises(prep.CallerPreparationError, match="whole-field"):
        run_case(tmp_path, source, p, out)

@pytest.mark.parametrize("end_tokens", ["END=5000;END=5000", "END=5000,5001"])
def test_serialized_duplicate_or_nonscalar_end_fails_bounded(tmp_path, local_tools, end_tokens):
    extra = '##INFO=<ID=END,Number=1,Type=Integer,Description="Synthetic">\n'
    raw = (HEADER.replace("#CHROM", extra + "#CHROM") + ROWS).replace("DP=10;", f"DP=10;{end_tokens};")
    source, p, out = case(tmp_path, raw)
    with pytest.raises(prep.CallerPreparationError, match="duplicate or malformed serialized INFO/END"):
        run_case(tmp_path, source, p, out)

@pytest.mark.parametrize("replacement,match", [("10002", "contig length"), ("polyploid", "Number=G")])
def test_unsupported_coordinate_or_projection_fails_bounded(tmp_path, local_tools, replacement, match):
    raw = HEADER + ROWS
    raw = raw.replace("10001", replacement) if replacement != "polyploid" else raw.replace("1|2:", "1|2|2:")
    source, p, out = case(tmp_path, raw)
    with pytest.raises(prep.CallerPreparationError, match=match): run_case(tmp_path, source, p, out)

def test_pinned_cluster_end_to_end_synthetic(tmp_path):
    if not importlib.util.find_spec("truvari"):
        pytest.skip(f"pinned end-to-end requires Truvari 5.4.0; absent locally (Python {sys.version.split()[0]})")
    try: prep._runtime()
    except (ImportError, ValueError) as exc: pytest.skip(f"pinned cluster end-to-end unavailable: {exc}")
    source, p, out = case(tmp_path)
    report = run_case(tmp_path, source, p, out)
    assert report["runtime"] == prep.RUNTIME and report["status"] == "complete"
    assert report["counts"]["children"] == 4 and report["native_counts"]["kept"] == 3
