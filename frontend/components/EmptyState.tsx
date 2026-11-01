import type { ReactNode } from "react";

/** Honest placeholder: states what is missing and what unblocks it. Never draws fake data. */
export function EmptyState({
  title,
  children,
  phase,
}: {
  title: string;
  children: ReactNode;
  phase?: string;
}) {
  return (
    <div className="border-rule-strong border border-dashed px-6 py-8">
      <p className="font-display text-lg">{title}</p>
      <div className="text-ink-2 mt-2 max-w-[64ch] text-sm leading-relaxed">{children}</div>
      {phase ? (
        <p className="text-ink-3 mt-4 font-mono text-[11px] tracking-wide uppercase">{phase}</p>
      ) : null}
    </div>
  );
}
