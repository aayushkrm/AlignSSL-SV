"""Unit contracts for the real-read depth oracle utility."""
from types import SimpleNamespace

import numpy as np
import pytest

from scripts.validate_depth_oracle import (
    deterministic_starts,
    parse_regions,
    pileup_base_depth,
)


def _read(**flags):
    values = dict(is_unmapped=False, is_secondary=False,
                  is_supplementary=False, query_sequence="A")
    values.update(flags)
    return SimpleNamespace(**values)


def _item(query_position=0, **flags):
    return SimpleNamespace(alignment=_read(**flags),
                           query_position=query_position)


def test_pileup_oracle_counts_only_tensor_eligible_aligned_bases():
    columns = [
        SimpleNamespace(reference_pos=100, pileups=[
            _item(), _item(), _item(query_position=None),
            _item(is_secondary=True), _item(is_supplementary=True),
            _item(is_unmapped=True), _item(query_sequence=None),
        ]),
        SimpleNamespace(reference_pos=102, pileups=[_item()]),
        SimpleNamespace(reference_pos=105, pileups=[_item()]),
    ]
    assert np.array_equal(
        pileup_base_depth(columns, start=100, span=4),
        np.array([2, 0, 1, 0], dtype=np.float32),
    )


def test_deterministic_starts_cover_region_endpoints():
    assert deterministic_starts(100, 200, span=20, n=3) == [100, 140, 180]
    assert deterministic_starts(100, 200, span=20, n=1) == [140]


def test_invalid_window_grid_rejected():
    with pytest.raises(ValueError, match="exceeds"):
        deterministic_starts(100, 110, span=20, n=2)
    with pytest.raises(ValueError, match="positive"):
        deterministic_starts(100, 200, span=20, n=0)


def test_region_parser_uses_half_open_coordinates():
    assert parse_regions(["1:10-20"]) == [("1", 10, 20)]
    with pytest.raises(ValueError, match="Invalid region"):
        parse_regions(["1:20-10"])
