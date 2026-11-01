"""SYNTHETIC — NOT STUDY DATA. Gaussian estimate and KL divergence properties."""

import numpy as np
import pytest

from mindful.stats.gaussian import Gaussian, estimate
from mindful.stats.kld import kl_divergence, prepare_reference

ESTIMATORS = ("uncentered_second_moment", "sample_covariance")


def gaussian_sample(seed: int, n: int = 4000, k: int = 5, shift: float = 0.0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    a = rng.normal(size=(k, k))
    return rng.normal(size=(n, k)) @ (a + k * np.eye(k)) / k + shift


def upstream_calc_kl(x1: np.ndarray, x2: np.ndarray) -> float:
    """Literal port of ProbDistributionEst + CalcKL (inv, SVD log-det, uncentred sigma)."""

    def pd(x: np.ndarray) -> dict[str, np.ndarray | float]:
        sigma = x.T @ x / x.shape[0]
        return {
            "mu": x.mean(0),
            "sigma": sigma,
            "logdet": float(np.sum(np.log(np.linalg.svd(sigma)[1]))),
        }

    p1, p2 = pd(x1), pd(x2)
    inv = np.linalg.inv(p2["sigma"])
    d = p2["mu"] - p1["mu"]
    return 0.5 * (
        np.trace(inv @ p1["sigma"]) + d @ inv @ d - x1.shape[1] + p2["logdet"] - p1["logdet"]
    )


@pytest.mark.parametrize("estimator", ESTIMATORS)
def test_kl_of_a_distribution_with_itself_is_zero(estimator: str) -> None:
    g = estimate(gaussian_sample(0), estimator)  # type: ignore[arg-type]
    assert kl_divergence(prepare_reference(g), g).value == pytest.approx(0.0, abs=1e-12)


@pytest.mark.parametrize("estimator", ESTIMATORS)
def test_kl_is_positive_for_a_shift_and_asymmetric(estimator: str) -> None:
    p = estimate(gaussian_sample(0), estimator)  # type: ignore[arg-type]
    q = estimate(gaussian_sample(1, shift=0.5) * 1.7, estimator)  # type: ignore[arg-type]
    pq = kl_divergence(prepare_reference(p), q).value
    qp = kl_divergence(prepare_reference(q), p).value
    assert pq > 0 and qp > 0
    assert abs(pq - qp) > 1e-3


def test_one_dimensional_closed_form() -> None:
    m1, s1, m2, s2 = 0.3, 1.2, -0.4, 0.7
    p = Gaussian(np.array([m1]), np.array([[s1**2]]), 100)
    q = Gaussian(np.array([m2]), np.array([[s2**2]]), 100)
    expected = np.log(s2 / s1) + (s1**2 + (m1 - m2) ** 2) / (2 * s2**2) - 0.5
    assert kl_divergence(prepare_reference(p), q).value == pytest.approx(expected, rel=1e-12)


@pytest.mark.parametrize("k", [2, 5, 9])
def test_matches_upstream_inv_formula_on_well_conditioned_data(k: int) -> None:
    x_ref = gaussian_sample(10, k=k)
    x_cur = gaussian_sample(11, n=3000, k=k, shift=0.2)
    ours = kl_divergence(
        prepare_reference(estimate(x_ref, "uncentered_second_moment")),
        estimate(x_cur, "uncentered_second_moment"),
    )
    assert ours.reason == "ok"
    assert ours.value == pytest.approx(upstream_calc_kl(x_ref, x_cur), rel=1e-10)


def test_direction_is_reference_first() -> None:
    x_ref, x_cur = gaussian_sample(20), gaussian_sample(21, shift=0.3) * 2
    ours = kl_divergence(
        prepare_reference(estimate(x_ref, "uncentered_second_moment")),
        estimate(x_cur, "uncentered_second_moment"),
    ).value
    assert ours == pytest.approx(upstream_calc_kl(x_ref, x_cur), rel=1e-10)
    assert ours != pytest.approx(upstream_calc_kl(x_cur, x_ref), rel=1e-3)


@pytest.mark.parametrize("estimator", ESTIMATORS)
def test_kl_is_non_negative(estimator: str) -> None:
    for seed in range(20):
        ref = prepare_reference(estimate(gaussian_sample(seed), estimator))  # type: ignore[arg-type]
        cur = estimate(gaussian_sample(seed + 100, n=300, shift=seed / 10), estimator)  # type: ignore[arg-type]
        assert kl_divergence(ref, cur).value >= -1e-10


@pytest.mark.parametrize("estimator", ESTIMATORS)
def test_sign_flip_of_a_feature_does_not_change_kl(estimator: str) -> None:
    """PCA signs are arbitrary; flipping a component in both ref and window is harmless."""
    x_ref, x_cur = gaussian_sample(30), gaussian_sample(31, shift=0.4)
    flip = np.array([1, -1, 1, -1, 1.0])
    a = kl_divergence(prepare_reference(estimate(x_ref, estimator)), estimate(x_cur, estimator))  # type: ignore[arg-type]
    b = kl_divergence(
        prepare_reference(estimate(x_ref * flip, estimator)),  # type: ignore[arg-type]
        estimate(x_cur * flip, estimator),  # type: ignore[arg-type]
    )
    assert a.value == pytest.approx(b.value, rel=1e-10)


def test_uncentred_equals_centred_plus_outer_mean() -> None:
    x = gaussian_sample(40, n=500) + 3.0
    u = estimate(x, "uncentered_second_moment")
    centred_ddof0 = np.cov(x, rowvar=False, ddof=0)
    np.testing.assert_allclose(u.cov, centred_ddof0 + np.outer(u.mean, u.mean), rtol=1e-12)
    np.testing.assert_allclose(
        estimate(x, "sample_covariance").cov, np.cov(x, rowvar=False), rtol=1e-12
    )


def test_rank_deficient_window_is_nan_with_reason() -> None:
    ref = prepare_reference(estimate(gaussian_sample(50, k=3), "sample_covariance"))
    x = gaussian_sample(51, n=200, k=3)
    x[:, 2] = x[:, 0]  # duplicate feature -> singular covariance
    result = kl_divergence(ref, estimate(x, "sample_covariance"))
    assert np.isnan(result.value) and result.reason == "rank_deficient" and result.rank == 2


def test_too_few_bins_is_nan_with_reason() -> None:
    ref = prepare_reference(estimate(gaussian_sample(60, k=2), "sample_covariance"))
    result = kl_divergence(ref, estimate(np.ones((1, 2)), "sample_covariance"))
    assert np.isnan(result.value) and result.reason == "too_few_bins"


def test_singular_reference_is_an_error_not_a_nan() -> None:
    x = gaussian_sample(70, k=3)
    x[:, 1] = 0.0
    with pytest.raises(ValueError, match="rank"):
        prepare_reference(estimate(x, "sample_covariance"))
