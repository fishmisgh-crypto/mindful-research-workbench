import type { ReactNode } from "react";

export interface KeyValueRow {
  label: string;
  value: ReactNode;
  mono?: boolean;
}

/** Two-column definition table with hairline row rules. */
export function KeyValueTable({ rows }: { rows: readonly KeyValueRow[] }) {
  return (
    <dl className="border-rule border-t text-sm">
      {rows.map((row) => (
        <div
          key={row.label}
          className="border-rule grid grid-cols-1 gap-1 border-b py-2.5 sm:grid-cols-[14rem_1fr] sm:gap-6"
        >
          <dt className="text-ink-3">{row.label}</dt>
          <dd className={`min-w-0 break-words ${row.mono ? "font-mono text-[13px]" : ""}`}>
            {row.value}
          </dd>
        </div>
      ))}
    </dl>
  );
}
