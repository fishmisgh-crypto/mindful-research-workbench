"""Causal rolling z-score per channel, ported from `utils/BGzscoreNew.m`.

Upstream call: `movmean(x, [K 0], 'omitnan')` and `movstd(x, [K 0], 'omitnan')`
with K = 9000, i.e. the current bin plus up to K previous bins of the same block.
`movstd` normalises by N-1 and returns 0 for a single sample; any std < 1e-5 is
replaced by 1, so the first bin of a block z-scores to exactly 0.
"""

import numpy as np
import numpy.typing as npt
import pandas as pd

FloatArray = npt.NDArray[np.float64]


def rolling_stats(x: FloatArray, trailing_bins: int) -> tuple[FloatArray, FloatArray]:
    """Trailing mean and std (ddof=1, 0 for one sample), NaN-omitting, per column."""
    frame = pd.DataFrame(x)
    roll = frame.rolling(window=trailing_bins + 1, min_periods=1)
    mean = roll.mean().to_numpy(copy=True)
    std = roll.std(ddof=1).to_numpy(copy=True)
    count = roll.count().to_numpy()
    std[count == 1] = 0.0
    if np.isnan(mean).any() or np.isnan(std[count > 1]).any():
        # Upstream fills all-NaN windows with fillmissing(..., 'linear'); not ported
        # because the study data contain no NaN neural values.
        raise ValueError("rolling window with no finite samples: fillmissing path not ported")
    return mean, std


def rolling_zscore(x: FloatArray, trailing_bins: int, std_floor: float) -> FloatArray:
    """z = (x - trailing mean) / trailing std, with std < std_floor replaced by 1."""
    mean, std = rolling_stats(np.asarray(x, dtype=np.float64), trailing_bins)
    std = np.where(std < std_floor, 1.0, std)
    out: FloatArray = (x - mean) / std
    return out
