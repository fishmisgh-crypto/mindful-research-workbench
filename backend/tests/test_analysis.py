"""SYNTHETIC — NOT STUDY DATA. Window engine, session-end NaN, and the npz round trip."""

import json
import warnings
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from mindful.analysis import AnalysisConfig, analyse, run_analysis
from mindful.io.discovery import discover_participant
from mindful.preprocess.config import PreprocessConfig
from mindful.preprocess.pipeline import (
    PreparedParticipant,
    load_prepared,
    prepare_participant,
    save_prepared,
)
from mindful.stats.gaussian import estimate
from mindful.stats.kld import kl_divergence, prepare_reference
from tests.synthetic import write_dataset

PRE = PreprocessConfig(zscore_window_bins=50, window_bins=120, step_bins=30)
UPSTREAM = AnalysisConfig("test-upstream", PRE, "uncentered_second_moment")
PAPER = AnalysisConfig("test-paper", PRE, "sample_covariance")


@pytest.fixture(scope="module")
def prep(tmp_path_factory: pytest.TempPathFactory) -> PreparedParticipant:
    root = tmp_path_factory.mktemp("data")
    write_dataset(root, {"T5": {10: (1, 2), 12: (1,), 15: (1, 2)}}, n_bins=900, n_trials=8)
    return prepare_participant(discover_participant(root, "T5"), PRE)


def test_every_window_matches_a_direct_computation(prep: PreparedParticipant) -> None:
    table = analyse(prep, "pca5", UPSTREAM)
    x = prep.pc_scores
    ref = prepare_reference(estimate(x[prep.reference_bins], "uncentered_second_moment"))
    for i in (0, 3, table.start.size // 2):
        a, b = table.start[i], table.stop[i]
        expected = kl_divergence(ref, estimate(x[a : b + 1], "uncentered_second_moment")).value
        assert table.kld_raw[i] == pytest.approx(expected, rel=1e-12)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            expected_ae = np.nanmedian(prep.angle_error[a : b + 1])
        if i not in prep.windows.session_end_windows():
            assert table.median_ae[i] == pytest.approx(expected_ae)


def test_session_end_windows_are_nan_for_kld_and_ae(prep: PreparedParticipant) -> None:
    table = analyse(prep, "pca5", UPSTREAM)
    ends = prep.windows.session_end_windows()
    assert ends.size > 0
    assert np.all(np.isnan(table.kld[ends])) and np.all(np.isnan(table.median_ae[ends]))
    assert all(table.reason[i] == "session_end" for i in ends)
    assert np.isfinite(table.kld_raw[ends]).any()  # computed, then discarded, as upstream
    others = np.setdiff1d(np.arange(table.start.size), ends)
    assert np.isfinite(table.kld[others]).all()


def test_estimators_give_different_kld(prep: PreparedParticipant) -> None:
    u = analyse(prep, "extended9", UPSTREAM).kld_raw
    p = analyse(prep, "extended9", PAPER).kld_raw
    assert not np.allclose(u, p)


def test_config_mismatch_is_rejected(prep: PreparedParticipant) -> None:
    other = replace(UPSTREAM, preprocess=replace(PRE, step_bins=60))
    with pytest.raises(ValueError, match="different preprocessing"):
        analyse(prep, "pca5", other)


def test_run_analysis_covers_all_feature_sets_and_serialises(prep: PreparedParticipant) -> None:
    out = run_analysis(prep, UPSTREAM)
    assert set(out["feature_sets"]) == {"pca5", "extended9", "velocity2", "velocity4"}
    assert out["kld_direction"] == "D_KL(P_reference || P_current)"
    s = out["feature_sets"]["extended9"]["summary"]
    assert s["dim"] == 9 and s["n_windows"] == prep.windows.n_windows
    assert sum(s["reasons"].values()) == s["n_windows"]
    assert "pearson" not in json.dumps(out).lower()  # correlation belongs to Phase 5


def test_prepared_npz_round_trip(prep: PreparedParticipant, tmp_path: Path) -> None:
    save_prepared(prep, tmp_path / "p.npz")
    back = load_prepared(tmp_path / "p.npz")
    assert back.config == prep.config and back.blocks == prep.blocks
    np.testing.assert_array_equal(back.windows.starts, prep.windows.starts)
    np.testing.assert_array_equal(back.reference_bins, prep.reference_bins)
    np.testing.assert_allclose(
        analyse(back, "extended9", UPSTREAM).kld_raw, analyse(prep, "extended9", UPSTREAM).kld_raw
    )
