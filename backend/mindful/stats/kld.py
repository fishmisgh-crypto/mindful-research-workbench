"""Gaussian KL divergence D_KL(P_reference || P_current), ported from `CalcKL.m`.

    D = 1/2 [ tr(S_cur^-1 S_ref) + (m_cur - m_ref)' S_cur^-1 (m_cur - m_ref)
              - k + ln det S_cur - ln det S_ref ]

Upstream checks `rank(S_cur)` and returns NaN when it is deficient, then uses
`inv()`. Here: the same MATLAB rank test, then a Cholesky factorisation and
`cho_solve`; log-determinants come from the Cholesky diagonal. No
regularisation. A window that cannot be evaluated gets NaN and a reason code.
"""

from dataclasses import dataclass
from typing import Literal

import numpy as np
import numpy.typing as npt
from scipy.linalg import LinAlgError, cho_factor, cho_solve

from mindful.stats.gaussian import Gaussian

FloatArray = npt.NDArray[np.float64]
Reason = Literal["ok", "rank_deficient", "not_positive_definite", "non_finite", "too_few_bins"]


@dataclass(frozen=True)
class Reference:
    """Reference distribution with its log-determinant precomputed."""

    gaussian: Gaussian
    logdet: float
    condition: float


@dataclass(frozen=True)
class KldResult:
    value: float
    reason: Reason
    rank: int
    condition: float


def matlab_rank(a: FloatArray) -> tuple[int, FloatArray]:
    """MATLAB `rank`: singular values above max(size) * eps(max singular value)."""
    s = np.linalg.svd(a, compute_uv=False)
    tol = max(a.shape) * np.spacing(s[0]) if s.size and s[0] > 0 else 0.0
    return int(np.sum(s > tol)), s


def _condition(s: FloatArray) -> float:
    return float(s[0] / s[-1]) if s.size and s[-1] > 0 else float("inf")


def prepare_reference(g: Gaussian) -> Reference:
    """Validate the reference; a singular reference is a configuration error, not a NaN."""
    if not (np.isfinite(g.mean).all() and np.isfinite(g.cov).all()):
        raise ValueError("reference distribution has non-finite values")
    rank, s = matlab_rank(g.cov)
    if rank < g.dim:
        raise ValueError(f"reference covariance is rank {rank} < {g.dim}")
    try:
        c, _ = cho_factor(g.cov, lower=True)
    except LinAlgError as exc:
        raise ValueError("reference covariance is not positive definite") from exc
    return Reference(
        gaussian=g, logdet=float(2 * np.log(np.diag(c)).sum()), condition=_condition(s)
    )


def kl_divergence(ref: Reference, cur: Gaussian) -> KldResult:
    """D_KL(ref || cur). Argument order is fixed: reference first."""
    k = ref.gaussian.dim
    if cur.n < 2:
        return KldResult(float("nan"), "too_few_bins", 0, float("nan"))
    if not (np.isfinite(cur.mean).all() and np.isfinite(cur.cov).all()):
        return KldResult(float("nan"), "non_finite", 0, float("nan"))
    rank, s = matlab_rank(cur.cov)
    condition = _condition(s)
    if rank < k:
        return KldResult(float("nan"), "rank_deficient", rank, condition)
    try:
        factor = cho_factor(cur.cov, lower=True)
    except LinAlgError:
        return KldResult(float("nan"), "not_positive_definite", rank, condition)
    logdet_cur = float(2 * np.log(np.diag(factor[0])).sum())
    diff = cur.mean - ref.gaussian.mean
    trace = float(np.trace(cho_solve(factor, ref.gaussian.cov)))
    quad = float(diff @ cho_solve(factor, diff))
    value = 0.5 * (trace + quad - k + logdet_cur - ref.logdet)
    return KldResult(value, "ok", rank, condition)
