import { EmptyState } from "@/components/EmptyState";
import { KeyValueTable } from "@/components/KeyValueTable";
import { OverviewHero } from "@/components/OverviewHero";
import { Section } from "@/components/Section";
import { StatusMark } from "@/components/StatusMark";
import { getAnalysis, getHealth, getReport } from "@/lib/api";
import { PARTICIPANTS, PUBLISHED_TARGETS, STUDY } from "@/lib/study";

export const dynamic = "force-dynamic";

export default async function OverviewPage() {
  const [health, report, analysis] = await Promise.all([
    getHealth(),
    getReport(),
    getAnalysis("T11", "upstream", "pca5"),
  ]);
  const reproduced = (participant: string, configuration: string) => {
    if (!report.ok) return null;
    const fs = configuration === "PCA-5" ? "pca5" : "extended9";
    return report.data.rows.find((r) => r.id === `${participant}-${fs}-upstream`) ?? null;
  };

  return (
    <>
      <OverviewHero analysis={analysis} report={report} />

      <Section title="System status" note="GET /api/health">
        {health.ok ? (
          <KeyValueTable
            rows={[
              { label: "Backend", value: <StatusMark tone="ok">Running</StatusMark> },
              {
                label: "Dataset",
                value: (
                  <StatusMark tone={health.data.dataset.state === "present" ? "ok" : "pending"}>
                    {health.data.dataset.state === "present" ? "Folders found" : "Not found"}
                  </StatusMark>
                ),
              },
              { label: "Dataset path", value: health.data.dataset.configured_path, mono: true },
              {
                label: "Upstream reference",
                value: (
                  <StatusMark tone={health.data.upstream_reference_present ? "ok" : "fault"}>
                    {health.data.upstream_reference_present
                      ? `Present · ${STUDY.codeCommit.slice(0, 7)}`
                      : "Missing"}
                  </StatusMark>
                ),
              },
              { label: "Last analysis run", value: health.data.last_analysis_run ?? "None yet", mono: true },
              {
                label: "Runtime",
                value: `Python ${health.data.versions.python} · NumPy ${health.data.versions.numpy} · SciPy ${health.data.versions.scipy} · FastAPI ${health.data.versions.fastapi}`,
                mono: true,
              },
            ]}
          />
        ) : (
          <EmptyState title="Backend not reachable" phase="Start the API to continue">
            {health.error}. Start it from <code className="font-mono">backend/</code> with{" "}
            <code className="font-mono">uvicorn app.main:app --host 127.0.0.1 --port 8000</code>.
          </EmptyState>
        )}
        {health.ok && health.data.dataset.state === "missing" ? (
          <div className="mt-6">
            <EmptyState title="Study data not loaded" phase="Needed for Phase 2">
              {health.data.dataset.message}
            </EmptyState>
          </div>
        ) : null}
      </Section>

      <Section title="Source study" note={`doi:${STUDY.doi}`}>
        <KeyValueTable
          rows={[
            { label: "Title", value: STUDY.title },
            { label: "Authors", value: STUDY.authors },
            { label: "Journal", value: STUDY.journal },
            { label: "Reference code", value: `${STUDY.codeUrl} @ ${STUDY.codeCommit.slice(0, 7)}`, mono: true },
            { label: "Dataset", value: `doi:${STUDY.datasetDoi}`, mono: true },
          ]}
        />
      </Section>

      <Section title="Participants" note="From the paper; checked against the released files on the Data Explorer">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[40rem] text-left text-sm">
            <thead className="text-ink-3 border-rule-strong border-b">
              <tr>
                <th className="py-2 pr-6 font-normal">Participant</th>
                <th className="py-2 pr-6 font-normal">Features</th>
                <th className="py-2 pr-6 text-right font-normal">Dim.</th>
                <th className="py-2 pr-6 text-right font-normal">Sessions</th>
                <th className="py-2 pr-6 font-normal">Span</th>
                <th className="py-2 font-normal">Reference</th>
              </tr>
            </thead>
            <tbody>
              {PARTICIPANTS.map((p) => (
                <tr key={p.id} className="border-rule border-b">
                  <td className="py-2.5 pr-6 font-mono">{p.id}</td>
                  <td className="py-2.5 pr-6">{p.features}</td>
                  <td className="py-2.5 pr-6 text-right font-mono">{p.featureCount}</td>
                  <td className="py-2.5 pr-6 text-right font-mono">{p.sessions}</td>
                  <td className="py-2.5 pr-6">{p.span}</td>
                  <td className="py-2.5">{p.referenceSessions}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>

      <Section title="Validation targets" note="Published values · reproduced with the upstream preset">
        <p className="text-ink-2 mb-4 max-w-[68ch] text-sm leading-relaxed">
          Correlation between window-level KLD and median angular error, as reported in the paper,
          next to the values reproduced with the released code&apos;s settings. Published values are
          never used in any calculation. Every run and its settings are on the Reproduction Report.
        </p>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[36rem] text-left text-sm">
            <thead className="text-ink-3 border-rule-strong border-b">
              <tr>
                <th className="py-2 pr-6 font-normal">Participant</th>
                <th className="py-2 pr-6 font-normal">Configuration</th>
                <th className="py-2 pr-6 text-right font-normal">Pearson r</th>
                <th className="py-2 pr-6 text-right font-normal">Spearman ρ</th>
                <th className="py-2 pr-6 text-right font-normal">Reproduced r / ρ</th>
                <th className="py-2 font-normal">Source</th>
              </tr>
            </thead>
            <tbody>
              {PUBLISHED_TARGETS.map((t) => (
                <tr key={`${t.participant}-${t.configuration}`} className="border-rule border-b">
                  <td className="py-2.5 pr-6 font-mono">{t.participant}</td>
                  <td className="py-2.5 pr-6">{t.configuration}</td>
                  <td className="py-2.5 pr-6 text-right font-mono">{t.pearson.toFixed(3)}</td>
                  <td className="py-2.5 pr-6 text-right font-mono">{t.spearman.toFixed(3)}</td>
                  <td className="py-2.5 pr-6 text-right font-mono">
                    {(() => {
                      const r = reproduced(t.participant, t.configuration);
                      return r?.pearson_r != null && r.spearman_rho != null
                        ? `${r.pearson_r.toFixed(3)} / ${r.spearman_rho.toFixed(3)}`
                        : "—";
                    })()}
                  </td>
                  <td className="py-2.5">{t.figure}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>
    </>
  );
}
