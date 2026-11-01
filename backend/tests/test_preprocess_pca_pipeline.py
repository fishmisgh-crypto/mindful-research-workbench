"""SYNTHETIC — NOT STUDY DATA. PCA conventions and the participant pipeline end to end."""

from pathlib import Path

import numpy as np
import pytest
from sklearn.decomposition import PCA

from mindful.io.block import load_block
from mindful.io.discovery import discover_participant
from mindful.preprocess.config import PreprocessConfig
from mindful.preprocess.pca import fit_pca
from mindful.preprocess.pipeline import diagnostics, prepare_participant
from mindful.preprocess.zscore import rolling_zscore
from tests.synthetic import write_dataset

CONFIG = PreprocessConfig(zscore_window_bins=50, window_bins=120, step_bins=30, pca_dim=5)


def test_pca_matches_sklearn_up_to_sign_and_follows_matlab_sign_rule() -> None:
    x = np.random.default_rng(0).normal(size=(300, 12)) @ np.random.default_rng(1).normal(
        size=(12, 12)
    )
    model = fit_pca(x)
    ref = PCA().fit(x)
    np.testing.assert_allclose(model.explained_pct, 100 * ref.explained_variance_ratio_, rtol=1e-8)
    for j in range(12):
        np.testing.assert_allclose(
            np.abs(model.components[:, j]), np.abs(ref.components_[j]), atol=1e-8
        )
        assert model.components[np.argmax(np.abs(model.components[:, j])), j] > 0
    assert model.explained_pct.sum() == pytest.approx(100.0)
    scores = model.transform(x, 5)
    np.testing.assert_allclose(scores.mean(axis=0), 0.0, atol=1e-10)
    np.testing.assert_allclose(scores, (x - x.mean(axis=0)) @ model.components[:, :5])


@pytest.fixture
def t5_root(tmp_path: Path) -> Path:
    write_dataset(tmp_path, {"T5": {10: (1, 2), 12: (1,), 15: (1, 2)}}, n_bins=600, n_trials=6)
    return tmp_path


def test_pipeline_selection_reference_and_pca(t5_root: Path) -> None:
    participant = discover_participant(t5_root, "T5")
    prep = prepare_participant(participant, CONFIG)
    blocks = [load_block(r) for s in participant.sessions for r in s.blocks]
    masks = [b.trial_mask() for b in blocks]

    assert prep.n_bins == sum(int(m.sum()) for m in masks)
    assert prep.reference_sessions == (1, 2)
    assert np.all(prep.session_of_bin()[prep.reference_bins] <= 2)
    assert np.all(prep.angle_error[prep.reference_bins] < 4.0)

    # PCA is fitted on z-scored reference bins only (recomputed independently here).
    z = np.vstack(
        [rolling_zscore(b.neural, 50, 1e-5)[m] for b, m in zip(blocks, masks, strict=True)]
    )
    np.testing.assert_allclose(prep.pca.mean, z[prep.reference_bins].mean(axis=0), atol=1e-10)
    np.testing.assert_allclose(prep.pc_scores[prep.reference_bins].mean(axis=0), 0.0, atol=1e-9)
    np.testing.assert_allclose(prep.pc_scores, prep.pca.transform(z, 5), atol=1e-9)

    assert prep.features("pca5").shape == (prep.n_bins, 5)
    assert prep.features("extended9").shape == (prep.n_bins, 9)
    assert prep.features("velocity4").shape == (prep.n_bins, 4)


def test_lag_is_computed_before_trial_selection(t5_root: Path) -> None:
    participant = discover_participant(t5_root, "T5")
    prep = prepare_participant(participant, CONFIG)
    block = load_block(participant.sessions[0].blocks[0])
    first_trial_start = int(block.start_stops[0, 0]) - 1  # 0-based
    # The first selected bin's lag is the bin before it, which lies outside any trial.
    np.testing.assert_array_equal(prep.velocity_lag[0], block.cursor_vel[first_trial_start - 1])


def test_excluded_trials_are_dropped_unless_configured(tmp_path: Path) -> None:
    write_dataset(tmp_path, {"T5": {1: (1,), 2: (1,)}}, n_bins=600, n_trials=6, excluded=(2,))
    participant = discover_participant(tmp_path, "T5")
    kept = prepare_participant(participant, CONFIG).n_bins
    with_excluded = prepare_participant(
        participant,
        PreprocessConfig(
            zscore_window_bins=50, window_bins=120, step_bins=30, include_excluded_trials=True
        ),
    ).n_bins
    assert with_excluded > kept


def test_diagnostics_are_aggregates(t5_root: Path) -> None:
    prep = prepare_participant(discover_participant(t5_root, "T5"), CONFIG)
    d = diagnostics(prep)
    assert d["n_selected_bins"] == prep.n_bins
    assert d["pca"]["explained_pct_sum"] == pytest.approx(100.0)
    assert d["zscore"]["blocks_first_bin_zero"] == len(prep.blocks)
    assert len(d["sessions"]) == 3
    assert d["reference"]["bins"] == prep.reference_bins.size
