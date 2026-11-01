# Reproduction Plan

## 1. Strategy: one engine, explicit fidelity settings

The published code and the paper text disagree on several points (RESEARCH_SPEC §5, D1–D8). We will not quietly pick one side. Every disagreement becomes a **named, typed configuration parameter**. Two presets bundle those parameters:

| Parameter | `upstream` preset (what the released MATLAB does) | `paper` preset (what the Methods text says) |
|---|---|---|
| `covariance_estimator` | `uncentered_second_moment` (`X'X/n`) | `sample_covariance` (centered, ddof=1) |
| `step_bins` | 500 (10 s) | 50 (1 s) |
| `window_bins` | 3000 | 3000 |
| `bin_selection` | `trial_only_excluding_outliers` | `trial_only_excluding_outliers` (see OPEN Q3) |
| `cross_block_windows` | `allow_within_session` | `allow_within_session` (strict mode available) |
| `session_end_handling` | `nan_last_n_windows` (n = window/step) | same |
| `regularization` | `none` (rank-deficient → NaN) | `none` |
| `zscore` | per block, trailing 9001 bins, `movstd` ddof=1, std<1e-5 → 1 | same |
| `pca_dim` | 5 | 5 |
| `reference_sessions` | T11: [1], T5: [1, 2] by **chronological** order (D5 recorded as a finding) | same |
| `reference_ae_max_deg` | 4.0 (strict `<`) | 4.0 |
| `ae_source` | `provided` (`info.angleError`) | `provided` (recomputed AE used only as a check) |
| `correlation_smoothing` | none | none |

Every run writes its full resolved configuration and a hash into its outputs. The dashboard displays the preset name next to every number. We will report **both** presets. Which one counts as the "headline" reproduction is OPEN Q1.

Run matrix for Phase 5: {T11, T5} × {PCA-5, 9-D} × {upstream, paper} = 8 primary results. We will also run single-parameter variations (change one setting from `upstream`, e.g. covariance alone, step alone) to see which discrepancy explains any gap. Secondary checks: the 2-D/4-D velocity-only sets (Fig 2a/b) and the AE-binned KLD (Fig 1b).

## 2. Step-by-step pipeline and validation per step

| # | Step | Implementation | Validation (pytest unless noted) |
|---|---|---|---|
| 1 | Discover sessions and blocks | Walk `T5/` and `T11/`. Parse the day number and block number. Sort numerically | Expected counts: T11 = 15 sessions / 29 blocks; T5 = 6 sessions. Print the sort order and compare it to MATLAB `dir` order (D5) |
| 2 | Load `.mat` | `scipy.io.loadmat`, falling back to `h5py` for v7.3 files | Synthetic v5 and v7.3 fixtures give identical arrays. Orientation check (rows = bins). Same row count across fields |
| 3 | Feature assembly | T11 `[nctx, spikePower]`, T5 `nctx` | F = 384 / 192. If T5 has `spikePower`, record it and keep 192 (paper), and flag it (D8) |
| 4 | Rolling z-score | Pandas `rolling(9001, min_periods=1)` per block. Std with ddof=1. NaN-aware. Floor at 1e-5 → 1 | Compare with a hand-written reference loop on random data. First bin = 0. Matches MATLAB `movmean/movstd([K 0])` semantics, including shrinking windows at block start |
| 5 | Trial selection | Mask from `startStops` (1-based inclusive), minus `excludeTrials` | Bin counts per block. Trial counts T11 = 1840 − 34 excluded; T5 = 1200 |
| 6 | Windows | Port `SelectEpoch` exactly. Also a strict mode that never crosses a block | Window count formula. No window spans sessions after masking. Strict mode never spans blocks |
| 7 | Reference bins | Port `GetSessionData` plus AE < 4 | Count is reported. Every reference bin has AE < 4 and belongs to a reference session |
| 8 | PCA | `numpy.linalg.svd` on reference bins centered by their own mean. No sklearn whitening | Explained variance sums to 100%. Reference scores have mean 0. Note: sign flips do not change KLD (tested) |
| 9 | Lagged velocity | Port `getlagX` on the full block before trial selection | First bin of each block = 0. Shift is exactly 1 bin |
| 10 | Gaussian estimate | `mean`, plus covariance per `covariance_estimator` | Identity tests. Uncentered equals centered + μμᵀ (exactly, for ddof=0) |
| 11 | KLD | Cholesky of Σ_cur, `cho_solve`, `logdet = 2·Σ log diag(L)`. Rank or Cholesky failure → NaN plus a reason code | KL(P‖P) ≈ 0. Shifted mean > 0. KL(P‖Q) ≠ KL(Q‖P). Closed form for 1-D Gaussians. Matches `inv`-based formula on well-conditioned input. Condition number logged per window |
| 12 | Median AE per window | `nanmedian` over the same bin range | Hand-built windows |
| 13 | Correlation | `scipy.stats.pearsonr` / `spearmanr` on pairwise-complete windows | Report r, ρ, p, n, participant, config hash. Spearman p in MATLAB uses a t-approximation for large n; scipy does too, but small p-values may differ in the last digit |
| 14 | AE recomputation (check only) | `atan2` angle between `labels` and `cursorVel`, wrapped to [0, 180]. NaN if either vector is zero | Agreement with `info.angleError` reported (median abs diff, % within 0.5°). If they differ, investigate. Do not substitute |

## 3. How discrepancies with the paper will be investigated (Phase 5)
1. Run `upstream` first. If it matches the paper within about ±0.02, the pipeline is behaving like the authors' code.
2. Change one parameter at a time (D1, D2, D3, D5) and record how much each one moves the result.
3. Check intermediate values: reference bin count, PCA explained variance, number of windows, number of NaN windows, and the KLD range. The paper gives KLD ranges of [0, ~2.75] for T11 and [0, ~0.9] for T5.
4. Without MATLAB we cannot run the original code to compare numbers directly. If you have MATLAB access (e.g. through your university), a direct comparison would be the strongest check (OPEN Q7).
5. We will not tune parameters, drop windows, or pick whichever configuration fits best in order to match the paper. Every run gets reported.

## 4. Things explicitly out of scope
- Fig 3 (tuning), Fig 4 (dPCA), Fig 6 (other reference tasks), and the pairwise session KLD matrix. These could become optional later phases.
- Any claim of clinical utility.
