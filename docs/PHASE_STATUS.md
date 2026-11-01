# Phase Status

| Phase | Name | Status | Date |
|---|---|---|---|
| 0 | Research & repository audit | **Approved** | 2026-11-01 |
| 1 | Application foundation | **Approved** | 2026-11-01 |
| 2 | Dataset ingestion | **Approved** | 2026-11-01 |
| 3 | Preprocessing & feature engineering | In progress | 2026-11-01 |
| 4 | KLD & MINDFUL engine | Pending | |
| 5 | Reproduce the research results | Pending | |
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
