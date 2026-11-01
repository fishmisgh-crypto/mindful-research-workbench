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
