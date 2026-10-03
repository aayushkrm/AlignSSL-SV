"""Synthetic reproducer for the released SVPG replicate-evaluator contract.

This module implements a small, independent model of the observable source
semantics. It does not load, compile, or execute code from the pinned archive.
The optional source check reads the archive as bytes, verifies its hashes, and
parses the relevant member with :mod:`ast` only.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import io
import json
import zipfile
from dataclasses import dataclass
from pathlib import Path


SOURCE_ARCHIVE = Path(
    "/Users/akm/aayushkrm-AlignSSL/data/source_archives/"
    "svpg-18456502-scripts.zip"
)
SOURCE_ARCHIVE_BYTES = 18_200
SOURCE_ARCHIVE_MD5 = "57dce6316194c5147628b9cb933367fb"
SOURCE_ARCHIVE_SHA256 = "cc7f077cee6a1e0c503aa21d04e935feae44f79ee32857343017bdb16215091e"
PINNED_MEMBERS = {
    "scripts/eval_inconsistency.py": {
        "bytes": 6_919,
        "sha256": "8415334589ca48be6652dd583c7aab5ba7dd99590a9f5ccc1de7b3979f8656b0",
    },
    "scripts/merge_specfic.vcf.py": {
        "bytes": 3_597,
        "sha256": "b198ad182d7eb5e8d08ea39b551916d5c6f960e3807aeded2d104f477e67d6f9",
    },
}


@dataclass(frozen=True)
class SyntheticCall:
    """One synthetic DEL or INS call; coordinates are 1-based VCF-like values."""

    chrom: str
    start: int
    end: int
    svtype: str
    svlen: int
    genotype: str


def phase_gt(genotype_field: str) -> str:
    """Model the released script's unphased GT-to-class mapping."""
    gt = genotype_field.split(":", 1)[0]
    if gt in ("0/1", "1/0"):
        return "het"
    if gt == "1/1":
        return "hom"
    return "unknown"


def retained_by_released_contract(call: SyntheticCall) -> bool:
    """Model the relevant load filter for type, size, and recognized GT."""
    return (
        call.svtype in ("DEL", "INS")
        and call.svlen >= 50
        and phase_gt(call.genotype) != "unknown"
    )


def _event_match(
    call_a: SyntheticCall,
    call_b: SyntheticCall,
    *,
    bias: float,
    offset: int,
) -> bool:
    """Reproduce the evaluator's type, chromosome, and geometry checks."""
    if call_a.svtype != call_b.svtype or call_a.chrom != call_b.chrom:
        return False
    if max(call_a.svlen, call_b.svlen) <= 0:
        return False
    length_ratio = min(call_a.svlen, call_b.svlen) / max(call_a.svlen, call_b.svlen)
    if call_b.svtype == "INS":
        return abs(call_b.start - call_a.start) <= offset and length_ratio >= bias
    if call_b.svtype == "DEL":
        overlap = max(call_b.start - offset, call_a.start) <= min(
            call_b.end + offset, call_a.end
        )
        return overlap and length_ratio >= bias
    return False


def compare_callsets(
    call_a: tuple[SyntheticCall, ...] | list[SyntheticCall],
    call_b: tuple[SyntheticCall, ...] | list[SyntheticCall],
    *,
    bias: float = 0.7,
    offset: int = 500,
) -> dict:
    """Count candidate events and event matches, without comparing paired GTs.

    This models the directional F2-side event-inconsistency statistic. Each
    retained call in ``call_b`` is counted once, whether or not its matching
    call in ``call_a`` has the same genotype.
    """
    retained_a = [call for call in call_a if retained_by_released_contract(call)]
    retained_b = [call for call in call_b if retained_by_released_contract(call)]
    matched = [
        any(_event_match(a, b, bias=bias, offset=offset) for a in retained_a)
        for b in retained_b
    ]
    matched_count = sum(matched)
    return {
        "candidate_records": len(retained_b),
        "event_matches": matched_count,
        "event_inconsistency": len(retained_b) - matched_count,
        "candidate_genotype_classes": [phase_gt(call.genotype) for call in retained_b],
    }


