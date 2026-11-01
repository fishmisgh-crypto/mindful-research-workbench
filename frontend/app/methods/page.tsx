import type { Metadata } from "next";

import { KeyValueTable } from "@/components/KeyValueTable";
import { PageHeader } from "@/components/PageHeader";
import { Section } from "@/components/Section";
import { STUDY } from "@/lib/study";

export const metadata: Metadata = { title: "Methods & Sources" };

export default function MethodsPage() {
  return (
    <>
      <PageHeader index="05" title="Methods & Sources">
        The method as implemented, where it comes from, and where the paper and the reference
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
            { label: "Reference", value: "T11: session 1 · T5: sessions 1–2 · angular error < 4°" },
            { label: "Dimensionality reduction", value: "PCA fit on reference bins only" },
            { label: "Numerics", value: "Cholesky solves and log-determinants; no matrix inverse; no regularisation unless configured" },
          ]}
        />
      </Section>

      <Section title="Sources">
        <KeyValueTable
          rows={[
            { label: "Paper", value: `${STUDY.journal} · doi:${STUDY.doi}` },
            { label: "Reference code", value: `${STUDY.codeUrl} @ ${STUDY.codeCommit}`, mono: true },
            { label: "Dataset", value: `Dryad · doi:${STUDY.datasetDoi}`, mono: true },
          ]}
        />
      </Section>

      <Section title="Paper–code discrepancies" note="D1–D8 · each is a config parameter">
        <p className="text-ink-2 max-w-[68ch] text-sm leading-relaxed">
          Eight places where the paper and the reference code differ are recorded in{" "}
          <code className="font-mono text-[0.9em]">docs/RESEARCH_SPEC.md</code> §5. Two examples:
          the code&apos;s covariance is uncentred (D1), and the Fig. 1c script steps windows by
          10 s, not 1 s (D2). None is resolved silently. An interactive table of all eight is
          added in Phase 6.
        </p>
      </Section>
    </>
  );
}
