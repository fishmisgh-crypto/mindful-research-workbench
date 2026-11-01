"""SYNTHETIC — NOT STUDY DATA. Writers for tiny fake blocks with the documented file layout."""

from pathlib import Path

import numpy as np
import scipy.io as sio

SYNTHETIC_LABEL = "SYNTHETIC — NOT STUDY DATA"


def write_block(
    path: Path,
    *,
    n_bins: int = 400,
    n_trials: int = 4,
    spike_power: bool = True,
    excluded: tuple[int, ...] = (),
    seed: int = 0,
) -> None:
    """Write data/task/info.mat for one synthetic block (trials back to back, 1-based)."""
    rng = np.random.default_rng(seed)
    path.mkdir(parents=True, exist_ok=True)
    head = 20
    edges = np.linspace(head + 1, n_bins - 10, n_trials + 1).astype(int)
    start_stops = np.column_stack([edges[:-1], edges[1:] - 1]).astype(np.uint16)
    exclude = np.zeros((n_trials, 1), dtype=np.uint8)
    exclude[list(excluded)] = 1

    target = rng.uniform(-1, 1, (n_bins, 2)).astype(np.float32)
    cursor = rng.uniform(-1, 1, (n_bins, 2)).astype(np.float32)
    labels = (target - cursor).astype(np.float32)
    vel = rng.normal(0, 0.01, (n_bins, 2)).astype(np.float32)
    ang = np.degrees(
        np.arccos(
            np.clip(
                np.sum(labels.astype(float) * vel, 1)
                / (
                    np.linalg.norm(labels.astype(float), axis=1)
                    * np.linalg.norm(vel.astype(float), axis=1)
                ),
                -1,
                1,
            )
        )
    ).astype(np.float32)

    data = {
        "nctx": (rng.poisson(1.0, (n_bins, 192)) * 50).astype(np.float32),
        "labels": labels,
        "cursorVel": vel,
    }
    if spike_power:
        data["spikePower"] = rng.gamma(2.0, 50.0, (n_bins, 192)).astype(np.float32)
    sio.savemat(path / "data.mat", data)
    sio.savemat(
        path / "task.mat",
        {
            "name": "synthetic",
            "nPointsPerBlock": np.array([[n_bins]], dtype=np.uint16),
            "startStops": start_stops,
            "excludeTrials": exclude,
            "useClick": np.array([[1]], dtype=np.uint8),
            "moveDirVect": np.zeros((n_trials, 2), dtype=np.float32),
        },
    )
    sio.savemat(
        path / "info.mat",
        {
            "angleError": ang.reshape(-1, 1),
            "targetPos": target,
            "cursorPos": cursor,
            "trialSuccess": np.ones((n_trials, 1), dtype=np.uint8),
            "timeToTarget": np.full((n_trials, 1), 2.0),
            "angleErrorPerTrial": np.full((n_trials, 1), 30.0),
            "percentCorrect": np.array([[100.0]]),
        },
    )


def write_dataset(
    root: Path, layout: dict[str, dict[int, tuple[int, ...]]], **kwargs: object
) -> None:
    """layout = {participant: {day: (block numbers...)}}."""
    for participant, days in layout.items():
        for day, blocks in days.items():
            for number in blocks:
                write_block(
                    root / participant / f"day_{day}" / f"Block_{number:02d}",
                    spike_power=participant == "T11",
                    seed=day * 100 + number,
                    **kwargs,  # type: ignore[arg-type]
                )
