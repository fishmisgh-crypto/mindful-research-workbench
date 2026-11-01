# Build Log

## 2026-11-01 — Phase 0: research audit
- Cloned `ewinapun/MINDFUL` at `1809e132549f3c4b03327e3a14c748927d765e6e` into `references/upstream-mindful/` and set its files read-only.
- Read: README, LICENSE (Brown University permissive notice-retaining licence; bundled dPCA is MIT), `MINDFUL_main_script.m`, `fig1_grouped_by_AE.m`, `fig2_plot_MINDFUL.m`, `fig5_param_sweep.m`, `MINDFUL.m`, `ConcatSavedSessionsData.m`, `BGzscoreNew.m`, `ProbDistributionEst.m`, `CalcKL.m`, `CalcJKL.m`, `getlagX.m`, `angdiffdeg.m`, `RowColon.m`.
- Paper: full text from PMC11494208. The nature.com page redirects to a login. Inline equations are missing from the PMC text, so they were rebuilt from the prose and the code.
- Dataset: metadata and README text via the Dryad API (version 6, 411,951,588 bytes). Scripted file download returns 401, so the user must download manually.
- Key findings:
  - **D1**: the code's "covariance" is uncentered `X'X/n`.
  - **D2**: the Fig 1c/2 script steps windows by 500 bins (10 s), not 1 s.
  - **D5**: sessions are ordered alphabetically by `dir`.
  - Full list in RESEARCH_SPEC §5.
- Environment: Python 3.13.14, Node 24.18.1, npm 11.16.0. MATLAB is not installed.
- No application code written (per Phase 0 rules).

## 2026-11-01 — Phase 1: application foundation
- Paused partway because drive C: was full (~50 MB free). Resumed after the npm and pip caches were cleared and the drive had ~11.4 GB free. The five layout components that failed to save were rewritten.
- Python: kept 3.13.14. Every dependency had a cp313 wheel. Pinned in `backend/requirements.lock` (fastapi 0.162.0, numpy 2.5.4, scipy 1.18.1, pandas 3.1.0, scikit-learn 1.9.1, h5py 3.16.0, pyarrow 26.0.0, pydantic 2.14.2).
- `pip install -e .` failed: the isolated build environment could not resolve setuptools. Installed the dependency list directly instead. The backend is not installed as a package; pytest uses `pythonpath = ["."]`.
- mypy strict: scipy, h5py and sklearn have no bundled stubs, so a `ignore_missing_imports` override was added for those three modules only.
- Frontend: Next.js 15.5.28, React 19.1.0, Tailwind 4.3.3, TypeScript 5.9.3, Playwright 1.56.1. Plotly is deferred to Phase 6 (no charts yet).
- Design decisions: oxblood `#8A2B1F` is the single accent. Fonts are Newsreader (display), IBM Plex Sans (UI) and IBM Plex Mono (numbers), self-hosted via `next/font`.
- Fixed during review: the sidebar's right rule stopped at viewport height; the phone-width test now also asserts the page rendered.
- Windows gotcha: stopping the background `npm run start` shell left its `node` child holding port 3000, and Playwright reused that stale server after a rebuild ("Application error"). Killed the process; noted in CLAUDE.md.
- Approved by the user on 2026-11-01 and committed locally.

## 2026-11-01 — Phase 2: dataset ingestion
- The user extracted the Dryad release to `data/raw/MINDFUL_Data`. 162 `.mat` files, 413.5 MB, all MATLAB v5. The zip was not kept locally, so a content digest of the extracted files is recorded instead.
- Probed every block before writing the loader (scratch scripts, not committed). A full load of 50 blocks takes ≈ 8 s; an inventory build including hashing takes ≈ 15–30 s on OneDrive.
- Built `mindful.io` with no web imports. The loader raises on any per-bin row-count mismatch and never transposes. Display-only per-trial fields with the wrong length are set aside with a warning; the analysis fields (`startStops`, `excludeTrials`) stay strict.
- Bug found while running on real data: the first loader treated a length mismatch in `trialSuccess` as fatal and dropped T11 day_689 Block_14, which made T11 look like 1764 trials. Fixed as described above.
- Robustness: unreadable files (`OSError`/`ValueError`) are reported as a failed `load` check, not as a 500. A test covers this.
- Findings: D5, D6 and D8 have no effect on this release. Q10 resolved. T11 trial counts are off by one in each direction (Q12). `useClick` is per block, not per trial.
- The inventory cache is keyed on path, size and mtime of every `.mat` file. A CLI-built cache with a relative root is rebuilt once by the API (which uses the absolute root).
- Approved by the user on 2026-11-01 and committed locally.

