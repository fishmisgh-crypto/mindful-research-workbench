import type { Metadata } from "next";

import { KeyValueTable } from "@/components/KeyValueTable";
import { PageHeader } from "@/components/PageHeader";
import { Section } from "@/components/Section";
import { getReport, type ReproductionReport } from "@/lib/api";
import { DISCREPANCIES, type Discrepancy } from "@/lib/discrepancies";
import { STUDY } from "@/lib/study";

export const metadata: Metadata = { title: "Methods & Sources" };
export const dynamic = "force-dynamic";

const FEATURE_LABEL: Record<string, string> = {
  pca5: "PCA-5",
  extended9: "9-D",
  velocity2: "velocity",
  velocity4: "velocity + lag",
};

/** Measured effect of one discrepancy, computed from the report (never written by hand). */
function measuredEffect(d: Discrepancy, report: ReproductionReport | null): string | null {
  if (!report) return null;
  if (d.aeBinned) {
    const byP = ["T11", "T5"].map((p) => {
      const rows = report.ae_binned.filter((r) => r.participant === p);
      const code = rows.find((r) => r.n_bins === 44)?.pearson_r;
      const paper = rows.find((r) => r.n_bins === 45)?.pearson_r;
      return code != null && paper != null ? `${p}: r = ${code.toFixed(3)} (44 bins) vs ${paper.toFixed(3)} (45 bins)` : null;
    });
    return byP.filter(Boolean).join("; ") + ".";
  }
  if (!d.ablation) return null;
  const upstream = new Map(
    report.rows.filter((r) => r.preset === "upstream").map((r) => [`${r.participant}-${r.feature_set}`, r]),
  );
  const changes = report.rows
    .filter((r) => r.id.endsWith(`-${d.ablation}`))
    .map((r) => {
      const base = upstream.get(`${r.participant}-${r.feature_set}`);
      return base?.pearson_r != null && r.pearson_r != null
        ? { label: `${r.participant} ${FEATURE_LABEL[r.feature_set]}`, delta: r.pearson_r - base.pearson_r, vsPub: r.delta_r }
        : null;
    })
    .filter((c): c is { label: string; delta: number; vsPub: number | null } => c !== null);
  if (changes.length === 0) return null;
  const largest = changes.reduce((a, b) => (Math.abs(b.delta) > Math.abs(a.delta) ? b : a));
  const parts = [
    `Changing only this setting moves Pearson r by at most ${Math.abs(largest.delta).toFixed(3)} (${largest.label}), across ${changes.length} runs.`,
  ];
  if (d.ablation === "excluded_trials") {
    const worst = Math.max(...changes.map((c) => Math.abs(c.vsPub ?? NaN)));
    if (Number.isFinite(worst)) {
      parts.push(
        `With the flagged trials kept, every T11 run is within ${worst.toFixed(3)} of the published r; see the Reproduction Report.`,
      );
    }
  }
  return parts.join(" ");
}

function DiscrepancyRow({ d, effect }: { d: Discrepancy; effect: string | null }) {
  return (
    <details className="group border-rule border-b">
      <summary className="hover:bg-paper-raised grid cursor-pointer list-none grid-cols-[3rem_1fr] gap-x-4 gap-y-1 py-3 sm:grid-cols-[3rem_1fr_13rem] [&::-webkit-details-marker]:hidden">
        <span className="font-mono text-sm">{d.id}</span>
        <span className="text-sm font-medium">
          {d.topic}
          <span aria-hidden className="text-ink-3 ml-2 inline-block transition-transform group-open:rotate-90">
            ›
          </span>
        </span>
        <span className="text-ink-3 col-start-2 text-[13px] sm:col-start-auto sm:text-right">{d.status}</span>
      </summary>
      <dl className="grid gap-x-6 gap-y-3 pb-5 text-sm sm:grid-cols-[9rem_1fr] sm:pl-16">
        <dt className="text-ink-3">Paper</dt>
        <dd>{d.paper}</dd>
        <dt className="text-ink-3">Released code</dt>
        <dd>{d.code}</dd>
        <dt className="text-ink-3">What we did</dt>
        <dd>{d.handling}</dd>
        {effect ? (
          <>
            <dt className="text-ink-3">Measured effect</dt>
            <dd className="font-mono text-[13px] leading-relaxed">{effect}</dd>
          </>
        ) : null}
      </dl>
    </details>
  );
}

export default async function MethodsPage() {
  const report = await getReport();
  const data = report.ok ? report.data : null;

  return (
    <>
      <PageHeader title="Methods & Sources">
        The method as implemented, where it comes from, and every place the paper and the released
        code disagree. The full specification is in{" "}
        <code className="font-mono text-[0.9em]">docs/RESEARCH_SPEC.md</code>.
      </PageHeader>

      <Section title="Method summary" note="Fixed parameters">
        <KeyValueTable
          rows={[
            { label: "Bin width", value: "20 ms", mono: true },
            { label: "Window", value: "3000 bins (60 s)", mono: true },
            { label: "Step", value: "50 bins (1 s, paper) or 500 bins (10 s, upstream script)", mono: true },
            { label: "Divergence", value: "D_KL(P_reference ‖ P_current), Gaussian closed form", mono: true },
            { label: "Reference", value: "T11: session 1; T5: sessions 1–2; bins with angular error < 4°" },
            { label: "Dimensionality reduction", value: "PCA fitted on reference bins only" },
            {
              label: "Numerics",
              value: "Cholesky solves and log-determinants; no matrix inverse; no regularisation",
            },
          ]}
        />
      </Section>

      <Section title="Paper–code discrepancies" note={`${DISCREPANCIES.length} recorded · open a row for details`}>
        <p className="text-ink-2 mb-4 max-w-[68ch] text-sm leading-relaxed">
          None is resolved silently: each one is either a configuration setting with its effect
          measured, or checked against the data and shown to make no difference here.
        </p>
        <div className="border-rule-strong border-t">
          {DISCREPANCIES.map((d) => (
            <DiscrepancyRow key={d.id} d={d} effect={measuredEffect(d, data)} />
          ))}
        </div>
      </Section>

      <Section title="Sources">
        <KeyValueTable
          rows={[
            { label: "Paper", value: `${STUDY.journal}, doi:${STUDY.doi}` },
            { label: "Reference code", value: `${STUDY.codeUrl} @ ${STUDY.codeCommit}`, mono: true },
            { label: "Dataset", value: `Dryad, doi:${STUDY.datasetDoi}`, mono: true },
          ]}
        />
      </Section>
    </>
  );
}
