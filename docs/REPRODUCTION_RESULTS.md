# Reproduction Results (Phase 5)

Generated from `data/processed/report/reproduction_2c5946e7bddc.json` (run-matrix digest `2c5946e7bddc`, generated 2026-11-01T14:54:17+00:00).
Every run in the matrix is listed as computed. Published values (doi:10.1038/s42003-024-06784-4) are used for comparison only.

- **Correlation:** Pearson and Spearman over pairwise-complete windows (MATLAB corr, 'rows','complete'); no smoothing. Correlation measures how closely KLD tracks decoder error. It is not an accuracy.
- **Tolerance:** ±0.02 on both r and ρ (REPRODUCTION_PLAN §3). It is a reporting threshold, not a tuning target.
- **p-values:** every Pearson and Spearman p-value underflows to exactly 0 in double precision, so p < 1e-300 in every run.
- **Presets:** `upstream` = released script settings (uncentred covariance X'X/n, windows every 10 s, outlier trials removed). `paper` = Methods text (centred sample covariance, windows every 1 s).

## Primary results (Fig. 1c, Fig. 2c)
| Participant | Features | Preset | Windows | r | published r | Δr | ρ | published ρ | Δρ | ±0.02 |
|---|---|---|---|---|---|---|---|---|---|---|
| T11 | PCA-5 | upstream | 727 | 0.924 | 0.910 | +0.014 | 0.899 | 0.900 | -0.001 | within tolerance |
| T11 | PCA-5 | paper | 7398 | 0.925 | 0.910 | +0.015 | 0.898 | 0.900 | -0.002 | within tolerance |
| T11 | 9-D | upstream | 727 | 0.945 | 0.926 | +0.019 | 0.916 | 0.913 | +0.003 | within tolerance |
| T11 | 9-D | paper | 7398 | 0.945 | 0.926 | +0.019 | 0.915 | 0.913 | +0.002 | within tolerance |
| T5 | PCA-5 | upstream | 437 | 0.580 | 0.590 | -0.010 | 0.586 | 0.600 | -0.014 | within tolerance |
| T5 | PCA-5 | paper | 4481 | 0.594 | 0.590 | +0.004 | 0.600 | 0.600 | -0.000 | within tolerance |
| T5 | 9-D | upstream | 437 | 0.735 | 0.719 | +0.016 | 0.770 | 0.759 | +0.011 | within tolerance |
| T5 | 9-D | paper | 4481 | 0.760 | 0.719 | +0.041 | 0.784 | 0.759 | +0.025 | differs |

## Velocity-only feature sets (Fig. 2a, 2b; upstream preset)
| Participant | Features | Windows | r | published r | Δr | ρ | published ρ | Δρ | ±0.02 |
|---|---|---|---|---|---|---|---|---|---|
| T11 | Velocity | 727 | 0.506 | 0.464 | +0.042 | 0.393 | 0.407 | -0.014 | differs |
| T11 | Velocity + lag | 727 | 0.891 | 0.819 | +0.072 | 0.846 | 0.840 | +0.006 | differs |
| T5 | Velocity | 437 | 0.720 | 0.704 | +0.016 | 0.770 | 0.763 | +0.007 | within tolerance |
| T5 | Velocity + lag | 437 | 0.719 | 0.702 | +0.017 | 0.775 | 0.765 | +0.010 | within tolerance |

## Single-parameter changes from `upstream`
| Participant | Features | Change from upstream | Windows | r | published r | Δr | ρ | published ρ | Δρ | ±0.02 |
|---|---|---|---|---|---|---|---|---|---|---|
| T11 | PCA-5 | D1: centred sample covariance instead of X'X/n | 727 | 0.925 | 0.910 | +0.015 | 0.899 | 0.900 | -0.001 | within tolerance |
| T11 | 9-D | D1: centred sample covariance instead of X'X/n | 727 | 0.946 | 0.926 | +0.020 | 0.916 | 0.913 | +0.003 | within tolerance |
| T11 | Velocity | D1: centred sample covariance instead of X'X/n | 727 | 0.557 | 0.464 | +0.093 | 0.443 | 0.407 | +0.036 | differs |
| T11 | Velocity + lag | D1: centred sample covariance instead of X'X/n | 727 | 0.899 | 0.819 | +0.080 | 0.854 | 0.840 | +0.014 | differs |
| T11 | PCA-5 | D2: windows every 50 bins (1 s) instead of 500 (10 s) | 7398 | 0.924 | 0.910 | +0.015 | 0.899 | 0.900 | -0.001 | within tolerance |
| T11 | 9-D | D2: windows every 50 bins (1 s) instead of 500 (10 s) | 7398 | 0.945 | 0.926 | +0.019 | 0.915 | 0.913 | +0.002 | within tolerance |
| T11 | Velocity | D2: windows every 50 bins (1 s) instead of 500 (10 s) | 7398 | 0.503 | 0.464 | +0.039 | 0.392 | 0.407 | -0.015 | differs |
| T11 | Velocity + lag | D2: windows every 50 bins (1 s) instead of 500 (10 s) | 7398 | 0.888 | 0.819 | +0.069 | 0.843 | 0.840 | +0.003 | differs |
| T11 | PCA-5 | D3: outlier trials (excludeTrials) kept | 750 | 0.911 | 0.910 | +0.001 | 0.901 | 0.900 | +0.001 | within tolerance |
| T11 | 9-D | D3: outlier trials (excludeTrials) kept | 750 | 0.924 | 0.926 | -0.002 | 0.912 | 0.913 | -0.001 | within tolerance |
| T11 | Velocity | D3: outlier trials (excludeTrials) kept | 750 | 0.465 | 0.464 | +0.001 | 0.407 | 0.407 | +0.000 | within tolerance |
| T11 | Velocity + lag | D3: outlier trials (excludeTrials) kept | 750 | 0.814 | 0.819 | -0.005 | 0.836 | 0.840 | -0.004 | within tolerance |
| T5 | PCA-5 | D1: centred sample covariance instead of X'X/n | 437 | 0.591 | 0.590 | +0.001 | 0.598 | 0.600 | -0.002 | within tolerance |
| T5 | 9-D | D1: centred sample covariance instead of X'X/n | 437 | 0.751 | 0.719 | +0.032 | 0.778 | 0.759 | +0.019 | differs |
| T5 | Velocity | D1: centred sample covariance instead of X'X/n | 437 | 0.738 | 0.704 | +0.034 | 0.782 | 0.763 | +0.019 | differs |
| T5 | Velocity + lag | D1: centred sample covariance instead of X'X/n | 437 | 0.738 | 0.702 | +0.036 | 0.786 | 0.765 | +0.021 | differs |
| T5 | PCA-5 | D2: windows every 50 bins (1 s) instead of 500 (10 s) | 4481 | 0.582 | 0.590 | -0.008 | 0.589 | 0.600 | -0.011 | within tolerance |
| T5 | 9-D | D2: windows every 50 bins (1 s) instead of 500 (10 s) | 4481 | 0.746 | 0.719 | +0.027 | 0.776 | 0.759 | +0.017 | differs |
| T5 | Velocity | D2: windows every 50 bins (1 s) instead of 500 (10 s) | 4481 | 0.732 | 0.704 | +0.028 | 0.777 | 0.763 | +0.014 | differs |
| T5 | Velocity + lag | D2: windows every 50 bins (1 s) instead of 500 (10 s) | 4481 | 0.731 | 0.702 | +0.029 | 0.782 | 0.765 | +0.017 | differs |

T5 has no outlier trials, so the D3 change is not run for T5.

## KLD grouped by angular error (Fig. 1b)
| Participant | Variant | r | published r | Δr |
|---|---|---|---|---|
| T11 | code loop (44 bins) | 0.985 | 0.985 | +0.000 |
| T11 | paper text (45 bins) | 0.985 | 0.985 | +0.000 |
| T5 | code loop (44 bins) | 0.983 | 0.983 | +0.000 |
| T5 | paper text (45 bins) | 0.982 | 0.983 | -0.001 |

The released script computes 44 bins: its loop stops one short of the 45 edges and skips [176°, 180°). The paper says 45. Both are shown; the difference is at most 0.001.

## Findings
1. **The upstream preset reproduces all four primary results within ±0.02** on both r and ρ, and Fig. 1b to three decimals.
2. **D3: outlier trials.** For T11, keeping the `excludeTrials` trials, which the released script removes, brings all four feature sets to within 0.005 of the published r and ρ. That includes the velocity-only sets, which otherwise differ by up to 0.072. This suggests the published T11 figures were computed with those trials included, either because the authors' run did not apply the flags or because the released flags differ from theirs. The files flag 35 trials; the paper says 34 (OPEN Q12). This is evidence, not proof. The presets are left as specified, and the change is reported as an ablation, not adopted.
3. **D1 (covariance) and D2 (step) barely change T11's PCA-5 and 9-D results** (at most 0.001 in r). For T5 they move PCA-5 and 9-D r by up to +0.016 each. Combined in the `paper` preset, they move T5 9-D r by +0.025 (0.735 → 0.760), which takes it outside the tolerance. D1 also moves T11's velocity-only r by up to +0.051.
4. **KLD ranges** (upstream, PCA-5): T11 0.060–2.356, T5 0.168–0.786 nats. The paper's approximate ranges are [0, 2.75] and [0, 0.9].
