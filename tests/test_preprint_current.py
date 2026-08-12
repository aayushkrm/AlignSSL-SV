"""Gates the shipped preprint PDF against the sources it was built from.

Motivating defect (2026-08-12): docs/AlignSSL_SV_preprint.pdf was committed on
2026-08-04 and never rebuilt, while the manuscript took 18 further commits
(+403/-162 lines) and eight of the ten figures were regenerated. The repository
therefore shipped, as its preprint, a document that no longer matched the paper
-- it predated the withdrawal of the cross-ancestry claim, the candidate-filtered
re-benchmark, and the field audit. Nothing caught it: the PDF is a binary, so a
diff shows only that its bytes changed, and no test related it to its inputs.

analysis/build_preprint.py now emits docs/preprint_build.json recording the
SHA-256 of the manuscript and of every embedded figure at build time. These
tests compare that record against the working tree, so an edit to the paper
that is not followed by a rebuild fails here rather than shipping.

Deliberately NOT gated: the PDF's own byte content against a fresh render. The
builder stamps the build date into a footer, so two renders of identical sources
on different days differ legitimately. What is gated is that the PDF on disk is
the one the manifest describes, and that the manifest describes today's sources.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs" / "preprint_build.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture(scope="module")
def manifest() -> dict:
    assert MANIFEST.exists(), (
        "docs/preprint_build.json is missing: rebuild with "
        "python analysis/build_preprint.py --manuscript docs/AlignSSL_SV_manuscript.md "
        "--results-dir results --out docs/AlignSSL_SV_preprint.pdf"
    )
    return json.loads(MANIFEST.read_text())


def test_pdf_on_disk_is_the_one_the_manifest_describes(manifest):
    pdf = ROOT / manifest["pdf"]["path"]
    assert pdf.exists(), f"{pdf} recorded in the manifest but absent"
    assert pdf.stat().st_size == manifest["pdf"]["size_bytes"]
    assert _sha256(pdf) == manifest["pdf"]["sha256"], (
        "the committed PDF is not the file this manifest was written for"
    )


def test_manuscript_has_not_changed_since_the_pdf_was_built(manifest):
    src = ROOT / manifest["manuscript"]["path"]
    assert _sha256(src) == manifest["manuscript"]["sha256"], (
        f"{src.name} has changed since the preprint was built "
        f"({manifest['built']}); rebuild the PDF before committing"
    )


def test_every_embedded_figure_is_current(manifest):
    stale = []
    for num, rec in sorted(manifest["figures"].items(), key=lambda kv: int(kv[0])):
        fig = ROOT / rec["path"]
        assert fig.exists(), f"figure {num} recorded at {rec['path']} but absent"
        if _sha256(fig) != rec["sha256"]:
            stale.append(f"figure {num} ({fig.name})")
    assert not stale, (
        "regenerated since the preprint was built: "
        + ", ".join(stale)
        + " -- rebuild the PDF"
    )


def test_manifest_covers_every_figure_the_manuscript_embeds(manifest):
    """A figure added to the paper must appear in the build record."""
    import re

    ms = (ROOT / manifest["manuscript"]["path"]).read_text()
    embedded = {m.group(1) for m in re.finditer(r"!\[Figure (\d+)\.", ms)}
    assert embedded == set(manifest["figures"]), (
        f"manuscript embeds figures {sorted(embedded, key=int)} but the build "
        f"record covers {sorted(manifest['figures'], key=int)}"
    )
