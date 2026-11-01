/**
 * Two stacked panels on one x-axis (window index): KLD on top, median AE below.
 * No dual axes, no smoothing, NaN windows are gaps, session boundaries are hairlines.
 * Server-rendered SVG; values are drawn exactly as the API returns them.
 */

type Series = (number | null)[];

const W = 960;
const PANEL_H = 190;
const GAP = 34;
const M = { top: 34, right: 16, bottom: 46, left: 64 };
const H = M.top + PANEL_H * 2 + GAP + M.bottom;

function niceMax(v: number): number {
  if (!(v > 0)) return 1;
  const p = 10 ** Math.floor(Math.log10(v));
  for (const f of [1, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10]) if (f * p >= v) return f * p;
  return 10 * p;
}

function linePath(values: Series, x: (i: number) => number, y: (v: number) => number): string {
  let d = "";
  let pen = false;
  values.forEach((v, i) => {
    if (v == null || !Number.isFinite(v)) {
      pen = false;
      return;
    }
    d += `${pen ? "L" : "M"}${x(i).toFixed(1)},${y(v).toFixed(1)}`;
    pen = true;
  });
  return d;
}

function Panel({
  values,
  top,
  yMax,
  label,
  stroke,
  x,
}: {
  values: Series;
  top: number;
  yMax: number;
  label: string;
  stroke: string;
  x: (i: number) => number;
}) {
  const y = (v: number) => top + PANEL_H - (v / yMax) * PANEL_H;
  const ticks = [0, 0.25, 0.5, 0.75, 1].map((f) => f * yMax);
  return (
    <g>
      {ticks.map((t) => (
        <g key={t}>
          <line x1={M.left} x2={W - M.right} y1={y(t)} y2={y(t)} className="stroke-rule" strokeWidth={1} />
          <text x={M.left - 8} y={y(t)} dy="0.32em" textAnchor="end" className="fill-ink-3 font-mono text-[10px]">
            {Number(t.toPrecision(3))}
          </text>
        </g>
      ))}
      <path d={linePath(values, x, y)} fill="none" className={stroke} strokeWidth={1.25} strokeLinejoin="round" />
      <text
        transform={`translate(16 ${top + PANEL_H / 2}) rotate(-90)`}
        textAnchor="middle"
        className="fill-ink-2 text-[11px]"
      >
        {label}
      </text>
    </g>
  );
}

export function DriftChart({
  title,
  context,
  kld,
  medianAe,
  sessionIndex,
  dayOfSession,
  referenceDays,
  xLabel,
}: {
  title: string;
  context: string;
  kld: Series;
  medianAe: Series;
  sessionIndex: number[];
  dayOfSession: Record<number, number>;
  referenceDays: number[];
  xLabel: string;
}) {
  const n = Math.max(1, kld.length);
  const x = (i: number) => M.left + (i / Math.max(1, n - 1)) * (W - M.left - M.right);
  const finite = (s: Series) => s.filter((v): v is number => v != null && Number.isFinite(v));
  const kMax = niceMax(Math.max(0, ...finite(kld)));
  const aMax = Math.min(180, niceMax(Math.max(0, ...finite(medianAe))));
  const boundaries = sessionIndex
    .map((s, i) => (i === 0 || s !== sessionIndex[i - 1] ? i : -1))
    .filter((i) => i >= 0);
  const kTop = M.top;
  const aTop = M.top + PANEL_H + GAP;

  return (
    <figure>
      <figcaption className="mb-3">
        <p className="font-display text-lg">{title}</p>
        <p className="text-ink-3 font-mono text-[11px] leading-relaxed">{context}</p>
      </figcaption>
      <div className="overflow-x-auto">
        <svg viewBox={`0 0 ${W} ${H}`} className="h-auto w-full min-w-[640px]" role="img" aria-label={`${title}. ${context}`}>
          {boundaries.map((i) => {
            const day = dayOfSession[sessionIndex[i]];
            const isRef = referenceDays.includes(day);
            return (
              <g key={i}>
                <line
                  x1={x(i)}
                  x2={x(i)}
                  y1={M.top - 6}
                  y2={aTop + PANEL_H}
                  className={i === 0 ? "stroke-transparent" : "stroke-rule-strong"}
                  strokeWidth={1}
                />
                <text x={x(i) + 3} y={M.top - 12} className="fill-ink-3 font-mono text-[9px]">
                  {day}
                  {isRef ? " ref" : ""}
                </text>
              </g>
            );
          })}
          <Panel values={kld} top={kTop} yMax={kMax} label="KLD (nats)" stroke="stroke-accent" x={x} />
          <Panel values={medianAe} top={aTop} yMax={aMax} label="Median AE (°)" stroke="stroke-ink" x={x} />
          <line x1={M.left} x2={W - M.right} y1={aTop + PANEL_H} y2={aTop + PANEL_H} className="stroke-ink" strokeWidth={1} />
          {[0, 0.25, 0.5, 0.75, 1].map((f) => {
            const i = Math.round(f * (n - 1));
            return (
              <text key={f} x={x(i)} y={aTop + PANEL_H + 16} textAnchor="middle" className="fill-ink-3 font-mono text-[10px]">
                {i}
              </text>
            );
          })}
          <text x={M.left + (W - M.left - M.right) / 2} y={H - 8} textAnchor="middle" className="fill-ink-2 text-[11px]">
            {xLabel}
          </text>
        </svg>
      </div>
    </figure>
  );
}
