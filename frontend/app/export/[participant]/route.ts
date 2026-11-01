/** Proxies the backend's window CSV so the browser never needs the API address. */

import { readFile } from "node:fs/promises";

import { SNAPSHOT, snapshotFile } from "@/lib/api";

const API_URL = process.env.MINDFUL_API_URL ?? "http://127.0.0.1:8000";
const ALLOWED = {
  participant: ["T11", "T5"],
  preset: ["upstream", "paper"],
  feature_set: ["pca5", "extended9", "velocity2", "velocity4"],
};

export async function GET(request: Request, { params }: { params: Promise<{ participant: string }> }) {
  const { participant } = await params;
  const query = new URL(request.url).searchParams;
  const preset = query.get("preset") ?? "upstream";
  const featureSet = query.get("feature_set") ?? "pca5";
  if (
    !ALLOWED.participant.includes(participant) ||
    !ALLOWED.preset.includes(preset) ||
    !ALLOWED.feature_set.includes(featureSet)
  ) {
    return new Response("Unknown participant, preset or feature set.", { status: 400 });
  }
  const apiPath = `/api/exports/${participant}.csv?preset=${preset}&feature_set=${featureSet}`;
  if (SNAPSHOT) {
    try {
      return new Response(await readFile(snapshotFile(apiPath)), {
        headers: {
          "Content-Type": "text/csv; charset=utf-8",
          "Content-Disposition": `attachment; filename="mindful_${participant}_${preset}_${featureSet}.csv"`,
        },
      });
    } catch {
      return new Response("Not in the saved snapshot.", { status: 404 });
    }
  }
  try {
    const upstream = await fetch(`${API_URL}${apiPath}`, { cache: "no-store" });
    return new Response(upstream.body, {
      status: upstream.status,
      headers: {
        "Content-Type": upstream.headers.get("content-type") ?? "text/csv",
        "Content-Disposition": upstream.headers.get("content-disposition") ?? "attachment",
      },
    });
  } catch {
    return new Response(`Backend unreachable at ${API_URL}.`, { status: 502 });
  }
}
