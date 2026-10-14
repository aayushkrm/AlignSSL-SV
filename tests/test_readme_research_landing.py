"""Checks the repository-root README as the current research landing page."""

from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
README = " ".join((ROOT / "README.md").read_text(encoding="utf-8").split())
BRANCH_BASE = (
    "https://github.com/aayushkrm/AlignSSL-SV/blob/"
    "research/genotype-confidence-contracts-20261001/"
)


def test_landing_page_states_scope_and_evidence_limits():
    required = (
        "structural-variant (SV) calling and genotyping",
        "Self-supervised learning (SSL) is optional.",
        "DeepSV is historical context only",
        "Completed engineering diagnostics (2026-10-08)",
        "20 native controls passed",
        "all 11,490 unchanged rows are metadata-compatible",
        "41 REF controls passed",
        "all 11,490 anchored REF spans agree",
        "truth denominator, ALT alleles, phase, callability, or scoring",
        "Caller preparation follows a fixed reviewed process",
        "Earlier input check (2026-10-09): 44 cluster controls passed.",
        "Current decision (2026-10-14): stop the selected simple-inversion case",
        "no further case compute is allocated",
        "This does not show biological absence or native caller success.",
        "Earlier decision (2026-10-12): stop the HG002 annotation-exclusion pilot",
        "before genome-wide calling",
        "scientific investment stop, not a biological null",
        "No new calling, assembly or RNA campaign is released.",
        "The archive route is closed",
        "the required ONT-to-HiFi caller views were not sufficiently established",
        "No genotype outcome was scored.",
        "an input-readiness stop, not a biological null result",
        "No novel method, publication lead, or performance claim is established.",
        "research/genotype-confidence-contracts-20261001",
        "default main may not contain those records",
    )
    for phrase in required:
        assert phrase in README, f"current README is missing: {phrase}"


def test_current_research_links_use_the_named_branch_without_fetching():
    paths = (
        "PROGRESS.md",
        "docs/research/README.md",
        "docs/research/RESTART_STATE.md",
        "docs/research/2026-10-08-native-throughput-result.md",
        "docs/research/2026-10-08-reference-throughput-result.md",
        "docs/research/2026-10-08-metadata-census-result.md",
        "docs/research/2026-10-08-caller-preparation-review.md",
        "docs/research/2026-10-09-svupp-provenance-header-result01.md",
        "docs/research/2026-10-09-svupp-provenance-header-review.md",
        "docs/research/2026-10-11-hg002-calling-release-decision.md",
        "docs/research/2026-10-11-hg002-source-readset-result.md",
        "results/inv_mapped_trace_20261014/README.md",
        "docs/research/2026-10-14-inversion-post-trace-investment.md",
    )
    for path in paths:
        url = BRANCH_BASE + path
        assert url.startswith("https://github.com/aayushkrm/AlignSSL-SV/blob/")
        assert "/blob/research/genotype-confidence-contracts-20261001/" in url
        assert f"]({url})" in README, f"README must link to {url}"


def test_historical_navigation_uses_default_main_paths():
    for target in ("results/", "docs/archive/README-legacy-ssl.md"):
        assert f"]({target})" in README, f"README must retain the historical path: {target}"


def test_current_read_counts_match_complete_retained_extraction_evidence():
    raw = json.loads((ROOT / "results/hg002_read_extract_20261010/readiness.json").read_text())
    assert raw["pass1_complete"] and raw["pass2_complete"]
    assert raw["archive_differences"]["complete_census"]
    census = raw["census"]
    assert census["original_ids"] == census["resolved_ids"] == raw["counts"]["emitted_ids"]
    assert census["original_bases"] == census["resolved_bases"] == raw["counts"]["emitted_bases"]
    assert f"{census['original_ids']:,} original read identities" in README
    assert f"{census['original_bases']:,} bases" in README
    assert raw["alignment_calling_phase_qualification"] == "NOT_ASSESSED"
    assert "no publication result is claimed" in README


def test_current_regional_counts_match_complete_descriptive_summary():
    report = json.loads(
        (ROOT / "results/inv_mapped_trace_20261014/observed-query-order-02.json").read_text()
    )
    counts = report["counts"]
    assert counts["observed_alignment_records"] == report["provenance"]["retained_alignment_records"]
    assert sum(item["observed_record_count"] for item in report["qnames"]) == counts["observed_alignment_records"]
    assert len(report["qnames"]) == counts["unique_named_qnames"]
    phrase = (
        f"{counts['observed_alignment_records']} alignment records from "
        f"{counts['unique_named_qnames']} read-name labels"
    )
    assert phrase in README
