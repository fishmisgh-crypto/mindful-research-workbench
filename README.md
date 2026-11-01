# MINDFUL Research Workbench

An independent Python reproduction of **MINDFUL**, the neural-instability measure from Pun et al., *Measuring instability in chronic human intracortical neural recordings towards stable, long-term brain-computer interfaces*, Communications Biology 7, 1363 (2024), [doi:10.1038/s42003-024-06784-4](https://doi.org/10.1038/s42003-024-06784-4).

MINDFUL compares each minute of activity recorded by an implanted brain–computer interface with a reference day, using the Kullback–Leibler divergence (KLD) between Gaussian fits, and asks how closely that drift tracks the cursor's angular error. This repository recomputes it from the released recordings and code, compares the result with the paper, and provides a local dashboard for inspecting every step.

## Results

With the released code's settings (the `upstream` preset), all four primary results fall within ±0.02 of the published values:

| Participant | Features | Reproduced r / ρ | Published r / ρ |
|---|---|---|---|
| T11 | PCA-5 (Fig. 1c) | 0.924 / 0.899 | 0.910 / 0.900 |
| T11 | 9-D (Fig. 2c) | 0.945 / 0.916 | 0.926 / 0.913 |
| T5 | PCA-5 (Fig. 1c) | 0.580 / 0.586 | 0.590 / 0.600 |
| T5 | 9-D (Fig. 2c) | 0.735 / 0.770 | 0.719 / 0.759 |
| T11 / T5 | AE-binned KLD (Fig. 1b) | 0.985 / 0.983 (r) | 0.985 / 0.983 (r) |

For participant T11, keeping the outlier trials that the released script removes brings all four T11 feature sets within 0.005 of the published values. This suggests the published T11 figures included those trials. It is reported as evidence, not adopted as a setting.

- Full results, single-parameter changes and findings: [docs/REPRODUCTION_RESULTS.md](docs/REPRODUCTION_RESULTS.md)
- Standalone report to share (one HTML file, aggregates only): [reports/reproduction_report.html](reports/reproduction_report.html)
- Every paper–code discrepancy (D1–D9) and how it was handled: [docs/RESEARCH_SPEC.md](docs/RESEARCH_SPEC.md) §5

Correlation describes how closely KLD tracks decoder error; it is not an accuracy. Published values are used for comparison only, never in a calculation.

## Repository layout

```
backend/
  mindful/      scientific package (no web code): io, preprocess, stats, analysis, reproduce, export_report
  app/          FastAPI service (local only, 127.0.0.1)
  tests/        pytest; synthetic fixtures are labelled SYNTHETIC — NOT STUDY DATA
frontend/       Next.js dashboard: Overview, Data Explorer, Drift Analysis, Reproduction Report, Methods & Sources
docs/           specification, plan, data dictionary, results, open questions, build log, manifest
reports/        screenshots per phase and the standalone report
data/           git-ignored: raw dataset and computed caches
references/     git-ignored: the upstream MATLAB code, pinned at commit 1809e13
```

## Requirements

- Python 3.13, Node.js 24 (npm 11). Developed on Windows 11 with Git Bash; the commands below use that shell.
- About 8 GB of RAM and 2 GB of free disk for dependencies and caches.
- The dataset: download `MINDFUL_Data.zip` from Dryad ([doi:10.5061/dryad.n2z34tn5s](https://doi.org/10.5061/dryad.n2z34tn5s)); scripted download is refused, so this step is manual. Extract it to `data/raw/MINDFUL_Data/` (it contains `T11/`, `T5/` and `T11(additional)/`).
- Optional: clone the upstream code into `references/upstream-mindful/` at commit `1809e132549f3c4b03327e3a14c748927d765e6e` for side-by-side reading.

## Set up

```bash
cd backend && python -m venv .venv && .venv/Scripts/python -m pip install -r requirements.lock
```

```bash
cd frontend && npm ci && npx playwright install chromium
```

## Run

Start the API (port 8000) and the dashboard (port 3000) in two terminals:

```bash
cd backend && .venv/Scripts/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

```bash
cd frontend && npm run build && npm run start
```

Then open http://localhost:3000. The first visit to a page computes and caches its results (about 5 minutes in total on a laptop).

Compute everything from the command line instead (from `backend/`):

```bash
.venv/Scripts/python -m mindful.reproduce ../data/raw/MINDFUL_Data ../data/processed
```

```bash
.venv/Scripts/python -m mindful.export_report ../data/raw/MINDFUL_Data ../data/processed ../reports/reproduction_report.html
```

## Test

```bash
cd backend && .venv/Scripts/python -m pytest -q && .venv/Scripts/python -m ruff check . && .venv/Scripts/python -m mypy
```

```bash
cd frontend && npm run typecheck && npm run lint && npm run test:e2e
```

The end-to-end tests need the API running and the dataset present; tests that need the dataset skip themselves without it.

## Data and privacy

The raw recordings stay on your disk: `data/` is git-ignored, and the API returns only aggregates and metadata (window tables, summaries, check results), never neural matrices. Everything runs locally; nothing is uploaded. This is research software, not a medical device.

## Licence and attribution

The method, data and reference code belong to their authors; the upstream MATLAB code is under Brown University's notice-retaining licence (see its `LICENSE.txt`). No licence has been chosen yet for the code in this repository. If you use the results, cite the paper and the Dryad dataset above.
