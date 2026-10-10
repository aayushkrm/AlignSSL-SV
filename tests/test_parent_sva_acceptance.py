from scripts.run_parent_sva_diagnostic import acceptance_fields


def test_pass_and_nonreference_genotype_are_separate():
    assert acceptance_fields(["PASS"], {"parent": {"GT": (0, 0)}}) == {
        "native_filter_pass": True, "has_nonreference_gt": False}


def test_filtered_nonreference_is_not_accepted():
    assert acceptance_fields(["MOSAIC_VAF"], {"parent": {"GT": (0, 1)}}) == {
        "native_filter_pass": False, "has_nonreference_gt": True}


def test_missing_filter_or_genotype_is_not_positive():
    assert acceptance_fields([], {"parent": {"GT": (None, None)}}) == {
        "native_filter_pass": False, "has_nonreference_gt": False}


def test_pass_nonreference_germline_can_be_separately_identified():
    flags = acceptance_fields(["PASS"], {"parent": {"GT": (0, 1)}})
    assert flags["native_filter_pass"] and flags["has_nonreference_gt"]
