import type { Metadata } from "next";
import { IBM_Plex_Mono, IBM_Plex_Sans, Newsreader } from "next/font/google";

import { Sidebar } from "@/components/Sidebar";

import "./globals.css";

const newsreader = Newsreader({ variable: "--font-newsreader", subsets: ["latin"] });
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

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${newsreader.variable} ${plexSans.variable} ${plexMono.variable}`}>
      <body className="min-h-screen md:flex">
        <Sidebar />
        <main className="min-w-0 flex-1 px-4 py-8 sm:px-8 md:px-12 md:py-12">
          <div className="max-w-5xl">{children}</div>
        </main>
      </body>
    </html>
  );
}