def run_probe() -> dict:
    """Return a deterministic synthetic counterexample and negative controls."""
    genotype_mismatch = compare_callsets(
        [SyntheticCall("chr1", 10_000, 11_000, "DEL", 1_001, "0/1")],
        [SyntheticCall("chr1", 10_000, 11_000, "DEL", 1_001, "1/1")],
    )
    phased = SyntheticCall("chr1", 15_000, 16_000, "DEL", 1_001, "0|1")
    phased_result = compare_callsets([phased], [phased])

    controls = {
        "genuine_no_overlap": compare_callsets(
            [SyntheticCall("chr1", 1_000, 1_999, "DEL", 1_000, "0/1")],
            [SyntheticCall("chr1", 10_000, 10_999, "DEL", 1_000, "1/1")],
        ),
        "type_mismatch": compare_callsets(
            [SyntheticCall("chr1", 20_000, 20_000, "INS", 100, "0/1")],
            [SyntheticCall("chr1", 20_000, 20_099, "DEL", 100, "1/1")],
        ),
        "chromosome_mismatch": compare_callsets(
            [SyntheticCall("chr1", 30_000, 30_999, "DEL", 1_000, "0/1")],
            [SyntheticCall("chr2", 30_000, 30_999, "DEL", 1_000, "1/1")],
        ),
        "length_ratio_below_bias": compare_callsets(
            [SyntheticCall("chr1", 40_000, 43_999, "DEL", 4_000, "0/1")],
            [SyntheticCall("chr1", 40_000, 40_099, "DEL", 100, "1/1")],
        ),
    }
    return {
        "schema_version": 1,
        "scope": (
            "Synthetic source-semantics reproduction only. This does not execute "
            "the released code, use published records, or estimate biological frequency."
        ),
        "genotype_mismatch_counterexample": {
            "call_a_genotype_class": "het",
            "call_b_genotype_class": "hom",
            **genotype_mismatch,
            "genotypes_agree": False,
        },
        "phased_call": {
            "genotype": phased.genotype,
            "genotype_class": phase_gt(phased.genotype),
            "retained": retained_by_released_contract(phased),
            **phased_result,
        },
        "negative_controls": controls,
        "interpretation": (
            "Matching event geometry marks the candidate call as matched even when "
            "the two genotype classes differ; the reported event-inconsistency "
            "count therefore does not measure genotype disagreement."
        ),
        "source_execution": False,
    }


def _function(tree: ast.AST, name: str) -> ast.FunctionDef:
    found = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == name
    ]
    if len(found) != 1:
        raise ValueError(f"expected one static definition of {name}, found {len(found)}")
    return found[0]


def _has_expression(node: ast.AST, expression: str) -> bool:
    target = ast.dump(ast.parse(expression, mode="eval").body)
    return any(ast.dump(candidate) == target for candidate in ast.walk(node))


def _calls_with_name(node: ast.AST, name: str) -> list[ast.Call]:
    return [
        candidate
        for candidate in ast.walk(node)
        if isinstance(candidate, ast.Call)
        and isinstance(candidate.func, ast.Name)
        and candidate.func.id == name
    ]


def _last_arg_strings(call: ast.Call) -> tuple[str, ...] | None:
    if not call.args or not isinstance(call.args[-1], ast.List):
        return None
    values = call.args[-1].elts
    if not all(isinstance(value, ast.Constant) and isinstance(value.value, str) for value in values):
        return None
    return tuple(value.value for value in values)


