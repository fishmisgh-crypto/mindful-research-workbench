"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { NAV_ITEMS } from "@/lib/nav";

function isActive(pathname: string, href: string): boolean {
  return href === "/" ? pathname === "/" : pathname.startsWith(href);
}

/** Left rail: project mark and the five research sections. */
export function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="border-rule border-b md:w-60 md:shrink-0 md:border-r md:border-b-0">
      <div className="md:sticky md:top-0">
        <div className="px-6 pt-6 pb-5 md:pt-8">
          <p className="font-display text-xl leading-tight">MINDFUL</p>
          <p className="text-ink-3 mt-1 font-mono text-[11px] tracking-wide uppercase">
            Research workbench
          </p>
        </div>
        <nav aria-label="Sections" className="pb-4 md:pb-0">
          <ul className="flex overflow-x-auto md:block">
            {NAV_ITEMS.map((item) => {
              const active = isActive(pathname, item.href);
              return (
                <li key={item.href} className="shrink-0">
                  <Link
                    href={item.href}
                    aria-current={active ? "page" : undefined}
                    className={`flex items-baseline gap-3 border-l-2 px-6 py-2 text-sm md:py-1.5 ${
                      active
                        ? "border-accent text-ink font-medium"
                        : "text-ink-2 hover:text-ink border-transparent"
                    }`}
                  >
                    <span className="text-ink-3 font-mono text-[11px]">{item.index}</span>
                    <span>{item.label}</span>
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>
        <p className="text-ink-3 hidden px-6 pt-8 font-mono text-[11px] leading-relaxed md:block">
          Local only · 127.0.0.1
          <br />
          Not a medical device
        </p>
      </div>
    </aside>
  );
}
