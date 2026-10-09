from pathlib import Path

import pytest

from analysis import run_native_cigar_fixture as launcher


@pytest.fixture
def synthetic_roots(tmp_path, monkeypatch):
    base = tmp_path.resolve()
    physical_workspace = base / "approved-physical-workspace"
    physical_workspace.mkdir()
    physical_root = physical_workspace / launcher.EXPERIMENT
    physical_root.mkdir()

    logical_workspace = base / "scratch-workspace"
    logical_workspace.symlink_to(physical_workspace, target_is_directory=True)
    logical_root = logical_workspace / launcher.EXPERIMENT

    monkeypatch.setattr(launcher, "ROOT", logical_root)
    monkeypatch.setattr(launcher, "PHYSICAL_ROOT", physical_root)
    return {
        "base": base,
        "physical_workspace": physical_workspace,
        "physical_root": physical_root,
        "logical_workspace": logical_workspace,
        "logical_root": logical_root,
    }


@pytest.mark.parametrize("root_name", ["logical_root", "physical_root"])
def test_resolves_only_the_logical_alias_or_exact_physical_root(
    synthetic_roots, root_name
):
    physical_root = synthetic_roots["physical_root"]

    resolved = launcher.resolve_experiment_root(synthetic_roots[root_name])

    assert resolved == physical_root
    assert resolved.is_absolute()
    assert not resolved.is_symlink()
    assert all(not parent.is_symlink() for parent in resolved.parents)


def test_rejects_unapproved_alias_destination(synthetic_roots):
    base = synthetic_roots["base"]
    other_workspace = base / "unapproved-physical-workspace"
    other_workspace.mkdir()
    (other_workspace / launcher.EXPERIMENT).mkdir()
    # Redirect the *allowed spelling*, rather than only an unexpected path.
    # This reaches the destination check after the lexical allowlist passes.
    logical_workspace = synthetic_roots["logical_workspace"]
    logical_workspace.unlink()
    logical_workspace.symlink_to(other_workspace, target_is_directory=True)

    with pytest.raises(ValueError, match="trusted physical path"):
        launcher.resolve_experiment_root(synthetic_roots["logical_root"])


def test_rejects_symlink_experiment_leaf(synthetic_roots, monkeypatch):
    linked_root = synthetic_roots["physical_workspace"] / "linked-experiment-leaf"
    linked_root.symlink_to(synthetic_roots["physical_root"], target_is_directory=True)
    monkeypatch.setattr(launcher, "ROOT", linked_root)

    with pytest.raises(ValueError):
        launcher.resolve_experiment_root(linked_root)


def test_rejects_missing_experiment_leaf(synthetic_roots, monkeypatch):
    missing_physical_root = (
        synthetic_roots["physical_workspace"] / "missing-experiment-leaf"
    )
    missing_logical_root = (
        synthetic_roots["logical_workspace"] / "missing-experiment-leaf"
    )
    monkeypatch.setattr(launcher, "ROOT", missing_logical_root)
    monkeypatch.setattr(launcher, "PHYSICAL_ROOT", missing_physical_root)

    with pytest.raises(ValueError):
        launcher.resolve_experiment_root(missing_logical_root)


def test_rejects_physical_root_with_symlink_ancestor(synthetic_roots, monkeypatch):
    aliased_workspace = synthetic_roots["base"] / "physical-ancestor-alias"
    aliased_workspace.symlink_to(
        synthetic_roots["physical_workspace"], target_is_directory=True
    )
    aliased_physical_root = aliased_workspace / launcher.EXPERIMENT
    monkeypatch.setattr(launcher, "PHYSICAL_ROOT", aliased_physical_root)

    with pytest.raises(ValueError):
        launcher.resolve_experiment_root(aliased_physical_root)


def test_rejects_unexpected_relative_parent_path(synthetic_roots):
    relative_root = Path("scratch-workspace") / ".." / "untrusted" / launcher.EXPERIMENT

    with pytest.raises(ValueError):
        launcher.resolve_experiment_root(relative_root)


def test_fixture_factory_uses_resolved_path_and_keeps_ancestor_guard(
    synthetic_roots,
):
    pytest.importorskip("pysam")
    from analysis.native_cigar_fixture import create_fixture

    logical_root = synthetic_roots["logical_root"]
    physical_root = launcher.resolve_experiment_root(logical_root)
    physical_output = physical_root / "fixture-through-physical-root"

    created = create_fixture(physical_output)

    assert created == physical_output
    assert (created / "manifest.json").is_file()
    with pytest.raises(ValueError, match="ancestors must not be links"):
        create_fixture(logical_root / "fixture-through-logical-alias")
