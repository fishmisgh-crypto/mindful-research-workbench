"""MINDFUL window engine: KLD and median angular error for every window.

Mirrors `MINDFUL.CalcDistanceFromData`, `GetMedianAEperSeg` and `SetIndstoNaN`:
  - one reference Gaussian from the reference bins of the chosen feature set
  - for each window (start..stop, inclusive, over the selected bins): Gaussian
    estimate and D_KL(reference || window); median of angleError, NaN omitted
  - afterwards the last `lastn` windows of every session are set to NaN for both

Each feature set's summary carries the Pearson / Spearman correlation between
window median AE and KLD over pairwise-complete windows (computed from unrounded
values; the JSON window table is rounded for transport).
"""

import hashlib
import json
import warnings
from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
import numpy.typing as npt

from mindful.preprocess.config import PRESETS, PreprocessConfig
from mindful.preprocess.pipeline import FEATURE_SETS, PreparedParticipant
from mindful.stats.correlation import correlate
from mindful.stats.gaussian import CovarianceEstimator, estimate
from mindful.stats.kld import kl_divergence, prepare_reference

FloatArray = npt.NDArray[np.float64]
IntArray = npt.NDArray[np.int64]


@dataclass(frozen=True)
class AnalysisConfig:
    preset: str
    preprocess: PreprocessConfig
    covariance_estimator: CovarianceEstimator
    session_end_handling: str = "nan_last_n_windows"
    regularization: str = "none"

    def as_dict(self) -> dict[str, Any]:
        return {**asdict(self), "preprocess": self.preprocess.as_dict()}

    def digest(self) -> str:
        return hashlib.sha256(json.dumps(self.as_dict(), sort_keys=True).encode()).hexdigest()[:12]


ANALYSIS_PRESETS: dict[str, AnalysisConfig] = {
    "upstream": AnalysisConfig("upstream", PRESETS["upstream"], "uncentered_second_moment"),
    "paper": AnalysisConfig("paper", PRESETS["paper"], "sample_covariance"),
}


@dataclass(frozen=True)
class WindowTable:
    feature_set: str
    start: IntArray  # 0-based, over the selected bins
    stop: IntArray  # inclusive
    session_index: IntArray
    kld_raw: FloatArray  # before session-end NaN
    kld: FloatArray  # after session-end NaN: what goes into a correlation
    median_ae: FloatArray  # after session-end NaN
    reason: list[str]
    rank: IntArray
    condition: FloatArray
    reference_condition: float
    n_reference_bins: int

    @property
    def valid(self) -> npt.NDArray[np.bool_]:
        return np.isfinite(self.kld) & np.isfinite(self.median_ae)


def _median_ae(ae: FloatArray, start: IntArray, stop: IntArray) -> FloatArray:
    out = np.empty(start.size)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)  # all-NaN window -> NaN, as MATLAB
        for i, (a, b) in enumerate(zip(start, stop, strict=True)):
            out[i] = np.nanmedian(ae[a : b + 1])
    return out


def analyse(prep: PreparedParticipant, feature_set: str, config: AnalysisConfig) -> WindowTable:
    """KLD and median AE for every window of one feature set."""
    if prep.config != config.preprocess:
        raise ValueError("prepared data was built with a different preprocessing config")
    x = prep.features(feature_set)
    ref = prepare_reference(estimate(x[prep.reference_bins], config.covariance_estimator))
    w = prep.windows
    n = w.n_windows
    kld_raw = np.empty(n)
    reasons: list[str] = []
    rank = np.empty(n, dtype=np.int64)
    condition = np.empty(n)
    for i in range(n):
        result = kl_divergence(
            ref, estimate(x[w.starts[i] : w.stops[i] + 1], config.covariance_estimator)
        )
        kld_raw[i] = result.value
        reasons.append(result.reason)
        rank[i] = result.rank
        condition[i] = result.condition

    median_ae = _median_ae(prep.angle_error, w.starts, w.stops)
    kld = kld_raw.copy()
    session_end = w.session_end_windows()
    kld[session_end] = np.nan
    median_ae[session_end] = np.nan
    for i in session_end.tolist():
        reasons[i] = "session_end"
    for i in np.flatnonzero(np.isnan(median_ae)).tolist():
        if reasons[i] == "ok":
            reasons[i] = "ae_all_nan"
    return WindowTable(
        feature_set=feature_set,
        start=w.starts,
        stop=w.stops,
        session_index=w.session_of_window,
        kld_raw=kld_raw,
        kld=kld,
        median_ae=median_ae,
        reason=reasons,
        rank=rank,
        condition=condition,
        reference_condition=ref.condition,
        n_reference_bins=int(prep.reference_bins.size),
    )


