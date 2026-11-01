# Open Questions

Each question is either **blocking**, meaning work cannot start without an answer, **decision**, meaning you choose and a default is proposed, or **verify**, meaning the answer comes from the data in Phase 2.

| # | Type | Question | Proposed default / how it will be resolved |
|---|---|---|---|
| Q0 | **resolved (Phase 2)** | The Dryad download needs a browser. | Extracted by the user to `data/raw/MINDFUL_Data` on 2026-11-01. The zip itself is not in `data/raw/`, so its SHA-256 is still unrecorded; recorded instead: content digest of all 162 `.mat` files, `5517510f…765c7` (REPRODUCIBILITY_MANIFEST). |
| Q1 | decision | Which preset is the headline reproduction: `upstream` (the code that produced the published numbers) or `paper` (the Methods text: centered covariance and 1 s step)? | **Report both, side by side, with equal visibility.** The Reproduction Report shows both. "Reproduced" is claimed only for the presets that actually match. |
| Q2 | verify | D1: does the uncentered `X'X/n` estimator explain the published values? | Phase 5 ablation. |
| Q3 | decision | D3: Fig 1c/2 code uses trial-only bins with outlier trials removed. The paper says KLD spikes from outlier trials are visible in Fig 2 and that a supplement excludes them. | Default = trial-only with exclusions removed (matches the script). Also run "include excluded trials" and "all bins, including inter-trial" as ablations. |
| Q4 | decision | D4: windows cross block boundaries within a session in the original code. Your rules forbid crossing recording boundaries unless the original does so. It does, but only within a session. | Default = code behaviour (allowed within a session). A strict per-block mode is available and its result reported. |
| Q5 | verify | The README describes `nctx` as "non-causal threshold crossings". Is there any non-causal filtering that matters? | Phase 2: `nctx` is stored as crossings/s (×50 per 20 ms bin). In T5 every value is a whole number of crossings; in T11 86–100% per block are, so some T11 values are fractional. Recorded; it does not change the reproduction. |
| Q6 | verify | D5/D8: real session folder names (zero-padded?) and whether T5 files contain `spikePower`. | **Resolved (Phase 2)**: folder names are equal-width trial days, so `dir` order is chronological (D5: no effect); T5 has no `spikePower` (D8: no effect). No `session_order` option needed. |
| Q7 | decision | Do you have MATLAB R2022b access (e.g. a university licence)? Running the original code on the same data would allow a numeric comparison. | Optional. Without it, we validate against published numbers and our own tests only. |
| Q8 | decision | Commit the upstream clone into our repo, or git-ignore it and pin the commit? | **Git-ignore and pin** (license permits either way). |
| Q9 | verify | The supplementary material has not been read (Supplementary Table: no z-score / M = 10 / no PCA variants; supplementary figure on first-session-only reference for T5). | Read the Supplementary PDF before Phase 3. You can download it from the article page if my fetch is blocked. |
| Q10 | verify | Are `labels` and `angleError` consistent with `atan2` recomputation? What about bins where the cursor is on the target (zero vector)? | **Resolved (Phase 2)**: `angleError` = unsigned angle between `labels` (= targetPos − cursorPos) and `cursorVel` in the same bin; within 0.5° in 99.8–100% of bins; NaN exactly at zero cursor-to-target vectors. The provided `angleError` stays authoritative. |
| Q11 | decision | Python 3.13 (installed) vs 3.12. | Use 3.13 if every pinned dependency has wheels, otherwise install 3.12. Decided in Phase 1. |
| Q12 | verify | Phase 2 found T11 has 1839 trials and 35 excluded, vs 1840 and 34 in the paper. | Reported as observed; nothing adjusted. Analyses use what the files contain. Revisit only if a Phase 5 result hinges on it. |
| Q13 | decision | The user's `ui inspirations/` references (dark cinematic, glass, motion) conflict with the CLAUDE.md visual rules. | **Decided 2026-11-01 (user accepted the proposal):** apply the inspiration styling to the Overview and section headers; charts and data tables keep the scientific rules. Implemented in Phase 6, with the CLAUDE.md visual rules updated to match. |

Defaults in effect since Phase 0 approval (2026-11-01). The user approved Phase 0 without objecting to these; each can still be revisited:
- Q1: report the `upstream` and `paper` presets side by side.
- Q8: the upstream clone stays git-ignored and pinned to its commit.
