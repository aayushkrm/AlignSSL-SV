"""Contracts for corrected read-thinning and mask-aware row pooling."""
import torch

from alignssl.encoder import AlignEncoder
from alignssl.ssl import subsample_rows
from alignssl.tensorize import Q_DEPTH, Q_MASK, REF_ONEHOT


def _tensor(rows=5, width=8):
    x = torch.zeros(1, 18, rows, width)
    x[:, Q_DEPTH] = torch.linspace(0.1, 0.8, width)[None, None, :]
    x[:, REF_ONEHOT.start] = 1.0
    for row, value in zip([0, 2, 4], [0.2, 0.4, 0.6]):
        if row < rows:
            x[0, 6, row] = value
            x[0, Q_MASK, row] = 1.0
    return x


def test_corrected_row_view_preserves_global_channels_and_compacts_reads():
    x = _tensor()
    out = subsample_rows(
        x, 0.5, generator=torch.Generator().manual_seed(4),
        mode="preserve_globals_compact",
    )
    assert torch.equal(out[:, Q_DEPTH], x[:, Q_DEPTH])
    assert torch.equal(out[:, REF_ONEHOT], x[:, REF_ONEHOT])
    real = (out[0, Q_MASK].sum(dim=1) > 0).nonzero(as_tuple=True)[0]
    assert real.tolist() == [0, 1]
    kept_values = out[0, 6, real, 0]
    allowed = torch.tensor([0.2, 0.4, 0.6])
    assert all(torch.isclose(value, allowed).any() for value in kept_values)
    assert torch.all(kept_values[1:] >= kept_values[:-1])
    assert torch.count_nonzero(out[0, :Q_DEPTH, 2:]) == 0
    assert torch.count_nonzero(out[0, Q_MASK, 2:]) == 0


def test_keep_all_is_bitwise_identity_in_both_modes():
    x = _tensor()
    for mode in ["legacy", "preserve_globals_compact"]:
        assert torch.equal(subsample_rows(x, 1.0, mode=mode), x)


def test_legacy_view_remains_available_and_zeros_broadcast_channels():
    x = _tensor()
    out = subsample_rows(
        x, 0.5, generator=torch.Generator().manual_seed(4), mode="legacy")
    dropped = (out[0, Q_MASK].sum(dim=1) == 0) & (
        x[0, Q_MASK].sum(dim=1) > 0)
    assert dropped.any()
    assert torch.count_nonzero(out[0, Q_DEPTH, dropped]) == 0


def test_mask_aware_encoder_is_invariant_to_appended_padding_rows():
    torch.manual_seed(3)
    x = torch.rand(1, 18, 2, 16)
    x[:, Q_MASK] = 1.0
    padded = torch.zeros(1, 18, 5, 16)
    padded[:, :, :2] = x
    # Tensorization broadcasts globals into padding; mask-aware input gating
    # must make these extra rows semantically absent.
    padded[:, Q_DEPTH, 2:] = x[:, Q_DEPTH, :1]
    padded[:, REF_ONEHOT, 2:] = x[:, REF_ONEHOT, :1]
    enc = AlignEncoder(stem_ch=4, body_ch=8, n_res=1, d_model=8,
                       n_tx=1, n_heads=2, row_pool_mode="mask_aware").eval()
    with torch.no_grad():
        base_embedding = enc(x)
        padded_embedding = enc(padded)
    torch.testing.assert_close(base_embedding, padded_embedding,
                               rtol=1e-5, atol=1e-6)


def test_row_pool_modes_share_a_strictly_compatible_state_dict():
    legacy = AlignEncoder(stem_ch=4, body_ch=8, n_res=1, d_model=8,
                          n_tx=1, n_heads=2, row_pool_mode="legacy")
    corrected = AlignEncoder(stem_ch=4, body_ch=8, n_res=1, d_model=8,
                             n_tx=1, n_heads=2, row_pool_mode="mask_aware")
    corrected.load_state_dict(legacy.state_dict(), strict=True)


def test_invalid_row_modes_fail_loudly():
    x = _tensor()
    try:
        subsample_rows(x, 0.5, mode="unknown")
    except ValueError as exc:
        assert "row view mode" in str(exc)
    else:
        raise AssertionError("invalid row view mode was accepted")
    try:
        AlignEncoder(row_pool_mode="unknown")
    except ValueError as exc:
        assert "row_pool_mode" in str(exc)
    else:
        raise AssertionError("invalid row pool mode was accepted")
