import json
import pytest
from analysis.hg002_cds_overlap_cohort import build_manifest, main

GTF = """chr1\ttest\tCDS\t101\t200\t.\t+\t0\tgene_id "g1"; transcript_id "t1"; gene_name "G"; gene_type "protein_coding";
chr1\ttest\tCDS\t151\t250\t.\t+\t0\tgene_id "g1"; transcript_id "t2"; gene_name "G"; gene_type "protein_coding";
"""
HEADER = "##fileformat=VCFv4.2\n#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tHG002\n"

def record(pos, alt, info=".", gt="0|1:12", filt="PASS", ref="N", fmt="GT:PS", ident="v"):
    return f"chr1\t{pos}\t{ident}\t{ref}\t{alt}\t.\t{filt}\t{info}\t{fmt}\t{gt}\n"

def run(tmp_path, body, counters=None, gtf_text=GTF, sample="HG002", header=HEADER):
    gtf, vcf = tmp_path/"tiny.gtf", tmp_path/"tiny.vcf"
    gtf.write_text(gtf_text); vcf.write_text(header+body)
    return build_manifest(vcf, gtf, sample, counters)

def test_literal_deletion_all_isoforms(tmp_path):
    row, = run(tmp_path, record(150, "N", "SVTYPE=DEL;END=200;SVLEN=-50", ref="N"+"A"*50))
    assert (row["start0"], row["end0"], row["size_bp"]) == (150, 200, 50)
    assert row["transcripts"] == ["t1", "t2"]
    assert (row["candidate_state"], row["p1_state"], row["overlap_status"]) == ("CANDIDATE", "NOT_ASSESSED", "OVERLAPS_CDS")

@pytest.mark.parametrize("pos,prefix,boundary,tx", [(100, True, 100, ["t1"]), (200, True, 200, ["t1","t2"]), (251, False, 250, ["t2"])])
def test_insertion_boundaries_and_suffix_only(tmp_path, pos, prefix, boundary, tx):
    alt = "A"+"C"*50 if prefix else "C"*50+"A"
    row, = run(tmp_path, record(pos, alt, ref="A"))
    assert (row["insertion_boundary0"], row["size_bp"], row["transcripts"]) == (boundary, 50, tx)

@pytest.mark.parametrize("pos,expected", [(50, "OUTSIDE_CDS"), (100, "OVERLAPS_CDS"), (250, "OUTSIDE_CDS")])
def test_del_anchor_and_half_open_edges(tmp_path, pos, expected):
    row, = run(tmp_path, record(pos, "N", ref="N"+"A"*50))
    assert (row["start0"], row["end0"], row["overlap_status"]) == (pos, pos+50, expected)

def test_duplicates_filters_symbolic_and_phase_metadata(tmp_path):
    body = record(150, "<DEL>", "END=200;SVLEN=-50")
    body += record(150, "<DEL>", "END=200;SVLEN=-50", filt="LowQual", ident="v2")
    row, = run(tmp_path, body)
    assert len(row["source_records"]) == 2 and row["candidate_state"] == "UNKNOWN"
    assert [r["FILTER"] for r in row["source_records"]] == ["PASS", "LowQual"]
    assert row["source_records"][0]["GT"] == "0|1" and row["source_records"][0]["phase"] == {"PS":"12"}
    assert row["overlap_status"] == "OVERLAPS_CDS" and "symbolic_allele_sequence_unavailable" in row["unknown_reasons"]

@pytest.mark.parametrize("gt,fmt,reason", [(".", "PS", "missing_GT"), ("0/1:.", "GT:PS", "unphased_GT"),
    ("0|1:.", "GT:PS", "missing_phase_block"), ("0|2:12", "GT:PS", "partial_or_invalid_GT"),
    ("0|.:12", "GT:PS", "partial_or_invalid_GT")])
def test_uncertain_genotypes(tmp_path, gt, fmt, reason):
    row, = run(tmp_path, record(100, "A"+"C"*50, gt=gt, fmt=fmt, ref="A"))
    assert row["candidate_state"] == "UNKNOWN" and reason in row["unknown_reasons"]
    if reason in ("missing_GT", "partial_or_invalid_GT"):
        assert row["source_records"][0]["alt_copy_count"] is None
        assert row["source_records"][0]["phase_status"] == "UNKNOWN"

def test_missing_gene_identity(tmp_path):
    row, = run(tmp_path, record(100, "A"+"C"*50, ref="A"), gtf_text=GTF.replace('transcript_id "t1"; ', ""))
    assert "gene_biotype_unknown" in row["unknown_reasons"]

def test_missing_representation_event_level_unknown(tmp_path):
    row, = run(tmp_path, record(150, ".", "SVTYPE=DEL"))
    assert row["gene_id"] is None and row["overlap_status"] == "UNKNOWN"
    assert row["candidate_state"] == "UNKNOWN" and "missing_coordinates_and_size" in row["unknown_reasons"]

