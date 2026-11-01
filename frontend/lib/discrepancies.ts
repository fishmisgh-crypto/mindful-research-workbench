/**
 * Paper-versus-code discrepancies (docs/RESEARCH_SPEC.md §5). Prose only; any measured
 * effect is computed from the reproduction report at render time (see `ablation`).
 */

export type DiscrepancyStatus = "measured" | "no effect on this data" | "reproduced as in the code";

export interface Discrepancy {
  id: string;
  topic: string;
  paper: string;
  code: string;
  handling: string;
  status: DiscrepancyStatus;
  /** Report ablation id suffix whose runs measure this discrepancy, if any. */
  ablation?: "covariance" | "step" | "excluded_trials";
  aeBinned?: boolean;
}

export const DISCREPANCIES: readonly Discrepancy[] = [
  {
    id: "D1",
    topic: "Covariance estimate",
    paper: "Sample covariance of each window.",
    code: "Uncentred second moment X'X/n, used together with the sample mean.",
    handling: "Both are implemented; the upstream preset uses the code's estimator, the paper preset the sample covariance.",
    status: "measured",
    ablation: "covariance",
  },
  {
    id: "D2",
    topic: "Window step",
    paper: "Windows shifted in steps of 1 s.",
    code: "The figure script steps windows by 10 s (500 bins).",
    handling: "Upstream preset: 10 s. Paper preset: 1 s.",
    status: "measured",
    ablation: "step",
  },
  {
    id: "D3",
    topic: "Which bins enter a window",
    paper: "All time bins in a 60-s interval; outlier trials said to cause visible KLD spikes.",
    code: "Bins inside trials only, with trials flagged in excludeTrials removed.",
    handling: "Upstream follows the code. Keeping the flagged trials is run as a single-parameter change.",
    status: "measured",
    ablation: "excluded_trials",
  },
  {
    id: "D4",
    topic: "Windows crossing boundaries",
    paper: "Not stated.",
    code: "Windows run across blocks within a session; the last windows of each session are set to NaN afterwards.",
    handling:
      "Reproduced. On the real data every window that crosses into the next session is inside that NaN set, so only within-session block crossings reach a correlation.",
    status: "reproduced as in the code",
  },
  {
    id: "D5",
    topic: "Session order",
    paper: "Chronological (implied).",
    code: "Alphabetical folder order (MATLAB dir).",
    handling: "Folder names are trial days with equal digit counts, so the two orders are identical for this release.",
    status: "no effect on this data",
  },
  {
    id: "D6",
    topic: "Block order",
    paper: "Chronological.",
    code: "File modification time.",
    handling: "Blocks are ordered by block number; modification-time order matched it in all 21 sessions.",
    status: "no effect on this data",
  },
  {
    id: "D7",
    topic: "Reference window trimming",
    paper: "Not stated.",
    code: "Reference uses a session's windows minus the last n−1; the session-end NaN removes the last n.",
    handling:
      "Reproduced exactly. Because the reference is defined through windows, the step size changes it slightly (T11: 3,042 bins at 10 s, 3,048 at 1 s).",
    status: "reproduced as in the code",
  },
  {
    id: "D8",
    topic: "T5 feature count",
    paper: "192 features (threshold crossings).",
    code: "Adds spike-band power whenever a file contains it.",
    handling: "T5 files contain no spike-band power, so both give 192 features.",
    status: "no effect on this data",
  },
  {
    id: "D9",
    topic: "Fig. 1b bin count",
    paper: "45 angular-error bins of 4°.",
    code: "The loop stops one short, so 44 bins are computed and [176°, 180°) is skipped.",
    handling: "Both variants are computed and reported.",
    status: "measured",
    aeBinned: true,
  },
];
