# Data Dictionary

Source: the Dryad README (dataset v6, 2024-10-25). The tables below are the documentation's claims, kept as written in Phase 0. **What the real files contain (Phase 2, all 50 blocks inspected) is in [Verified against the files](#verified-against-the-files-phase-2) at the end. Where the two differ, the verified section is authoritative.**

Conventions [D]:
- `nStep` = number of 20 ms bins in a block.
- `nChan` = number of channels across both arrays (expected 192).
- `nTrial` = number of trials in the block. A trial runs from target cue to target acquisition.

## Folder layout [D]
```
MINDFUL_Data/
├── T5/
│   └── day <k>/            # exact folder naming to be verified (README shows "day k"; code expects "day_<n>")
│       └── block_01/, block_02/, ...   # code parses block number as folder_name[7:]
│           ├── data.mat
│           ├── task.mat
│           └── info.mat
├── T11/            (same structure)
└── T11(additional)/        # personal use (day 658) + random target (day 665); Fig 6 only
```
Only selected blocks from each session are included [D].

## data.mat

| Field | Documented shape | Meaning | Used by | Planned use | Verified |
|---|---|---|---|---|---|
| `nctx` | nStep × nChan | Threshold-crossing counts per 20 ms bin (−3.5 RMS). The README calls them "non-causal"; meaning unclear (OPEN Q5) | Both participants | Neural features, columns 1–192 | ☐ |
| `spikePower` | nStep × nChan | Spike-band power, 250–5000 Hz | T11 | Neural features, columns 193–384 (T11 only, see D8) | ☐ |
| `labels` | nStep × 2 | Inferred intended direction = cursor-to-target vector [x, y] | Not used directly upstream | Recompute AE (validation) | ☐ |
| `cursorVel` | nStep × 2 | Decoded velocity [x, y] (Xhat) | Both | 9-D features, AE recomputation | ☐ |

## task.mat

| Field | Documented shape | Meaning | Planned use | Verified |
|---|---|---|---|---|
| `name` | string | Task name: "Fitts", "circle", "personal use" | Data Explorer; check that reference and comparison tasks match | ☐ |
| `nPointsPerBlock` | 1 × 1 | Bins in the block | Consistency check against `size(nctx,1)` | ☐ |
| `startStops` | nTrial × 2 | Trial start and stop bin indices. **MATLAB 1-based, inclusive** (assumed; the code uses them with `RowColon`) | Trial-only selection | ☐ |
| `excludeTrials` | nTrial × 1 bool | True if mean noise > 5% during the trial (outlier trial) | Drop trials (code-faithful mode) | ☐ |
| `useClick` | nTrial × 1 bool | Target selected by click | Explorer only | ☐ |
| `moveDirVect` | nTrial × 2 | Task movement direction | Explorer only | ☐ |

## info.mat

| Field | Documented shape | Meaning | Planned use | Verified |
|---|---|---|---|---|
| `targetPos` | nStep × 2 | Target position [x, y] | Recompute cursor-to-target vector to cross-check `labels` | ☐ |
| `cursorPos` | nStep × 2 | Cursor position [x, y] | Same as above | ☐ |
| `magEst` | nStep × 1 | Adjusted decoded cursor-to-target magnitude | Not used | ☐ |
| `angleError` | nStep × 1 | **Instantaneous AE in degrees**. Upstream reads this directly | Reference selection (AE < 4°), median AE per window | ☐ |
| `angleErrorPerTrial` | nTrial × 1 | Median AE per trial | Explorer, sanity check | ☐ |
| `percentCorrect` | 1 × 1 | Block success rate (%) | Explorer | ☐ |
| `pathEfficiency` | nTrial × 1 | Path efficiency per trial | Explorer | ☐ |
| `trialSuccess` | nTrial × 1 bool | Trial outcome | Explorer | ☐ |
| `orthChanges` | nTrial × 1 | Number of orthogonal direction changes per trial | Explorer | ☐ |
| `timeToTarget` | nTrial × 1 | Time to target, in seconds | Explorer | ☐ |
| `prctOutliers` | nStep × nChan, sparse (optional) | Percent of outliers per channel per step | Explorer (missing-data view) | ☐ |
| `avgOutliers` | nStep × 1 (optional) | Maximum average outlier across arrays | Explorer | ☐ |

## Derived quantities (our pipeline)

| Name | Shape | Definition | Spec ref |
|---|---|---|---|
| `X_raw` | nStep × F | T11: `[nctx, spikePower]` (F = 384). T5: `nctx` (F = 192) | RESEARCH_SPEC §3.1 |
| `X_z` | nStep × F | Per-block trailing z-score, 9001-bin window | §3.2 |
| `trial_mask` | nStep bool | Bin lies in a trial that is not excluded | §3.3 |
| `Z_pc` | nSel × 5 | PCA scores from the reference fit | §3.6 |
| `V`, `V_lag` | nSel × 2 each | `cursorVel`, plus the same lagged one bin within the block (zero at block start) | §3.7 |
| `ae_deg` | nStep | Provided `angleError`. Recomputed `ae_recomputed` kept alongside it for validation | §3.10 |
| window table | nWin rows | start/end bin, session, block(s) spanned, `valid` flag, KLD, median AE, n bins, NaN reason | §3.4, §3.11 |

