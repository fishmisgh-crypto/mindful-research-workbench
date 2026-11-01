"""SYNTHETIC — NOT STUDY DATA. Block loading, index conversion and strict shape handling."""

from pathlib import Path

import numpy as np
import pytest
import scipy.io as sio

from mindful.io.block import BlockFormatError, load_block
from mindful.io.discovery import discover_participant
from tests.synthetic import write_block


def load_single(root: Path, participant: str = "T11"):  # type: ignore[no-untyped-def]
    return load_block(discover_participant(root, participant).sessions[0].blocks[0])


def test_loads_with_rows_as_bins(tmp_path: Path) -> None:
    write_block(tmp_path / "T11/day_1/Block_01", n_bins=300)
    block = load_single(tmp_path)
    assert block.n_bins == 300
    assert block.nctx.shape == (300, 192)
    assert block.neural.shape == (300, 384)
    assert block.angle_error.shape == (300,)
    assert block.exclude_trials.dtype == bool
    assert block.nctx.dtype == np.float64


def test_t5_style_block_has_192_features(tmp_path: Path) -> None:
    write_block(tmp_path / "T5/day_1/Block_01", spike_power=False)
    assert load_single(tmp_path, "T5").neural.shape[1] == 192


def test_trial_slices_convert_one_based_inclusive(tmp_path: Path) -> None:
    write_block(tmp_path / "T11/day_1/Block_01", n_bins=400, n_trials=4)
    block = load_single(tmp_path)
    first_start, first_stop = (int(v) for v in block.start_stops[0])
    s = block.trial_slices()[0]
    assert (s.start, s.stop) == (first_start - 1, first_stop)
    assert s.stop - s.start == first_stop - first_start + 1


def test_trial_mask_drops_excluded_trials(tmp_path: Path) -> None:
    write_block(tmp_path / "T11/day_1/Block_01", n_trials=4, excluded=(1,))
    block = load_single(tmp_path)
    excluded = block.trial_slices()[1]
    assert not block.trial_mask()[excluded].any()
    assert block.trial_mask(include_excluded=True)[excluded].all()
    assert not block.trial_mask(include_excluded=True)[: block.trial_slices()[0].start].any()


def test_transposed_neural_matrix_is_rejected_not_fixed(tmp_path: Path) -> None:
    folder = tmp_path / "T11/day_1/Block_01"
    write_block(folder, n_bins=300)
    data = sio.loadmat(folder / "data.mat")
    sio.savemat(
        folder / "data.mat",
        {**{k: v for k, v in data.items() if not k.startswith("__")}, "nctx": data["nctx"].T},
    )
    with pytest.raises(BlockFormatError, match="nctx"):
        load_single(tmp_path)


def test_per_trial_length_mismatch_recorded_not_truncated(tmp_path: Path) -> None:
    folder = tmp_path / "T11/day_1/Block_01"
    write_block(folder, n_trials=4)
    info = sio.loadmat(folder / "info.mat")
    info = {k: v for k, v in info.items() if not k.startswith("__")}
    info["trialSuccess"] = np.ones((5, 1), dtype=np.uint8)
    sio.savemat(folder / "info.mat", info)
    block = load_single(tmp_path)
    assert block.per_trial_length_mismatch == {"trialSuccess": 5}
    assert "trialSuccess" not in block.per_trial
    assert "timeToTarget" in block.per_trial


def test_missing_required_field_raises(tmp_path: Path) -> None:
    folder = tmp_path / "T11/day_1/Block_01"
    write_block(folder)
    task = sio.loadmat(folder / "task.mat")
    sio.savemat(
        folder / "task.mat",
        {k: v for k, v in task.items() if not k.startswith("__") and k != "excludeTrials"},
    )
    with pytest.raises(BlockFormatError, match="excludeTrials"):
        load_single(tmp_path)
