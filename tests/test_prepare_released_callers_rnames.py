"""Synthetic controls for the optional INFO/RNAMES preparation policy."""
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

_HELPERS_SPEC = importlib.util.spec_from_file_location(
    "_prepare_released_callers_test_helpers",
    Path(__file__).with_name("test_prepare_released_callers.py"),
)
_helpers = importlib.util.module_from_spec(_HELPERS_SPEC)
_HELPERS_SPEC.loader.exec_module(_helpers)

prep = _helpers.prep
case = _helpers.case
run_case = _helpers.run_case
local_tools = _helpers.local_tools

OMIT_IDENTITY_INFO = ("RNAMES", *prep.TAGS)
VCF_OUTPUTS = ("annotated", "split", "derived", "sorted", "released", "native", "native_bgzf")


def _rnames_source(*, large=False):
    header = _helpers.HEADER.replace(
        '##INFO=<ID=AF,Number=A,Type=Float,Description="Synthetic">\n',
        '##INFO=<ID=RNAMES,Number=.,Type=String,Description="Synthetic read names">\n'
        '##INFO=<ID=AF,Number=A,Type=Float,Description="Synthetic">\n',
    )
    long_name = "synthetic_read_" + "x" * 65_536 if large else ""
    first_value = long_name if large else "read_a,read_b"
    rows = _helpers.ROWS.replace(
        "AF=0.1,0.2;", f"RNAMES={first_value};AF=0.1,0.2;", 1
    ).replace("AF=.;DP=5;", "RNAMES=read_third;AF=.;DP=5;", 1)
    return header + rows, long_name


def _case_with_rnames(tmp_path, *, large=False, **updates):
    raw, long_name = _rnames_source(large=large)
    source, protocol, out = case(tmp_path, raw=raw, **updates)
    protocol["max_line_bytes"] = 128 * 1024
    return source, protocol, out, raw.encode(), long_name


def _read_vcf(pysam, path):
    with pysam.VariantFile(str(path)) as reader:
        header = reader.header
        declared = "RNAMES" in header.info
        declaration = (header.info["RNAMES"].number, header.info["RNAMES"].type,
                       header.info["RNAMES"].description) if declared else None
        records = list(reader)
    return declared, declaration, records


def _semantic(record, omitted_info):
    return json.loads(prep._semantic_child(record, omitted_info=omitted_info))


def _assert_rnames_pipeline(pysam, source, out, source_bytes, *, omitted):
    assert source.read_bytes() == source_bytes
    assert hashlib.sha256(source.read_bytes()).hexdigest() == hashlib.sha256(source_bytes).hexdigest()

    source_declared, source_declaration, source_records = _read_vcf(pysam, source)
    assert source_declared
    assert source_declaration == (".", "String", "Synthetic read names")

    source_omissions = ("RNAMES",) if omitted else ()
    output_omissions = (*source_omissions, *prep.TAGS)
    source_semantics = {}
    expected_children = {}
    expected_rnames_presence = {}
    for ordinal, record in enumerate(source_records, 1):
        source_semantics[ordinal] = _semantic(record, source_omissions)
        has_rnames = "RNAMES" in record.info
        for alt_index in range(1, len(record.alts) + 1):
            pair = (ordinal, alt_index)
            expected_children[pair] = json.loads(
                prep._semantic_child(record, alt_index, omitted_info=source_omissions)
            )
            expected_rnames_presence[pair] = has_rnames and not omitted

    all_pairs = set(expected_children)
    native_pairs = {pair for pair in all_pairs if pair[0] != 3}
    for key in VCF_OUTPUTS:
        declared, declaration, records = _read_vcf(pysam, out / prep.FILES[key])
        assert declared, f"{key} dropped the RNAMES header declaration"
        assert declaration == source_declaration

        observed_pairs = set()
        for record in records:
            ordinal = record.info[prep.TAGS[0]]
            if key == "annotated":
                assert ordinal not in observed_pairs
                observed_pairs.add(ordinal)
                observed = _semantic(record, output_omissions)
                assert observed == source_semantics[ordinal]
                pair = (ordinal, 1)
                has_rnames = "RNAMES" in record.info
                assert has_rnames == (expected_rnames_presence[pair])
                if omitted:
                    assert not has_rnames
                continue

            alt_index = prep._one(record.info[prep.TAGS[1]])
            pair = (ordinal, alt_index)
            assert pair not in observed_pairs
            observed_pairs.add(pair)
            expected = expected_children[pair]
            observed = _semantic(record, output_omissions)
            if key not in {"annotated", "split"}:
                assert record.id == prep.child_identity(
                    hashlib.sha256(source_bytes).hexdigest(), ordinal, alt_index
                )
                # The derived views replace the caller ID with the stable child ID.
                observed[4] = expected[4]
            else:
                assert record.id == expected[4]
            assert observed == expected, f"non-RNAMES field changed in {key} for {pair}"
            has_rnames = "RNAMES" in record.info
            assert has_rnames == expected_rnames_presence[pair]
            if omitted:
                assert not has_rnames

        expected_pairs = ({1, 2, 3} if key == "annotated" else
                          native_pairs if key in {"native", "native_bgzf"} else all_pairs)
        assert observed_pairs == expected_pairs, f"source/ALT identities changed in {key}"


