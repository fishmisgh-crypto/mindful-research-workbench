/** Typed client for the local FastAPI backend. Server-side only. */

const API_URL = process.env.MINDFUL_API_URL ?? "http://127.0.0.1:8000";

export interface DatasetStatus {
  state: "missing" | "present";
  configured_path: string;
  participant_folders: string[];
  message: string;
}

export interface HealthResponse {
  status: "ok";
  service: string;
  versions: { python: string; numpy: string; scipy: string; fastapi: string };
  dataset: DatasetStatus;
  upstream_reference_present: boolean;
  last_analysis_run: string | null;
}

export type ApiResult<T> = { ok: true; data: T } | { ok: false; error: string };

export async function getHealth(): Promise<ApiResult<HealthResponse>> {
  try {
    const response = await fetch(`${API_URL}/api/health`, { cache: "no-store" });
    if (!response.ok) {
      return { ok: false, error: `Backend responded with HTTP ${response.status}` };
    }
    return { ok: true, data: (await response.json()) as HealthResponse };
  } catch {
    return { ok: false, error: `Backend unreachable at ${API_URL}` };
  }
}
