/**
 * Bibliographic facts and published validation targets.
 * Published values are displayed for comparison only; they are never used in calculations.
 */

export const STUDY = {
  title:
    "Measuring instability in chronic human intracortical neural recordings towards stable, long-term brain-computer interfaces",
  authors:
    "Pun TK, Khoshnevis M, Hosman T, Wilson GH, Kapitonava A, Kamdar F, Henderson JM, Simeral JD, Vargas-Irwin CE, Harrison MT, Hochberg LR",
  journal: "Communications Biology 7, 1363 (2024)",
  doi: "10.1038/s42003-024-06784-4",
  codeUrl: "https://github.com/ewinapun/MINDFUL",
  codeCommit: "1809e132549f3c4b03327e3a14c748927d765e6e",
  datasetDoi: "10.5061/dryad.n2z34tn5s",
} as const;

export type Participant = "T11" | "T5";
export type Configuration = "PCA-5" | "Extended 9-D";

export interface ParticipantProfile {
  id: Participant;
  features: string;
  featureCount: number;
  sessions: number;
  span: string;
  task: string;
  referenceSessions: string;
}

export const PARTICIPANTS: readonly ParticipantProfile[] = [
  {
    id: "T11",
    features: "Threshold crossings + spike-band power",
    featureCount: 384,
    sessions: 15,
    span: "Trial days 658–800",
    task: "Center-out-and-back",
    referenceSessions: "Session 1",
  },
  {
    id: "T5",
    features: "Threshold crossings",
    featureCount: 192,
    sessions: 6,
    span: "Trial days 2121–2149",
    task: "Random target",
    referenceSessions: "Sessions 1–2",
  },
];

export interface PublishedTarget {
  participant: Participant;
  configuration: Configuration;
  pearson: number;
  spearman: number;
  figure: string;
}

export const PUBLISHED_TARGETS: readonly PublishedTarget[] = [
  { participant: "T11", configuration: "PCA-5", pearson: 0.91, spearman: 0.9, figure: "Fig. 1c" },
  { participant: "T5", configuration: "PCA-5", pearson: 0.59, spearman: 0.6, figure: "Fig. 1c" },
  { participant: "T11", configuration: "Extended 9-D", pearson: 0.926, spearman: 0.913, figure: "Fig. 2c" },
  { participant: "T5", configuration: "Extended 9-D", pearson: 0.719, spearman: 0.759, figure: "Fig. 2c" },
];
