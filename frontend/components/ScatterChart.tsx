import type { ReactNode } from "react";

/** Static SVG scatter: x and y with units, title and data context always printed. */

const W = 520;
const H = 300;
const M = { top: 14, right: 14, bottom: 44, left: 58 };

function niceMax(v: number): number {
  if (!(v > 0)) return 1;
  const p = 10 ** Math.floor(Math.log10(v));
  for (const f of [1, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10]) if (f * p >= v) return f * p;
  return 10 * p;
}

export function ScatterChart({
  title,
  context,
  points,
  xMax,
  xLabel,
  yLabel,
  wrap,
}: {
  title: string;
  context: string;
  points: { x: number | null; y: number | null }[];
  xMax: number;
  xLabel: string;
  yLabel: string;
  wrap?: (staticChart: ReactNode) => ReactNode;
}) {
  const valid = points.filter(
    (p): p is { x: number; y: number } => p.x != null && p.y != null && Number.isFinite(p.y),
  );
  const yMax = niceMax(Math.max(0, ...valid.map((p) => p.y)));
  const x = (v: number) => M.left + (v / xMax) * (W - M.left - M.right);
  const y = (v: number) => M.top + (1 - v / yMax) * (H - M.top - M.bottom);
  const yTicks = [0, 0.25, 0.5, 0.75, 1].map((f) => f * yMax);
  const xTicks = [0, 45, 90, 135, 180].filter((t) => t <= xMax);
  const svg = (
    <svg viewBox={`0 0 ${W} ${H}`} className="h-auto w-full max-w-[520px]" role="img" aria-label={`${title}. ${context}`}>
      {yTicks.map((t) => (
        <g key={t}>
          <line x1={M.left} x2={W - M.right} y1={y(t)} y2={y(t)} className="stroke-rule" strokeWidth={1} />
          <text x={M.left - 8} y={y(t)} dy="0.32em" textAnchor="end" className="fill-ink-3 font-mono text-[10px]">
            {Number(t.toPrecision(3))}
          </text>
        </g>
      ))}
      <line x1={M.left} x2={W - M.right} y1={y(0)} y2={y(0)} className="stroke-ink" strokeWidth={1} />
      {xTicks.map((t) => (
        <text key={t} x={x(t)} y={y(0) + 16} textAnchor="middle" className="fill-ink-3 font-mono text-[10px]">
          {t}
        </text>
      ))}
      {valid.map((p, i) => (
        <circle key={i} cx={x(p.x)} cy={y(p.y)} r={3} className="fill-accent" />
      ))}
      <text x={M.left + (W - M.left - M.right) / 2} y={H - 6} textAnchor="middle" className="fill-ink-2 text-[11px]">
        {xLabel}
      </text>
      <text transform={`translate(14 ${M.top + (H - M.top - M.bottom) / 2}) rotate(-90)`} textAnchor="middle" className="fill-ink-2 text-[11px]">
        {yLabel}
      </text>
    </svg>
  );

  return (
    <figure>
      <figcaption className="mb-2">
        <p className="font-display text-lg">{title}</p>
        <p className="text-ink-3 font-mono text-[11px] leading-relaxed">{context}</p>
      </figcaption>
      {wrap ? wrap(svg) : svg}
    </figure>
  );
}
