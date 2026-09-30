"""Synthetic contract probes for a pinned retrospective SV ensemble script.

These probes reproduce only the explicitly reviewed set/key/vote operations.
They never execute downloaded code, inspect biological calls, or establish an
error rate. A retrospective oracle may be useful, but is not a deployable VCF
merger that is independent of test truth.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
from dataclasses import dataclass
from pathlib import Path


SOURCE_COMMIT = "64b8aafc1b83a93c6718b577d8408c9b691dd60d"
SOURCE_PATH = "workflow/scripts/exhaustive-search-ensemble.py"
SOURCE_BLOB = "427f8db84aa1d110a2797ad975de131337fbbe7f"
SOURCE_URL = (
    "https://raw.githubusercontent.com/yuliu-guo/SV-Benchmarking-Germline/"
    f"{SOURCE_COMMIT}/{SOURCE_PATH}"
)


@dataclass(frozen=True)
class Variant:
    chrom: str
    pos: int
    ref: str
    alt: str
    end: int
    svtype: str

    def upstream_key(self) -> tuple[str, int, str, str]:
        """The four fields queried by the pinned parse_vcf operation."""
        return self.chrom, self.pos, self.ref, self.alt


def fp_position_clusters(keys: set[tuple], window: int = 50) -> set[tuple]:
    """Reviewed position-only, single-linkage FP canonicalization semantics."""
    if window < 0:
        raise ValueError("window must be nonnegative")
    if not keys:
        return set()
    ordered = sorted(keys, key=lambda key: (key[0], key[1]))
    representatives = {ordered[0]}
    previous = ordered[0]
    for key in ordered[1:]:
        if key[0] != previous[0] or key[1] - previous[1] > window:
            representatives.add(key)
        previous = key
    return representatives


def retrospective_calls(tp_base: set[tuple], fp_calls: set[tuple]) -> set[tuple]:
    """Oracle TP truth representatives union separately clustered FP keys."""
    return tp_base | fp_position_clusters(fp_calls)


def vote_counts(votes: dict[str, int], truth: set[str], support: int = 2) -> dict:
    """Contrast the two explicit FP support rules on identical toy votes."""
    if support < 1 or any(value < 0 for value in votes.values()):
        raise ValueError("support must be positive and votes nonnegative")
    tp = sum(count >= support for key, count in votes.items() if key in truth)
    union_fp = sum(count >= 1 for key, count in votes.items() if key not in truth)
    consensus_fp = sum(
        count >= support for key, count in votes.items() if key not in truth
    )
    return {
        "tp_at_required_support": tp,
        "fp_at_any_support": union_fp,
        "fp_at_required_support": consensus_fp,
        "retrospective_precision": tp / (tp + union_fp) if tp + union_fp else None,
        "consistent_support_precision": (
            tp / (tp + consensus_fp) if tp + consensus_fp else None
        ),
    }


def run_probes() -> dict:
    # END differs but CHROM/POS/REF/symbolic ALT do not. This does not assert
    # that all sequence-resolved truth alleles lose their length in this key.
    short = Variant("chr1", 100, "N", "<DEL>", 200, "DEL")
    long = Variant("chr1", 100, "N", "<DEL>", 1000, "DEL")
    chain = [
        Variant("chr1", 100, "N", "<DEL>", 200, "DEL"),
        Variant("chr1", 145, "N", "<INS>", 145, "INS"),
        Variant("chr1", 190, "N", "<DUP>", 390, "DUP"),
    ]
    chain_keys = {variant.upstream_key() for variant in chain}
    fixed_predictions = {
        Variant("chr1", 100, "N", "<DEL>", 200, "DEL").upstream_key(),
        Variant("chr1", 120, "N", "<DEL>", 300, "DEL").upstream_key(),
    }
    all_fp = retrospective_calls(set(), fixed_predictions)
    truth_representative = ("chr1", 101, "N", "<DEL>")
    one_tp = retrospective_calls(
        {truth_representative}, {key for key in fixed_predictions if key[1] == 120}
    )
    return {
        "scope": "synthetic operational counterexamples, not biological performance",
        "symbolic_key_collision": {
            "full_record_count": len({short, long}),
            "four_field_key_count": len({short.upstream_key(), long.upstream_key()}),
            "end_values": [short.end, long.end],
        },
        "position_only_fp_chain": {
            "input_key_count": len(chain_keys),
            "representative_count": len(fp_position_clusters(chain_keys)),
            "input_types": [variant.svtype for variant in chain],
            "max_start_span": chain[-1].pos - chain[0].pos,
            "single_linkage_window": 50,
            "allele_equivalence_tested": False,
        },
        "truth_conditioned_output": {
            "fixed_prediction_count": len(fixed_predictions),
            "all_fp_output": sorted(all_fp),
            "one_tp_output": sorted(one_tp),
            "output_changes_with_truth_partition": all_fp != one_tp,
        },
        "asymmetric_consensus_support": vote_counts(
            {"synthetic_true": 2, "synthetic_false": 1}, {"synthetic_true"}
        ),
        "limits": [
            "No real VCF records, truth labels, or published CSV metrics were scored.",
            "Retrospective oracle summaries can be legitimate when labeled as such.",
            "No inference about biological effect size, caller ranking, or novelty.",
            "No allegation that this source script produced every published result.",
            "Position/key changes require allele-aware assessment on real data.",
        ],
    }


def verified_source() -> dict:
    """Read at most 64 KiB and verify the exact Git blob; do not execute it."""
    with urllib.request.urlopen(SOURCE_URL, timeout=30) as response:
        if response.status != 200 or response.geturl() != SOURCE_URL:
            raise ValueError("Unexpected response for pinned source")
        data = response.read(65537)
    if len(data) > 65536:
        raise ValueError("Source exceeds bounded read")
    blob = hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()
    if blob != SOURCE_BLOB:
        raise ValueError("Pinned source Git blob mismatch")
    return {
        "commit": SOURCE_COMMIT,
        "path": SOURCE_PATH,
        "url": SOURCE_URL,
        "git_blob": blob,
        "sha256": hashlib.sha256(data).hexdigest(),
        "bytes": len(data),
        "downloaded_code_executed": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", required=True, type=Path)
    args = parser.parse_args()
    if args.out_dir.exists():
        parser.error(f"Refusing to overwrite existing output: {args.out_dir}")
    report = {"schema_version": 1, "source": verified_source(), "probes": run_probes()}
    payload = (json.dumps(report, indent=2, sort_keys=True) + "\n").encode()
    args.out_dir.mkdir(parents=True, exist_ok=False)
    (args.out_dir / "probe.json").write_bytes(payload)
    (args.out_dir / "SHA256SUMS").write_text(
        f"{hashlib.sha256(payload).hexdigest()}  probe.json\n"
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
