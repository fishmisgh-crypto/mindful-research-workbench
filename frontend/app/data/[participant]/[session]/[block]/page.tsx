import type { Metadata } from "next";
import Link from "next/link";

import { CheckList } from "@/components/CheckList";
import { EmptyState } from "@/components/EmptyState";
import { Histogram } from "@/components/Histogram";
import { KeyValueTable } from "@/components/KeyValueTable";
import { PageHeader } from "@/components/PageHeader";
import { Section } from "@/components/Section";
import { getBlockDetail, type BlockDetail } from "@/lib/api";
import { deg, fixed, int, median, pct } from "@/lib/format";

type Params = { participant: string; session: string; block: string };

export const dynamic = "force-dynamic";

export async function generateMetadata({ params }: { params: Promise<Params> }): Promise<Metadata> {
  const { participant, session, block } = await params;
  return { title: `${participant} ${session} ${block}` };
}

const TH = "py-2 pr-4 font-normal whitespace-nowrap";
const NUM = "py-1.5 pr-4 text-right font-mono whitespace-nowrap";

function TrialTable({ detail }: { detail: BlockDetail }) {
  return (
    <div className="max-h-[32rem] overflow-auto">
      <table className="w-full min-w-[44rem] text-left text-sm">
        <thead className="bg-paper text-ink-3 border-rule-strong sticky top-0 border-b">
          <tr>
            <th className={`${TH} text-right`}>Trial</th>
            <th className={`${TH} text-right`}>Start bin</th>
            <th className={`${TH} text-right`}>Stop bin</th>
            <th className={`${TH} text-right`}>Bins</th>
            <th className={`${TH} text-right`}>Median AE</th>
            <th className={`${TH} text-right`}>Time to target (s)</th>
            <th className={TH}>Success</th>
            <th className={TH}>Excluded</th>
          </tr>
        </thead>
        <tbody>
          {detail.trials.map((t) => (
            <tr key={t.trial} className={`border-rule border-b ${t.excluded ? "text-ink-3" : ""}`}>
              <td className={NUM}>{t.trial}</td>
              <td className={NUM}>{t.start}</td>
              <td className={NUM}>{t.stop}</td>
              <td className={NUM}>{t.n_bins}</td>
              <td className={NUM}>{deg(t.ae_median_deg)}</td>
              <td className={NUM}>{fixed(t.time_to_target_s, 2)}</td>
              <td className="py-1.5 pr-4">{t.success == null ? "—" : t.success ? "yes" : "no"}</td>
              <td className="py-1.5 pr-4">
                {t.excluded ? <span className="text-accent font-medium">excluded</span> : ""}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default async function BlockPage({ params }: { params: Promise<Params> }) {
  const { participant, session, block } = await params;
  const result = await getBlockDetail(participant, session, block);
  const crumb = (
    <p className="text-ink-3 mb-6 font-mono text-[11px]">
      <Link href="/data" className="hover:text-ink underline underline-offset-4">
        Data Explorer
      </Link>{" "}
      / {participant} / {session} / {block}
    </p>
  );

  if (!result.ok) {
    return (
      <>
        {crumb}
        <PageHeader index="02" title={`${participant} · ${session} · ${block}`} />
        <Section title="Block">
          <EmptyState title="Block unavailable">{result.error}</EmptyState>
        </Section>
      </>
    );
  }

  const d = result.data;
  const s = d.summary;
  const nctxMeans = d.channel_means.nctx ?? [];
  const spMeans = d.channel_means.spikePower;
  const context = `${d.participant} · ${d.session} · ${s.name} · kept-trial bins (n = ${int(s.kept_trial_bins)}) · raw provided angleError, no preprocessing`;

  return (
    <>
      {crumb}
      <PageHeader index="02" title={`${d.participant} · ${d.session} · ${s.name}`}>
        Task “{s.task_name}”, {fixed(s.duration_s, 1)} s of 20 ms bins. Trial bins use the
        file&apos;s 1-based inclusive <code className="font-mono text-[0.9em]">startStops</code>.
      </PageHeader>

      <Section title="Summary">
        <KeyValueTable
          rows={[
            { label: "Bins", value: `${int(s.n_bins)} (${fixed(s.duration_s, 1)} s)`, mono: true },
            {
              label: "Trials",
              value: `${int(s.n_trials)} · ${int(s.n_excluded_trials)} excluded · ${int(s.kept_trial_bins)} kept-trial bins`,
              mono: true,
            },
            {
              label: "Features",
              value: `${int(s.feature_count)} (${s.has_spike_power ? "nctx + spikePower" : "nctx"})`,
              mono: true,
            },
            {
              label: "Success rate",
              value: s.percent_correct == null ? "—" : `${fixed(s.percent_correct, 1)}%`,
              mono: true,
            },
            { label: "Median AE (kept trials)", value: deg(s.ae_median_kept_deg), mono: true },
            {
              label: "Channel mean nctx",
              value: `median ${fixed(median(nctxMeans), 1)} /s across ${nctxMeans.length} channels`,
              mono: true,
            },
            ...(spMeans
              ? [
                  {
                    label: "Channel mean spikePower",
                    value: `median ${fixed(median(spMeans), 1)} across ${spMeans.length} channels (units as provided)`,
                    mono: true,
                  },
                ]
              : []),
          ]}
        />
      </Section>

      <Section title="Validation">
        <CheckList checks={s.checks} />
      </Section>

      <Section title="Missing data">
        <KeyValueTable
          rows={[
            {
              label: "angleError NaN bins",
              value: `${int(d.missing_data.ae_nan_bins)} (${pct(s.ae_nan_fraction)})`,
              mono: true,
            },
            {
              label: "Bins with outliers",
              value:
                d.missing_data.outlier_bins == null
                  ? "not provided for this participant"
                  : `${int(d.missing_data.outlier_bins)} (avgOutliers > 0)`,
              mono: true,
            },
            {
              label: "Channels with outliers",
              value:
                d.missing_data.channels_with_outliers == null
                  ? "not provided"
                  : `${d.missing_data.channels_with_outliers} of 192 (prctOutliers non-zero anywhere in block)`,
              mono: true,
            },
            {
              label: "Per-trial field lengths",
              value:
                Object.keys(d.missing_data.per_trial_length_mismatch).length === 0
                  ? "consistent with startStops"
                  : Object.entries(d.missing_data.per_trial_length_mismatch)
                      .map(([k, n]) => `${k}: ${n}`)
                      .join(", ") + ` vs ${s.n_trials} trials (set aside)`,
              mono: true,
            },
          ]}
        />
      </Section>

      <Section title="Angular error distribution">
        <Histogram
          title="Per-bin angular error, kept trials"
          context={context}
          edges={d.ae_histogram.edges_deg}
          counts={d.ae_histogram.counts}
          xLabel="Angular error (degrees)"
          yLabel="Bins (20 ms)"
        />
      </Section>

      <Section title="Trials" note="Start/stop as in file: 1-based, inclusive">
        <TrialTable detail={d} />
      </Section>
    </>
  );
}
