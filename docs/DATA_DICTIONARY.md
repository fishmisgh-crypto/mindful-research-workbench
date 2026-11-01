# Data Dictionary

Source: the Dryad README (dataset v6, 2024-10-25). The archive has **not** been inspected yet. Every shape, dtype and orientation below is a claim from the documentation. Phase 2 must check each one against the real files and update this table. Columns marked *Verified* are filled in during Phase 2.

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
