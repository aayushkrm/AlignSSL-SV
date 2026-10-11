import importlib.metadata
import importlib.util
import sys
from types import SimpleNamespace

import pytest

from scripts import probe_released_reference_controls as probe


class _Record:
    id = "synthetic"

    def __init__(self, ref, alt, svlen, svtype, native_size, native_type):
        self.ref = ref
        self.alts = (alt,)
        self.info = {"SVLEN": svlen, "SVTYPE": svtype}
        self._native_size = native_size
        self._native_type = native_type

    def var_size(self):
        return self._native_size

    def var_type(self):
        return self._native_type


class _Truvari:
    class SV:
        INS = object()
        DEL = object()


def test_canonical_allele_length_and_type():
    assert probe._canonical("A", "ATT") == {"type": "INS", "size": 2, "svlen": 2}
    assert probe._canonical("ACGT", "A") == {"type": "DEL", "size": 3, "svlen": -3}
    for ref, alt in (("ACG", "ATTGG"), ("AN", "A")):
        with pytest.raises(RuntimeError):
            probe._canonical(ref, alt)


def test_wrong_truth_svlen_and_svtype_fail_independently():
    deletion = ("ACGT", "A", -3, "DEL", 3, _Truvari.SV.DEL)
    valid = probe._audit_record(_Record(*deletion), _Truvari)
    wrong_length = probe._audit_record(_Record("ACGT", "A", -2, "DEL", 3, _Truvari.SV.DEL), _Truvari)
    wrong_type = probe._audit_record(_Record("ACGT", "A", -3, "INS", 3, _Truvari.SV.DEL), _Truvari)

    assert all(valid["checks"].values())
    assert wrong_length["checks"] == {
        "native_size_matches_canonical": True,
        "native_type_matches_canonical": True,
        "info_svlen_matches_canonical": False,
        "info_svtype_matches_canonical": True,
    }
    assert wrong_type["checks"] == {
        "native_size_matches_canonical": True,
        "native_type_matches_canonical": True,
        "info_svlen_matches_canonical": True,
        "info_svtype_matches_canonical": False,
    }


def test_versions_use_pysam_version_metadata(monkeypatch):
    fake_version = SimpleNamespace(__bcftools_version__="1.23.1", __htslib_version__="1.23.1")
    monkeypatch.setitem(sys.modules, "pysam.version", fake_version)
    monkeypatch.setattr(importlib.metadata, "version", lambda package: "5.4.0")

    result = probe._versions(SimpleNamespace(__version__="0.24.0"))

    assert result["pysam"] == "0.24.0"
    assert result["bcftools"] == result["htslib"] == "1.23.1"
    assert result["truvari"] == "5.4.0"


def test_pinned_cluster_synthetic_probe():
    if not importlib.util.find_spec("pysam"):
        pytest.skip("cluster-only integration skipped: pysam is not installed")
    import pysam
    from pysam.version import __bcftools_version__, __htslib_version__

    if not importlib.util.find_spec("truvari"):
        pytest.skip(
            "cluster-only integration skipped: local stack has "
            f"pysam {pysam.__version__}/bcftools {__bcftools_version__}; "
            "Truvari is absent; requires pysam 0.24.0/bcftools 1.23.1/Truvari 5.4.0"
        )
    try:
        truvari_version = importlib.metadata.version("truvari")
    except importlib.metadata.PackageNotFoundError:
        pytest.skip("cluster-only integration skipped: Truvari package metadata is unavailable")
    observed = (pysam.__version__, __bcftools_version__, __htslib_version__, truvari_version)
    expected = ("0.24.0", "1.23.1", "1.23.1", "5.4.0")
    if observed != expected:
        pytest.skip(f"cluster-only integration skipped: requires {expected}; local stack is {observed}")

    result = probe.run_probe()

    assert result["status"] == "pass"
    assert result["scope"] == "synthetic_only"
    assert all(result["assertions"].values())
