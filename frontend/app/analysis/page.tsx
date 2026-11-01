import type { Metadata } from "next";
import Link from "next/link";

import { DriftChart } from "@/components/DriftChart";
import { EmptyState } from "@/components/EmptyState";
import { KeyValueTable } from "@/components/KeyValueTable";
import { PageHeader } from "@/components/PageHeader";
import { Section } from "@/components/Section";
import { getAnalysis, type FeatureSet, type Preset } from "@/lib/api";
import { fixed, int } from "@/lib/format";

export const metadata: Metadata = { title: "Drift Analysis" };
export const dynamic = "force-dynamic";

const PARTICIPANTS = ["T11", "T5"] as const;
const PRESETS: Preset[] = ["upstream", "paper"];
const FEATURE_SETS: { id: FeatureSet; label: string }[] = [
  { id: "pca5", label: "PCA-5" },
  { id: "extended9", label: "9-D (PCs + velocity + lag)" },
  { id: "velocity2", label: "Velocity" },
  { id: "velocity4", label: "Velocity + lag" },
];

type Search = { participant?: string; preset?: string; features?: string };

function pick<T extends string>(value: string | undefined, allowed: readonly T[], fallback: T): T {
  return allowed.includes(value as T) ? (value as T) : fallback;
}

function Choice({
  label,
  options,
  current,
  href,
}: {
  label: string;
  options: readonly { id: string; label: string }[];
  current: string;
  href: (id: string) => string;
}) {
  return (
    <div className="flex flex-wrap items-baseline gap-x-4 gap-y-1 text-sm">
      <span className="text-ink-3 w-24 font-mono text-[11px] tracking-wide uppercase">{label}</span>
      {options.map((o) => (
        <Link
          key={o.id}
          href={href(o.id)}
          aria-current={o.id === current ? "true" : undefined}
          className={
            o.id === current
              ? "text-ink decoration-accent font-medium underline decoration-2 underline-offset-4"
              : "text-ink-2 hover:text-ink"
          }
        >
          {o.label}
        </Link>
      ))}
    </div>
  );
}

