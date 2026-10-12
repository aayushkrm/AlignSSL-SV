from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from analysis import compare_inv_declared_paths as inv


def _record(position: int, end: int, *, record_id: str, genotype: str, filt: str = "PASS", support: int = 5) -> dict:
    info = f"END={end};SUPPORT={support};REPEAT_FLANK=tagged"
    fields = [
        "chr2",
        str(position),
        record_id,
        "N",
        "<INV>",
        ".",
        filt,
        info,
        "GT:DV:DR",
        f"{genotype}:3:7",
    ]
    return {
        "line_number": 100 + support,
        "raw_record": "\t".join(fields),
        "fields": fields,
        "chromosome": "chr2",
        "position": position,
        "id": record_id,
        "ref": "N",
        "alt": "<INV>",
        "qual": ".",
        "filter": filt,
        "info": info,
        "end_field_values": [str(end)],
        "end_positions": [end],
        "mate_endpoints": [],
        "format_and_samples": fields[8:],
    }


def _manifest_and_reference() -> tuple[dict, dict]:
    expected_paths = inv._expected_source_paths()
    all_sources: list[dict] = []
    for group in (inv.CALL_GROUP, inv.CONTROL_GROUP, inv.TRUTH_GROUP):
        for index, path in enumerate(sorted(expected_paths[group])):
            blob = hashlib.sha1(path.encode()).hexdigest()
            source = {
                "group": group,
                "path": path,
                "raw_url": inv.RAW_FILE_BASE + path,
                "size": 1,
                "downloaded_bytes": 1,
                "download_status": "VALIDATED",
                "http_status": 200,
                "sha256": hashlib.sha256(path.encode()).hexdigest(),
                "git_blob_sha1": blob,
                "git_blob_sha1_computed": blob,
                "git_blob_sha1_verified": True,
                "vcf_summary": {
                    "relevant_headers": [
                        "##contig=<ID=chr2,length=242193529>",
                        "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tHG002",
                    ],
                    "nearby_records": [],
                    "spanning_records": [],
                },
            }
            all_sources.append(source)

    caller_by_path = {source["path"]: source for source in all_sources if source["group"] == inv.CALL_GROUP}
    near_path = inv.CALLER_DIRECTORY + "inv_severus_ont_minimap2.vcf"
    span_paths = [
        inv.CALLER_DIRECTORY + "inv_severus_ont_vacmap.vcf",
        inv.CALLER_DIRECTORY + "inv_severus_pb_vacmap.vcf",
        inv.CALLER_DIRECTORY + "inv_sniffles2_ont_vacmap.vcf",
        inv.CALLER_DIRECTORY + "inv_sniffles2_pb_vacmap.vcf",
    ]
    caller_by_path[near_path]["vcf_summary"]["nearby_records"].append(
        _record(inv.TARGET_POS, inv.TARGET_END, record_id="near-0", genotype="0/0", filt="LowQual", support=10)
    )
    span_genotypes = ["0/0", "0/1", "1/1", "0/1", "./.", "0/1", "1/0", "0/0"]
    for index, genotype in enumerate(span_genotypes):
        path = span_paths[index % len(span_paths)]
        delta = 0 if index == 0 else index
        caller_by_path[path]["vcf_summary"]["spanning_records"].append(
            _record(
                inv.TARGET_POS + delta,
                inv.TARGET_END + delta,
                record_id=f"span-{index}",
                genotype=genotype,
                filt="PASS" if index else "LowQual",
                support=20 + index,
            )
        )

    tier1_path = next(path for path in expected_paths[inv.TRUTH_GROUP] if path.endswith("merged.vcf_Tier1.vcf.gz"))
    merged_path = next(path for path in expected_paths[inv.TRUTH_GROUP] if path.endswith("merged.vcf.gz"))
    truth = _record(inv.TARGET_POS, inv.TARGET_END, record_id="fixed-truth", genotype="0/1", support=99)
    for path in (tier1_path, merged_path):
        source = next(entry for entry in all_sources if entry["path"] == path)
        source["vcf_summary"]["nearby_records"].append(copy.deepcopy(truth))

    total_size = sum(source["size"] for source in all_sources)
    manifest = {
        "schema_version": 1,
        "status": "COMPLETE",
        "case": {
            "chromosome": "chr2",
            "start": inv.TARGET_POS,
            "end": inv.TARGET_END,
            "reported_length_bp": inv.TARGET_LENGTH,
            "supplement_label": "GRCh38/hg38",
            "coordinate_build_status": "UNKNOWN_PENDING_INDEPENDENT_HEADER_AND_RECORD_REVIEW",
            "coordinate_convention_status": "UNKNOWN; coordinates are used verbatim without conversion",
        },
        "provenance": {
            "repository": inv.REPOSITORY,
            "commit": inv.PINNED_COMMIT,
            "tree_url": inv.TREE_URL,
            "tree_entry_count_expected": inv.TREE_ENTRY_COUNT,
            "raw_file_base": inv.RAW_FILE_BASE,
            "source_directory": "/temporary/source-cache",
        },
        "retrieval": {
            "tree_truncated": False,
            "tree_entries": inv.TREE_ENTRY_COUNT,
            "source_bytes_transferred": total_size,
            "declared_source_bytes": total_size,
            "whole_source_set_sha256": hashlib.sha256(b"fixture sources").hexdigest(),
        },
        "sources": all_sources,
    }
    reference = {
        "genome": "hg38",
        "chrom": "chr2",
        "start": inv.REFERENCE_START,
        "end": inv.REFERENCE_END,
        "dna": ("AAACCGT" * ((inv.REFERENCE_LENGTH // 7) + 1))[: inv.REFERENCE_LENGTH],
    }
    return manifest, reference


def _build(manifest: dict | None = None, reference: dict | None = None) -> dict:
    default_manifest, default_reference = _manifest_and_reference()
    return inv.build_diagnostic(
        manifest if manifest is not None else default_manifest,
        reference if reference is not None else default_reference,
        manifest_sha256=hashlib.sha256(b"synthetic manifest").hexdigest(),
        reference_json_sha256=hashlib.sha256(b"synthetic reference").hexdigest(),
    )


def _set_first_call_alt(manifest: dict, alt: str) -> None:
    source = next(
        item
        for item in manifest["sources"]
        if item["path"].endswith("inv_severus_ont_minimap2.vcf")
    )
    row = source["vcf_summary"]["nearby_records"][0]
    row["fields"][4] = alt
    row["alt"] = alt
    row["raw_record"] = "\t".join(row["fields"])


def test_reference_guards_metadata_length_and_unambiguous_bases() -> None:
    _, reference = _manifest_and_reference()
    normalized, metadata = inv.validate_reference_document(reference)
    assert len(normalized) == 29000
    assert metadata["original_caller_fasta_identity"] == "UNKNOWN"

    mixed_case = dict(reference, dna="a" + reference["dna"][1:])
    _, mixed_metadata = inv.validate_reference_document(mixed_case)
    assert mixed_metadata["case_counts"] == {"uppercase_bases": 28999, "lowercase_bases": 1}

    invalid_documents = [
        dict(reference, genome="GRCh38"),
        dict(reference, chrom="2"),
        dict(reference, start=inv.REFERENCE_START + 1),
        dict(reference, end=inv.REFERENCE_END - 1),
        dict(reference, dna=reference["dna"][:-1]),
        dict(reference, dna="N" + reference["dna"][1:]),
        dict(reference, dna="X" + reference["dna"][1:]),
    ]
    for document in invalid_documents:
        with pytest.raises(inv.DiagnosticError):
            inv.validate_reference_document(document)


def test_reference_json_byte_cap_is_enforced(tmp_path: Path) -> None:
    with pytest.raises(inv.DiagnosticError, match="128 KiB"):
        inv.build_from_json_bytes(b"{}", b" " * (inv.REFERENCE_JSON_MAX_BYTES + 1))

    too_large = tmp_path / "oversized-reference-fixture.json"
    too_large.write_bytes(b"x" * (inv.REFERENCE_JSON_MAX_BYTES + 1))
    with pytest.raises(inv.DiagnosticError, match="cap"):
        inv.read_bounded_file(too_large, inv.REFERENCE_JSON_MAX_BYTES)


def test_coordinate_modes_preserve_declared_span_without_relabeling() -> None:
    pos, end = inv.TARGET_POS, inv.TARGET_END
    assert inv.interval_for_mode(pos, end, "A") == (pos, end)
    assert inv.interval_for_mode(pos, end, "B") == (pos - 1, end - 1)
    with pytest.raises(inv.DiagnosticError):
        inv.interval_for_mode(pos, pos, "A")
    with pytest.raises(inv.DiagnosticError):
        inv.interval_for_mode(pos + 1, pos, "B")
    with pytest.raises(inv.DiagnosticError):
        inv.interval_for_mode(1, 2, "B")
    with pytest.raises(inv.DiagnosticError):
        inv.interval_for_mode(pos, end, "best")


def test_equivalent_center_inversion_and_expanded_inversion_fixture() -> None:
    context = "AC" + "TTGC" + "GT"
    center = inv.invert_interval_in_context(context, 0, 2, 6)
    expanded = inv.invert_interval_in_context(context, 0, 0, 8)
    assert center == expanded


def test_altered_flank_breaks_the_exact_expanded_inversion_equivalence() -> None:
    context = "AC" + "TTGC" + "GA"
    center = inv.invert_interval_in_context(context, 0, 2, 6)
    expanded = inv.invert_interval_in_context(context, 0, 0, 8)
    metrics = inv.compare_full_contexts(context, center, expanded)
    assert not metrics["exact_string_equal"]
    assert metrics["mismatched_positions"] > 0
    assert not metrics["equivalence_claim_eligible"]


def test_palindromic_no_change_is_equal_but_not_an_eligible_rescue() -> None:
    reference = "ATGCAT"
    assert inv.invert_interval_in_context(reference, 0, 0, len(reference)) == reference
    metrics = inv.compare_full_contexts(reference, reference, reference)
    assert metrics["exact_string_equal"]
    assert metrics["truth_alternate_equals_reference"]
    assert metrics["call_alternate_equals_reference"]
    assert not metrics["equivalence_claim_eligible"]


def test_manifest_provenance_pin_and_all_36_mode_comparisons() -> None:
    result = _build()
    assert result["call_record_count"] == 9
    assert result["comparison_count"] == 36
    assert result["provenance_pin"]["source_count"] == 25
    assert result["provenance_pin"]["chr2_declared_length_bp_all_sources"] == 242193529
    assert result["provenance_pin"]["original_caller_fasta_identity"] == "UNKNOWN"
    assert result["truth"]["merged_duplicate_verified"] is True
    assert result["truth"]["merged_duplicate"]["source"]["path"].endswith("merged.vcf.gz")
    assert {item["mode_pair_key"] for item in result["comparisons"]} == set(inv.MODE_PAIR_KEYS)
    assert all(sum(item["call_record_key"] == call["record_key"] for item in result["comparisons"]) == 4 for call in result["call_records"])
    assert result["inputs"]["manifest_json_sha256"] == hashlib.sha256(b"synthetic manifest").hexdigest()
    assert result["inputs"]["reference_json_sha256"] == hashlib.sha256(b"synthetic reference").hexdigest()


def test_gt_zero_zero_filter_and_support_are_visible_not_a_recovery_claim() -> None:
    result = _build()
    near_call = next(call for call in result["call_records"] if call["selection"]["bucket"] == "nearby_records")
    assert near_call["genotypes"] == ["0/0"]
    assert near_call["raw_gt_values"] == ["0/0"]
    assert near_call["filter"] == "LowQual"
    assert near_call["filter_raw"] == "LowQual"
    assert "SUPPORT=10" in near_call["info"]
    assert near_call["sample_columns"] == ["0/0:3:7"]
    assert result["carrier_recovery_claimed"] is False
    assert near_call["carrier_or_detection_interpretation"] == "NOT_ASSESSED"


def test_duplicate_coordinates_remain_separate_traceable_call_records() -> None:
    result = _build()
    calls = result["call_records"]
    assert len(calls) == 9
    duplicate = [call for call in calls if call["position"] == inv.TARGET_POS and call["end"] == inv.TARGET_END]
    assert len(duplicate) >= 2
    assert len({call["record_key"] for call in duplicate}) == len(duplicate)


@pytest.mark.parametrize("alt", ["<DEL>", ".", "A", "<INV:ME>", "N]chr2:10]"])
def test_ambiguous_or_unmodeled_alt_is_refused(alt: str) -> None:
    manifest, _ = _manifest_and_reference()
    _set_first_call_alt(manifest, alt)
    with pytest.raises(inv.DiagnosticError, match="ALT"):
        _build(manifest=manifest)


def test_truth_merged_tier1_duplicate_is_required_and_tier1_is_target() -> None:
    manifest, _ = _manifest_and_reference()
    tier1 = next(source for source in manifest["sources"] if source["path"].endswith("merged.vcf_Tier1.vcf.gz"))
    row = tier1["vcf_summary"]["nearby_records"][0]
    row["fields"][9] = "1/1:3:7"
    row["format_and_samples"] = row["fields"][8:]
    row["raw_record"] = "\t".join(row["fields"])
    with pytest.raises(inv.DiagnosticError, match="duplicate|GT 0/1"):
        _build(manifest=manifest)


def test_manifest_pin_rejects_changed_commit_and_missing_source() -> None:
    manifest, _ = _manifest_and_reference()
    changed_commit = copy.deepcopy(manifest)
    changed_commit["provenance"]["commit"] = "0" * 40
    with pytest.raises(inv.DiagnosticError, match="provenance pin"):
        _build(manifest=changed_commit)

    missing_source = copy.deepcopy(manifest)
    missing_source["sources"].pop()
    with pytest.raises(inv.DiagnosticError, match="25 pinned source"):
        _build(manifest=missing_source)


def test_out_of_reference_interval_is_refused() -> None:
    manifest, _ = _manifest_and_reference()
    source = next(item for item in manifest["sources"] if item["path"].endswith("inv_severus_ont_minimap2.vcf"))
    row = source["vcf_summary"]["nearby_records"][0]
    pos, end = inv.REFERENCE_START - 5, inv.REFERENCE_START - 1
    row["fields"][1] = str(pos)
    row["position"] = pos
    row["fields"][7] = f"END={end};SUPPORT=10;REPEAT_FLANK=tagged"
    row["info"] = row["fields"][7]
    row["end_positions"] = [end]
    row["end_field_values"] = [str(end)]
    row["raw_record"] = "\t".join(row["fields"])
    with pytest.raises(inv.DiagnosticError, match="outside the fetched reference window"):
        _build(manifest=manifest)


def test_interval_past_reference_end_is_refused() -> None:
    with pytest.raises(inv.DiagnosticError, match="outside the fetched reference window"):
        inv.interval_for_mode(inv.REFERENCE_END - 5, inv.REFERENCE_END + 2, "A")


def test_exclusive_output_refuses_existing_file_without_changing_it(tmp_path: Path) -> None:
    output = tmp_path / "already-there.json"
    output.write_text("keep this\n", encoding="utf-8")
    with pytest.raises(inv.DiagnosticError, match="refusing to overwrite"):
        inv.write_json_exclusive(output, {"value": 1})
    assert output.read_text(encoding="utf-8") == "keep this\n"


def test_output_json_is_strict_and_new_path_is_created_exclusively(tmp_path: Path) -> None:
    output = tmp_path / "new.json"
    inv.write_json_exclusive(output, {"value": 1})
    assert json.loads(output.read_text(encoding="utf-8")) == {"value": 1}
    invalid_output = tmp_path / "nan.json"
    with pytest.raises(ValueError):
        inv.write_json_exclusive(invalid_output, {"bad": float("nan")})
    assert not invalid_output.exists()
