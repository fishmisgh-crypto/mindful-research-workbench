import type { Metadata } from "next";
import Link from "next/link";

import { CheckList } from "@/components/CheckList";
import { EmptyState } from "@/components/EmptyState";
import { KeyValueTable } from "@/components/KeyValueTable";
import { PageHeader } from "@/components/PageHeader";
import { Section } from "@/components/Section";
import { CheckMark } from "@/components/StatusMark";
import { PreprocessTable } from "@/components/PreprocessTable";
import {
  getDatasetSummary,
  getPreprocess,
  type ApiResult,
  type ParticipantSummary,
  type PreprocessDiagnostics,
} from "@/lib/api";
import { bytes, deg, fixed, int, pct } from "@/lib/format";

export const metadata: Metadata = { title: "Data Explorer" };
export const dynamic = "force-dynamic";

const TH = "py-2 pr-4 font-normal whitespace-nowrap";
const TD = "py-2 pr-4 whitespace-nowrap";
const NUM = `${TD} text-right font-mono`;

function BlockTable({ participant }: { participant: ParticipantSummary }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[56rem] text-left text-sm">
        <thead className="text-ink-3 border-rule-strong border-b">
          <tr>
            <th className={TH}>Session</th>
            <th className={TH}>Block</th>
            <th className={`${TH} text-right`}>Duration (s)</th>
            <th className={`${TH} text-right`}>Trials</th>
            <th className={`${TH} text-right`}>Excl.</th>
            <th className={`${TH} text-right`}>Kept bins</th>
            <th className={`${TH} text-right`}>Features</th>
            <th className={`${TH} text-right`}>Correct</th>
            <th className={`${TH} text-right`}>Median AE</th>
            <th className={`${TH} text-right`}>AE missing</th>
            <th className={TH}>Status</th>
          </tr>
        </thead>
        <tbody>
          {participant.sessions.flatMap((session) =>
            session.blocks.map((block, i) => (
              <tr key={`${session.name}-${block.name}`} className="border-rule border-b">
                <td className={`${TD} font-mono`}>
                  {i === 0 ? (
                    <>
                      {session.name}
                      <span className="text-ink-3"> · S{session.index}</span>
                    </>
                  ) : null}
                </td>
                <td className={`${TD} font-mono`}>
                  <Link
                    href={`/data/${participant.id}/${session.name}/${block.name}`}
                    className="decoration-rule-strong hover:decoration-ink underline underline-offset-4"
                  >
                    {block.name}
                  </Link>
                </td>
                <td className={NUM}>{fixed(block.duration_s, 1)}</td>
                <td className={NUM}>{int(block.n_trials)}</td>
                <td className={NUM}>{int(block.n_excluded_trials)}</td>
                <td className={NUM}>{int(block.kept_trial_bins)}</td>
                <td className={NUM}>{int(block.feature_count)}</td>
                <td className={NUM}>{block.percent_correct == null ? "—" : `${fixed(block.percent_correct, 1)}%`}</td>
                <td className={NUM}>{deg(block.ae_median_kept_deg)}</td>
                <td className={NUM}>{pct(block.ae_nan_fraction)}</td>
                <td className={`${TD} font-mono text-[12px]`}>
                  <CheckMark status={block.status} />
                </td>
              </tr>
            )),
          )}
        </tbody>
      </table>
    </div>
  );
}

function ParticipantSection({
  participant,
  preprocess,
}: {
  participant: ParticipantSummary;
  preprocess: [ApiResult<PreprocessDiagnostics>, ApiResult<PreprocessDiagnostics>];
}) {
  return (
    <Section
      title={`Participant ${participant.id}`}
      note={`${participant.task_names.join(", ")} · ${participant.feature_counts.join("/")} features`}
    >
      <KeyValueTable
        rows={[
          {
            label: "Recorded",
            value: `${participant.n_sessions} sessions · ${participant.n_blocks} blocks · ${fixed(participant.duration_min, 1)} min`,
            mono: true,
          },
          {
            label: "Trials",
            value: `${int(participant.n_trials)} (${int(participant.n_excluded_trials)} excluded) · ${int(participant.kept_trial_bins)} kept-trial bins`,
            mono: true,
          },
          {
            label: "Session order",
            value: participant.session_order.chronological.join(" → "),
            mono: true,
          },
        ]}
      />
      <h3 className="text-ink-3 mt-8 mb-2 font-mono text-[11px] tracking-wide uppercase">
        Checks against documentation
      </h3>
      <CheckList checks={participant.checks} />
      <h3 className="text-ink-3 mt-8 mb-2 font-mono text-[11px] tracking-wide uppercase">
        Blocks · median AE over kept-trial bins
      </h3>
      <BlockTable participant={participant} />
      <h3 className="text-ink-3 mt-8 mb-2 font-mono text-[11px] tracking-wide uppercase">
        Preprocessing · computed, both presets
      </h3>
      <p className="text-ink-2 mb-4 max-w-[68ch] text-sm leading-relaxed">
        Rolling z-score per block, kept-trial bins, windows over the joined bins, reference bins
        with angular error below 4°, and PCA fitted on those reference bins only. The presets
        differ only in window step here (D2), which changes the reference windows slightly.
      </p>
      <PreprocessTable upstream={preprocess[0]} paper={preprocess[1]} />
    </Section>
  );
}

export default async function DataExplorerPage() {
  const summary = await getDatasetSummary();
  const preprocess = summary.ok
    ? await Promise.all(
        summary.data.participants.map((p) =>
          Promise.all([getPreprocess(p.id, "upstream"), getPreprocess(p.id, "paper")]),
        ),
      )
    : [];

  return (
    <>
      <PageHeader index="02" title="Data Explorer">
        Every session and block in the Dryad release, loaded from the original MATLAB files and
        checked against the paper and dataset README. Only aggregates and metadata reach the
        browser. Raw neural matrices stay on disk.
      </PageHeader>

      {!summary.ok ? (
        <Section title="Sessions">
          <EmptyState
            title={summary.status === 404 ? "Study data not found" : "Inventory unavailable"}
            phase="Phase 2 · Dataset ingestion"
          >
            {summary.error}
          </EmptyState>
        </Section>
      ) : (
        <>
          <Section title="Release" note="Dryad doi:10.5061/dryad.n2z34tn5s">
            <KeyValueTable
              rows={[
                { label: "Location", value: summary.data.root, mono: true },
                {
                  label: "Files",
                  value: `${summary.data.n_mat_files} .mat files · ${bytes(summary.data.mat_bytes)}`,
                  mono: true,
                },
                {
                  label: "Content digest",
                  value: `sha256 ${summary.data.content_digest_sha256}`,
                  mono: true,
                },
                { label: "Inventory built", value: summary.data.built_at, mono: true },
                {
                  label: "Not analysed",
                  value: `${summary.data.out_of_scope_blocks.length} blocks in T11(additional) (personal use, random targets; Fig. 6 only)`,
                },
              ]}
            />
          </Section>
          {summary.data.participants.map((p, i) => (
            <ParticipantSection key={p.id} participant={p} preprocess={preprocess[i]} />
          ))}
        </>
      )}
    </>
  );
}
