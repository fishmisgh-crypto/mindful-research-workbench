"""Correlation between window KLD and median AE, as `corr(..., 'rows', 'complete')`.

Only pairs where both values are finite enter. No smoothing (`nsmooth = 1` upstream).
Correlation measures association; it is not an accuracy.
"""

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt
from scipy import stats

FloatArray = npt.NDArray[np.float64]


@dataclass(frozen=True)
class Correlation:
    pearson_r: float
    pearson_p: float
    spearman_rho: float
    spearman_p: float
    n: int


def correlate(x: FloatArray, y: FloatArray) -> Correlation:
    """Pearson and Spearman on pairwise-complete observations."""
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    ok = np.isfinite(x) & np.isfinite(y)
    n = int(ok.sum())
    if n < 3:
        nan = float("nan")
        return Correlation(nan, nan, nan, nan, n)
    pr = stats.pearsonr(x[ok], y[ok])
    sr = stats.spearmanr(x[ok], y[ok])
    return Correlation(
        pearson_r=float(pr.statistic),
        pearson_p=float(pr.pvalue),
        spearman_rho=float(sr.statistic),
        spearman_p=float(sr.pvalue),
        n=n,
    )
