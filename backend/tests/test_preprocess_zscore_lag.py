"""SYNTHETIC — NOT STUDY DATA. Rolling z-score and lag against literal reference loops."""

import numpy as np
import pytest

from mindful.preprocess.lag import lag_within_block
from mindful.preprocess.zscore import rolling_zscore


def matlab_trailing_zscore(x: np.ndarray, k: int, floor: float) -> np.ndarray:
    """Literal loop: movmean/movstd(x, [k 0], 'omitnan'); std of one sample = 0; std<floor -> 1."""
    out = np.empty_like(x, dtype=float)
    for t in range(x.shape[0]):
        win = x[max(0, t - k) : t + 1]
        for c in range(x.shape[1]):
            v = win[:, c][~np.isnan(win[:, c])]
            mean = v.mean()
            std = 0.0 if v.size == 1 else v.std(ddof=1)
            out[t, c] = (x[t, c] - mean) / (1.0 if std < floor else std)
    return out


@pytest.mark.parametrize("k", [1, 7, 9000])
def test_matches_reference_loop(k: int) -> None:
    rng = np.random.default_rng(k)
    x = rng.gamma(2.0, 30.0, size=(120, 6))
    np.testing.assert_allclose(
        rolling_zscore(x, k, 1e-5), matlab_trailing_zscore(x, k, 1e-5), rtol=1e-9, atol=1e-9
    )


def test_first_bin_is_exactly_zero() -> None:
    x = np.random.default_rng(0).normal(5, 2, size=(50, 4))
    assert np.all(rolling_zscore(x, 9000, 1e-5)[0] == 0.0)


def test_constant_channel_uses_std_floor() -> None:
    x = np.column_stack([np.full(40, 3.0), np.arange(40.0)])
    z = rolling_zscore(x, 10, 1e-5)
    assert np.all(z[:, 0] == 0.0)


def test_window_is_trailing_not_centred() -> None:
    x = np.zeros((30, 1))
    x[20:] = 100.0  # a step later in time must not affect earlier bins
    z = rolling_zscore(x, 5, 1e-5)
    assert np.all(z[:20] == 0.0)
    assert z[20, 0] > 0


def test_nan_values_are_omitted_like_omitnan() -> None:
    rng = np.random.default_rng(3)
    x = rng.normal(size=(60, 3))
    x[10, 1] = np.nan
    x[33, 2] = np.nan
    z = rolling_zscore(x, 8, 1e-5)
    ref = matlab_trailing_zscore(x, 8, 1e-5)
    finite = np.isfinite(ref)
    np.testing.assert_allclose(z[finite], ref[finite], rtol=1e-9, atol=1e-9)


def test_all_nan_window_is_not_silently_filled() -> None:
    x = np.random.default_rng(1).normal(size=(20, 2))
    x[:3, 0] = np.nan
    with pytest.raises(ValueError, match="fillmissing"):
        rolling_zscore(x, 5, 1e-5)


def test_lag_shifts_by_exactly_one_and_zero_fills() -> None:
    x = np.arange(12.0).reshape(6, 2)
    lagged = lag_within_block(x, 1)
    assert np.all(lagged[0] == 0)
    np.testing.assert_array_equal(lagged[1:], x[:-1])
    np.testing.assert_array_equal(lag_within_block(x, 0), x)
