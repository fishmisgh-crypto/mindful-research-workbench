"""KLD of bins grouped by angular error (Fig 1b), ported from `fig1_grouped_by_AE.m`.

Upstream: reference = every kept-trial bin with AE < 4 across all sessions; PCA
fitted on it; edges 0:4:176 give 45 bins [a, a+4), but the loop runs to
`length(AErange) - 1`, so only 44 bins (up to [172, 176)) are computed. The paper
text says 45 bins. Both counts are supported; the x value is the mean AE of the
bin and r is a Pearson correlation across bins.
"""

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

from mindful.preprocess.pipeline import PreparedParticipant
from mindful.stats.correlation import Correlation, correlate
from mindful.stats.gaussian import CovarianceEstimator, estimate
from mindful.stats.kld import kl_divergence, prepare_reference

FloatArray = npt.NDArray[np.float64]

UPSTREAM_N_BINS = 44  # loop bound in fig1_grouped_by_AE.m
PAPER_N_BINS = 45


@dataclass(frozen=True)
class AeBinned:
    lower_deg: FloatArray
    mean_ae: FloatArray
    kld: FloatArray
    n_bins_each: npt.NDArray[np.int64]
    reasons: list[str]
    correlation: Correlation


def ae_binned_kld(
    prep: PreparedParticipant, n_bins: int, estimator: CovarianceEstimator, width_deg: float = 4.0
) -> AeBinned:
    if prep.config.reference_scope != "all":
        raise ValueError("Fig 1b uses an all-session AE < 4 reference (reference_scope='all')")
    x = prep.features("pca5")
    ae = prep.angle_error
    ref = prepare_reference(estimate(x[prep.reference_bins], estimator))
    lower = np.arange(n_bins, dtype=np.float64) * width_deg
    mean_ae = np.full(n_bins, np.nan)
    kld = np.full(n_bins, np.nan)
    counts = np.zeros(n_bins, dtype=np.int64)
    reasons: list[str] = []
    for j, a in enumerate(lower):
        sel = (ae >= a) & (ae < a + width_deg)  # NaN AE never selected
        counts[j] = int(sel.sum())
        if counts[j]:
            mean_ae[j] = float(ae[sel].mean())
        result = kl_divergence(ref, estimate(x[sel], estimator))
        kld[j] = result.value
        reasons.append(result.reason)
    return AeBinned(lower, mean_ae, kld, counts, reasons, correlate(mean_ae, kld))
