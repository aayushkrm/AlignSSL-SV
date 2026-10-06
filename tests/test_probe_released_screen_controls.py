import importlib.metadata
import importlib.util
import pytest

from scripts import probe_released_screen_controls as probe


def test_paired_readers_reject_length_or_full_row_mismatch():
    assert list(probe._paired_records(["rowA"], ["rowA"])) == [("rowA", "rowA")]
    for raw, native in ((["rowA"], []), ([], ["rowA"]), (["idGT01"], ["idGT11"])):
        with pytest.raises(RuntimeError, match="reader"):
            list(probe._paired_records(raw, native))


def test_fixed_controls_and_header():
    args = probe._args("truvari", "truth", "calls", "out", "ref")
    fixed = (("-s", "50"), ("-S", "30"), ("--sizemax", "-1"), ("-r", "1000"),
             ("-p", "0"), ("-P", "0.5"), ("-O", "0"), ("--bnddist", "-1"), ("--pick", "multi"))
    assert all(args[args.index(k) + 1] == v for k, v in fixed)
    assert all(k in args for k in ("--dup-to-ins", "--no-decompose"))
    assert all(k not in args for k in ("--passonly", "--no-ref"))
    assert "##FORMAT=<ID=PS" not in probe.HEADER
    assert all(k in probe.HEADER for k in ("##FORMAT=<ID=GT", "##FORMAT=<ID=AD,Number=R",
                                           "##INFO=<ID=SVLEN,Number=1", "##INFO=<ID=SVTYPE,Number=1"))
    assert all(f'##FILTER=<ID={f},' in probe.HEADER for f in ("HET1", "HET2", "GAP1", "GAP2"))
    assert all(f"##contig=<ID={n},length={z}>" in probe.HEADER for n, z in zip(probe.NAMES, probe.LENGTHS))


def test_pinned_synthetic_end_to_end_probe():
    if not importlib.util.find_spec("pysam") or not importlib.util.find_spec("truvari"):
        pytest.skip("pinned Truvari/pysam stack is not installed")
    import pysam
    if importlib.metadata.version("truvari") != "5.4.0" or pysam.__version__ != "0.24.0":
        pytest.skip("requires cluster-pinned Truvari 5.4.0 / pysam 0.24.0")
    result = probe.run_probe()
    assert result["status"] in ("pass", "pass_with_limitations")
    controls = result["coordinate_controls"]
    for key, coord in (("pos0_and_nplus1", "pos0"), ("nplus1_only", "nplus1")):
        item = controls[key]
        if key == "pos0_and_nplus1": assert item["source_records"] == 2
        if item["status"] != "pass": assert item["stage"] in ("norm", "sort", "index") and coord in item["limitation"]
    counts = result["fixture_counts"]
    assert (counts["decomposed_children"], counts["native_kept_dot_filter"], counts["native_filtered_children"]) == (6, 1, 3)
    assert result["bench"]["truth_denominator_unchanged"] is True
    assert result["bench"]["as_released"]["truth_ids_sha256"] == result["bench"]["native_filtered"]["truth_ids_sha256"]
    assert result["bench"]["lenient_one_to_many"] is True
    assert result["bench"]["duplicate_truth_multiplicity_preserved"] is True
    assert result["bench"]["nonempty_fn_identity_preserved"] is True
    assert counts["truth_records"] == 4 and counts["duplicate_truth_event_rows"] == 2
    assert result["full_row_sort_and_native_preservation"] is True
    assert result["identity_safe_reader_pairing"] is True
