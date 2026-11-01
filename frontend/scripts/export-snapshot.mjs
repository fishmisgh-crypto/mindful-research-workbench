// Saves the running backend's responses (aggregates only, never raw data) as static JSON/CSV
// under snapshot/, so a hosted build with MINDFUL_SNAPSHOT=1 can render without the API.
// Usage: start the backend, then `npm run snapshot`.

import { mkdir, rm, writeFile } from "node:fs/promises";
import path from "node:path";

const API_URL = process.env.MINDFUL_API_URL ?? "http://127.0.0.1:8000";
const OUT = path.join(import.meta.dirname, "..", "snapshot");
const PARTICIPANTS = ["T11", "T5"];
const PRESETS = ["upstream", "paper"];
const FEATURE_SETS = ["pca5", "extended9", "velocity2", "velocity4"];

/** Must match snapshotFile() in lib/api.ts. */
const fileFor = (apiPath) => encodeURIComponent(apiPath);

/** Local machine paths are not useful online and name the user's folders. */
const scrubPaths = (text) =>
  text.replace(/"(configured_path|root)":\s*"[^"]*"/g, (_, key) => `"${key}": "data/raw (local only)"`);

async function save(apiPath, ext = ".json") {
  const response = await fetch(`${API_URL}${apiPath}`);
  if (!response.ok) throw new Error(`${apiPath}: HTTP ${response.status}`);
  const body = scrubPaths(await response.text());
  await writeFile(path.join(OUT, fileFor(apiPath) + ext), body);
  return body;
}

await rm(OUT, { recursive: true, force: true });
await mkdir(OUT, { recursive: true });

const health = JSON.parse(await save("/api/health"));
const summary = JSON.parse(await save("/api/dataset/summary"));
await save("/api/report");

for (const p of PARTICIPANTS) {
  for (const preset of PRESETS) {
    await save(`/api/preprocess/${p}?preset=${preset}`);
    for (const fs of FEATURE_SETS) {
      const query = `preset=${preset}&feature_set=${fs}`;
      await save(`/api/analysis/${p}?${query}`);
      await save(`/api/exports/${p}.csv?${query}`, "");
    }
  }
}

let blocks = 0;
for (const participant of summary.participants) {
  for (const session of participant.sessions) {
    for (const block of session.blocks) {
      await save(`/api/dataset/${participant.id}/${session.name}/${block.name}`);
      blocks += 1;
    }
  }
}

await writeFile(
  path.join(OUT, "meta.json"),
  JSON.stringify({ taken_at: new Date().toISOString(), source_last_analysis_run: health.last_analysis_run }, null, 2),
);
console.log(`Snapshot written to ${OUT} (${blocks} blocks).`);
