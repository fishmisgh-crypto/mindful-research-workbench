import type { ReactNode } from "react";

/**
 * Full-bleed dark header band: the page title in the display serif and a short lede.
 * Marked data-band so the layout does not wrap it in the readable column.
 */
export function PageHeader({
  title,
  children,
  aside,
  crumb,
}: {
  title: string;
  crumb?: ReactNode;
  children?: ReactNode;
  aside?: ReactNode;
}) {
  return (
    <header data-band data-surface="housing" className="bg-housing text-bone mb-4">
      <div className="max-w-5xl px-4 pt-10 pb-10 sm:px-8 md:px-12 md:pt-16 md:pb-14">
        {crumb ? <div className="text-bone-3 mb-6 text-[13px]">{crumb}</div> : null}
        <h1 className="font-display text-[2.75rem] leading-[1.02] tracking-[-0.02em] md:text-[4rem]">
          {title}
        </h1>
        {children ? (
          <div className="text-bone-2 mt-5 max-w-[62ch] text-[15px] leading-relaxed md:text-base">
            {children}
          </div>
        ) : null}
        {aside ? <div className="mt-6">{aside}</div> : null}
      </div>
    </header>
  );
}
