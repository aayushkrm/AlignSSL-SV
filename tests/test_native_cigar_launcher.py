import io
import tarfile

import pytest

from analysis.run_native_cigar_fixture import (
    extract_binary, new_json, tree_size, validate_outcome,
)


def _tar(path, names, *, link=False):
    with tarfile.open(path, "w:gz") as archive:
        for name in names:
            info = tarfile.TarInfo(name)
            if link:
                info.type = tarfile.SYMTYPE
                info.linkname = "/outside"
                archive.addfile(info)
            else:
                info.size = 4
                archive.addfile(info, io.BytesIO(b"TEST"))


def test_extraction_selects_only_executable_and_preserves_destination(tmp_path):
    archive = tmp_path / "asset.tar.gz"
    _tar(archive, ["release/bin/sawfish", "release/README"])
    target = tmp_path / "sawfish"
    assert len(extract_binary(archive, target)) == 64
    assert target.read_bytes() == b"TEST"
    assert not (tmp_path / "release").exists()
    with pytest.raises(FileExistsError):
        extract_binary(archive, target)
    assert target.read_bytes() == b"TEST"


@pytest.mark.parametrize("names,link", [
    (["../sawfish"], False), (["/sawfish"], False),
    (["sawfish"], True), (["one/sawfish", "two/sawfish"], False),
])
def test_unsafe_or_ambiguous_archive_is_rejected(tmp_path, names, link):
    archive = tmp_path / "asset.tar.gz"
    _tar(archive, names, link=link)
    with pytest.raises(ValueError):
        extract_binary(archive, tmp_path / "sawfish")
    assert not (tmp_path / "sawfish").exists()


def test_tree_caps_and_links_are_rejected(tmp_path):
    tree = tmp_path / "tree"
    tree.mkdir()
    (tree / "file").write_bytes(b"1234")
    assert tree_size(tree, 4) == 4
    with pytest.raises(ValueError):
        tree_size(tree, 3)
    (tree / "link").symlink_to(tree / "file")
    with pytest.raises(ValueError, match="link"):
        tree_size(tree, 4)


def test_metadata_is_exclusive(tmp_path):
    path = tmp_path / "claim.json"
    new_json(path, {"one": True})
    original = path.read_bytes()
    with pytest.raises(FileExistsError):
        new_json(path, {"two": True})
    assert path.read_bytes() == original


def _report(candidate="ABSENT_FROM_OUTPUT", final="ABSENT_FROM_OUTPUT", recovered=0):
    return {"candidate": {"single_record_output_state": candidate},
            "final": {"single_record_output_state": final,
                      "pass_heterozygous_exact_allele_records": recovered}}


def test_controller_uses_states_not_only_individual_unresolved_counts():
    validate_outcome("reference_only", _report())
    validate_outcome("canonical", _report("PRESENT", "PRESENT", 1))
    with pytest.raises(ValueError, match="unresolved"):
        validate_outcome("fragmented", _report("UNRESOLVED"))
    with pytest.raises(ValueError, match="canonical"):
        validate_outcome("canonical", _report())
    with pytest.raises(ValueError, match="negative control"):
        validate_outcome("reference_only", _report("PRESENT"))
