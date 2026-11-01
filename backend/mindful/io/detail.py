"""Per-block detail for inspection: trial table, channel means, missing data. Aggregates only."""

from typing import Any

import numpy as np

from mindful.io.block import Block
from mindful.io.inventory import block_summary
from mindful.io.validation import validate_block

AE_HISTOGRAM_EDGES_DEG = tuple(range(0, 181, 10))


def _opt(value: float) -> float | None:
    return None if not np.isfinite(value) else round(float(value), 4)


def trial_table(block: Block) -> list[dict[str, Any]]:
    """One row per trial. `start`/`stop` are the file's 1-based inclusive bin indices."""
    rows: list[dict[str, Any]] = []
    for i, s in enumerate(block.trial_slices()):
        ae = block.angle_error[s]
        row: dict[str, Any] = {
            "trial": i + 1,
            "start": int(block.start_stops[i, 0]),
            "stop": int(block.start_stops[i, 1]),
            "n_bins": s.stop - s.start,
            "excluded": bool(block.exclude_trials[i]),
            "ae_median_deg": _opt(float(np.nanmedian(ae))) if np.isfinite(ae).any() else None,
            "ae_nan_bins": int(np.isnan(ae).sum()),
        }
        for key, out in (
            ("trialSuccess", "success"),
            ("timeToTarget", "time_to_target_s"),
            ("pathEfficiency", "path_efficiency"),
            ("angleErrorPerTrial", "ae_per_trial_deg"),
        ):
            values = block.per_trial.get(key)
            row[out] = None if values is None else _opt(float(values[i]))
        if row["success"] is not None:
            row["success"] = bool(row["success"])
        rows.append(row)
    return rows


def channel_means(block: Block) -> dict[str, list[float]]:
    """Mean of each channel over the whole block, per feature family."""
    out = {"nctx": np.round(block.nctx.mean(axis=0), 3).tolist()}
    if block.spike_power is not None:
        out["spikePower"] = np.round(block.spike_power.mean(axis=0), 3).tolist()
    return out


def missing_data(block: Block) -> dict[str, Any]:
    prct = block.prct_outliers
    channels_with_outliers: int | None = None
    if prct is not None:
        channels_with_outliers = int(np.unique(prct.nonzero()[1]).size)
    return {
        "ae_nan_bins": int(np.isnan(block.angle_error).sum()),
        "outlier_bins": int((block.avg_outliers > 0).sum())
        if block.avg_outliers is not None
        else None,
        "channels_with_outliers": channels_with_outliers,
        "per_trial_length_mismatch": block.per_trial_length_mismatch,
    }


def ae_histogram(block: Block) -> dict[str, list[int]]:
    """Counts of per-bin angular error over kept-trial bins, 10° bins."""
    ae = block.angle_error[block.trial_mask()]
    counts, _ = np.histogram(ae[np.isfinite(ae)], bins=AE_HISTOGRAM_EDGES_DEG)
    return {"edges_deg": list(AE_HISTOGRAM_EDGES_DEG), "counts": counts.tolist()}


def block_detail(block: Block) -> dict[str, Any]:
    return {
        "participant": block.ref.participant,
        "session": f"day_{block.ref.day}",
        "summary": block_summary(block, validate_block(block)),
        "trials": trial_table(block),
        "channel_means": channel_means(block),
        "missing_data": missing_data(block),
        "ae_histogram": ae_histogram(block),
        "source_dtypes": block.source_dtypes,
    }
