"use client";

import type { ReactNode } from "react";

import { ACCENT, BASE_CONFIG, CHART_FONT, INK, INK_3, InteractivePlot, MONO_FONT, RULE, RULE_STRONG } from "./Plot";

/** Fig 1b: KLD of each angular-error bin against the bin's mean angular error. */
export function AeBinnedPlot({
  meanAe,
  kld,
  n,
  lowerDeg,
  filename,
  fallback,
}: {
  meanAe: (number | null)[];
  kld: (number | null)[];
  n: number[];
  lowerDeg: number[];
  filename: string;
  fallback: ReactNode;
}) {
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
      height={320}
      data={[
        {
          type: "scatter",
          mode: "markers",
          x: meanAe,
          y: kld,
          customdata: lowerDeg.map((a, i) => [a, a + 4, n[i]]),
          marker: { color: ACCENT, size: 7 },
          hovertemplate:
            "Bin %{customdata[0]}–%{customdata[1]}°<br>Mean AE %{x:.1f}°<br>KLD %{y:.4f} nats<br>%{customdata[2]} bins<extra></extra>",
        },
      ]}
      layout={{
        autosize: true,
        height: 320,
        margin: { l: 60, r: 12, t: 12, b: 50 },
        paper_bgcolor: "rgba(0,0,0,0)",
        plot_bgcolor: "rgba(0,0,0,0)",
        font: { family: CHART_FONT, color: INK },
        showlegend: false,
        hoverlabel: { bgcolor: "#fbfaf6", bordercolor: RULE_STRONG, font: { family: MONO_FONT, size: 11 } },
        xaxis: { ...axis, range: [0, 180], dtick: 45, title: { ...axis.title, text: "Mean angular error of bin (°)" } },
        yaxis: { ...axis, rangemode: "tozero", title: { ...axis.title, text: "KLD (nats)" } },
      }}
      config={{ ...BASE_CONFIG, toImageButtonOptions: { filename, format: "png", scale: 2 } }}
    />
  );
}
