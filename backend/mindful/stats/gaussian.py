"""Gaussian estimate of a window, ported from `utils/dist_metrics/ProbDistributionEst.m`.

D1: upstream uses the uncentred second moment X'X/n as the "covariance" while
still using the sample mean in the KLD; the paper says "sample covariance".
Both are available; neither is the default here, the preset chooses.
"""

from dataclasses import dataclass
from typing import Literal

import numpy as np
import numpy.typing as npt

FloatArray = npt.NDArray[np.float64]
CovarianceEstimator = Literal["uncentered_second_moment", "sample_covariance"]


@dataclass(frozen=True)
class Gaussian:
    mean: FloatArray  # (k,)
    cov: FloatArray  # (k, k)
    n: int

    @property
    def dim(self) -> int:
        return int(self.mean.size)


def estimate(x: FloatArray, estimator: CovarianceEstimator) -> Gaussian:
    """Mean and covariance of the rows of x (bins x features)."""
    data = np.asarray(x, dtype=np.float64)
    n, k = data.shape
    mean = data.mean(axis=0) if n else np.full(k, np.nan)
    if estimator == "uncentered_second_moment":
        cov = data.T @ data / n if n else np.full((k, k), np.nan)
    elif estimator == "sample_covariance":
        centred = data - mean
        cov = centred.T @ centred / (n - 1) if n > 1 else np.full((k, k), np.nan)
    else:
        raise ValueError(f"unknown covariance estimator {estimator!r}")
    return Gaussian(mean=mean, cov=cov, n=n)
