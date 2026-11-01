import type { Metadata } from "next";

import { EmptyState } from "@/components/EmptyState";
import { PageHeader } from "@/components/PageHeader";
import { Section } from "@/components/Section";

export const metadata: Metadata = { title: "Drift Analysis" };

export default function DriftAnalysisPage() {
  return (
    <>
      <PageHeader index="03" title="Drift Analysis">
        Window-level KLD, D<sub>KL</sub>(P<sub>reference</sub> ‖ P<sub>current</sub>), and median
        angular error over time. They are drawn as two stacked panels on one time axis, with
        session boundaries marked and rank-deficient windows left as gaps.
      </PageHeader>
      <Section title="KLD and angular error">
        <EmptyState title="No analysis runs" phase="Phase 4 · KLD & MINDFUL engine">
          Charts appear once the MINDFUL engine has run on real study data. This page never
          draws placeholder curves.
        </EmptyState>
      </Section>
    </>
  );
}