## 2026-11-01 — Phase 3: preprocessing and feature engineering
- Read the upstream code again before porting: `BGzscoreNew.m`, `MINDFUL.m` (`SelectEpoch`, `GetSessionSegmentInds`, `GetSegmentData`, `SetIndstoNaN`, `CalculatePCA`, `PCAtransform`, `getlagX`), `fig2_plot_MINDFUL.m`, `MINDFUL_main_script.m`.
- Memory: a concatenated 384-feature T11 matrix would be ≈ 1.3 GB, so the pipeline z-scores block by block, fits PCA on reference blocks first, then projects every block to 5 PCs. Only the PC scores (n × 5) are kept. T11 takes ≈ 45 s, T5 ≈ 13 s.
- Precision: on real data, pandas' rolling z-score matches a direct per-window recomputation to 4e-14 (largest spike-power channels, 9000-bin window).
- Invariant verified on real data and added as a test: every window that crosses a session end, or is clipped at the end of the data, is inside upstream's session-end NaN set, for both presets.
- Bugs caught by tests before any real run: pandas returned a read-only array (in-place floor failed); a D7 test fixture had too few windows to test anything.
- UI fix: preprocessing table labels wrapped one word per line at ≈ 800 px; labels are now nowrap and the table scrolls inside its container.
- `ui inspirations/` (user's design references: Dribbble shots, motion-site prompts) read; it conflicts with the CLAUDE.md visual rules. Raised for a decision before the dashboard phase; left untracked.
- Approved by the user on 2026-11-01 and committed locally.

## 2026-11-01 — Phase 4: KLD and MINDFUL engine
- Ported `ProbDistributionEst.m`, `CalcKL.m`, `CalcDistanceFromData`, `GetMedianAEperSeg`, `SetIndstoNaN`. Upstream mixes the uncentred second moment (as Σ) with the sample mean in the KLD formula; the `upstream` preset reproduces exactly that. The `paper` preset uses the centred sample covariance (ddof = 1).
- Rank test is MATLAB's (`max(size) · eps(σ_max)`), then Cholesky + `cho_solve`; log-determinants from the Cholesky diagonal. No `inv()`, no regularisation.
- Real data, all four participant × preset combinations, all four feature sets: no rank-deficient or non-PD windows, no negative KLD. The only NaNs are session-end windows (T11: 90 of 817 upstream, 900 of 8298 paper; T5: 36 of 473, 360 of 4841).
- The 9-D feature set is badly scaled by design (raw cursorVel ≈ 1e-3 appended to PC scores ≈ 1, as upstream): condition numbers up to 4.7e8. On the 10 worst-conditioned real windows, our Cholesky KLD matches a literal `inv()`/SVD port of `CalcKL` to ≤ 9e-11 relative.
- Runtime: T11 paper ≈ 52 s including preprocessing; cached API responses 0.2–1 s (T11 paper 9-D window table ≈ 575 kB).
- No correlation computed in this phase (Phase 5).
- Environment: the machine ran out of memory (0.2 GB of 7.7 GB free; mostly other apps). Parallel Playwright workers crashed (0xC0000409) and the Next server dropped connections. Closed the in-app browser tab and pinned Playwright to one worker; all 15 tests pass.
- Test fix: the selection test clicked the next link before the previous navigation finished.
- Approved by the user on 2026-11-01 and committed locally.

## 2026-11-01 — Phase 5: reproduce the research results
- Read `fig1_grouped_by_AE.m` again: Fig 1b uses an all-session AE < 4 reference and computes only 44 of 45 AE bins (the loop runs to `length - 1`). Added `reference_scope = "all"` and both bin counts.
- Removed the reference-block cache from the preprocessing pipeline. With an all-session reference it would hold every z-scored block in memory (≈ 1.3 GB on an 8 GB machine). Blocks are reloaded instead.
- Generalised caches to config digests, so ablations are ordinary configurations.
- The first full run took 306 s and then crashed while printing: the Windows console (cp1252) cannot encode Δ / ρ. The report had already been written. Fixed with UTF-8 stdout. Removed superseded preset-named cache files (≈ 170 MB).
- After seeing that the D3 ablation matched T11's PCA-5 and 9-D values, ablations were extended from 2 to all 4 feature sets. All four were already computed, so this makes the matrix complete rather than selective. Nothing was tuned or dropped.
- Results: see docs/REPRODUCTION_RESULTS.md.
- UI fixes: the comparison tables overflowed the content column; replaced the all-identical p-value column with one data-driven line; the tolerance column now reads within / differs instead of pass / warn.
- Approved by the user on 2026-11-01 and committed locally. Design direction for Phase 6 decided (OPEN Q13).

## 2026-11-01 — Phase 6: dashboard integration
- Design direction decided by the user (OPEN Q13). Read the inspiration prompts and opened the two BCI Dribbble shots: both are light card dashboards with a lime accent, so only the dark rail and oversized display headline were taken from them; the hero mechanics (spotlight reveal, staggered blur-rise, pill links) come from the prompts file.
- The hero's memorable element is the study's own claim made tangible: the pointer reveals median angular error under the KLD trace. Each series is scaled to its own range, and the caption says so.
- Plotly loads only in the browser (`next/dynamic`, `ssr: false`), from the basic bundle. First-load JS on /analysis stays at 109 kB. The static SVG remains until Plotly has drawn.
- CSV export proxies through a Next route so the browser never needs the API address. Inputs are allow-listed on both sides.
- Fixes found while reviewing screenshots: nav marker measured the link inside a positioned `<li>` (always offset 0); entrance animation blurred screenshots (tests now use reduced motion); `last_analysis_run` was always null; stale "not yet verified" and "computed in Phase 5" notes; hero caption claimed pointer-only reveal on touch screens; all-caps tracked labels replaced with sentence case.
- Approved by the user on 2026-11-01 and committed locally.
