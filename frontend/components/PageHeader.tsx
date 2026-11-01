import type { ReactNode } from "react";

/** Page title block: section index, serif title, one-paragraph standfirst. */
export function PageHeader({
  index,
  title,
  children,
}: {
  index: string;
  title: string;
  children?: ReactNode;
}) {
  return (
    <header className="border-rule-strong border-b pb-6">
      <p className="text-ink-3 font-mono text-[11px] tracking-wide uppercase">Section {index}</p>
      <h1 className="font-display mt-2 text-4xl leading-[1.1] tracking-[-0.01em]">{title}</h1>
      {children ? <div className="text-ink-2 mt-4 max-w-[68ch] leading-relaxed">{children}</div> : null}
    </header>
  );
}
