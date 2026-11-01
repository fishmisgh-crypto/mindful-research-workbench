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
