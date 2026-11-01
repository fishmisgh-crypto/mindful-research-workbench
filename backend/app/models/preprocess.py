"""Response schema for preprocessing diagnostics. Aggregates only."""

from pydantic import BaseModel


class BlockRow(BaseModel):
    session_index: int
    day: int
    block: int
    n_bins: int
    n_selected: int
    n_windows: int


class WindowSummary(BaseModel):
    n_windows: int
    window_bins: int
    step_bins: int
    lastn: int
    n_session_end_windows: int
    n_windows_crossing_blocks: int
    n_windows_crossing_sessions: int


class ReferenceSummary(BaseModel):
    sessions: list[int]
    days: list[int]
    candidate_bins: int
    candidate_ae_nan: int
    bins: int
    ae_max_deg: float
    fraction_kept: float | None


class PcaSummary(BaseModel):
    n_reference_bins: int
    explained_pct_top10: list[float]
    cumulative_pct_at_dim: float | None
    explained_pct_sum: float | None
    reference_score_mean: list[float]
    reference_score_std: list[float]


class ZscoreSummary(BaseModel):
    trailing_bins: int
    blocks_first_bin_zero: int
    max_abs_first_bin: float
    floored_std_fraction: float | None


class SessionRow(BaseModel):
    session_index: int
    day: int
    n_bins: int
    n_windows: int
    pc_mean: list[float]
    pc_std: list[float]
    ae_median_deg: float | None


class PreprocessDiagnostics(BaseModel):
    participant: str
    preset: str
    config: dict[str, float | int | bool | str]
    config_digest: str
    n_features: int
    n_blocks: int
    n_selected_bins: int
    blocks: list[BlockRow]
    windows: WindowSummary
    reference: ReferenceSummary
    pca: PcaSummary
    zscore: ZscoreSummary
    sessions: list[SessionRow]
    feature_sets: dict[str, str]
    elapsed_s: float
