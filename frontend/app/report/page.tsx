import type { Metadata } from "next";

import { EmptyState } from "@/components/EmptyState";
import { KeyValueTable } from "@/components/KeyValueTable";
import { PageHeader } from "@/components/PageHeader";
import { ScatterChart } from "@/components/ScatterChart";
import { Section } from "@/components/Section";
import { StatusMark } from "@/components/StatusMark";
import { getReport, type ReportRow, type ReproductionReport } from "@/lib/api";
import { int } from "@/lib/format";

export const metadata: Metadata = { title: "Reproduction Report" };
export const dynamic = "force-dynamic";

const FEATURE_LABEL: Record<string, string> = {
  pca5: "PCA-5",
  extended9: "9-D",
  velocity2: "Velocity",
  velocity4: "Velocity + lag",
};

const TH = "py-2 pr-4 font-normal whitespace-nowrap";
const NUM = "py-2 pr-4 text-right font-mono whitespace-nowrap";

function r3(v: number | null | undefined): string {
  return v == null ? "—" : v.toFixed(3);
}

function signed(v: number | null | undefined): string {
  return v == null ? "—" : `${v >= 0 ? "+" : "−"}${Math.abs(v).toFixed(3)}`;
}

function pValue(p: number | null): string {
  if (p == null) return "—";
  if (p === 0) return "< 1e-300";
  return p < 0.001 ? p.toExponential(0) : p.toFixed(3);
}

function Verdict({ v }: { v: ReportRow["verdict"] }) {
  if (v === "no published value")
    return <span className="text-ink-3">no target</span>;
  return v === "within tolerance" ? (
    <StatusMark tone="ok">within</StatusMark>
  ) : (
    <StatusMark tone="warn">differs</StatusMark>
  );
}

function ComparisonTable({
  rows,
  showPreset,
}: {
  rows: ReportRow[];
  showPreset: boolean;
}) {
  const pMax = Math.max(
    ...rows.flatMap((r) => [r.pearson_p ?? NaN, r.spearman_p ?? NaN]),
  );
  return (
    <>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[50rem] text-left text-sm">
          <thead className="text-ink-3 border-rule-strong border-b">
            <tr>
              <th className={TH}>Participant</th>
              <th className={TH}>Features</th>
              {showPreset ? <th className={TH}>Preset</th> : null}
              <th className={`${TH} text-right`}>Windows</th>
              <th className={`${TH} text-right`}>r</th>
              <th className={`${TH} text-right`}>published</th>
              <th className={`${TH} text-right`}>Δr</th>
              <th className={`${TH} text-right`}>ρ</th>
              <th className={`${TH} text-right`}>published</th>
              <th className={`${TH} text-right`}>Δρ</th>
              <th className={TH}>±0.02</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id} className="border-rule border-b">
                <td className="py-2 pr-4 font-mono">{r.participant}</td>
                <td className="py-2 pr-4 whitespace-nowrap">
                  {FEATURE_LABEL[r.feature_set]}
                  {r.published ? (
                    <span className="text-ink-3"> · {r.published.figure}</span>
                  ) : null}
                </td>
                {showPreset ? (
                  <td className="py-2 pr-4 font-mono text-[13px]">
                    {r.preset}
                  </td>
                ) : null}
                <td className={NUM}>{int(r.n_used)}</td>
                <td className={`${NUM} text-ink font-medium`}>
                  {r3(r.pearson_r)}
                </td>
                <td className={`${NUM} text-ink-3`}>
                  {r3(r.published?.pearson)}
                </td>
                <td className={NUM}>{signed(r.delta_r)}</td>
                <td className={`${NUM} text-ink font-medium`}>
                  {r3(r.spearman_rho)}
                </td>
                <td className={`${NUM} text-ink-3`}>
                  {r3(r.published?.spearman)}
                </td>
                <td className={NUM}>{signed(r.delta_rho)}</td>
                <td className="py-2 font-mono text-[12px] whitespace-nowrap">
                  <Verdict v={r.verdict} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-ink-3 mt-3 font-mono text-[11px]">
        Largest p-value in this table (Pearson or Spearman):{" "}
        {pValue(Number.isFinite(pMax) ? pMax : null)}
      </p>
    </>
  );
}

