"""Gates on how the GIAB HG002 benchmark is described across the documents.

Motivation (2026-08-12): Section 6.5 builds a GIAB Tier1 v0.6 benchmark, but the
limitations list still said "a curated orthogonal benchmark (GIAB HG002) remains
deferred", PROGRESS.md said HG002 was not on the cluster, and all three named the
GRCh38 v4.2.1 benchmark as a blocker -- v4.2.1 is the *small-variant* benchmark;
the SV benchmark used here is Tier1 v0.6, which ships for GRCh37 and needs no
lift-over. Three documents disagreed with the experiment and with each other.

The distinction these gates protect: the orthogonal *truth set* is done; the
call-set-level *Truvari* comparison is not, and is blocked on model capability
(no breakpoint or genotype head => no VCF to match), not on data availability.
"""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
MS = (ROOT / "docs" / "AlignSSL_SV_manuscript.md").read_text()
README = (ROOT / "README.md").read_text()
PROGRESS = (ROOT / "PROGRESS.md").read_text()
DOCS = {"manuscript": MS, "README": README, "PROGRESS": PROGRESS}


def test_no_document_calls_the_giab_truth_set_deferred():
    """The truth set is used in Section 6.5; no document may call it future work.

    Scoped deliberately: a sentence may say a *call-set-level Truvari* comparison
    remains deferred, because that one is genuinely outstanding. What is forbidden
    is deferring GIAB *itself*. The discriminator is therefore whether the same
    sentence names Truvari or call-set matching -- an earlier draft of this gate
    used proximity alone and flagged the two correctly-scoped sentences.
    """
    defer = re.compile(r"remains? deferred|is deferred|will use|future work", re.I)
    for name, text in DOCS.items():
        hits = []
        for sentence in re.split(r"(?<=[.!?])\s+", text):
            if "GIAB" not in sentence or not defer.search(sentence):
                continue
            if re.search(r"Truvari|call[- ]set", sentence, re.I):
                continue  # correctly scoped to the outstanding half
            hits.append(sentence.strip()[:160])
        assert not hits, f"{name} defers GIAB itself rather than the Truvari half: {hits}"


def test_deferred_item_is_scoped_to_truvari_call_set_matching():
    """Each document must name what is actually still missing, not 'GIAB'."""
    for name, text in DOCS.items():
        assert re.search(r"Truvari", text), f"{name} never names Truvari"
        assert re.search(
            r"call[- ]set", text, re.I
        ), f"{name} does not scope the deferral to call-set-level comparison"


def test_truvari_blocker_is_stated_as_model_capability():
    """The blocker is a missing breakpoint/genotype head, not missing data."""
    for name, text in DOCS.items():
        window = " ".join(
            text[max(0, m.start() - 700): m.start() + 700]
            for m in re.finditer(r"Truvari", text)
        )
        assert re.search(r"breakpoint", window, re.I), f"{name}: no breakpoint blocker near Truvari"
        assert re.search(r"genotype", window, re.I), f"{name}: no genotype blocker near Truvari"


def test_no_document_claims_v4_2_1_as_the_sv_benchmark():
    """v4.2.1 is the small-variant benchmark; the SV benchmark here is Tier1 v0.6."""
    for name, text in DOCS.items():
        for m in re.finditer(r"v?4\.2\.1", text):
            # Wide window: a historical entry is superseded by a correction note
            # appended after it rather than by editing the entry, so the
            # disambiguation can sit a paragraph away from the mention.
            window = text[max(0, m.start() - 400): m.start() + 1400]
            assert re.search(
                r"small[- ]variant", window, re.I
            ), f"{name}: v4.2.1 mentioned without noting it is the small-variant benchmark"


def test_giab_reference_build_is_grch37_everywhere_it_is_stated():
    """Tier1 v0.6 ships for GRCh37/hs37d5; no document may pair it with GRCh38.

    Uses a fixed-width window, not a sentence match. An earlier version scanned
    ``Tier1[^.\n]{0,120}`` to stay inside one sentence, but the version string
    "v0.6" contains a period, so every window truncated to "Tier1 v0" and the
    gate could never see a build name. Falsification caught it.
    """
    for m_name, text in DOCS.items():
        for m in re.finditer(r"Tier1", text):
            window = text[m.start(): m.start() + 160]
            assert "GRCh38" not in window, (
                f"{m_name}: Tier1 paired with GRCh38 -- Tier1 v0.6 is a GRCh37 "
                f"benchmark: {window!r}"
            )
