import type { Metadata } from "next";
import { IBM_Plex_Mono, IBM_Plex_Sans, Instrument_Serif } from "next/font/google";

import { Sidebar } from "@/components/Sidebar";

import "./globals.css";

const instrument = Instrument_Serif({
  variable: "--font-instrument",
  subsets: ["latin"],
  weight: "400",
  style: ["normal", "italic"],
});
const plexSans = IBM_Plex_Sans({
  variable: "--font-plex-sans",
  subsets: ["latin"],
  weight: ["400", "500", "600"],
});
const plexMono = IBM_Plex_Mono({
  variable: "--font-plex-mono",
  subsets: ["latin"],
  weight: ["400", "500"],
});

export const metadata: Metadata = {
  title: { default: "MINDFUL Research Workbench", template: "%s · MINDFUL Workbench" },
  description: "Independent reproduction of the MINDFUL neural-instability method (Pun et al., 2024).",
};

/** Children of <main> that are not full-bleed bands get the readable column and gutters. */
const COLUMN =
  "[&>*:not([data-band])]:mx-4 sm:[&>*:not([data-band])]:mx-8 md:[&>*:not([data-band])]:mx-12 " +
  "[&>*:not([data-band])]:max-w-5xl";

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${instrument.variable} ${plexSans.variable} ${plexMono.variable}`}>
      <body className="min-h-screen md:flex">
        <Sidebar />
        <main className={`min-w-0 flex-1 pb-20 ${COLUMN}`}>{children}</main>
      </body>
    </html>
  );
}
