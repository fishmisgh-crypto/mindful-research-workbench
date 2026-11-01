"use client";

import dynamic from "next/dynamic";
import { useState, type ReactNode } from "react";
import type { PlotParams } from "react-plotly.js";

/** Plotly (basic bundle), loaded in the browser only. */
const PlotlyPlot = dynamic(
  async () => {
    const [{ default: createPlotlyComponent }, plotly] = await Promise.all([
      import("react-plotly.js/factory"),
      import("plotly.js-basic-dist-min"),
    ]);
    return createPlotlyComponent(plotly);
  },
  { ssr: false, loading: () => null },
);

export const CHART_FONT = "var(--font-plex-sans), system-ui, sans-serif";
export const MONO_FONT = "var(--font-plex-mono), ui-monospace, monospace";
export const INK = "#161513";
export const INK_3 = "#77736a";
export const RULE = "#dcd7cb";
export const RULE_STRONG = "#b9b3a5";
export const ACCENT = "#8a2b1f";

export const BASE_CONFIG: PlotParams["config"] = {
  displaylogo: false,
  responsive: true,
  modeBarButtonsToRemove: [
    "select2d",
    "lasso2d",
    "autoScale2d",
    "toggleSpikelines",
    "hoverClosestCartesian",
    "hoverCompareCartesian",
  ],
};

/**
 * Interactive chart that keeps the server-rendered static version (children) on screen
 * until Plotly has drawn, so the page never shows an empty box and works without JS.
 */
export function InteractivePlot({
  fallback,
  height,
  ...plot
}: PlotParams & { fallback: ReactNode; height: number }) {
  const [ready, setReady] = useState(false);
  return (
    <div className="relative">
      <div
        className={ready ? "" : "pointer-events-none absolute inset-x-0 top-0 opacity-0"}
        aria-hidden={!ready}
      >
        <PlotlyPlot
          {...plot}
          style={{ width: "100%", height }}
          useResizeHandler
          onInitialized={() => setReady(true)}
        />
      </div>
      {ready ? null : fallback}
    </div>
  );
}
