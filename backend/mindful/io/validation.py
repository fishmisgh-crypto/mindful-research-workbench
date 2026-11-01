"""Per-block structural and semantic checks.

Status meanings: `fail` = the block cannot be used as documented; `warn` =
usable but differs from the documentation or from an expectation; `info` =
a measured property worth recording; `pass` = check satisfied.
"""

from dataclasses import dataclass
from typing import Literal

import numpy as np

from mindful.io.block import Block
from mindful.stats.angular import angle_between_deg

Status = Literal["pass", "info", "warn", "fail"]

EXPECTS_SPIKE_POWER = {"T11": True, "T5": False}
AE_AGREEMENT_TOLERANCE_DEG = 0.5
AE_AGREEMENT_MIN_FRACTION = 0.99
LABELS_TOLERANCE = 1e-4
RATE_UNIT = 50.0  # one threshold crossing in a 20 ms bin = 50 per second


@dataclass(frozen=True)
class Check:
    id: str
    status: Status
    message: str


def _feature_set(block: Block) -> Check:
    has_sp = block.spike_power is not None
    expected = EXPECTS_SPIKE_POWER.get(block.ref.participant)
    n = block.neural.shape[1]
    if expected is None or has_sp == expected:
        return Check(
            "feature_set", "pass", f"{n} features ({'nctx + spikePower' if has_sp else 'nctx'})"
        )
    if has_sp:
        return Check(
            "feature_set", "warn", f"spikePower present; upstream would build {n} features (D8)"
        )
    return Check("feature_set", "fail", "spikePower missing; T11 needs 384 features")


def _neural_values(block: Block) -> list[Check]:
    arrays = [("nctx", block.nctx)] + (
        [("spikePower", block.spike_power)] if block.spike_power is not None else []
    )
    bad = [
        f"{name}: {int((~np.isfinite(a)).sum())}" for name, a in arrays if not np.isfinite(a).all()
    ]
    finite = (
        Check("neural_finite", "fail", f"non-finite values ({'; '.join(bad)})")
        if bad
        else Check("neural_finite", "pass", "all neural values finite")
    )
    negative = int((block.nctx < 0).sum())
    nonneg = (
        Check("nctx_nonnegative", "fail", f"{negative} negative threshold-crossing values")
        if negative
        else Check("nctx_nonnegative", "pass", "threshold crossings ≥ 0")
    )
    positive = block.nctx[block.nctx > 0]
    frac = (
        float(np.mean(np.isclose(np.mod(positive, RATE_UNIT), 0.0)))
        if positive.size
        else float("nan")
    )
    units = Check(
        "nctx_units",
        "info",
        f"{frac:.1%} of non-zero nctx values are multiples of {RATE_UNIT:g} "
        "(crossings/s at 20 ms bins)",
    )
    return [finite, nonneg, units]


def _trials(block: Block) -> list[Check]:
    ss = block.start_stops
    starts, stops = ss[:, 0], ss[:, 1]
    checks: list[Check] = []
    in_bounds = bool(
        (starts >= 1).all() and (stops <= block.n_bins).all() and (starts <= stops).all()
    )
    checks.append(
        Check(
            "trial_bounds",
            "pass",
            "1 ≤ start ≤ stop ≤ nPointsPerBlock for every trial (1-based, inclusive)",
        )
        if in_bounds
        else Check(
            "trial_bounds", "fail", "startStops outside [1, nPointsPerBlock] or start > stop"
        )
    )
    ordered = bool((starts[1:] > stops[:-1]).all())
    gaps = starts[1:] - stops[:-1]
    contiguous = int((gaps == 1).sum())
    checks.append(
        Check(
            "trial_order",
            "pass",
            f"trials ordered, non-overlapping; {contiguous}/{len(gaps)} back to back",
        )
        if ordered
        else Check("trial_order", "fail", "trials overlap or are out of order")
    )
    if block.per_trial_length_mismatch:
        detail = ", ".join(
            f"{k} has {n}" for k, n in sorted(block.per_trial_length_mismatch.items())
        )
        checks.append(
            Check(
                "per_trial_lengths",
                "warn",
                f"{detail} entries but startStops has {block.n_trials} trials; "
                "these display-only fields are set aside",
            )
        )
    if in_bounds:
        head = int(starts[0] - 1) if len(ss) else block.n_bins
        tail = int(block.n_bins - stops[-1]) if len(ss) else 0
        kept = int(block.trial_mask().sum())
        checks.append(
            Check(
                "trial_coverage",
                "info",
                f"{kept} bins in kept trials; {head} bins before the first trial, "
                f"{tail} after the last; "
                f"{int(block.exclude_trials.sum())} of {block.n_trials} trials excluded",
            )
        )
    return checks


def _angle_error(block: Block) -> list[Check]:
    ae = block.angle_error
    finite = ae[np.isfinite(ae)]
    in_range = bool(((finite >= 0) & (finite <= 180)).all())
    checks = [
        Check("ae_range", "pass", "angleError within [0°, 180°]")
        if in_range
        else Check("ae_range", "fail", "angleError outside [0°, 180°]")
    ]
    mask = block.trial_mask()
    nan_all = float(np.isnan(ae).mean())
    nan_trial = float(np.isnan(ae[mask]).mean()) if mask.any() else float("nan")
    checks.append(
        Check(
            "ae_missing",
            "info",
            f"angleError NaN in {nan_all:.2%} of bins, {nan_trial:.2%} of kept-trial bins",
        )
    )

    recomputed = angle_between_deg(block.labels, block.cursor_vel)
    both = np.isfinite(ae) & np.isfinite(recomputed)
    nan_mismatch = int((np.isnan(ae) != np.isnan(recomputed)).sum())
    within = (
        float(np.mean(np.abs(ae[both] - recomputed[both]) < AE_AGREEMENT_TOLERANCE_DEG))
        if both.any()
        else 0.0
    )
    status: Status = "pass" if within >= AE_AGREEMENT_MIN_FRACTION and nan_mismatch == 0 else "warn"
    checks.append(
        Check(
            "ae_recomputed",
            status,
            f"angle(labels, cursorVel) within {AE_AGREEMENT_TOLERANCE_DEG}° of angleError "
            f"in {within:.2%} of bins; "
            f"NaN pattern differs in {nan_mismatch} bins",
        )
    )
    c2t = block.target_pos - block.cursor_pos
    finite_rows = np.isfinite(c2t).all(axis=1)
    max_diff = (
        float(np.max(np.abs(block.labels[finite_rows] - c2t[finite_rows])))
        if finite_rows.any()
        else float("nan")
    )
    checks.append(
        Check(
            "labels_definition", "pass", f"labels = targetPos − cursorPos (max |Δ| {max_diff:.1e})"
        )
        if max_diff <= LABELS_TOLERANCE
        else Check(
            "labels_definition",
            "warn",
            f"labels differ from targetPos − cursorPos (max |Δ| {max_diff:.3g})",
        )
    )
    return checks


def validate_block(block: Block) -> list[Check]:
    """Run every block-level check."""
    return [_feature_set(block), *_neural_values(block), *_trials(block), *_angle_error(block)]


def worst(checks: list[Check]) -> Status:
    order: list[Status] = ["pass", "info", "warn", "fail"]
    return max((c.status for c in checks), key=order.index, default="pass")
