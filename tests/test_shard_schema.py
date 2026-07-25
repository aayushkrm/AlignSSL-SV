"""The two extractors must write ONE shard schema.

`alignssl.data.ShardDataset` is the single loader for both the uniform-negative
arm (`scripts/extract_tensors.py`) and the hard-negative control
(`scripts/extract_tensors_hardneg.py`). When the hard-negative extractor was
written it emitted `x`/`bp0`/`bp1` where the canonical one emits `X`/`bp`; the
shards were produced without error and every downstream evaluator then died on
`KeyError: 'X is not a file in the archive'` after ~2 h of extraction.

Extracting is expensive and the failure is silent at write time, so the
agreement is asserted statically here: parse both `np.savez_compressed` calls
and compare their keyword sets, and require that every field `ShardDataset`
reads is among them.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "scripts" / "extract_tensors.py"
HARDNEG = ROOT / "scripts" / "extract_tensors_hardneg.py"
LOADER = ROOT / "alignssl" / "data.py"


def savez_keywords(path: Path) -> set[str]:
    """Keyword names of the single np.savez_compressed call in `path`."""
    tree = ast.parse(path.read_text())
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        if isinstance(fn, ast.Attribute) and fn.attr == "savez_compressed":
            found.append({kw.arg for kw in node.keywords if kw.arg})
    assert len(found) == 1, f"{path.name}: expected 1 savez call, found {len(found)}"
    return found[0]


def loader_fields() -> set[str]:
    """Archive keys read by ShardDataset, i.e. every `d["..."]` subscript."""
    tree = ast.parse(LOADER.read_text())
    cls = next(n for n in ast.walk(tree)
               if isinstance(n, ast.ClassDef) and n.name == "ShardDataset")
    keys = set()
    for node in ast.walk(cls):
        if (isinstance(node, ast.Subscript)
                and isinstance(node.value, ast.Name) and node.value.id == "d"
                and isinstance(node.slice, ast.Constant)
                and isinstance(node.slice.value, str)):
            keys.add(node.slice.value)
    assert keys, "no d[\"...\"] reads found in ShardDataset"
    return keys


def test_extractors_agree_on_schema():
    canon, hard = savez_keywords(CANONICAL), savez_keywords(HARDNEG)
    assert canon == hard, (
        "hard-negative shards would be unreadable by ShardDataset; "
        f"only in canonical: {sorted(canon - hard)}; "
        f"only in hard-negative: {sorted(hard - canon)}")


@pytest.mark.parametrize("path", [CANONICAL, HARDNEG],
                         ids=lambda p: p.name)
def test_loader_fields_are_written(path: Path):
    missing = loader_fields() - savez_keywords(path)
    assert not missing, f"{path.name} never writes {sorted(missing)}"


if __name__ == "__main__":
    # Runnable without pytest: the cluster environment (deepsv2_new) has no
    # pytest, and this file is used there as a pre-extraction gate.
    test_extractors_agree_on_schema()
    for _p in (CANONICAL, HARDNEG):
        test_loader_fields_are_written(_p)
    print("PASS: extractors agree on shard schema and cover every loader field")
