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
