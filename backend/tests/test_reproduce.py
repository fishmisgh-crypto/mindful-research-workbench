"""SYNTHETIC — NOT STUDY DATA. Correlation, Fig 1b binning, and the reproduction matrix."""

from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest
from scipy import stats

from mindful import reproduce
from mindful.ae_binned import PAPER_N_BINS, UPSTREAM_N_BINS, ae_binned_kld
from mindful.io.discovery import discover_participant
from mindful.preprocess.config import PreprocessConfig
from mindful.preprocess.pipeline import prepare_participant
from mindful.stats.correlation import correlate
from tests.synthetic import write_dataset


def test_correlation_matches_scipy_on_complete_pairs() -> None:
    rng = np.random.default_rng(0)
    x = rng.normal(size=200)
    y = 0.6 * x + rng.normal(size=200)
    x[[3, 50]] = np.nan
    y[[7]] = np.nan
    c = correlate(x, y)
    ok = np.isfinite(x) & np.isfinite(y)
    assert c.n == 197
    assert c.pearson_r == pytest.approx(stats.pearsonr(x[ok], y[ok]).statistic)
    assert c.spearman_rho == pytest.approx(stats.spearmanr(x[ok], y[ok]).statistic)


def test_correlation_of_monotone_but_nonlinear_data() -> None:
    x = np.linspace(0, 3, 50)
    c = correlate(x, np.exp(x))
    assert c.spearman_rho == pytest.approx(1.0)
    assert c.pearson_r < 1.0


def test_correlation_with_too_few_pairs_is_nan() -> None:
    c = correlate(np.array([1.0, np.nan, 2.0]), np.array([1.0, 2.0, np.nan]))
    assert c.n == 1 and np.isnan(c.pearson_r)


@pytest.fixture(scope="module")
def all_ref_prep(tmp_path_factory: pytest.TempPathFactory):  # type: ignore[no-untyped-def]
    root = tmp_path_factory.mktemp("data")
    write_dataset(root, {"T5": {1: (1, 2), 2: (1,)}}, n_bins=3000, n_trials=12)
    config = PreprocessConfig(
        zscore_window_bins=50, window_bins=120, step_bins=30, reference_scope="all"
    )
    return prepare_participant(discover_participant(root, "T5"), config)


def test_all_session_reference_uses_every_session(all_ref_prep) -> None:  # type: ignore[no-untyped-def]
    sessions = all_ref_prep.session_of_bin()[all_ref_prep.reference_bins]
    assert set(sessions.tolist()) == {1, 2}
    assert np.all(all_ref_prep.angle_error[all_ref_prep.reference_bins] < 4)


def test_fig1b_bin_counts_and_edges(all_ref_prep) -> None:  # type: ignore[no-untyped-def]
    code = ae_binned_kld(all_ref_prep, UPSTREAM_N_BINS, "uncentered_second_moment")
    paper = ae_binned_kld(all_ref_prep, PAPER_N_BINS, "uncentered_second_moment")
    assert code.lower_deg.size == 44 and code.lower_deg[-1] == 172
    assert paper.lower_deg.size == 45 and paper.lower_deg[-1] == 176
    ae = all_ref_prep.angle_error
    assert code.n_bins_each[0] == int(((ae >= 0) & (ae < 4)).sum())
    np.testing.assert_allclose(paper.kld[:44], code.kld, equal_nan=True)


def test_fig1b_requires_all_session_reference(all_ref_prep) -> None:  # type: ignore[no-untyped-def]
    sessions_scope = replace(
        all_ref_prep, config=replace(all_ref_prep.config, reference_scope="sessions")
    )
    with pytest.raises(ValueError, match="reference_scope"):
        ae_binned_kld(sessions_scope, 44, "uncentered_second_moment")


def test_run_matrix_shape() -> None:
    specs = reproduce.run_specs()
    groups = {g: [s for s in specs if s.group == g] for g in ("primary", "secondary", "ablation")}
    assert len(groups["primary"]) == 8
    assert len(groups["secondary"]) == 4
    assert len(groups["ablation"]) == 20  # 4 feature sets; T5 has no excluded trials
    assert len({s.id for s in specs}) == len(specs)
    for s in groups["ablation"]:  # each ablation changes exactly one thing from upstream
        u = reproduce.UPSTREAM
        changed = int(s.config.covariance_estimator != u.covariance_estimator) + sum(
            getattr(s.config.preprocess, f) != getattr(u.preprocess, f)
            for f in ("step_bins", "include_excluded_trials")
        )
        assert changed == 1, s.id


SUMMARY = {
    "n_windows": 100,
    "kld_min": 0.1,
    "kld_max": 2.0,
    "n_reference_bins": 3000,
    "correlation": {
        "pearson_r": 0.9,
        "pearson_p": 1e-30,
        "spearman_rho": 0.88,
        "spearman_p": 1e-29,
        "n": 90,
    },
}


def test_published_values_only_affect_comparison_fields() -> None:
    spec = next(s for s in reproduce.run_specs() if s.id == "T11-pca5-upstream")
    targets = reproduce.load_targets()
    a = reproduce._row(spec, SUMMARY, targets)
    shifted = {
        **targets,
        "correlations": [{**t, "pearson": 0.1, "spearman": 0.1} for t in targets["correlations"]],
    }
    b = reproduce._row(spec, SUMMARY, shifted)
    comparison = {"published", "delta_r", "delta_rho", "verdict"}
    assert {k: v for k, v in a.items() if k not in comparison} == {
        k: v for k, v in b.items() if k not in comparison
    }
    assert a["delta_r"] == pytest.approx(0.9 - 0.91) and a["verdict"] == "within tolerance"
    assert b["verdict"] == "differs"


def test_secondary_without_target_has_no_verdict(tmp_path: Path) -> None:
    spec = reproduce.RunSpec("x", "ablation", "T11", "pca5", reproduce.UPSTREAM, "none")
    targets = {**reproduce.load_targets(), "correlations": []}
    assert reproduce._row(spec, SUMMARY, targets)["verdict"] == "no published value"


def test_targets_file_is_documented_and_complete() -> None:
    t = reproduce.load_targets()
    assert "never used in any calculation" in t["_note"]
    assert {(c["participant"], c["feature_set"]) for c in t["correlations"]} == {
        (p, f) for p in ("T11", "T5") for f in ("pca5", "extended9", "velocity2", "velocity4")
    }


def test_report_endpoint_404_without_dataset(tmp_path: Path) -> None:
    from fastapi.testclient import TestClient

    from app.core.settings import Settings, get_settings
    from app.main import create_app

    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings(
        data_dir=tmp_path / "absent", processed_dir=tmp_path / "p"
    )
    assert TestClient(app).get("/api/report").status_code == 404
