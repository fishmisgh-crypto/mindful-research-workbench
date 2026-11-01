import type { ReactNode } from "react";

/** Titled content block separated by a hairline rule; no card chrome. */
export function Section({
  title,
  note,
  children,
}: {
  title: string;
  note?: string;
  children: ReactNode;
}) {
  return (
    <section className="border-rule border-b py-8 last:border-b-0">
      <div className="mb-4 flex flex-wrap items-baseline justify-between gap-x-6 gap-y-1">
        <h2 className="font-display text-xl">{title}</h2>
        {note ? <p className="text-ink-3 font-mono text-[11px]">{note}</p> : null}
      </div>
      {children}
    </section>
  );
}
