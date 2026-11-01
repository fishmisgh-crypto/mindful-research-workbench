import type { Metadata } from "next";

import { EmptyState } from "@/components/EmptyState";
import { PageHeader } from "@/components/PageHeader";
import { Section } from "@/components/Section";

export const metadata: Metadata = { title: "Reproduction Report" };

export default function ReproductionReportPage() {
  return (
    <>
      <PageHeader index="04" title="Reproduction Report">
        Published and reproduced correlations side by side for each participant and
        configuration. Each row records the preset used and how each paper-versus-code
        discrepancy (D1–D8) was resolved.
      </PageHeader>
      <Section title="Published vs reproduced">
        <EmptyState title="Nothing reproduced yet" phase="Phase 5 · Reproduce the research results">
          The published targets are listed on the Overview page. Reproduced values fill in here
          after the primary runs finish. They are reported as computed, whether or not they
          match.
        </EmptyState>
      </Section>
    </>
  );
}
