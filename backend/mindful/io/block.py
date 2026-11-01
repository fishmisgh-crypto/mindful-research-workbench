"""Typed view of one recording block (data.mat + task.mat + info.mat).

Arrays keep rows = 20 ms bins. Nothing is transposed or reshaped silently:
a per-bin field whose row count differs from `nPointsPerBlock` raises
`BlockFormatError`. `start_stops` keeps the file's MATLAB convention
(1-based, inclusive); use `trial_slices()` for Python indexing.
"""

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import numpy.typing as npt
import scipy.sparse as sp

from mindful.io.discovery import BlockRef
from mindful.io.matfile import load_mat

FloatArray = npt.NDArray[np.float64]
BoolArray = npt.NDArray[np.bool_]
IntArray = npt.NDArray[np.int64]

N_CHANNELS = 192

REQUIRED: dict[str, tuple[str, ...]] = {
    "data": ("nctx", "labels", "cursorVel"),
    "task": ("name", "nPointsPerBlock", "startStops", "excludeTrials"),
    "info": ("angleError", "targetPos", "cursorPos"),
}
PER_TRIAL_INFO: tuple[str, ...] = (
    "angleErrorPerTrial",
    "trialSuccess",
    "timeToTarget",
    "pathEfficiency",
    "orthChanges",
)


class BlockFormatError(ValueError):
    """The files of a block do not have the documented structure."""


LOAD_ERRORS: tuple[type[Exception], ...] = (BlockFormatError, OSError, ValueError, KeyError)
"""Exceptions that mean 'this block cannot be read', as opposed to a programming error."""


@dataclass
class Block:
    ref: BlockRef
    task_name: str
    n_bins: int
    nctx: FloatArray
    spike_power: FloatArray | None
    labels: FloatArray
    cursor_vel: FloatArray
    start_stops: IntArray
    exclude_trials: BoolArray
    angle_error: FloatArray
    target_pos: FloatArray
    cursor_pos: FloatArray
    per_trial: dict[str, FloatArray]
    per_trial_length_mismatch: dict[str, int]
    percent_correct: float | None
    prct_outliers: Any | None
    avg_outliers: FloatArray | None
    source_dtypes: dict[str, str] = field(default_factory=dict)

    @property
    def n_trials(self) -> int:
        return int(self.start_stops.shape[0])

    @property
    def neural(self) -> FloatArray:
        """Feature matrix as the upstream loader builds it: [nctx, spikePower] if present."""
        if self.spike_power is None:
            return self.nctx
        return np.hstack([self.nctx, self.spike_power])

    def trial_slices(self) -> list[slice]:
        """Python slices for each trial (converts 1-based inclusive to 0-based half-open)."""
        return [slice(int(a) - 1, int(b)) for a, b in self.start_stops]

    def trial_mask(self, include_excluded: bool = False) -> BoolArray:
        """True for bins inside trials; excluded trials are dropped unless asked for."""
        mask = np.zeros(self.n_bins, dtype=bool)
        for i, s in enumerate(self.trial_slices()):
            if include_excluded or not self.exclude_trials[i]:
                mask[s] = True
        return mask


def _per_bin(name: str, value: Any, n_bins: int, width: int | None) -> FloatArray:
    arr = np.asarray(value)
    if arr.ndim != 2 or arr.shape[0] != n_bins or (width is not None and arr.shape[1] != width):
        expected = f"({n_bins}, {width if width is not None else 'k'})"
        raise BlockFormatError(f"{name}: shape {arr.shape}, expected {expected} (rows = bins)")
    return arr.astype(np.float64)


def _column(name: str, value: Any, length: int) -> FloatArray:
    arr = np.asarray(value)
    if arr.size != length or (arr.ndim == 2 and min(arr.shape) != 1 and length > 1):
        raise BlockFormatError(f"{name}: shape {arr.shape}, expected {length} values")
    return arr.astype(np.float64).ravel()


def _scalar(value: Any) -> float:
    return float(np.asarray(value).ravel()[0])


def _text(value: Any) -> str:
    if isinstance(value, str):
        return value
    arr = np.asarray(value).ravel()
    return str(arr[0]) if arr.size else ""


def load_block(ref: BlockRef) -> Block:
    """Load and type-check one block. Raises BlockFormatError on structural problems."""
    if ref.missing_files:
        raise BlockFormatError(f"missing files: {', '.join(ref.missing_files)}")
    files = {name: load_mat(ref.path / f"{name}.mat") for name in REQUIRED}
    for name, keys in REQUIRED.items():
        missing = [k for k in keys if k not in files[name]]
        if missing:
            raise BlockFormatError(f"{name}.mat lacks {', '.join(missing)}")
    data, task, info = files["data"], files["task"], files["info"]

    n_bins = int(_scalar(task["nPointsPerBlock"]))
    start_stops = np.asarray(task["startStops"]).astype(np.int64)
    if start_stops.ndim != 2 or start_stops.shape[1] != 2:
        raise BlockFormatError(f"startStops: shape {start_stops.shape}, expected (nTrial, 2)")
    n_trials = start_stops.shape[0]

    # Display-only per-trial fields: a length mismatch is recorded, not fatal, and never truncated.
    per_trial: dict[str, FloatArray] = {}
    per_trial_length_mismatch: dict[str, int] = {}
    for key in PER_TRIAL_INFO:
        if key not in info:
            continue
        values = np.asarray(info[key])
        if values.size == n_trials:
            per_trial[key] = values.astype(np.float64).ravel()
        else:
            per_trial_length_mismatch[key] = int(values.size)
    prct = info.get("prctOutliers")
    if prct is not None and sp.issparse(prct):
        prct = sp.csr_array(prct)

    return Block(
        ref=ref,
        task_name=_text(task["name"]),
        n_bins=n_bins,
        nctx=_per_bin("nctx", data["nctx"], n_bins, N_CHANNELS),
        spike_power=(
            _per_bin("spikePower", data["spikePower"], n_bins, N_CHANNELS)
            if "spikePower" in data
            else None
        ),
        labels=_per_bin("labels", data["labels"], n_bins, 2),
        cursor_vel=_per_bin("cursorVel", data["cursorVel"], n_bins, 2),
        start_stops=start_stops,
        exclude_trials=_column("excludeTrials", task["excludeTrials"], n_trials).astype(bool),
        angle_error=_per_bin("angleError", info["angleError"], n_bins, 1).ravel(),
        target_pos=_per_bin("targetPos", info["targetPos"], n_bins, 2),
        cursor_pos=_per_bin("cursorPos", info["cursorPos"], n_bins, 2),
        per_trial=per_trial,
        per_trial_length_mismatch=per_trial_length_mismatch,
        percent_correct=_scalar(info["percentCorrect"]) if "percentCorrect" in info else None,
        prct_outliers=prct,
        avg_outliers=(
            _per_bin("avgOutliers", info["avgOutliers"], n_bins, 1).ravel()
            if "avgOutliers" in info
            else None
        ),
        source_dtypes={
            f"{fname}.{key}": str(getattr(val, "dtype", type(val).__name__))
            for fname, vars_ in files.items()
            for key, val in vars_.items()
        },
    )
