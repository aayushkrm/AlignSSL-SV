"""Independent mathematical contract probe; never execute upstream code/data.

Haplotype labels are arbitrary. Marginal diploid genotype probabilities should
be invariant to swapping them. This probe models the reviewed likelihood formula
and a zero-as-missing lookup separately, not the full caller or its accuracy.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import urllib.request
from pathlib import Path

COMMIT = "eb3d79de3b87ad823552f1156627c79de61d587c"
SOURCES = {
    "src/cuteSV/cuteSV_genotype.py": "3a7e77fabd2005c6e6ae300be8fdec04340688cf",
    "src/cuteSV/cuteSV_forcecalling.py": "a4fc0d7ffda0fc8d3eddd307fcfd9984c5992da1",
    "src/cuteSV/cuteSV": "c91edb6ece4d8d4b33d60c71c6ed5eeda9910840",
}
QUILT_COMMIT = "30a14b0326979be69c6310e736d4853e9119b30d"
QUILT_SOURCES = {
    "QUILT/R/functions.R": "5e12075687c17b97d3743eefa65d5ff861195a48",
    "QUILT/R/quilt.R": "33c6ee22c384d8855e56d6f2a24489c53641b833",
    "QUILT/src/copied-from-stitch.cpp": "059f64e1b8326e357a10f91a71e6612b62cc91d1",
}
QUILT_204_COMMIT = "05056767c64d1f1405c7cbccd4eaec41a45bc9cb"


def posterior(reads: list[tuple[int, float | None]], zero_as_missing: bool) -> dict:
    """Marginalize two heterozygous phases, with uniform genotype priors.

    reads = (REF/ALT evidence, probability of haplotype 1); None means absent.
    Tail floors/rounding model the pinned output, not calibrated probability.
    """
    if not reads:
        raise ValueError("at least one read required")
    likelihoods = []
    for genotype in ((0, 0), (0, 1), (1, 0), (1, 1)):
        value = 0.0
        for allele, phase in reads:
            if allele not in (0, 1) or (
                phase is not None and (not math.isfinite(phase) or not 0 <= phase <= 1)
            ):
                raise ValueError("invalid allele or haplotype probability")
            p = 0.5 if phase is None or (zero_as_missing and phase == 0) else phase
            like = sum(
                weight * (0.99 if allele == called else 0.01)
                for weight, called in zip((p, 1 - p), genotype)
            )
            value += math.log10(like)
        likelihoods.append(value)
    offset = max(likelihoods)
    scaled = [10 ** (value - offset) for value in likelihoods]
    marginal = [scaled[0], (scaled[1] + scaled[2]) / 2, scaled[3]]
    probabilities = [value / sum(marginal) for value in marginal]
    best = max(range(3), key=probabilities.__getitem__)
    emitted = [max(9e-9, value) for value in probabilities]
    return {
        "gt": ("0/0", "0/1", "1/1")[best],
        "posterior_before_output_floor": probabilities,
        "pl": [round(-10 * math.log10(value)) for value in emitted],
        "gq": min(int(-10 * math.log10(max(1e-10, 1 - emitted[best]))), 100),
    }


def swap(reads: list[tuple[int, float | None]]) -> list[tuple[int, float | None]]:
    return [(allele, None if phase is None else 1 - phase) for allele, phase in reads]


def run_probes() -> dict:
    fixtures = {
        "endpoints_six_ref_one_alt": [(0, 1.0)] * 6 + [(1, 0.0)],
        "interior_six_ref_one_alt": [(0, 0.99)] * 6 + [(1, 0.01)],
        "missing_six_ref_one_alt": [(0, None)] * 6 + [(1, None)],
        "unphased_half_six_ref_one_alt": [(0, 0.5)] * 6 + [(1, 0.5)],
    }
    results = {}
    for name, reads in fixtures.items():
        results[name] = {
            mode: {"original": posterior(reads, legacy), "swapped": posterior(swap(reads), legacy)}
            for mode, legacy in (("zero_as_missing", True), ("zero_is_probability", False))
        }
    return {
        "schema_version": 1,
        "scope": "synthetic source-contract diagnostic only; no biological accuracy",
        "read_error_probability": 0.01,
        "genotype_prior": "uniform; heterozygous phase marginalized equally",
        "fixtures": results,
        "synthetic_producer_endpoint": producer_endpoint(),
        "limits": [
            "Independent formula implementation, not execution of the upstream caller.",
            "Real endpoint frequency and assessment execution revision are unknown.",
            "No genomic calls, truth comparisons, calibration or effect size measured.",
            "Counterfactual explicit-missing handling is not an adopted caller patch.",
        ],
    }


def producer_endpoint() -> dict:
    """Six illustrative BQ30 SNP emissions, not a QUILT run or read sample."""
    eps = 10 ** (-30 / 10)
    favored = (1 - eps) ** 6
    other = (eps / 3) ** 6
    confidence = favored / (favored + other)
    opposite_ratio = other / (favored + other)
    opposite_folded = 1 - opposite_ratio if opposite_ratio < 0.5 else opposite_ratio
    return {"snp_count": 6, "base_quality": 30,
            "favored_haplotype_likelihood": favored,
            "other_haplotype_likelihood": other,
            "binary64_confidence": confidence,
            "opposite_raw_ratio": opposite_ratio,
            "opposite_folded_confidence": opposite_folded,
            "parsed_haplotype2_probability": 1 - confidence,
            "scope": "independent source-formula arithmetic, not upstream execution"}


def verify_sources() -> list[dict]:
    identities = []
    specs = [("Zilong-Li/cuteSV", COMMIT, SOURCES),
             ("rwdavies/QUILT", QUILT_COMMIT, QUILT_SOURCES),
             ("rwdavies/QUILT", QUILT_204_COMMIT,
              {path: blob for path, blob in QUILT_SOURCES.items() if path != "QUILT/R/quilt.R"})]
    for repo, commit, path, blob in (
        (repo, commit, path, blob)
        for repo, commit, sources in specs for path, blob in sources.items()
    ):
        url = f"https://raw.githubusercontent.com/{repo}/{commit}/{path}"
        with urllib.request.urlopen(url, timeout=30) as response:
            body = response.read(150_001)
        if len(body) > 150_000:
            raise ValueError("source exceeds bounded size")
        observed = hashlib.sha1(f"blob {len(body)}\0".encode() + body).hexdigest()
        if observed != blob:
            raise ValueError(f"source Git blob mismatch: {path}")
        identities.append({"repository": repo, "path": path, "url": url, "commit": commit,
                           "git_blob": observed, "sha256": hashlib.sha256(body).hexdigest(),
                           "bytes": len(body), "executed": False})
    return identities


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--verify-sources", action="store_true")
    args = parser.parse_args()
    report = run_probes()
    report["sources"] = verify_sources() if args.verify_sources else []
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x") as handle:
        json.dump(report, handle, indent=2, allow_nan=False)
        handle.write("\n")


if __name__ == "__main__":
    main()
