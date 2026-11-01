import type { ApiResult, PreprocessDiagnostics } from "@/lib/api";
import { fixed, int, pct } from "@/lib/format";

import { EmptyState } from "./EmptyState";

type Row = { label: string; value: (d: PreprocessDiagnostics) => string; note?: string };

const ROWS: Row[] = [
  { label: "Window / step (bins)", value: (d) => `${int(d.windows.window_bins)} / ${int(d.windows.step_bins)}` },
  { label: "Windows", value: (d) => int(d.windows.n_windows) },
  {
    label: "Cross a block end",
    value: (d) => int(d.windows.n_windows_crossing_blocks),
    note: "allowed within a session (D4)",
  },
  {
    label: "Cross a session end",
    value: (d) => int(d.windows.n_windows_crossing_sessions),
    note: "all inside the session-end NaN set",
  },
  { label: "Session-end windows set to NaN", value: (d) => int(d.windows.n_session_end_windows) },
  {
    label: "Reference sessions",
    value: (d) => d.reference.days.map((day) => `day_${day}`).join(" + "),
  },
  { label: "Reference candidate bins", value: (d) => int(d.reference.candidate_bins) },
  {
    label: "Reference bins (AE < 4°)",
    value: (d) => `${int(d.reference.bins)} (${pct(d.reference.fraction_kept)})`,
  },
  {
    label: "PCA variance, top 5",
    value: (d) => `${fixed(d.pca.cumulative_pct_at_dim, 2)}%`,
    note: "of reference-bin variance",
  },
  {
    label: "PC1–PC5 variance",
    value: (d) => d.pca.explained_pct_top10.slice(0, 5).map((v) => v.toFixed(2)).join(" · "),
  },
  {
    label: "First bin z = 0",
    value: (d) => `${d.zscore.blocks_first_bin_zero} / ${d.n_blocks} blocks`,
  },
  { label: "Std floored (< 1e-5 → 1)", value: (d) => pct(d.zscore.floored_std_fraction, 3) },
];

/** Upstream vs paper preset side by side. Values are computed, not published. */
export function PreprocessTable({
  upstream,
  paper,
}: {
  upstream: ApiResult<PreprocessDiagnostics>;
  paper: ApiResult<PreprocessDiagnostics>;
}) {
  if (!upstream.ok || !paper.ok) {
    const error = !upstream.ok ? upstream.error : !paper.ok ? paper.error : "";
    return <EmptyState title="Preprocessing unavailable">{error}</EmptyState>;
  }
  const u = upstream.data;
  const p = paper.data;
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[52rem] text-left text-sm">
        <thead className="text-ink-3 border-rule-strong border-b">
          <tr>
            <th className="py-2 pr-4 font-normal">Quantity</th>
            <th className="py-2 pr-4 text-right font-normal">
              upstream <span className="font-mono text-[11px]">{u.config_digest}</span>
            </th>
            <th className="py-2 pr-4 text-right font-normal">
              paper <span className="font-mono text-[11px]">{p.config_digest}</span>
            </th>
            <th className="py-2 font-normal">Note</th>
          </tr>
        </thead>
        <tbody>
          {ROWS.map((row) => (
            <tr key={row.label} className="border-rule border-b">
              <td className="py-2 pr-4 whitespace-nowrap">{row.label}</td>
              <td className="py-2 pr-4 text-right font-mono whitespace-nowrap">{row.value(u)}</td>
              <td className="py-2 pr-4 text-right font-mono whitespace-nowrap">{row.value(p)}</td>
              <td className="text-ink-3 min-w-[14rem] py-2 text-[13px]">{row.note ?? ""}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
