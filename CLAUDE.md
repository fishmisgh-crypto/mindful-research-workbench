# MINDFUL Research Workbench — project instructions

Independent Python reproduction of the MINDFUL neural-instability method (Pun et al., *Commun. Biol.* 2024, doi:10.1038/s42003-024-06784-4), with a local research dashboard. The scientific reproduction is the deliverable. The dashboard is how you inspect it.

## Start of every session
1. Read this file, `docs/PHASE_STATUS.md`, `docs/BUILD_LOG.md`, and `git status` / `git log`.
2. Do not start a phase the user has not approved. Do not redo completed work, and do not silently replace a validated implementation.

## Phase gates
Phases 0–7 are defined in `docs/PHASE_STATUS.md`. Every phase ends with a STOP and a report in this structure: WHAT WE BUILT / HOW IT WORKS / WHY IT MATTERS / WHAT I SHOULD INSPECT / VALIDATION / SCREENSHOTS / FILES CHANGED / KNOWN LIMITATIONS / NEXT PHASE.
After a phase is approved: update docs, run tests, review the diff, confirm no data or secrets are staged, commit locally, and update PHASE_STATUS.

## Scientific constraints (non-negotiable)
- The source of truth for the method is `docs/RESEARCH_SPEC.md`. Paper vs code discrepancies D1–D8 are listed there. Never resolve one silently. Each one is a config parameter.
- KLD direction is **D_KL(P_reference ‖ P_current)**. Never swap the arguments.
- Fit PCA on reference bins only. Reference = first session (T11) / first two sessions (T5), with AE < 4°.
- T11 uses 384 features (`nctx` + `spikePower`). T5 uses 192 (`nctx`). Never force both into one configuration.
- Bins are 20 ms. Window = 3000 bins (60 s). Step = 50 bins (1 s, paper) or 500 (10 s, upstream script). The preset says which.
- No covariance regularization unless it is explicitly configured. Rank-deficient windows → NaN with a reason code.
- Use Cholesky solves and stable log-determinants. Never `inv()`.
- Published r/ρ are **validation targets**. Never hardcode them, tune toward them, or drop observations to match them.
- Correlation is not accuracy. KLD is not a percentage.
- Synthetic data is allowed only in tests, and always labelled `SYNTHETIC — NOT STUDY DATA`. If the dataset is missing, show an empty state, never fake charts.

## Data and privacy
- `data/` is git-ignored. Never commit, upload, or serve raw `.mat` files. The API sends only aggregates and metadata.
- `references/upstream-mindful/` (pinned commit `1809e13`) is read-only. Never edit it.
- Local only: bind to 127.0.0.1. No auth, no cloud.

## Architecture (see docs/TECHNICAL_ARCHITECTURE.md)
- `backend/mindful/` is the pure scientific package (no web imports). `backend/app/` is FastAPI (thin).
- `frontend/` is Next.js App Router + TypeScript + Tailwind + Plotly. It does no numerical work.
- Code style: type hints, small functions, short docstrings, few comments.

## Commands (filled in from Phase 1)
- Backend (from `backend/`): `.venv/Scripts/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`
- Frontend (from `frontend/`): `npm run dev` (dev) or `npm run build && npm run start` (production), both on 127.0.0.1:3000
- Backend checks: `.venv/Scripts/python -m pytest -q`, `-m ruff check .`, `-m ruff format --check .`, `-m mypy`
- Frontend checks: `npm run typecheck`, `npm run lint`, `npm run test:e2e` (needs the API running; saves screenshots to `reports/screenshots/phase1/`)
- Backend setup: `python -m venv .venv` then `.venv/Scripts/python -m pip install -r requirements.lock` (pinned versions)
- Standalone HTML report (from `backend/`): `.venv/Scripts/python -m mindful.export_report ../data/raw/MINDFUL_Data ../data/processed ../reports/reproduction_report.html`
- Reproduction report (from `backend/`): `.venv/Scripts/python -m mindful.reproduce ../data/raw/MINDFUL_Data ../data/processed` (≈ 5 min cold; cached afterwards)
- Analysis (from `backend/`): `.venv/Scripts/python -m mindful.cli analyse ../data/raw/MINDFUL_Data ../data/processed T11 upstream` (reuses preprocessing; writes `data/processed/analysis/*.json`)
- Playwright runs single-worker (`workers: 1`, this machine has ~8 GB RAM) with reduced motion, so screenshots are not taken mid-animation
- Preprocessing (from `backend/`): `.venv/Scripts/python -m mindful.preprocess.run ../data/raw/MINDFUL_Data T11 upstream ../data/processed/preprocess` prints diagnostics and writes `.json` + `.npz` (the API reuses them while the dataset fingerprint matches)
- Dataset inventory (from `backend/`): `.venv/Scripts/python -m mindful.io.inventory ../data/raw/MINDFUL_Data` prints every check. The API caches it in `data/processed/inventory.json` and rebuilds only when `.mat` files change.
- Windows: after rebuilding the frontend, make sure no old `next start` still holds port 3000. Playwright reuses an existing server, and a stale one serves mismatched chunks.

## Visual design rules
Two surfaces (decided 2026-11-01, OPEN_QUESTIONS Q13; references in `ui inspirations/`, untracked):
- **Housing** (dark graphite `#0d1418`, bone text): the rail, page header bands, and the Overview hero. Instrument Serif display type (a full line may be italic, never a single accented word), pill links in the hero only, one orchestrated entrance on the Overview, and the pointer-driven reveal of the drift trace. All motion respects `prefers-reduced-motion`.
- **Paper** (warm off-white, near-black ink, grey hairlines): every table and chart. The scientific rules below apply without exception.
- One accent family: oxblood `#8a2b1f` on paper, lifted `#c4545f` on the housing.
- Type: Instrument Serif for display, IBM Plex Sans for UI text, IBM Plex Mono for numbers and identifiers. Sentence case; no tracked all-caps labels.
- Not allowed on paper: gradients, glassmorphism, neon, heavy rounding, card grids, decorative icons, fake activity, gratuitous animation, oversized stat tiles.
- Navigation: Overview · Data Explorer · Drift Analysis · Reproduction Report · Methods & Sources. Nothing else without a research reason.
- Charts: titled, axes with units, participant + session/time range + preset printed on the chart, NaN shown as gaps, no smoothing, no dual axes (stack KLD and AE panels instead). Interactive charts (Plotly basic bundle, client-only) keep the server-rendered SVG as their fallback until they draw. The hero trace may scale each series to its own range only if the caption says so.
