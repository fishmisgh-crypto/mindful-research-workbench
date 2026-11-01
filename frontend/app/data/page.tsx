import type { Metadata } from "next";

import { EmptyState } from "@/components/EmptyState";
import { PageHeader } from "@/components/PageHeader";
import { Section } from "@/components/Section";

export const metadata: Metadata = { title: "Data Explorer" };

export default function DataExplorerPage() {
  return (
    <>
      <PageHeader index="02" title="Data Explorer">
        Session inventory, per-session validation and feature summaries for T11 and T5. Only
        aggregates and metadata reach the browser. Raw neural matrices stay on disk.
      </PageHeader>
      <Section title="Sessions">
        <EmptyState title="No sessions loaded" phase="Phase 2 · Dataset ingestion">
          Session discovery and MATLAB file parsing are built in Phase 2. That needs the Dryad
          dataset (doi:10.5061/dryad.n2z34tn5s) extracted to{" "}
          <code className="font-mono">data/raw/MINDFUL_Data</code>.
        </EmptyState>
      </Section>
    </>
  );
}