export default async function DriftAnalysisPage({ searchParams }: { searchParams: Promise<Search> }) {
  const sp = await searchParams;
  const participant = pick(sp.participant, PARTICIPANTS, "T11");
  const preset = pick(sp.preset, PRESETS, "upstream");
  const features = pick(
    sp.features,
    FEATURE_SETS.map((f) => f.id),
    "pca5",
  );
  const href = (p: Partial<Search>) => {
    const q = new URLSearchParams({ participant, preset, features, ...p } as Record<string, string>);
    return `/analysis?${q.toString()}`;
  };
  const result = await getAnalysis(participant, preset, features);

  return (
    <>
      <PageHeader index="03" title="Drift Analysis">
        Window-level KLD, D<sub>KL</sub>(P<sub>reference</sub> ‖ P<sub>current</sub>), and median
        angular error over time. They are drawn as two stacked panels on one time axis, with
        session boundaries marked and excluded windows left as gaps.
      </PageHeader>

      <Section title="Selection">
        <div className="space-y-2">
          <Choice
            label="Participant"
            options={PARTICIPANTS.map((p) => ({ id: p, label: p }))}
            current={participant}
            href={(id) => href({ participant: id })}
          />
          <Choice
            label="Preset"
            options={PRESETS.map((p) => ({ id: p, label: p }))}
            current={preset}
            href={(id) => href({ preset: id })}
          />
          <Choice
            label="Features"
            options={FEATURE_SETS}
            current={features}
            href={(id) => href({ features: id })}
          />
        </div>
      </Section>

      {!result.ok || !result.data.windows ? (
        <Section title="KLD and angular error">
          <EmptyState title="No analysis available" phase="Phase 4 · KLD & MINDFUL engine">
            {result.ok ? "The window table is missing." : result.error}
          </EmptyState>
        </Section>
      ) : (
        (() => {
          const d = result.data;
          const w = d.windows!;
          const s = d.summaries[features];
          const dayOfSession = Object.fromEntries(s.per_session.map((p) => [p.session_index, p.day]));
          const stepS = d.step_bins * d.bin_seconds;
          const days = d.session_days;
          const context =
            `${d.participant} · ${d.preset} preset (${d.config.covariance_estimator.replaceAll("_", " ")}, ` +
            `60-s windows every ${stepS} s) · ${FEATURE_SETS.find((f) => f.id === features)?.label} · ` +
            `trial days ${days[0]}–${days[days.length - 1]} · ${int(s.n_valid)} of ${int(s.n_windows)} windows shown`;
          return (
            <>
              <Section title="KLD and angular error" note={`config ${d.config_digest}`}>
                <DriftChart
                  title="KLD from reference and median angular error, per window"
                  context={context}
                  kld={w.kld}
                  medianAe={w.median_ae}
                  sessionIndex={w.session_index}
                  dayOfSession={dayOfSession}
                  referenceDays={d.reference_days}
                  xLabel={`Window index (each window 60 s of kept-trial bins; sessions labelled by trial day)`}
                />
                <p className="text-ink-3 mt-3 max-w-[72ch] text-[13px] leading-relaxed">
                  KLD is a divergence in nats, not a percentage. Gaps are the last {d.window_bins / d.step_bins}{" "}
                  windows of each session, which run into the next session and are set to NaN as in
                  the original code. How KLD tracks angular error (the correlation) is computed in
                  Phase 5.
                </p>
              </Section>

              <Section title="Summary" note={d.kld_direction}>
                <KeyValueTable
                  rows={[
                    { label: "Feature set", value: `${s.description} · ${s.dim} dimensions`, mono: false },
                    {
                      label: "Reference",
                      value: `trial day ${d.reference_days.join(" + ")} · ${int(s.n_reference_bins)} bins with AE < 4° · condition ${fixed(s.reference_condition, 1)}`,
                      mono: true,
                    },
                    {
                      label: "Windows",
                      value: Object.entries(s.reasons)
                        .map(([r, c]) => `${r}: ${int(c)}`)
                        .join(" · "),
                      mono: true,
                    },
                    {
                      label: "KLD min / median / max",
                      value: `${fixed(s.kld_min, 3)} / ${fixed(s.kld_median, 3)} / ${fixed(s.kld_max, 3)} nats`,
                      mono: true,
                    },
                    {
                      label: "Largest window condition",
                      value: fixed(s.window_condition_max, 1),
                      mono: true,
                    },
                  ]}
                />
              </Section>

              <Section title="By session">
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[36rem] text-left text-sm">
                    <thead className="text-ink-3 border-rule-strong border-b">
                      <tr>
                        <th className="py-2 pr-4 font-normal">Session</th>
                        <th className="py-2 pr-4 font-normal">Trial day</th>
                        <th className="py-2 pr-4 text-right font-normal">Windows (valid)</th>
                        <th className="py-2 pr-4 text-right font-normal">Median KLD</th>
                        <th className="py-2 text-right font-normal">Median of window AE</th>
                      </tr>
                    </thead>
                    <tbody>
                      {s.per_session.map((p) => (
                        <tr key={p.session_index} className="border-rule border-b">
                          <td className="py-2 pr-4 font-mono">
                            S{p.session_index}
                            {d.reference_days.includes(p.day) ? <span className="text-ink-3"> · ref</span> : null}
                          </td>
                          <td className="py-2 pr-4 font-mono">{p.day}</td>
                          <td className="py-2 pr-4 text-right font-mono">
                            {p.n_windows} ({p.n_valid})
                          </td>
                          <td className="py-2 pr-4 text-right font-mono">{fixed(p.kld_median, 3)}</td>
                          <td className="py-2 text-right font-mono">
                            {p.median_ae_median == null ? "—" : `${fixed(p.median_ae_median, 1)}°`}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Section>
            </>
          );
        })()
      )}
    </>
  );
}
