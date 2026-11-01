"use client";

import { useEffect, useId, useMemo, useRef, useState } from "react";

type Series = (number | null)[];

const W = 1200;
const H = 300;
const PAD_TOP = 16;
const PAD_BOTTOM = 34;
const RADIUS = 150;

function path(values: Series, max: number): string {
  const n = Math.max(1, values.length - 1);
  let d = "";
  let pen = false;
  values.forEach((v, i) => {
    if (v == null || !Number.isFinite(v)) {
      pen = false;
      return;
    }
    const x = (i / n) * W;
    const y = PAD_TOP + (1 - v / max) * (H - PAD_TOP - PAD_BOTTOM);
    d += `${pen ? "L" : "M"}${x.toFixed(1)},${y.toFixed(1)}`;
    pen = true;
  });
  return d;
}

/**
 * Real window-level KLD drawn as a pale trace; median angular error (accent) is revealed
 * under the pointer. Each series is scaled to its own range; the caption says so.
 */
export function DriftHero({
  kld,
  medianAe,
  sessionIndex,
  dayOfSession,
  caption,
}: {
  kld: Series;
  medianAe: Series;
  sessionIndex: number[];
  dayOfSession: Record<number, number>;
  caption: string;
}) {
  const id = useId().replace(/:/g, "");
  const box = useRef<HTMLDivElement>(null);
  const target = useRef({ x: -9999, y: -9999 });
  const [spot, setSpot] = useState({ x: -9999, y: -9999 });
  const [revealAll, setRevealAll] = useState(false);

  useEffect(() => {
    const touch = window.matchMedia("(hover: none)").matches;
    const still = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (touch) {
      setRevealAll(true);
      return;
    }
    let raf = 0;
    const tick = () => {
      setSpot((s) => {
        const t = target.current;
        if (still) return t;
        const nx = s.x + (t.x - s.x) * 0.14;
        const ny = s.y + (t.y - s.y) * 0.14;
        return Math.abs(nx - s.x) + Math.abs(ny - s.y) < 0.2 ? t : { x: nx, y: ny };
      });
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, []);

  const onMove = (e: React.PointerEvent) => {
    const r = box.current?.getBoundingClientRect();
    if (!r) return;
    const x = ((e.clientX - r.left) / r.width) * W;
    const y = ((e.clientY - r.top) / r.height) * H;
    if (target.current.x < -1000) setSpot({ x, y }); // first entry: no sweep from off-screen
    target.current = { x, y };
  };

  const [kldPath, aePath] = useMemo(() => {
    const k = kld.filter((v): v is number => v != null && Number.isFinite(v));
    return [path(kld, Math.max(...k) * 1.05), path(medianAe, 180)];
  }, [kld, medianAe]);
  const n = Math.max(1, sessionIndex.length - 1);
  const starts = sessionIndex
    .map((s, i) => (i === 0 || s !== sessionIndex[i - 1] ? i : -1))
    .filter((i) => i >= 0);

  return (
    <figure className="w-full">
      <div
        ref={box}
        onPointerMove={onMove}
        onPointerLeave={() => (target.current = { x: -9999, y: -9999 })}
        className="relative w-full touch-pan-y"
      >
        <svg
          viewBox={`0 0 ${W} ${H}`}
          preserveAspectRatio="none"
          className="block h-[220px] w-full md:h-[300px]"
          role="img"
          aria-label={caption}
        >
          <defs>
            <radialGradient id={`g${id}`}>
              <stop offset="0" stopColor="#fff" stopOpacity="1" />
              <stop offset="0.55" stopColor="#fff" stopOpacity="0.85" />
              <stop offset="1" stopColor="#fff" stopOpacity="0" />
            </radialGradient>
            <mask id={`m${id}`} maskUnits="userSpaceOnUse" x="0" y="0" width={W} height={H}>
              {revealAll ? (
                <rect width={W} height={H} fill="#fff" />
              ) : (
                <ellipse cx={spot.x} cy={spot.y} rx={RADIUS} ry={RADIUS * 1.4} fill={`url(#g${id})`} />
              )}
            </mask>
          </defs>
          {starts.map((i) => (
            <g key={i}>
              <line
                x1={(i / n) * W}
                x2={(i / n) * W}
                y1={H - PAD_BOTTOM + 6}
                y2={H - PAD_BOTTOM + 14}
                className="stroke-seam"
                vectorEffect="non-scaling-stroke"
              />
            </g>
          ))}
          <path
            d={aePath}
            fill="none"
            className="stroke-signal"
            strokeWidth={1.5}
            strokeOpacity={0.16}
            vectorEffect="non-scaling-stroke"
          />
          <path
            d={aePath}
            fill="none"
            className="stroke-signal"
            strokeWidth={1.75}
            mask={`url(#m${id})`}
            vectorEffect="non-scaling-stroke"
          />
          <path
            d={kldPath}
            fill="none"
            className="stroke-bone trace-in"
            strokeWidth={1.5}
            pathLength={1}
            vectorEffect="non-scaling-stroke"
          />
        </svg>
        <div className="text-bone-3 pointer-events-none absolute inset-x-0 bottom-0 hidden font-mono text-[10px] md:block">
          {starts.map((i) => (
            <span key={i} className="absolute" style={{ left: `${(i / n) * 100}%` }}>
              {dayOfSession[sessionIndex[i]]}
            </span>
          ))}
        </div>
      </div>
      <figcaption className="text-bone-3 mt-6 max-w-[78ch] text-[13px] leading-relaxed">{caption}</figcaption>
    </figure>
  );
}
