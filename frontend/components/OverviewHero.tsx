import Link from "next/link";

import type { AnalysisResponse, ApiResult, ReproductionReport } from "@/lib/api";

import { DriftHero } from "./DriftHero";

function resultSentence(report: ApiResult<ReproductionReport>): string | null {
  if (!report.ok) return null;
  const row = (p: string) => report.data.rows.find((r) => r.id === `${p}-pca5-upstream`);
  const t11 = row("T11");
  const t5 = row("T5");
  if (t11?.pearson_r == null || t5?.pearson_r == null || !t11.published || !t5.published) return null;
  return (
    `Rebuilt in Python from the released recordings, KLD tracks the cursor's median angular error ` +
    `with Pearson r = ${t11.pearson_r.toFixed(3)} for participant T11 (published ${t11.published.pearson.toFixed(2)}) ` +
    `and ${t5.pearson_r.toFixed(3)} for T5 (published ${t5.published.pearson.toFixed(2)}).`
  );
}

/** Full-bleed Overview opening: headline, the real T11 drift trace, and two ways in. */
export function OverviewHero({
  analysis,
  report,
}: {
  analysis: ApiResult<AnalysisResponse>;
  report: ApiResult<ReproductionReport>;
}) {
  const sentence = resultSentence(report);
  const w = analysis.ok ? analysis.data.windows : null;
  const dayOfSession = analysis.ok
    ? Object.fromEntries(analysis.data.summaries.pca5.per_session.map((p) => [p.session_index, p.day]))
    : {};

  return (
    <section
      data-band
      data-surface="housing"
      aria-labelledby="hero-title"
      className="bg-housing text-bone relative overflow-hidden"
    >
      <div className="px-4 pt-14 sm:px-8 md:px-12 md:pt-24">
        <h1
          id="hero-title"
          className="font-display max-w-[14ch] text-[3.25rem] leading-[0.98] tracking-[-0.025em] sm:text-[4.5rem] md:text-[6.25rem]"
        >
          <span className="rise-in block" style={{ animationDelay: "0.1s" }}>
            The signal drifts.
          </span>
          <span className="rise-in text-bone-2 block italic" style={{ animationDelay: "0.28s" }}>
            The cursor follows.
          </span>
        </h1>
        <div className="rise-in mt-8 max-w-[58ch] space-y-4" style={{ animationDelay: "0.45s" }}>
          <p className="text-bone-2 text-base leading-relaxed md:text-lg">
            MINDFUL measures how far each minute of activity on an implanted brain–computer interface has
            moved from a reference day. This workbench reproduces it independently from the published
            data and code.
          </p>
          {sentence ? <p className="text-bone text-base leading-relaxed">{sentence}</p> : null}
        </div>
        <div className="rise-in mt-9 flex flex-wrap gap-3" style={{ animationDelay: "0.6s" }}>
          <Link
            href="/analysis"
            className="bg-bone text-housing rounded-full px-6 py-2.5 text-sm font-medium transition-transform hover:-translate-y-px"
          >
            Explore the drift
          </Link>
          <Link
            href="/report"
            className="border-seam text-bone hover:border-bone-3 rounded-full border px-6 py-2.5 text-sm font-medium"
          >
            Read the reproduction report
          </Link>
        </div>
      </div>

      <div className="mt-14 px-4 pb-12 sm:px-8 md:mt-20 md:px-12 md:pb-16">
        {w ? (
          <DriftHero
            kld={w.kld}
            medianAe={w.median_ae}
            sessionIndex={w.session_index}
            dayOfSession={dayOfSession}
            caption={
              "Participant T11, trial days " +
              `${analysis.ok ? analysis.data.session_days[0] : ""}–` +
              `${analysis.ok ? analysis.data.session_days.at(-1) : ""}, upstream preset, top five principal components. ` +
              "Pale line: KLD of each 60-second window from the first session (nats). " +
              "Red line, revealed under the pointer (always shown on touch screens): median angular error of the same window (0–180°). " +
              "Each line is scaled to its own range; gaps are session ends. Ticks mark sessions, labelled by trial day."
            }
          />
        ) : (
          <p className="text-bone-3 text-sm">
            The drift trace appears once the analysis has run on the study data.
          </p>
        )}
      </div>
    </section>
  );
}
