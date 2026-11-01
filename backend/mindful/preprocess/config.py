"""Preprocessing configuration and presets.

Only the parameters that affect preprocessing live here. The step size is
included because reference bins are defined through the window index (D2, D7).
"""

import hashlib
import json
from dataclasses import asdict, dataclass

# Reference sessions by chronological position (1-based) [C MINDFUL_main_script.m:43-45].
REFERENCE_SESSIONS: dict[str, tuple[int, ...]] = {"T11": (1,), "T5": (1, 2)}


@dataclass(frozen=True)
class PreprocessConfig:
    zscore_window_bins: int = 9000  # trailing bins before the current one: movmean(x, [9000 0])
    zscore_std_floor: float = 1e-5  # std below this is replaced by 1
    window_bins: int = 3000
    step_bins: int = 500
    pca_dim: int = 5
    reference_ae_max_deg: float = 4.0  # strict "<"; NaN AE is excluded
    include_excluded_trials: bool = False  # D3 ablation; upstream drops excludeTrials
    velocity_lag_bins: int = 1

    def __post_init__(self) -> None:
        if min(self.zscore_window_bins, self.window_bins, self.step_bins, self.pca_dim) < 1:
            raise ValueError("window, step and pca_dim must be positive")

    def as_dict(self) -> dict[str, object]:
        return asdict(self)

    def digest(self) -> str:
        text = json.dumps(self.as_dict(), sort_keys=True)
        return hashlib.sha256(text.encode()).hexdigest()[:12]


PRESETS: dict[str, PreprocessConfig] = {
    "upstream": PreprocessConfig(step_bins=500),  # fig2_plot_MINDFUL.m: updateHz = 500
    "paper": PreprocessConfig(step_bins=50),  # Methods: windows shifted by 1 s
}


def matlab_round(x: float) -> int:
    """MATLAB `round`: halves away from zero (Python's round is half-to-even)."""
    return int(x + 0.5) if x >= 0 else -int(-x + 0.5)