def _finite(values: FloatArray) -> FloatArray:
    return values[np.isfinite(values)]


def _r(x: float, digits: int = 6) -> float | None:
    return None if not np.isfinite(x) else round(float(x), digits)


def summarise(table: WindowTable, prep: PreparedParticipant) -> dict[str, Any]:
    """Aggregates for inspection, including the KLD-vs-median-AE correlation."""
    reasons, counts = np.unique(np.array(table.reason), return_counts=True)
    day_of_session = {b.session_index: b.day for b in prep.blocks}
    per_session = []
    for s in sorted(day_of_session):
        sel = table.session_index == s
        k = _finite(table.kld[sel])
        a = _finite(table.median_ae[sel])
        per_session.append(
            {
                "session_index": s,
                "day": day_of_session[s],
                "n_windows": int(sel.sum()),
                "n_valid": int((table.valid & sel).sum()),
                "kld_median": _r(float(np.median(k))) if k.size else None,
                "median_ae_median": _r(float(np.median(a))) if a.size else None,
            }
        )
    k = _finite(table.kld)
    return {
        "feature_set": table.feature_set,
        "description": FEATURE_SETS[table.feature_set],
        "dim": int(prep.features(table.feature_set).shape[1]),
        "n_windows": int(table.start.size),
        "n_valid": int(table.valid.sum()),
        "reasons": {str(r): int(c) for r, c in zip(reasons, counts, strict=True)},
        "n_reference_bins": table.n_reference_bins,
        "reference_condition": _r(table.reference_condition, 3),
        "kld_min": _r(float(k.min())) if k.size else None,
        "kld_median": _r(float(np.median(k))) if k.size else None,
        "kld_max": _r(float(k.max())) if k.size else None,
        "kld_negative": int((k < 0).sum()),
        "window_condition_max": _r(float(np.nanmax(table.condition)), 3),
        "correlation": {
            k: (_r(v, 10) if isinstance(v, float) else v)
            for k, v in asdict(correlate(table.median_ae, table.kld)).items()
        },
        "per_session": per_session,
    }


def window_rows(table: WindowTable, prep: PreparedParticipant) -> dict[str, list[Any]]:
    """Column-oriented window table (JSON-friendly; aggregates per window only)."""
    day_of_session = {b.session_index: b.day for b in prep.blocks}
    return {
        "window": list(range(table.start.size)),
        "start": table.start.tolist(),
        "stop": table.stop.tolist(),
        "session_index": table.session_index.tolist(),
        "day": [day_of_session[int(s)] for s in table.session_index],
        "kld": [_r(v) for v in table.kld],
        "kld_raw": [_r(v) for v in table.kld_raw],
        "median_ae": [_r(v, 4) for v in table.median_ae],
        "reason": table.reason,
        "condition": [_r(v, 2) for v in table.condition],
    }


def run_analysis(prep: PreparedParticipant, config: AnalysisConfig) -> dict[str, Any]:
    """All feature sets for one participant and preset."""
    results = {}
    for name in FEATURE_SETS:
        table = analyse(prep, name, config)
        results[name] = {"summary": summarise(table, prep), "windows": window_rows(table, prep)}
    w = prep.windows
    return {
        "participant": prep.participant,
        "preset": config.preset,
        "config": config.as_dict(),
        "config_digest": config.digest(),
        "kld_direction": "D_KL(P_reference || P_current)",
        "window_bins": w.window_bins,
        "step_bins": w.step_bins,
        "bin_seconds": 0.02,
        "reference_days": sorted(
            {b.day for b in prep.blocks if b.session_index in prep.reference_sessions}
        ),
        "session_days": sorted({b.day for b in prep.blocks}),
        "feature_sets": results,
    }
