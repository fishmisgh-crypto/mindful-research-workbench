/**
 * Static SVG histogram (server-rendered, no chart library).
 * Title, axis labels with units and the data context are always printed.
 */
export function Histogram({
  title,
  context,
  edges,
  counts,
  xLabel,
  yLabel,
}: {
  title: string;
  context: string;
  edges: number[];
  counts: number[];
  xLabel: string;
  yLabel: string;
}) {
  const W = 640;
  const H = 260;
  const m = { top: 16, right: 12, bottom: 44, left: 56 };
  const iw = W - m.left - m.right;
  const ih = H - m.top - m.bottom;
  const x0 = edges[0];
  const x1 = edges[edges.length - 1];
  const yMax = Math.max(1, ...counts);
  const niceMax = niceCeil(yMax);
  const x = (v: number) => m.left + ((v - x0) / (x1 - x0)) * iw;
  const y = (v: number) => m.top + ih - (v / niceMax) * ih;
  const yTicks = [0, 0.25, 0.5, 0.75, 1].map((f) => f * niceMax);
  const xTicks = edges.filter((_, i) => i % 3 === 0);

  return (
    <figure>
      <figcaption className="mb-3">
        <p className="font-display text-lg">{title}</p>
        <p className="text-ink-3 font-mono text-[11px]">{context}</p>
      </figcaption>
      <svg
        viewBox={`0 0 ${W} ${H}`}
        className="h-auto w-full max-w-[640px]"
        role="img"
        aria-label={`${title}. ${context}`}
      >
        {yTicks.map((t) => (
          <g key={t}>
            <line x1={m.left} x2={W - m.right} y1={y(t)} y2={y(t)} className="stroke-rule" strokeWidth={1} />
            <text x={m.left - 8} y={y(t)} dy="0.32em" textAnchor="end" className="fill-ink-3 font-mono text-[10px]">
              {t.toLocaleString("en-US")}
            </text>
          </g>
        ))}
        {counts.map((c, i) => (
          <rect
            key={edges[i]}
            x={x(edges[i]) + 1}
            y={y(c)}
            width={Math.max(0, x(edges[i + 1]) - x(edges[i]) - 2)}
            height={m.top + ih - y(c)}
            className="fill-ink"
          />
        ))}
        <line x1={m.left} x2={W - m.right} y1={m.top + ih} y2={m.top + ih} className="stroke-ink" strokeWidth={1} />
        {xTicks.map((t) => (
          <text key={t} x={x(t)} y={m.top + ih + 16} textAnchor="middle" className="fill-ink-3 font-mono text-[10px]">
            {t}
          </text>
        ))}
        <text x={m.left + iw / 2} y={H - 6} textAnchor="middle" className="fill-ink-2 text-[11px]">
          {xLabel}
        </text>
        <text
          transform={`translate(14 ${m.top + ih / 2}) rotate(-90)`}
          textAnchor="middle"
          className="fill-ink-2 text-[11px]"
        >
          {yLabel}
        </text>
      </svg>
    </figure>
  );
}

function niceCeil(v: number): number {
  const p = 10 ** Math.floor(Math.log10(v));
  for (const f of [1, 2, 2.5, 5, 10]) if (f * p >= v) return f * p;
  return 10 * p;
}
