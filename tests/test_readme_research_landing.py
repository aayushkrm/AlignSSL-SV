"""Checks the repository-root README as the current research landing page."""

from pathlib import Path

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
    )
    for path in paths:
        url = BRANCH_BASE + path
        assert url.startswith("https://github.com/aayushkrm/AlignSSL-SV/blob/")
        assert "/blob/research/genotype-confidence-contracts-20261001/" in url
        assert f"]({url})" in README, f"README must link to {url}"


def test_historical_navigation_uses_default_main_paths():
    for target in ("results/", "docs/archive/README-legacy-ssl.md"):
        assert f"]({target})" in README, f"README must retain the historical path: {target}"
