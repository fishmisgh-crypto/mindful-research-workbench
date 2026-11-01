# Research Specification — MINDFUL Reproduction

Status: Phase 0 draft, awaiting approval.
Sources read for this spec:

| Source | Identifier | How it was accessed |
|---|---|---|
| Paper | Pun T.K. et al., *Commun. Biol.* 7, 1363 (2024). DOI [10.1038/s42003-024-06784-4](https://doi.org/10.1038/s42003-024-06784-4) | Full text via PubMed Central (PMC11494208). The PMC text drops inline math symbols, so equations below are rebuilt from the surrounding text plus the MATLAB code. |
| Code | [github.com/ewinapun/MINDFUL](https://github.com/ewinapun/MINDFUL) @ `1809e132549f3c4b03327e3a14c748927d765e6e` (2024-08-13) | Cloned to `references/upstream-mindful/`, read-only |
| Dataset | Dryad DOI [10.5061/dryad.n2z34tn5s](https://doi.org/10.5061/dryad.n2z34tn5s), version 6, published 2024-10-25, `MINDFUL_Data.zip` = 411,951,588 bytes | Dryad API metadata and landing-page README. **The archive itself is not downloaded yet.** |
| Supplementary material | Supplementary Figs/Table | **Not read yet** (see OPEN_QUESTIONS Q9) |

Throughout this document, `[P]` marks a claim from the paper, `[C]` a claim from the code (file:line), and `[D]` a claim from the dataset README.

---

## 1. What the study measures

A fixed (never retrained) cursor decoder works well at first. Over days to months the brain signals it reads drift, and cursor control gets worse. MINDFUL checks whether that decline can be detected **from the neural signals alone**, without knowing where the user meant to move.

How it works:
1. Take a **reference** set of neural-feature vectors from the period when the decoder was working well (first session(s), time bins with angular error < 4°).
2. Take a **comparison** set made of all bins in a 60 s window.
3. Fit a multivariate Gaussian (mean and covariance) to each set. The score is the Kullback–Leibler divergence D_KL(reference ‖ comparison).
4. Slide the window forward and repeat.
5. Validation (offline only): correlate the score with the median angular error (AE) in the same windows.

A high MINDFUL score means the current distribution of neural features differs from the reference. It is not a probability or a percentage, and it is not an accuracy figure.

## 2. Participants and data

| | T11 | T5 |
|---|---|---|
| Arrays | 2 × 96 ch, precentral gyrus [P] | 2 × 96 ch [P] |
| Recording | wireless broadband [P] | cabled [P] |
| Features | threshold crossings (−3.5 RMS) **+** spike-band power (250–5000 Hz) → **384** [P] | threshold crossings only → **192** [P] |
| Bin | 20 ms, non-overlapping [P] | 20 ms [P] |
| Task | center-out-and-back, 8 targets, click to select [P] | random target, 500 ms dwell [P] |
| Decoder | fixed LSTM [P] | fixed linear regression with exponential smoothing [P] |
| Online normalization | adaptive z-score, 3-min rolling window [P] | bias correction on the decoder output [P] |
| Sessions | 15 sessions, trial days 658–800 (~142 days); 2 × 5-min blocks each, but only 1 block on day 751 [P][D] | 6 sessions, trial days 2121–2149 (28 days); 2–4 × 4-min blocks each [P][D] |
| Trials | 1840 trials (145 min); 34 outlier trials [P] | 1200 trials (84 min); 0 outlier trials [P] |
| Reference sessions | first session [P][C `MINDFUL_main_script.m:43-45`] | first **two** sessions (the first is short) [P][C] |

There is also an extra folder, `T11(additional)/`, holding about 16 min of personal use (day 658) and about 10 min of random-target task (day 665) [D]. These belong to Fig. 6 (robustness to the choice of reference task), which is **out of scope** for the core reproduction.

## 3. Processing pipeline (as the authors actually ran it)

### 3.1 Loading and concatenation — `utils/ConcatSavedSessionsData.m`
- The loader reads each session folder under `T5/` or `T11/`. Session order is whatever MATLAB's `dir` returns, which is **alphabetical** [C:33-36]. The trial day is parsed from folder names of the form `day_<n>` [C:120-124].
- Blocks inside a session are sorted by **file modification time** (`datenum`) [C:75-76].
- Neural matrix per block [C:184-195]: if a block has both `nctx` and `spikePower`, the matrix is `[nctx spikePower]`. If it has only `nctx`, it is `nctx`. Values are cast to double.
- `labels`, `cursorVel` and every field in `info.mat` (including the per-bin `angleError`) are stacked vertically in block order. `blockStartStop` and `trialStartStop` are shifted so they index into the stacked array.

### 3.2 Per-channel rolling z-score — `utils/BGzscoreNew.m`
Applied **per block** before stacking [C `ConcatSavedSessionsData.m:198-200`], with `zscoreFeatures = true` and `trailingMoving = true` [C `MINDFUL_main_script.m:33-34`]:
- mean: `movmean(x, [9000 0], 'omitnan')`. This is a trailing window of 9000 previous bins plus the current bin, so 180 s × 50 Hz + 1. It is causal.
- std: `movstd(x, [9000 0], 'omitnan')`. MATLAB normalizes by N−1. A window with one sample gives std = 0.
- Any std `< 1e-5` is replaced by 1 [C:373]. As a result, the first bin of every block z-scores to exactly 0.
- z = (x − mean) / std.
- The rolling window restarts at the start of each block. It does not carry over between blocks.

### 3.3 Trial-only selection — `MINDFUL.SelectEpoch` with `excludeNonTrials = 1` [C `MINDFUL.m:118-139`, `fig2_plot_MINDFUL.m:13`]
- Trials flagged in `excludeTrials` are removed.
- For each block, only bins inside the remaining trials are kept, and the block's trials are joined end to end. The bins between trials are dropped.
- All blocks are then joined into one trial-only matrix. Bin-level `angleError` and `cursorVel` are subset the same way.

### 3.4 Windows — `SelectEpoch` [C:120-154]
- Window starts are spaced every `updateHz` bins within each block's trial-only data. The number of windows per block is `floor(nTrialBins / updateHz)`.
- Each window runs **forward**: `[start, start + winlen − 1]`, with `winlen = 3000` bins (60 s). Windows are clipped at the end of the data.
- A window that starts late in a block **runs on into the next block of the same session**. Near the end of a session, it can run into the next session.
- Windows that would cross a session end are fixed **after** the computation: `SetIndstoNaN` sets the last `round(winlen/updateHz)` windows of every session to NaN, for both KLD and median AE [C:562-591].
- Step size:
  - The paper says "shifted in increments of 1 s" [P], which is 50 bins.
  - **`fig2_plot_MINDFUL.m:15` (the script for Figs 1c and 2) sets `updateHz = 500`, i.e. 10 s.**
  - `fig5_param_sweep.m:14` uses 50 bins (1 s), but with `excludeNonTrials = 0`.
  - → Discrepancy D2.

### 3.5 Reference selection — `fig2_plot_MINDFUL.m:29-36`
1. `GetSessionData(init_day)` [C `MINDFUL.m:510-523`] takes the window indices for the reference session(s). It leaves out the last `round(winlen/updateHz) − 1` windows. It then returns the **unique** bins covered by those windows.
2. Only bins with `angleError < 4` are kept. NaN AE counts as "not < 4", so those bins are dropped.
3. The same bins are used both to fit the PCA and as the KLD reference.

### 3.6 PCA — `MINDFUL.CalculatePCA` / `PCAtransform` [C:177-233]
- MATLAB `pca(refData)`: centered by the reference mean, then SVD. Only the reference bins are used.
- Projection: `(X − mu_ref) · coeff[:, 1:5]`. This is applied to every trial-only bin, reference bins included.
- No whitening.

### 3.7 Feature sets — `fig2_plot_MINDFUL.m:39-47`
| Name in code | Dimensions | Composition | Paper figure |
|---|---|---|---|
| `NF` | 5 | top-5 PC scores | Fig 1c (**Configuration 1**) |
| `Xhat` | 2 | `cursorVel` | Fig 2a |
| `Xhatlag` | 4 | `cursorVel`, `cursorVel` lagged by 1 bin | Fig 2b |
| `NFXhatlag` | 9 | PC1–5, `cursorVel`(t), `cursorVel`(t−1) | Fig 2c (**Configuration 2**) |

How the lag is built [C `MINDFUL.m:619-627`]: it is computed on the **full** data (before trial selection), within each block. The first bin of each block gets zeros. The result is then subset to trial bins, so the lagged value at the first bin of a trial is the previous bin even if that bin was outside the trial. The two velocity sets are appended without any scaling.

### 3.8 Gaussian estimate — `utils/dist_metrics/ProbDistributionEst.m`
```matlab
pd.mu    = mean(X,1)';
pd.sigma = X'*X / pd.n;          % <-- NOT mean-centred
pd.logdetsigma = sum(log(diag(S)))  % S from svd(pd.sigma)
```
**Discrepancy D1.** The paper says "sample covariance matrices". The code computes the uncentered second-moment matrix E[xxᵀ] = Σ + μμᵀ. The two match only when μ ≈ 0. Reference bins have μ = 0 in PC space by construction (PCA centers on them), but the velocity features and the comparison windows do not.

### 3.9 KLD — `utils/dist_metrics/CalcKL.m`, called as `CalcKL(pd_ref, pd_cur)` [C `MINDFUL.m:275-285, 449-451`]
```
D_KL(P_ref ‖ P_cur) = ½ [ tr(Σ_cur⁻¹ Σ_ref)
                        + (μ_cur − μ_ref)ᵀ Σ_cur⁻¹ (μ_cur − μ_ref)
                        − k
                        + ln det Σ_cur − ln det Σ_ref ]
```
- The direction (reference first) matches the requirement and the paper's wording.
- If `rank(Σ_cur) < k`, KLD = NaN. No regularization is applied anywhere.
- The code uses `inv()`. We will use Cholesky solves instead, which gives the same answer more stably.
- The log-determinant comes from summing the logs of the singular values.

### 3.10 Angular error
- The paper defines it as the absolute angle between the cursor-to-target vector and the decoded velocity, ranging 0–180° [P].
- The code **does not compute AE**. It reads the precomputed per-bin `info.angleError` [C `fig2_plot_MINDFUL.m:34`; D].
- The upstream helper `angdiffdeg(x, y, 'absolute')` gives `min(mod(x−y,360), 360−mod(x−y,360))`.
- Our plan: recompute AE from `labels` and `cursorVel` (atan2) and check it against `angleError` (see REPRODUCTION_PLAN §2).
- Median AE per window: `median(angleError(window), 'omitnan')` over the same bin range as the KLD window [C:461-478].

### 3.11 Correlation — `CalcDistCorr2mAE` via `PlotCompFnvsAE(1, ...)` [C:480-501, 835-942]
- `nsmooth = 1`, so there is no smoothing.
- `SetIndstoNaN` runs first, then MATLAB `corr(..., 'Pearson'|'Spearman', 'rows', 'complete')`.
- Windows from the reference session **are included** in the correlation.

## 4. Published validation targets (do not hardcode)

| Participant | Config | Pearson r | Spearman ρ | Figure |
|---|---|---|---|---|
| T11 | PCA-5 (NF) | 0.91 | 0.90 | 1c |
| T5 | PCA-5 (NF) | 0.59 | 0.60 | 1c |
| T11 | 9-D (NF + Xhat + Xhat_lag) | 0.926 | 0.913 | 2c |
| T5 | 9-D | 0.719 | 0.759 | 2c |
| T11 | Xhat (2-D) | 0.464 | 0.407 | 2a (secondary) |
| T5 | Xhat (2-D) | 0.704 | 0.763 | 2a (secondary) |
| T11 | Xhat + lag (4-D) | 0.819 | 0.840 | 2b (secondary) |
| T5 | Xhat + lag (4-D) | 0.702 | 0.765 | 2b (secondary) |
| T11 | AE-binned KLD (45 bins) | 0.985 | — | 1b (secondary sanity check) |
| T5 | AE-binned KLD | 0.983 | — | 1b (secondary) |

All p < 0.001 [P]. The paper does not report n, the number of windows.

## 5. Discrepancies between paper and code

| ID | Topic | Paper | Code | Impact |
|---|---|---|---|---|
| D1 | Covariance | sample covariance | uncentered `X'X/n` | Changes KLD values, and the correlations may change too. **High.** Phase 4: both estimators implemented (`upstream` / `paper` presets); neither produced a rank-deficient window on the real data. |
| D2 | Window step | 1 s (50 bins) | 10 s (500 bins) in the Fig 1c/2 script | About 10× more windows at 1 s. Correlation changes should be small but are not zero. **Medium.** |
| D3 | Bins used | "all time bins in a 60-s interval" | trial bins only, with excluded trials removed (`excludeNonTrials=1`) | Medium. The paper also says T11's KLD spikes come from outlier trials and that a supplement shows them excluded. That is inconsistent with the Fig 2 script, which excludes them. |
| D4 | Window boundaries | not stated | windows cross block boundaries within a session; crossings into the next session are NaN'd afterwards | Low–medium. Conflicts with our rule against crossing recording boundaries, so it will be exposed as an option. Phase 3: with the real block lengths, every window that crosses a session end is inside upstream's session-end NaN set (both presets), so cross-session windows never reach a correlation; only cross-*block* windows do (T11: 140 of 817 at step 500). |
| D5 | Session order | chronological (implied) | alphabetical `dir` order | **Resolved in Phase 2: no effect.** Folders are named by trial day (`day_658`…`day_800`, `day_2121`…`day_2149`); within each participant all names have the same number of digits, so alphabetical order equals chronological order. T5 reference = day_2121 + day_2126. |
| D6 | Block order | chronological | file modification time | Low. We sort by block number. Phase 2: on this extraction, modification-time order matched block-number order in all 21 sessions. |
| D7 | Reference window trimming | — | `GetSessionSegmentInds` drops `lastn−1` windows while `SetIndstoNaN` drops `lastn` | Negligible. Reproduced exactly (`WindowIndex.session_reference_windows` vs `session_end_windows`, tested against literal MATLAB transcriptions). Because reference bins are defined through windows, the step size changes the reference set slightly: T11 3042 (step 500) vs 3048 (step 50) bins; T5 3998 vs 4008. |
| D8 | T5 feature count | 192 | `[nctx spikePower]` if `spikePower` exists in T5 files | **Resolved in Phase 2: no effect.** T5 files contain no `spikePower`, so the upstream loader also builds 192 features. |
