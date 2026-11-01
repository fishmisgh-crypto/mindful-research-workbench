# Phase Status

| Phase | Name | Status | Date |
|---|---|---|---|
| 0 | Research & repository audit | **Approved** | 2026-11-01 |
| 1 | Application foundation | **Approved** | 2026-11-01 |
| 2 | Dataset ingestion | **Approved** | 2026-11-01 |
| 3 | Preprocessing & feature engineering | **Approved** | 2026-11-01 |
| 4 | KLD & MINDFUL engine | **Approved** | 2026-11-01 |
| 5 | Reproduce the research results | **Approved** | 2026-11-01 |
| 6 | Dashboard integration | Pending | |
| 7 | Final validation & delivery | Pending | |

## Phase 0 deliverables
- docs/RESEARCH_SPEC.md
- docs/REPRODUCTION_PLAN.md
- docs/DATA_DICTIONARY.md
- docs/TECHNICAL_ARCHITECTURE.md
- docs/OPEN_QUESTIONS.md
- CLAUDE.md, docs/BUILD_LOG.md, docs/REPRODUCIBILITY_MANIFEST.json, .gitignore

## Phase 1 deliverables
- backend/: FastAPI app (`app/`), `/api/health`, settings, response schemas, 3 pytest tests, `requirements.lock`
- frontend/: Next.js shell with the five sections, design tokens, layout components, Overview wired to `/api/health`, honest empty states on the other four pages
- frontend/e2e/: Playwright smoke test (7 tests) producing `reports/screenshots/phase1/*.png`

## Phase 2 deliverables
- backend/mindful/io/: `discovery.py` (sessions/blocks, D5/D6 orders), `matfile.py` (v5 + v7.3), `block.py` (typed, strict-shape loader), `validation.py` (per-block checks), `inventory.py` (summary, documented-count comparison, content digest, CLI), `detail.py` (per-block aggregates)
- backend/mindful/stats/angular.py
- backend/app: `GET /api/dataset/summary`, `GET /api/dataset/{participant}/{session}/{block}`, inventory cache
- frontend: Data Explorer (inventory, checks, block table) and block detail pages (checks, missing data, AE histogram, trial table)
- tests: 32 backend (synthetic fixtures), 12 Playwright; screenshots in `reports/screenshots/phase2/`
- docs: DATA_DICTIONARY verified section; D5, D6, D8, Q0, Q5, Q6, Q10 resolved; Q12 added; manifest digest

## Phase 3 deliverables
- backend/mindful/preprocess/: `config.py` (PreprocessConfig, upstream/paper presets, matlab_round), `zscore.py` (BGzscoreNew port), `lag.py` (getlagX port), `windows.py` (SelectEpoch, GetSessionSegmentInds, GetSegmentData, SetIndstoNaN ports), `pca.py` (MATLAB pca conventions), `pipeline.py` (two-pass participant pipeline, diagnostics, npz output), `run.py` (CLI + cached entry point)
- backend/app: `GET /api/preprocess/{participant}?preset=upstream|paper`, cached by dataset fingerprint + config digest
- frontend: preprocessing comparison (upstream vs paper) per participant on the Data Explorer
- tests: 73 backend (literal 1-based MATLAB transcriptions for windows/reference/NaN logic; loop reference for z-score; sklearn cross-check for PCA), 12 Playwright; screenshots in `reports/screenshots/phase3/`

## Phase 4 deliverables
- backend/mindful/stats/: `gaussian.py` (uncentred second moment and sample covariance, D1), `kld.py` (D_KL(ref || cur) via Cholesky; MATLAB rank test; NaN + reason code; singular reference is an error)
- backend/mindful/: `analysis.py` (AnalysisConfig, upstream/paper presets, window engine, session-end NaN, summaries), `runs.py` (cache-aware orchestration), `cli.py` (`python -m mindful.cli analyse ...`)
- preprocessing `.npz` is now fully reloadable (`load_prepared`), so analysis does not repeat preprocessing
- backend/app: `GET /api/analysis/{participant}?preset=&feature_set=&include_windows=`
- frontend: Drift Analysis page with participant / preset / feature-set selection, stacked KLD and median-AE panels, summary and per-session table
- tests: 99 backend, 15 Playwright (now single-worker); screenshots in `reports/screenshots/phase4/`

## Phase 5 deliverables
- backend/mindful/: `stats/correlation.py` (pairwise-complete Pearson/Spearman), `ae_binned.py` (Fig 1b port, 44- and 45-bin variants), `reproduce.py` (run matrix: 8 primary, 4 secondary, 20 single-parameter ablations, 4 Fig 1b variants; comparison; CLI), `data/published_targets.json` (comparison only)
- preprocessing: `reference_scope` ("sessions" | "all", the latter for Fig 1b); blocks are no longer cached between passes (memory)
- caches keyed by config digest, so any configuration can be run
- backend/app: `GET /api/report`
- frontend: Reproduction Report page (summary, primary, ablations, velocity sets, Fig 1b scatters, provenance); Overview shows reproduced r / ρ next to published targets
- docs/REPRODUCTION_RESULTS.md (generated from the report JSON)
- tests: 110 backend, 18 Playwright; screenshots in `reports/screenshots/phase5/`
