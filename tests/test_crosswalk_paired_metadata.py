import pytest

from analysis.crosswalk_paired_metadata import crosswalk, read_dna


def rna_row(run, title, alias="LCLs-9"):
    return {"run_accession": run, "sample_title": title, "sample_alias": alias,
            "sample_accession": "SAMEA1", "secondary_sample_accession": "ERS1",
            "library_strategy": "OTHER"}


def test_exact_title_join_preserves_runs_and_unresolved_aliases():
    rows = [rna_row("ERR1", "HG00098"), rna_row("ERR2", "HG00098"),
            rna_row("ERR3", "LCLs-9")]
    dna = {"HG00098": [{"sample": "HG00098", "mode": "hg38", "path": "x", "bytes": 3, "md5": "x"}]}
    result = crosswalk(rows, dna, {"HG00098", "HG99999"})
    assert result["rna_runs"] == 3
    assert result["distinct_matching_format_titles"] == 1
    assert result["dna_matching_rna_titles"] == 1
    assert len(result["rows"][0]["rna_runs"]) == 2
    assert result["unresolved_rna_rows"][0]["run"] == "ERR3"
    assert result["author_list_not_in_rna_titles"] == ["HG99999"]


def test_duplicate_run_is_rejected():
    with pytest.raises(ValueError, match="duplicate RNA run"):
        crosswalk([rna_row("ERR1", "HG00098"), rna_row("ERR1", "HG00099")], {}, set())


def test_dna_manifest_excludes_indices_and_reports_conflicts(tmp_path):
    first, second = tmp_path / "a.tsv", tmp_path / "b.tsv"
    first.write_text("1KG/hg38/HG00098.hg38.cram\t3\taaa\n"
                     "1KG/hg38/HG00098.hg38.cram.crai\t1\tbbb\n")
    second.write_text("1KG/hg38/HG00098.hg38.cram\t4\tccc\n")
    groups, conflicts = read_dna([first, second])
    assert list(groups) == ["HG00098"]
    assert len(groups["HG00098"]) == 1
    assert len(conflicts) == 1