@pytest.mark.parametrize("alt,info", [("<INS>", "SVLEN=49"), ("<DEL>", "END=199;SVLEN=-49"), ("<DEL>", "END=199")])
def test_known_small_symbolic_excluded(tmp_path, alt, info):
    counts = {}
    assert run(tmp_path, record(150, alt, info), counts) == []
    assert counts["out_of_primary_known_small"] == 1

@pytest.mark.parametrize("alt,info,reason", [("<DEL>", "END=199;SVLEN=-60", "END_SVLEN_disagreement"),
    ("<DEL>", "END=200;END=200;SVLEN=-50", "END_duplicate_key"),
    ("<INS>", "SVLEN=50,60", "SVLEN_ambiguous_cardinality"),
    ("<DEL>", "END=bad;SVLEN=-50", "END_unparseable"),
    (".", "SVTYPE=DEL;SVTYPE=INS", "SVTYPE_duplicate_key"),
    ("<DEL>", "SVTYPE=INS;END=200;SVLEN=-50", "SVTYPE_ALT_disagreement"),
    ("N", "END=199;SVLEN=-50", "END_disagrees_with_sequence")])
def test_info_ambiguity_retained_without_confident_geometry(tmp_path, alt, info, reason):
    row, = run(tmp_path, record(150, alt, info, ref="N"+"A"*50 if alt=="N" else "N"))
    assert row["gene_id"] is None and row["overlap_status"] == "UNKNOWN"
    assert all(row[k] is None for k in ("start0", "end0", "insertion_boundary0", "size_bp"))
    assert reason in row["unknown_reasons"] and row["source_records"][0]["INFO_raw"] == info

def test_multiple_alts_and_genes(tmp_path):
    gtf = GTF + GTF.splitlines()[0].replace('gene_id "g1"', 'gene_id "g2"')+"\n"
    rows = run(tmp_path, record(150, "<DEL>,<INS>", "SVLEN=-50,60;END=200,150", gt="1|2:12"), gtf_text=gtf)
    assert len(rows) == 4 and {r["svtype"] for r in rows} == {"DEL", "INS"}
    assert all(r["source_records"][0]["alt_copy_count"] == 1 for r in rows)

def test_declared_info_cardinality(tmp_path):
    header = '##INFO=<ID=SVLEN,Number=A,Type=Integer,Description="Size">\n'+HEADER
    rows = run(tmp_path, record(150, "<DEL>,<INS>", "SVLEN=60", gt="1|2:12"), header=header)
    assert len(rows) == 2 and all(r["overlap_status"] == "UNKNOWN" for r in rows)
    assert all("SVLEN_ambiguous_cardinality" in r["unknown_reasons"] for r in rows)

def test_outside_rows_and_out_of_primary_counts(tmp_path):
    counts = {}; body = record(400, "A"+"C"*50, ref="A")
    body += record(150, "<DUP>", "SVLEN=60")+record(150, "<INS>", "SVLEN=60", gt="0|0:12")
    row, = run(tmp_path, body, counts)
    assert row["overlap_status"] == "OUTSIDE_CDS" and row["candidate_state"] == "OUTSIDE_PRIMARY"
    assert row["index_role"] == "PRELIMINARY_EVENT_GENE_ALT" and row["p1_state"] == "NOT_ASSESSED"
    assert counts["out_of_primary_outside_CDS"] == counts["out_of_primary_other_type"] == counts["out_of_primary_uncalled_ALT"] == 1

def test_contig_compatibility_and_empty_vcf(tmp_path):
    with pytest.raises(ValueError, match="share no contigs"):
        run(tmp_path, record(150, "<DEL>", "END=200").replace("chr1", "1"))
    assert run(tmp_path, "") == []
    rows = run(tmp_path, record(150, "<DEL>", "END=200")+record(150, "<DEL>", "END=200").replace("chr1", "chr2"))
    assert next(r for r in rows if r["chrom"]=="chr2")["overlap_status"] == "UNKNOWN"

def test_exact_sample_policy(tmp_path):
    header = HEADER.replace("HG002", "HG002_WGS")
    with pytest.raises(ValueError, match="Explicit sample"): run(tmp_path, "", header=header)
    assert run(tmp_path, "", sample="HG002_WGS", header=header) == []

def test_cli_exclusive_output_and_summary(tmp_path, monkeypatch):
    run(tmp_path, record(100, "A"+"C"*50, ref="A"))
    output = tmp_path/"index.jsonl"
    monkeypatch.setattr("sys.argv", ["cohort", "--vcf", str(tmp_path/"tiny.vcf"), "--gtf", str(tmp_path/"tiny.gtf"),
        "--sample", "HG002", "--output", str(output)])
    main(); saved = output.read_text(); summary = json.loads(saved.splitlines()[0])
    assert summary["final_D"] is None and summary["counters"]["index_rows"] == 1
    with pytest.raises(FileExistsError): main()
    assert output.read_text() == saved