@pytest.mark.parametrize("value", [0, 1, "true", None])
def test_nonboolean_rnames_policy_is_rejected_before_runtime(tmp_path, monkeypatch, value):
    source, protocol, out, _, _ = _case_with_rnames(
        tmp_path, omit_info_rnames=value
    )
    monkeypatch.setattr(prep, "_runtime", lambda: pytest.fail("runtime reached after bad policy"))
    with pytest.raises(ValueError, match="omit_info_rnames must be a boolean"):
        run_case(tmp_path, source, protocol, out)
    assert not out.exists()


def test_opt_in_omits_only_rnames_values_and_preserves_source(tmp_path, local_tools):
    source, protocol, out, source_bytes, long_name = _case_with_rnames(
        tmp_path, large=True, omit_info_rnames=True
    )
    assert len(long_name) >= 64 * 1024
    assert long_name.encode() in source_bytes
    report = run_case(tmp_path, source, protocol, out)

    pysam, _, _ = local_tools
    assert report["info_rnames_policy"] == "omit_values_only"
    assert report["counts"]["info_rnames_rows_removed"] == 2
    _assert_rnames_pipeline(pysam, source, out, source_bytes, omitted=True)


@pytest.mark.parametrize(
    "updates,explicit",
    [({}, False), ({"omit_info_rnames": False}, True)],
    ids=("absent", "explicit-false"),
)
def test_absent_or_false_protocol_policy_defaults_to_preserve(
        tmp_path, local_tools, updates, explicit):
    source, protocol, out, source_bytes, _ = _case_with_rnames(tmp_path, **updates)
    assert ("omit_info_rnames" in protocol) is explicit
    report = run_case(tmp_path, source, protocol, out)

    pysam, _, _ = local_tools
    assert report["info_rnames_policy"] == "preserve"
    assert report["counts"]["info_rnames_rows_removed"] == 0
    _assert_rnames_pipeline(pysam, source, out, source_bytes, omitted=False)


def test_other_info_corruption_still_fails_norm_when_rnames_omitted(
        tmp_path, local_tools, monkeypatch):
    source, protocol, out, source_bytes, _ = _case_with_rnames(
        tmp_path, omit_info_rnames=True
    )
    pysam, bcftools, _ = local_tools
    runtime = prep._runtime()

    def corrupt_norm(*args, **kwargs):
        bcftools.norm(*args, **kwargs)
        path = Path(args[args.index("-o") + 1])
        lines = path.read_text().splitlines(True)
        for index, line in enumerate(lines):
            if not line.startswith("#") and "DP=10" in line:
                lines[index] = line.replace("DP=10", "DP=999", 1)
                break
        else:
            raise AssertionError("synthetic DP field not found after norm")
        path.write_text("".join(lines))

    stub = type("BcftoolsStub", (), {"norm": staticmethod(corrupt_norm),
                                     "sort": staticmethod(bcftools.sort)})
    monkeypatch.setattr(prep, "_runtime", lambda: (pysam, stub, runtime[2], runtime[3]))
    with pytest.raises(prep.CallerPreparationError, match="norm source ALT identity/projected"):
        run_case(tmp_path, source, protocol, out)

    failure = json.loads((out / "caller_preparation_failure.json").read_text())
    assert failure["failed_phase"] == "norm"
    assert failure["counts"]["info_rnames_rows_removed"] == 2
    assert source.read_bytes() == source_bytes
    assert not (out / "caller_preparation_report.json").exists()


