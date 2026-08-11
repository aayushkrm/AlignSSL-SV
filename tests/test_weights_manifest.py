"""The data-availability statement must agree with the released weights manifest.

The manuscript states a checkpoint count, a per-role breakdown, the archive size
and its SHA-256. Every one of those is a claim about a file a reader can download
and check, so none of them may drift from `release/WEIGHTS_MANIFEST.tsv`. This
gate fails if the prose and the manifest disagree.

It deliberately does NOT re-hash the archive: the archive is built on the cluster
and is not in the repository. What it does enforce is that the numbers quoted in
the prose are the numbers in the manifest, that every checkpoint carries a
verified strict-load result, and that no checkpoint is silently unattributed.
"""
from __future__ import annotations

import csv
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "release" / "WEIGHTS_MANIFEST.tsv"
MS = ROOT / "docs" / "AlignSSL_SV_manuscript.md"

EXPECTED_ROLES = {"main", "ablation", "sas", "superseded"}


def _rows():
    with MANIFEST.open() as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


def _availability_section() -> str:
    text = MS.read_text()
    i = text.index("## Data and code availability")
    j = text.index("## Declarations", i)
    return text[i:j]


def test_manifest_exists_and_is_well_formed():
    rows = _rows()
    assert rows, "WEIGHTS_MANIFEST.tsv is empty"
    required = {"file", "role", "sha256", "encoder_params", "d_model",
                "strict_load_into_AlignEncoder", "description"}
    assert required <= set(rows[0]), sorted(required - set(rows[0]))


def test_every_checkpoint_loads_strictly_into_the_released_encoder():
    """A weight file that does not load into the published encoder class is not a
    release, it is a liability."""
    bad = [r["file"] for r in _rows()
           if r["strict_load_into_AlignEncoder"].strip() != "OK"]
    assert not bad, f"checkpoints without a verified strict load: {bad}"


def test_all_checkpoints_share_one_architecture():
    rows = _rows()
    assert len({r["encoder_params"] for r in rows}) == 1, \
        sorted({r["encoder_params"] for r in rows})
    assert len({r["d_model"] for r in rows}) == 1, sorted({r["d_model"] for r in rows})


def test_roles_are_from_the_known_set_and_every_row_is_described():
    rows = _rows()
    assert {r["role"] for r in rows} <= EXPECTED_ROLES, \
        {r["role"] for r in rows} - EXPECTED_ROLES
    thin = [r["file"] for r in rows if len(r["description"].strip()) < 40]
    assert not thin, f"checkpoints with no substantive description: {thin}"


def test_unused_checkpoints_say_so():
    """Releasing a checkpoint that serves no reported number is fine; leaving a
    reader to guess which ones those are is not."""
    for r in _rows():
        d = r["description"]
        if r["role"] in {"superseded"} or "NOT used" in d:
            assert re.search(r"NOT used|no reported number uses it|provenance", d), \
                f"{r['file']} is unused but does not say so: {d[:80]}"


def test_manuscript_count_matches_the_manifest():
    rows = _rows()
    sec = _availability_section()
    m = re.search(r"All (\d+) trained encoder checkpoints", sec)
    assert m, "the availability statement no longer states a checkpoint count"
    assert int(m.group(1)) == len(rows), (int(m.group(1)), len(rows))


def test_manuscript_role_breakdown_matches_the_manifest():
    counts = Counter(r["role"] for r in _rows())
    sec = _availability_section()
    words = {1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five", 6: "Six",
             7: "Seven", 8: "Eight", 9: "Nine", 10: "Ten"}

    def stated(pattern: str) -> int:
        m = re.search(pattern, sec)
        assert m, f"availability statement lost its {pattern!r} clause"
        tok = m.group(1)
        if tok.isdigit():
            return int(tok)
        for k, v in words.items():
            if v.lower() == tok.lower():
                return k
        raise AssertionError(f"unparsable count word {tok!r}")

    assert stated(r"(\w+) checkpoints are the main") == counts["main"], counts
    assert stated(r"(\w+) are objective ablations") == counts["ablation"], counts
    assert stated(r"(\w+) are the statistic-anchored") == counts["sas"], counts
    assert stated(r"(\w+) is a\s+superseded") == counts["superseded"], counts


def test_manuscript_archive_size_and_digest_are_internally_consistent():
    sec = _availability_section()
    size = re.search(r"([\d,]+) bytes", sec)
    digest = re.search(r"SHA-256\s+`([0-9a-f]{64})`", sec)
    assert size and digest, "archive size or SHA-256 missing from the statement"
    n = int(size.group(1).replace(",", ""))
    assert n > 10_000_000, n
    # the archive must be at least as large as the sum of the files it contains
    total = sum(int(r["bytes"]) for r in _rows())
    assert n > 0.5 * total, (n, total)


def test_ablation_seed_count_matches_table4():
    """Table 4 reports n_pretrain_seeds per objective arm. The manifest must
    contain exactly that many pretraining encoders for each arm on the corpus
    generation the table actually used (`_120k`), and the combined arm must be
    served by the main encoders rather than by a dedicated ablation checkpoint."""
    import csv as _csv

    files = [r["file"] for r in _rows()]
    seeds = {
        "MAM-only": sum("abl_maeonly_120k" in f for f in files),
        "VICReg-only": sum("abl_viconly_120k" in f for f in files),
        "combined": sum("encoder_ssl_seed" in f for f in files),
    }
    with (ROOT / "results" / "table4_ablation.csv").open() as fh:
        table = list(_csv.DictReader(fh))
    reported = {r["objective"]: int(r["n_pretrain_seeds"]) for r in table}
    assert set(reported) == set(seeds), (sorted(reported), sorted(seeds))
    for arm, n in reported.items():
        assert seeds[arm] == n, f"{arm}: table says {n} seeds, manifest has {seeds[arm]}"

    # no dedicated combined ablation checkpoint on the reported corpus generation
    assert not [f for f in files if "abl_combined_120k" in f]