function AblationTable({ report }: { report: ReproductionReport }) {
  const base = new Map(
    report.rows
      .filter((r) => r.preset === "upstream")
      .map((r) => [`${r.participant}-${r.feature_set}`, r]),
  );
  const rows = report.rows.filter((r) => r.group === "ablation");
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[54rem] text-left text-sm">
        <thead className="text-ink-3 border-rule-strong border-b">
          <tr>
            <th className={TH}>Participant</th>
            <th className={TH}>Features</th>
            <th className={TH}>Change from upstream</th>
            <th className={`${TH} text-right`}>r</th>
            <th className={`${TH} text-right`}>vs upstream</th>
            <th className={`${TH} text-right`}>vs published</th>
            <th className={`${TH} text-right`}>ρ</th>
            <th className={`${TH} text-right`}>vs upstream</th>
            <th className={`${TH} text-right`}>vs published</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => {
            const b = base.get(`${r.participant}-${r.feature_set}`);
            const dr =
              r.pearson_r != null && b?.pearson_r != null
                ? r.pearson_r - b.pearson_r
                : null;
            const drho =
              r.spearman_rho != null && b?.spearman_rho != null
                ? r.spearman_rho - b.spearman_rho
                : null;
            return (
              <tr key={r.id} className="border-rule border-b">
                <td className="py-2 pr-4 font-mono">{r.participant}</td>
                <td className="py-2 pr-4 whitespace-nowrap">
                  {FEATURE_LABEL[r.feature_set]}
                </td>
                <td className="max-w-[16rem] py-2 pr-4 text-[13px]">
                  {r.varies}
                </td>
                <td className={`${NUM} text-ink font-medium`}>
                  {r3(r.pearson_r)}
                </td>
                <td className={NUM}>{signed(dr)}</td>
                <td className={`${NUM} text-ink-3`}>{signed(r.delta_r)}</td>
                <td className={`${NUM} text-ink font-medium`}>
                  {r3(r.spearman_rho)}
                </td>
                <td className={NUM}>{signed(drho)}</td>
                <td className={`${NUM} text-ink-3`}>{signed(r.delta_rho)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export default async function ReproductionReportPage() {
  const result = await getReport();
  if (!result.ok) {
    return (
      <>
        <PageHeader index="04" title="Reproduction Report" />
        <Section title="Published vs reproduced">
          <EmptyState
            title="Report unavailable"
            phase="Phase 5 · Reproduce the research results"
          >
            {result.error}
          </EmptyState>
        </Section>
      </>
    );
  }
  const report = result.data;
  const primary = report.rows.filter((r) => r.group === "primary");
  const upstreamPrimary = primary.filter((r) => r.preset === "upstream");
  const secondary = report.rows.filter((r) => r.group === "secondary");
  const fig1b = report.ae_binned.filter((r) => r.n_bins === 44);
  const tol = report.match_tolerance;
  const matched = upstreamPrimary.filter(
    (r) => r.verdict === "within tolerance",
  ).length;
  const maxAbsDelta = (rows: ReportRow[]) =>
    Math.max(
      ...rows
        .flatMap((r) => [r.delta_r, r.delta_rho])
        .map((d) => Math.abs(d ?? NaN)),
    );
  const t11Kept = report.rows.filter(
    (r) => r.participant === "T11" && r.id.endsWith("excluded_trials"),
  );
  const t11Upstream = report.rows.filter(
    (r) => r.participant === "T11" && r.preset === "upstream",
  );
  const keptGap = t11Kept.length ? maxAbsDelta(t11Kept) : NaN;
  const upstreamGap = t11Upstream.length ? maxAbsDelta(t11Upstream) : NaN;

  return (
    <>
      <PageHeader index="04" title="Reproduction Report">
        Correlation between window KLD and median angular error, reproduced from
        the released data and compared with the published values. Every run in
        the matrix is shown as computed. A correlation describes how closely KLD
        tracks decoder error; it is not an accuracy.
      </PageHeader>

      <Section title="In short" note={`tolerance ±${tol} on both r and ρ`}>
        <div className="text-ink-2 max-w-[72ch] space-y-3 text-[15px] leading-relaxed">
          <p>
            With the released analysis code&apos;s settings (
            <span className="font-mono">upstream</span> preset), {matched} of{" "}
            {upstreamPrimary.length} primary results fall within ±{tol} of the
            published Pearson r and Spearman ρ. Fig. 1b (KLD of bins grouped by
            angular error) reproduces to three decimals.
          </p>
          {Number.isFinite(keptGap) ? (
            <p>
              For T11, keeping the outlier trials that the released script
              removes puts all {t11Kept.length} feature sets within{" "}
              {keptGap.toFixed(3)} of the published r and ρ; with them removed
              (upstream) the largest difference is {upstreamGap.toFixed(3)}.
              {keptGap < upstreamGap
                ? " This suggests the published T11 figures were computed with those trials included (discrepancy D3). It is evidence, not proof, and the presets are left as specified."
                : null}
            </p>
          ) : null}
        </div>
      </Section>

      <Section title="Primary results" note="Fig. 1c (PCA-5) and Fig. 2c (9-D)">
        <ComparisonTable rows={primary} showPreset />
      </Section>

      <Section
        title="Single-parameter changes"
        note="each row changes one setting from upstream"
      >
        <AblationTable report={report} />
        <p className="text-ink-3 mt-3 max-w-[72ch] text-[13px] leading-relaxed">
          T5 has no outlier trials, so that change is not run for T5. The{" "}
          <span className="font-mono">paper</span> preset combines the
          covariance and step changes.
        </p>
      </Section>

      <Section
        title="Velocity-only feature sets"
        note="Fig. 2a and 2b, upstream preset"
      >
        <ComparisonTable rows={secondary} showPreset={false} />
      </Section>

      <Section
        title="KLD grouped by angular error"
        note="Fig. 1b · Pearson r across bins"
      >
        <div className="grid gap-8 lg:grid-cols-2">
          {fig1b.map((row) => (
            <ScatterChart
              key={row.id}
              title={`${row.participant}: KLD of each 4° angular-error bin`}
              context={`${row.participant} · upstream estimator · reference: all kept-trial bins with AE < 4° (n = ${int(row.n_reference_bins)}) · ${row.n_bins} bins (code loop) · r = ${r3(row.pearson_r)}, published ${r3(row.published?.pearson)}`}
              points={row.bins.mean_ae.map((x, i) => ({
                x,
                y: row.bins.kld[i],
              }))}
              xMax={180}
              xLabel="Mean angular error of bin (degrees)"
              yLabel="KLD (nats)"
            />
          ))}
        </div>
        <div className="mt-6">
          <KeyValueTable
            rows={report.ae_binned.map((r) => ({
              label: `${r.participant} · ${r.variant}`,
              value: `r = ${r3(r.pearson_r)} (published ${r3(r.published?.pearson)}, Δ ${signed(r.delta_r)})`,
              mono: true,
            }))}
          />
        </div>
      </Section>

      <Section title="Method and provenance">
        <KeyValueTable
          rows={[
            { label: "Correlation", value: report.correlation_method },
            {
              label: "Published values",
              value: `${report.source} · comparison only, never used in a calculation`,
              mono: true,
            },
            {
              label: "Reference code",
              value: `ewinapun/MINDFUL @ ${report.upstream_commit.slice(0, 7)}`,
              mono: true,
            },
            {
              label: "Run matrix",
              value: `${report.rows.length} runs + ${report.ae_binned.length} Fig. 1b variants · digest ${report.specs_digest}`,
              mono: true,
            },
            { label: "Generated", value: report.generated_at, mono: true },
          ]}
        />
      </Section>
    </>
  );
}