def test_norm_rnames_reinsertion_fails_projection_when_omitted(
        tmp_path, local_tools, monkeypatch):
    source, protocol, out, source_bytes, _ = _case_with_rnames(
        tmp_path, omit_info_rnames=True
    )
    pysam, bcftools, _ = local_tools
    runtime = prep._runtime()

    def reinsert_norm(*args, **kwargs):
        bcftools.norm(*args, **kwargs)
        path = Path(args[args.index("-o") + 1])
        lines = path.read_text().splitlines(True)
        for index, line in enumerate(lines):
            if not line.startswith("#") and "DP=10" in line and "RNAMES=" not in line:
                fields = line.rstrip("\n").split("\t")
                fields[7] += ";RNAMES=synthetic_read_reinserted"
                lines[index] = "\t".join(fields) + "\n"
                break
        else:
            raise AssertionError("synthetic norm row for RNAMES reinsertion not found")
        path.write_text("".join(lines))

    stub = type("BcftoolsStub", (), {"norm": staticmethod(reinsert_norm),
                                     "sort": staticmethod(bcftools.sort)})
    monkeypatch.setattr(prep, "_runtime", lambda: (pysam, stub, runtime[2], runtime[3]))
    with pytest.raises(prep.CallerPreparationError, match="norm source ALT identity/projected"):
        run_case(tmp_path, source, protocol, out)

    failure = json.loads((out / "caller_preparation_failure.json").read_text())
    assert failure["failed_phase"] == "norm"
    assert failure["failure_type"] == "CallerPreparationGuardError"
    assert "norm source ALT identity/projected whole-field multiset differs" in failure["failure"]
    assert source.read_bytes() == source_bytes
    assert not (out / "caller_preparation_report.json").exists()


@pytest.mark.parametrize("error_type", [RuntimeError, ValueError], ids=("runtime-error", "builtin-value-error"))
def test_external_norm_errors_are_sanitized_in_failure_report(
        tmp_path, local_tools, monkeypatch, error_type):
    source, protocol, out, source_bytes, _ = _case_with_rnames(
        tmp_path, omit_info_rnames=True
    )
    pysam, bcftools, _ = local_tools
    runtime = prep._runtime()
    secret = "RNAMES=synthetic_read_secret"

    def failing_norm(*args, **kwargs):
        raise error_type(f"synthetic external parser diagnostic: {secret}")

    stub = type("BcftoolsStub", (), {"norm": staticmethod(failing_norm),
                                     "sort": staticmethod(bcftools.sort)})
    monkeypatch.setattr(prep, "_runtime", lambda: (pysam, stub, runtime[2], runtime[3]))
    with pytest.raises(prep.CallerPreparationError):
        run_case(tmp_path, source, protocol, out)

    failure_path = out / "caller_preparation_failure.json"
    failure_bytes = failure_path.read_bytes()
    failure = json.loads(failure_bytes)
    assert failure["failed_phase"] == "norm"
    assert failure["failure_type"] == error_type.__name__
    assert failure["failure"] == (
        "External parser/tool error; inspect retained cluster diagnostics before archival."
    )
    assert secret.encode() not in failure_bytes
    assert source.read_bytes() == source_bytes
    assert not (out / "caller_preparation_report.json").exists()


def test_pinned_runtime_opt_in_rnames_control_when_available(tmp_path):
    import importlib.util
    import sys

    if not importlib.util.find_spec("truvari"):
        pytest.skip(f"pinned runtime requires Truvari; absent locally (Python {sys.version.split()[0]})")
    try:
        pysam, _, _, versions = prep._runtime()
    except (ImportError, ValueError) as exc:
        pytest.skip(f"pinned runtime unavailable: {exc}")

    source, protocol, out, source_bytes, _ = _case_with_rnames(
        tmp_path, omit_info_rnames=True
    )
    report = run_case(tmp_path, source, protocol, out)
    assert versions == prep.RUNTIME and report["runtime"] == prep.RUNTIME
    assert report["info_rnames_policy"] == "omit_values_only"
    assert report["counts"]["info_rnames_rows_removed"] == 2
    _assert_rnames_pipeline(pysam, source, out, source_bytes, omitted=True)
