"use client";

import type { ReactNode } from "react";

import { ACCENT, BASE_CONFIG, CHART_FONT, INK, INK_3, InteractivePlot, MONO_FONT, RULE, RULE_STRONG } from "./Plot";

type Series = (number | null)[];

/**
 * Stacked KLD (top) and median AE (bottom) panels on one window axis.
 * No dual y-axes, no smoothing; null windows stay gaps; session starts are rules.
 */
export function DriftPlot({
  kld,
  medianAe,
  day,
  sessionIndex,
  referenceDays,
  filename,
  fallback,
}: {
  kld: Series;
  medianAe: Series;
  day: number[];
  sessionIndex: number[];
  referenceDays: number[];
  filename: string;
  fallback: ReactNode;
}) {
  const x = kld.map((_, i) => i);
  const starts = sessionIndex.map((s, i) => (i === 0 || s !== sessionIndex[i - 1] ? i : -1)).filter((i) => i >= 0);
  const axis = {
    gridcolor: RULE,
    zeroline: false,
    linecolor: INK,
    tickfont: { family: MONO_FONT, size: 10, color: INK_3 },
    title: { font: { family: CHART_FONT, size: 12, color: INK } },
  };

  return (
    <InteractivePlot
      fallback={fallback}
      height={520}
      data={[
        {
          type: "scatter",
          mode: "lines",
          name: "KLD",
          x,
          y: kld,
          customdata: day,
          line: { color: ACCENT, width: 1.3 },
          connectgaps: false,
          hovertemplate: "KLD %{y:.3f} nats<extra></extra>",
        },
        {
          type: "scatter",
          mode: "lines",
          name: "Median AE",
          x,
          y: medianAe,
          yaxis: "y2",
          customdata: day,
          line: { color: INK, width: 1.1 },
          connectgaps: false,
          hovertemplate: "Median AE %{y:.1f}°<extra>Window %{x} · day %{customdata}</extra>",
        },
      ]}
      layout={{
        autosize: true,
        height: 520,
        margin: { l: 64, r: 16, t: 36, b: 56 },
        paper_bgcolor: "rgba(0,0,0,0)",
        plot_bgcolor: "rgba(0,0,0,0)",
        font: { family: CHART_FONT, color: INK },
        showlegend: false,
        hovermode: "x unified",
        hoverlabel: { bgcolor: "#fbfaf6", bordercolor: RULE_STRONG, font: { family: MONO_FONT, size: 11 } },
        xaxis: { ...axis, anchor: "y2", title: { ...axis.title, text: "Window index (60-s windows)" } },
        yaxis: { ...axis, domain: [0.54, 1], rangemode: "tozero", title: { ...axis.title, text: "KLD (nats)" } },
        yaxis2: {
          ...axis,
          domain: [0, 0.44],
          rangemode: "tozero",
          anchor: "x",
          title: { ...axis.title, text: "Median AE (°)" },
        },
        shapes: starts
          .filter((i) => i > 0)
          .map((i) => ({
            type: "line" as const,
            xref: "x" as const,
            yref: "paper" as const,
            x0: i - 0.5,
            x1: i - 0.5,
            y0: 0,
            y1: 1,
            line: { color: RULE_STRONG, width: 1 },
          })),
        annotations: starts.map((i) => ({
          x: i,
          y: 1,
          xref: "x" as const,
          yref: "paper" as const,
          yanchor: "bottom" as const,
          xanchor: "left" as const,
          showarrow: false,
          text: `${day[i]}${referenceDays.includes(day[i]) ? " ref" : ""}`,
          font: { family: MONO_FONT, size: 9, color: INK_3 },
        })),
      }}
      config={{ ...BASE_CONFIG, toImageButtonOptions: { filename, format: "png", scale: 2 } }}
    />
  );
}