## Questions MATLAB-to-Python must not get wrong
- **Orientation.** All arrays are documented as rows = time bins. The loader asserts this: `shape[0]` must equal `nPointsPerBlock` and be identical across fields of one block. scipy's `loadmat` keeps MATLAB's row/column layout. h5py (v7.3 files) returns arrays **transposed** and must be transposed back explicitly, with a test.
- **Indexing.** `startStops` is 1-based and inclusive in MATLAB. Python slice = `[start−1 : stop]`.
- **Logical arrays.** They may load as `uint8`. Cast to `bool` explicitly.
- **Sparse `prctOutliers`.** scipy returns `scipy.sparse`. Keep it sparse.
- **Scalars and strings.** Use `squeeze_me=True` carefully. `name` may arrive as a `str` or as a char array.

## Verified against the files (Phase 2)

Checked on 2026-11-01 by loading every block of `T11/` (29) and `T5/` (21) with `mindful.io` (`python -m mindful.io.inventory`). Content digest of all 162 `.mat` files: `sha256 5517510fb15c724edc4d3d3246ea08aee7895b31c87356624ff4f793989765c7`.

**Layout**
- Folders are `T11/day_<trial day>/Block_<nn>/` and `T5/day_<trial day>/Block_<nn>/`, e.g. `T11/day_658/Block_05`. Block numbers are the original session block numbers (e.g. 05, 07), not 1..k. Each T11 session folder also has a `.DS_Store` (ignored).
- All files are **MATLAB v5** (`MATLAB 5.0 MAT-file, Platform: PCWIN64`); scipy reads them directly. No v7.3 files, so the h5py path is exercised only in tests.
- `T11(additional)/` holds `personal_use/day_658/Block_08,09` and `random_targets/day_665/Block_08,09` (4 blocks, out of scope).

**data.mat**
| Field | T11 | T5 | Notes |
|---|---|---|---|
| `nctx` | float32 (nStep, 192) | uint64 (nStep, 192) | Values are **rates in crossings/s**: one crossing in a 20 ms bin = 50. T5: 100% of non-zero values are multiples of 50. T11: 86–100% per block, so some T11 values are not whole crossings (cf. "non-causal", Q5). |
| `spikePower` | float32 (nStep, 192) | **absent** | D8 resolved: the upstream loader also builds 192 features for T5. |
| `labels` | float32 (nStep, 2) | float64 (nStep, 2) | Equals `targetPos − cursorPos` to < 1e-7 in every block. |
| `cursorVel` | float32 (nStep, 2) | float64 (nStep, 2) | |

**task.mat**
| Field | Verified | Notes |
|---|---|---|
| `name` | `"circleOfCircles"` (T11), `"Fitts"` (T5) | Not the README's "circle". |
| `nPointsPerBlock` | uint16 scalar | Equals the row count of every per-bin field in all 50 blocks. T11 ≈ 15,083–15,285 bins (≈ 302–306 s); T5 ≈ 11,995–12,004 (≈ 240 s). |
| `startStops` | uint16 / int64 (nTrial, 2) | **1-based, inclusive confirmed**: all starts ≥ 1, and `stop == nPointsPerBlock` occurs (T11 day_665 Block_07). Trials are **back to back** (`start[i+1] = stop[i] + 1`) in every block, so non-trial bins exist only before the first trial (≈ 90–500 bins) and after the last. |
| `excludeTrials` | uint8 (nTrial, 1) | Cast to bool. |
| `useClick` | uint8 **(1, 1)** | A per-block scalar, not per trial as documented. |
| `moveDirVect` | float32 (nTrial, 2) | |

**info.mat**
| Field | Verified | Notes |
|---|---|---|
| `angleError` | float32 (nStep, 1), in [0°, 180°] | **Q10 resolved**: the unsigned angle between `labels` and `cursorVel` in the same bin (within 0.5° in 99.8–100% of bins per block; median difference ≈ 1e-6°). NaN exactly where `labels` is the zero vector. T11: ≈ 1.7–2.5% NaN (mostly at the start of a block); T5: none. |
| `targetPos`, `cursorPos` | float32 (nStep, 2) | `targetPos` has NaNs in T11. |
| `magEst`, `prctOutliers`, `avgOutliers` | T11 only | `prctOutliers` is sparse (nStep, 192). |
| `trialSuccess`, `pathEfficiency`, `orthChanges` | (nTrial, 1) | **Exception: T11 day_689 Block_14 has 76 entries for 75 trials** (`timeToTarget`, `angleErrorPerTrial`, `startStops`, `excludeTrials` have 75). These three display-only fields are set aside for that block, not truncated. |
| `timeToTarget`, `angleErrorPerTrial`, `percentCorrect` | as documented | |

**Counts vs documentation**
| | Observed | Documented | |
|---|---|---|---|
| T11 sessions / blocks | 15 / 29 | 15 / 29 | match |
| T11 trials | **1839** | 1840 | Off by one. Counting the extra entry in day_689 Block_14's per-trial info fields would give 1840; plausible, unconfirmed (Q12). |
| T11 excluded trials | **35** | 34 | Unexplained (Q12). |
| T5 sessions / blocks | 6 / 21 | 6 / 2–4 per session | match |
| T5 trials / excluded | 1200 / 0 | 1200 / 0 | match |
