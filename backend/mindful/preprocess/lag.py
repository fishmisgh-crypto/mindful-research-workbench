"""Lagged copy of a signal within each block, ported from `MINDFUL.getlagX`."""

import numpy as np
import numpy.typing as npt

FloatArray = npt.NDArray[np.float64]


def lag_within_block(x: FloatArray, lag: int) -> FloatArray:
    """out[t] = x[t - lag]; the first `lag` bins of the block are zero."""
    if lag < 0:
        raise ValueError("lag must be non-negative")
    out = np.zeros_like(x, dtype=np.float64)
    if lag < x.shape[0]:
        out[lag:] = x[: x.shape[0] - lag]
    return out
