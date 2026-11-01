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

export type CheckStatus = "pass" | "info" | "warn" | "fail";

export interface Check {
  id: string;
  status: CheckStatus;
  message: string;
}

export interface BlockSummary {
  number: number;
  name: string;
  status: CheckStatus;
  checks: Check[];
  task_name: string | null;
  n_bins: number | null;
  duration_s: number | null;
  n_trials: number | null;
  n_excluded_trials: number | null;
  kept_trial_bins: number | null;
  feature_count: number | null;
  has_spike_power: boolean | null;
  percent_correct: number | null;
  ae_median_kept_deg: number | null;
  ae_nan_fraction: number | null;
  nctx_mean_rate: number | null;
  outlier_bin_fraction: number | null;
}

export interface SessionSummary {
  day: number;
  index: number;
  name: string;
  n_blocks: number;
  block_mtime_order_matches_numeric: boolean;
  status: CheckStatus;
  blocks: BlockSummary[];
}

export interface ParticipantSummary {
  id: string;
  n_sessions: number;
  n_blocks: number;
  n_trials: number;
  n_excluded_trials: number;
  n_bins: number;
  kept_trial_bins: number;
  duration_min: number;
  feature_counts: number[];
  task_names: string[];
  session_order: { chronological: string[]; matlab_dir: string[]; matches: boolean };
  status: CheckStatus;
  checks: Check[];
  sessions: SessionSummary[];
}

export interface DatasetSummary {
  schema_version: number;
  built_at: string;
  root: string;
  content_digest_sha256: string;
  n_mat_files: number;
  mat_bytes: number;
  documented: Record<string, Record<string, number>>;
  participants: ParticipantSummary[];
  out_of_scope_blocks: string[];
}

export interface TrialRow {
  trial: number;
  start: number;
  stop: number;
  n_bins: number;
  excluded: boolean;
  ae_median_deg: number | null;
  ae_nan_bins: number;
  success: boolean | null;
  time_to_target_s: number | null;
  path_efficiency: number | null;
  ae_per_trial_deg: number | null;
}

export interface BlockDetail {
  participant: string;
  session: string;
  summary: BlockSummary;
  trials: TrialRow[];
  channel_means: Record<string, number[]>;
  missing_data: {
    ae_nan_bins: number;
    outlier_bins: number | null;
    channels_with_outliers: number | null;
    per_trial_length_mismatch: Record<string, number>;
  };
  ae_histogram: { edges_deg: number[]; counts: number[] };
  source_dtypes: Record<string, string>;
}

export type ApiResult<T> =
  | { ok: true; data: T }
  | { ok: false; error: string; status?: number };

async function getJson<T>(path: string): Promise<ApiResult<T>> {
  try {
    const response = await fetch(`${API_URL}${path}`, { cache: "no-store" });
    if (!response.ok) {
      let detail = "";
      try {
        detail = ((await response.json()) as { detail?: string }).detail ?? "";
      } catch {}
      return {
        ok: false,
        status: response.status,
        error: detail || `Backend responded with HTTP ${response.status}`,
      };
    }
    return { ok: true, data: (await response.json()) as T };
  } catch {
    return { ok: false, error: `Backend unreachable at ${API_URL}` };
  }
}

export const getHealth = () => getJson<HealthResponse>("/api/health");

export const getDatasetSummary = () => getJson<DatasetSummary>("/api/dataset/summary");

export const getBlockDetail = (participant: string, session: string, block: string) =>
  getJson<BlockDetail>(
    `/api/dataset/${encodeURIComponent(participant)}/${encodeURIComponent(session)}/${encodeURIComponent(block)}`,
  );
