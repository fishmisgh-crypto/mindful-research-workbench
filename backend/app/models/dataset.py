"""Response schemas for the dataset endpoints. Aggregates and metadata only."""

from typing import Literal

from pydantic import BaseModel

Status = Literal["pass", "info", "warn", "fail"]


class CheckOut(BaseModel):
    id: str
    status: Status
    message: str


class BlockSummary(BaseModel):
    number: int
    name: str
    status: Status
    checks: list[CheckOut]
    task_name: str | None = None
    n_bins: int | None = None
    duration_s: float | None = None
    n_trials: int | None = None
    n_excluded_trials: int | None = None
    kept_trial_bins: int | None = None
    feature_count: int | None = None
    has_spike_power: bool | None = None
    percent_correct: float | None = None
    ae_median_kept_deg: float | None = None
    ae_nan_fraction: float | None = None
    nctx_mean_rate: float | None = None
    outlier_bin_fraction: float | None = None


class SessionSummary(BaseModel):
    day: int
    index: int
    name: str
    n_blocks: int
    block_mtime_order_matches_numeric: bool
    status: Status
    blocks: list[BlockSummary]


class SessionOrder(BaseModel):
    chronological: list[str]
    matlab_dir: list[str]
    matches: bool


class ParticipantSummary(BaseModel):
    id: str
    n_sessions: int
    n_blocks: int
    n_trials: int
    n_excluded_trials: int
    n_bins: int
    kept_trial_bins: int
    duration_min: float
    feature_counts: list[int]
    task_names: list[str]
    session_order: SessionOrder
    status: Status
    checks: list[CheckOut]
    sessions: list[SessionSummary]


class DatasetSummary(BaseModel):
    schema_version: int
    built_at: str
    root: str
    content_digest_sha256: str
    n_mat_files: int
    mat_bytes: int
    documented: dict[str, dict[str, int]]
    participants: list[ParticipantSummary]
    out_of_scope_blocks: list[str]


class TrialRow(BaseModel):
    trial: int
    start: int
    stop: int
    n_bins: int
    excluded: bool
    ae_median_deg: float | None
    ae_nan_bins: int
    success: bool | None
    time_to_target_s: float | None
    path_efficiency: float | None
    ae_per_trial_deg: float | None


class MissingData(BaseModel):
    ae_nan_bins: int
    outlier_bins: int | None
    channels_with_outliers: int | None
    per_trial_length_mismatch: dict[str, int]


class Histogram(BaseModel):
    edges_deg: list[int]
    counts: list[int]


class BlockDetail(BaseModel):
    participant: str
    session: str
    summary: BlockSummary
    trials: list[TrialRow]
    channel_means: dict[str, list[float]]
    missing_data: MissingData
    ae_histogram: Histogram
    source_dtypes: dict[str, str]
