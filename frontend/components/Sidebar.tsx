"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useLayoutEffect, useRef, useState } from "react";

import { NAV_ITEMS } from "@/lib/nav";

function isActive(pathname: string, href: string): boolean {
  return href === "/" ? pathname === "/" : pathname.startsWith(href);
}

type Marker = { x: number; y: number; w: number; h: number } | null;

/**
 * Dark rail with the five sections. A single marker slides to the active item when the
 * route changes (motion that answers the reader's navigation; off with reduced motion).
 */
export function Sidebar() {
  const pathname = usePathname();
  const listRef = useRef<HTMLUListElement>(null);
  const [marker, setMarker] = useState<Marker>(null);

  useLayoutEffect(() => {
    const place = () => {
      const link = listRef.current?.querySelector<HTMLElement>('[aria-current="page"]');
      const item = link?.parentElement; // the <li>, positioned within the <ul>
      if (!item) return setMarker(null);
      const rail = window.matchMedia("(min-width: 768px)").matches;
      const { offsetLeft: x, offsetTop: y, offsetWidth: w, offsetHeight: h } = item;
      // a 2px bar: vertical on the rail, an underline on the mobile strip
      setMarker(rail ? { x: 0, y, w: 2, h } : { x, y: y + h - 2, w, h: 2 });
    };
    place();
    window.addEventListener("resize", place);
    return () => window.removeEventListener("resize", place);
  }, [pathname]);

  return (
    <aside
      data-surface="housing"
      className="bg-housing text-bone border-seam border-b md:w-60 md:shrink-0 md:border-r md:border-b-0"
    >
      <div className="md:sticky md:top-0">
        <div className="px-6 pt-6 pb-5 md:pt-8">
          <Link href="/" className="font-display block text-2xl leading-none tracking-[-0.01em]">
            MINDFUL
          </Link>
          <p className="text-bone-3 mt-2 text-[13px]">Research workbench</p>
        </div>
        <nav aria-label="Sections" className="pb-3 md:pb-0">
          <ul ref={listRef} className="relative flex overflow-x-auto md:block">
            {marker ? (
              <span
                aria-hidden
                className="bg-signal pointer-events-none absolute top-0 left-0 transition-[transform,width,height] duration-500 ease-[cubic-bezier(0.16,1,0.3,1)]"
                style={{
                  transform: `translate(${marker.x}px, ${marker.y}px)`,
                  width: marker.w,
                  height: marker.h,
                }}
              />
            ) : null}
            {NAV_ITEMS.map((item) => {
              const active = isActive(pathname, item.href);
              return (
                <li key={item.href} className="relative shrink-0">
                  <Link
                    href={item.href}
                    aria-current={active ? "page" : undefined}
                    className={`relative block px-6 py-2.5 text-sm md:py-2 ${
                      active ? "text-bone font-medium" : "text-bone-2 hover:text-bone"
                    }`}
                  >
                    {item.label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>
        <p className="text-bone-3 hidden px-6 pt-10 text-[12px] leading-relaxed md:block">
          Runs on this computer only.
          <br />
          Research software, not a medical device.
        </p>
      </div>
    </aside>
  );
}
