# Technical Architecture

## Principles
- **The science lives in plain Python functions.** It does not depend on FastAPI, it can be tested on its own, and it can be run from the command line.
- **The API is a thin layer.** It loads cached results and starts runs. It never contains the math.
- **The frontend only displays results.** It does no numerical work. Every number it shows comes from a backend result that has a configuration hash.
- **Local only.** The server binds to `127.0.0.1`. There is no auth, no cloud, and no telemetry. Raw neural data never leaves the machine and is never served as a file.

## Repository layout
```
Mindful/
├── CLAUDE.md
├── backend/
│   ├── pyproject.toml            # dependency pins; uv.lock (or pip-tools requirements.lock)
│   ├── app/
│   │   ├── main.py               # FastAPI app factory, CORS limited to localhost:3000
│   │   ├── api/                  # routers: health, dataset, analysis, report
│   │   ├── core/                 # settings (pydantic-settings), logging, paths
│   │   ├── models/               # pydantic request/response schemas
│   │   └── services/             # orchestrates science functions + result cache
│   ├── mindful/                  # ← the scientific package (no web imports)
│   │   ├── io/                   # matfile.py (scipy/h5py), discovery.py, validation.py
│   │   ├── preprocess/           # zscore.py, selection.py, pca.py, lag.py
│   │   ├── stats/                # gaussian.py, kld.py, angular.py, correlation.py
│   │   ├── windows.py            # window generation + validity masks
│   │   ├── analysis.py           # AnalysisConfig + presets, window engine (named analysis.py: preprocess/pipeline.py exists)
│   │   ├── runs.py               # cache-aware orchestration (preprocess + analysis on disk)
│   │   └── cli.py                # `python -m mindful.cli run --participant T11 --preset upstream`
│   └── tests/                    # pytest; synthetic fixtures labelled SYNTHETIC
├── frontend/
│   ├── app/                      # Next.js App Router: /, /data, /analysis, /report, /methods
│   ├── components/               # shell, nav, tables, chart wrappers, empty states
│   ├── features/                 # page-level feature modules
│   ├── lib/                      # typed API client (types generated from OpenAPI)
│   ├── styles/                   # tokens.css (colour, type, spacing)
│   └── tests/                    # Playwright
├── data/            (git-ignored)
│   ├── raw/MINDFUL_Data/         # user extracts the Dryad zip here
│   └── processed/                # parquet/npz caches keyed by config hash
├── references/upstream-mindful/  # pinned clone, read-only, git-ignored (see below)
├── reports/{artifacts,screenshots,exports}/
└── docs/
```

## Data flow
```
data/raw/*.mat ─► io.discovery ─► io.matfile ─► validation report
                                       │
                                       ▼
                 preprocess (z-score → trial mask → PCA[ref] → lag)
                                       │
                                       ▼
                 windows ─► stats.gaussian ─► stats.kld ─► per-window table
                                       │                      │
                                       ▼                      ▼
                             stats.angular (median AE)   correlation
                                       │
                                       ▼
            data/processed/<config-hash>/{windows.parquet, result.json, manifest.json}
                                       │
                         FastAPI (read-only JSON) ─► Next.js + Plotly
```
A run takes 30 s to a few minutes, depending on step size (T11 at 1 s has about 8,700 windows of 5–9 dimensions). Runs go into a simple in-process background task with a status endpoint, plus result caching. No job-queue library.

## Stack and versions (pinned in Phase 1; exact versions in backend/requirements.lock and frontend/package-lock.json)
| Layer | Choice | Note |
|---|---|---|
| Python | 3.13.14 | all dependencies ship cp313 wheels (checked in Phase 1) |
| Science | numpy, scipy, pandas, scikit-learn (only for cross-checking PCA), h5py, pyarrow | |
| API | FastAPI, uvicorn, pydantic v2, pydantic-settings | |
| Tests | pytest, hypothesis (property tests for KLD), ruff, mypy | |
| Lock | `uv` lockfile (fallback: `pip-tools`) | |
| Node | 24.18.1 installed | |
| Frontend | Next.js (App Router), TypeScript strict, Tailwind CSS, `react-plotly.js` with `plotly.js-basic-dist-min` (smaller bundle) | Plotly needs `dynamic(import, {ssr:false})` |
| E2E | Playwright | |

## API surface (draft)
| Method | Path | Returns |
|---|---|---|
| GET | `/api/health` | status, versions, dataset path configured / found |
| GET | `/api/dataset/summary` | participants → sessions → blocks, shapes, durations, validation issues |
| GET | `/api/dataset/{participant}/{session}/{block}` | metadata, trial table, missing-data stats (no raw matrices) |
| GET | `/api/analysis/presets` | resolved preset configs |
| POST | `/api/analysis/runs` | start a run → run id |
| GET | `/api/analysis/runs/{id}` | status, config, window table (KLD, median AE, validity), PCA diagnostics, correlation |
| GET | `/api/report` | published vs. reproduced comparison for all completed primary runs |
| GET | `/api/exports/{id}.csv` | window-level CSV for a run |

Downsampled feature traces for plots (e.g. one PC over time) are computed server-side and returned as aggregated series. Raw neural matrices are never sent to the browser.

## Upstream reference handling
- Cloned at commit `1809e13…` into `references/upstream-mindful/`. Files are set read-only.
- **Recommendation:** git-ignore the clone and record the URL and commit in `REPRODUCIBILITY_MANIFEST.json`, with a setup script that re-clones and checks the commit. This keeps the authors' code out of our history. Their license allows redistribution with the notice, so committing it as a vendored copy is also legal (OPEN Q8).

## Design system (summary — full spec in Phase 1)
- Colors: warm off-white `#F7F5F0` background, near-black `#141414` text, gray `#D9D5CC` hairlines, and a single accent, oxblood `#8A2B1F` (chosen in Phase 1). Implemented tokens: paper `#F6F4EE`, ink `#161513`, rule `#DCD7CB`. Data series are drawn in near-black plus the accent only.
- Type: display serif for titles (e.g. *Newsreader* or *Source Serif 4*), *Inter* or *IBM Plex Sans* for UI text, *IBM Plex Mono* / *JetBrains Mono* for numbers. All self-hosted through `next/font`.
- Layout: left rail with the five navigation items, a 12-column content grid, hairline separators instead of cards, square corners (≤ 2 px radius).
- Charts: KLD and median AE as two separate stacked panels sharing one x-axis (no dual y-axis). Session boundaries drawn as hairline rules. NaN windows shown as gaps, never interpolated. The participant and preset are printed in every chart title.
