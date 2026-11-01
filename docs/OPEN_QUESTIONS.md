# Open Questions

Each question is either **blocking**, meaning work cannot start without an answer, **decision**, meaning you choose and a default is proposed, or **verify**, meaning the answer comes from the data in Phase 2.

| # | Type | Question | Proposed default / how it will be resolved |
|---|---|---|---|
| Q0 | **blocking (Phase 2)** | The Dryad download needs a browser: the API returns *"Unauthorized"* for scripted file downloads. | You download `MINDFUL_Data.zip` (412 MB) from https://doi.org/10.5061/dryad.n2z34tn5s and extract it to `data/raw/`. I will verify its SHA-256 and record it. |
| Q1 | decision | Which preset is the headline reproduction: `upstream` (the code that produced the published numbers) or `paper` (the Methods text: centered covariance and 1 s step)? | **Report both, side by side, with equal visibility.** The Reproduction Report shows both. "Reproduced" is claimed only for the presets that actually match. |
| Q2 | verify | D1: does the uncentered `X'X/n` estimator explain the published values? | Phase 5 ablation. |
| Q3 | decision | D3: Fig 1c/2 code uses trial-only bins with outlier trials removed. The paper says KLD spikes from outlier trials are visible in Fig 2 and that a supplement excludes them. | Default = trial-only with exclusions removed (matches the script). Also run "include excluded trials" and "all bins, including inter-trial" as ablations. |
| Q4 | decision | D4: windows cross block boundaries within a session in the original code. Your rules forbid crossing recording boundaries unless the original does so. It does, but only within a session. | Default = code behaviour (allowed within a session). A strict per-block mode is available and its result reported. |
| Q5 | verify | The README describes `nctx` as "non-causal threshold crossings". Is there any non-causal filtering that matters? | Recorded as a dataset property. It does not change the reproduction, because the authors used the same files. |
| Q6 | verify | D5/D8: real session folder names (zero-padded?) and whether T5 files contain `spikePower`. | Checked in Phase 2. If MATLAB's alphabetical order differs from chronological order, that goes in the report as a finding, and the `upstream` preset gets a `session_order: matlab_dir` option so its effect can be measured. |
| Q7 | decision | Do you have MATLAB R2022b access (e.g. a university licence)? Running the original code on the same data would allow a numeric comparison. | Optional. Without it, we validate against published numbers and our own tests only. |
| Q8 | decision | Commit the upstream clone into our repo, or git-ignore it and pin the commit? | **Git-ignore and pin** (license permits either way). |
| Q9 | verify | The supplementary material has not been read (Supplementary Table: no z-score / M = 10 / no PCA variants; supplementary figure on first-session-only reference for T5). | Read the Supplementary PDF before Phase 3. You can download it from the article page if my fetch is blocked. |
| Q10 | verify | Are `labels` and `angleError` consistent with `atan2` recomputation? What about bins where the cursor is on the target (zero vector)? | Phase 2/5 check. The provided `angleError` stays the authoritative AE (it is what the authors used). |
| Q11 | decision | Python 3.13 (installed) vs 3.12. | Use 3.13 if every pinned dependency has wheels, otherwise install 3.12. Decided in Phase 1. |

Defaults in effect since Phase 0 approval (2026-11-01). The user approved Phase 0 without objecting to these; each can still be revisited:
- Q1: report the `upstream` and `paper` presets side by side.
- Q8: the upstream clone stays git-ignored and pinned to its commit.