def _source_ast_contracts(source: bytes) -> dict[str, bool]:
    """Check the pinned source's syntax tree without compiling or running it."""
    tree = ast.parse(source.decode("utf-8"), filename="scripts/eval_inconsistency.py")
    phase = _function(tree, "phase_GT")
    load = _function(tree, "load_callset")
    evaluate = _function(tree, "eva_record")
    stats = _function(tree, "statistics_true_possitive")
    main = _function(tree, "main_ctrl")

    phase_literals = {
        node.value
        for node in ast.walk(phase)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    unknown_filter = False
    for node in ast.walk(load):
        if (
            isinstance(node, ast.If)
            and _has_expression(node.test, "phase_GT(seq[9]) == 'unknown'")
        ):
            unknown_filter = any(isinstance(child, ast.Continue) for child in ast.walk(node))
            break
    main_compare = [
        call for call in _calls_with_name(main, "eva_record")
        if len(call.args) >= 5
        and isinstance(call.args[0], ast.Name)
        and call.args[0].id == "call_base"
        and isinstance(call.args[1], ast.Name)
        and call.args[1].id == "call_comp"
        and _last_arg_strings(call) == ("hom", "het")
    ]
    main_stats = [
        call for call in _calls_with_name(main, "statistics_true_possitive")
        if len(call.args) >= 3
        and isinstance(call.args[0], ast.Name)
        and call.args[0].id == "call_comp"
        and _last_arg_strings(call) == ("hom", "het")
    ]
    return {
        "phase_GT_accepts_unphased_heterozygous_and_homozygous_forms": {
            "0/1", "1/0", "1/1", "het", "hom", "unknown"
        }.issubset(phase_literals),
        "phase_GT_does_not_recognize_phased_0_pipe_1": "0|1" not in phase_literals,
        "load_callset_drops_unknown_genotype_class": unknown_filter,
        "eva_record_filters_candidate_by_requested_class": _has_expression(
            evaluate, "i[-2] not in gt"
        ),
        "eva_record_checks_chromosome_and_event_geometry": all(
            _has_expression(evaluate, expression)
            for expression in (
                "svtype not in call_B",
                "i[0] != j[0]",
                "abs(i[1] - j[1]) <= offect",
                "max(i[1] - offect, j[1]) <= min(i[2] + offect, j[2])",
                "float(min(i[3], j[3]) / max(i[3], j[3])) >= bias",
            )
        ),
        "eva_record_does_not_compare_pairwise_genotypes": not any(
            _has_expression(evaluate, expression)
            for expression in ("i[-2] == j[-2]", "i[-2] != j[-2]", "j[-2]")
        ),
        "main_ctrl_reports_directional_candidate_callset_event_matches": bool(
            main_compare and main_stats and _has_expression(stats, "i[-1] == 1")
        ),
    }


def inspect_pinned_source(path: Path = SOURCE_ARCHIVE) -> dict:
    """Verify archive and member hashes, then inspect the evaluator AST only."""
    if path.stat().st_size != SOURCE_ARCHIVE_BYTES:
        raise ValueError("pinned archive size mismatch before read")
    with path.open("rb") as handle:
        payload = handle.read(SOURCE_ARCHIVE_BYTES + 1)
    observed = {
        "bytes": len(payload),
        "md5": hashlib.md5(payload).hexdigest(),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }
    expected = {
        "bytes": SOURCE_ARCHIVE_BYTES,
        "md5": SOURCE_ARCHIVE_MD5,
        "sha256": SOURCE_ARCHIVE_SHA256,
    }
    if observed != expected:
        raise ValueError(f"pinned archive identity mismatch: {observed}")

    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        members = {}
        source = None
        for name, pin in PINNED_MEMBERS.items():
            member_bytes = archive.read(name)
            member_identity = {
                "bytes": len(member_bytes),
                "sha256": hashlib.sha256(member_bytes).hexdigest(),
            }
            if member_identity != pin:
                raise ValueError(f"pinned member identity mismatch for {name}: {member_identity}")
            members[name] = member_identity
            if name == "scripts/eval_inconsistency.py":
                source = member_bytes
    if source is None:  # pragma: no cover - required member is pinned above
        raise ValueError("pinned evaluator member is absent")

    contracts = _source_ast_contracts(source)
    failed = sorted(name for name, passed in contracts.items() if not passed)
    if failed:
        raise ValueError(f"pinned evaluator AST contract changed: {failed}")
    return {
        "archive_path": str(path),
        "archive": observed,
        "members": members,
        "ast_contracts": contracts,
        "source_parsed_as_data_only": True,
        "source_compiled_or_executed": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--inspect-pinned-source",
        action="store_true",
        help="verify the optional local archive and check its evaluator AST without execution",
    )
    args = parser.parse_args()
    report = run_probe()
    if args.inspect_pinned_source:
        report["pinned_source"] = inspect_pinned_source()
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
