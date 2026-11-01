"""Response schema for window-level analysis. Per-window aggregates only."""

from typing import Any

from pydantic import BaseModel


class SessionSummary(BaseModel):
    session_index: int
    day: int
    n_windows: int
    n_valid: int
    kld_median: float | None
    median_ae_median: float | None


class FeatureSetSummary(BaseModel):
    feature_set: str
    description: str
    dim: int
    n_windows: int
    n_valid: int
    reasons: dict[str, int]
    n_reference_bins: int
    reference_condition: float | None
    kld_min: float | None
    kld_median: float | None
    kld_max: float | None
    kld_negative: int
    window_condition_max: float | None
    per_session: list[SessionSummary]


class WindowColumns(BaseModel):
    window: list[int]
    start: list[int]
    stop: list[int]
    session_index: list[int]
    day: list[int]
    kld: list[float | None]
    kld_raw: list[float | None]
    median_ae: list[float | None]
    reason: list[str]
    condition: list[float | None]


class AnalysisResponse(BaseModel):
    participant: str
    preset: str
    config: dict[str, Any]
    config_digest: str
    kld_direction: str
    window_bins: int
    step_bins: int
    bin_seconds: float
    reference_days: list[int]
    session_days: list[int]
    feature_set: str
    summaries: dict[str, FeatureSetSummary]
    windows: WindowColumns | None
