# MINDFUL Workbench — frontend

Next.js (App Router) + TypeScript + Tailwind. Does no numerical work; it renders what the local API returns.

```bash
npm install
npm run dev          # http://localhost:3000 (expects the API on 127.0.0.1:8000)
npm run lint
npm run typecheck
npm run build
npm run test:e2e     # Playwright smoke test; saves screenshots to ../reports/screenshots
```

`MINDFUL_API_URL` overrides the backend address (default `http://127.0.0.1:8000`).

## Hosted copy (snapshot mode)

With `MINDFUL_SNAPSHOT=1` the frontend reads saved API responses from `snapshot/` instead of the backend. The Vercel deployment runs this way. The snapshot holds the same aggregates the API serves (no raw `.mat` data), with local paths removed. To refresh it, start the backend, then:

```bash
npm run snapshot
```
