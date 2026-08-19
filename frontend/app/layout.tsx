import type { Metadata } from "next";
import { Caprasimo, Figtree } from "next/font/google";

import "./globals.css";

// Two families, two jobs: Caprasimo carries headings (it has personality and is
// never asked to be read at length), Figtree does every other job. Loaded
// through next/font so the files are self-hosted and there's no render-blocking
// request to Google at runtime.
const caprasimo = Caprasimo({
  weight: "400",
  subsets: ["latin"],
  variable: "--font-caprasimo",
  display: "swap",
});

const figtree = Figtree({
  weight: ["400", "500", "600", "700"],
  subsets: ["latin"],
  variable: "--font-figtree",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Workisto",
  description: "Find and book local service providers.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html
      lang="en"
      className={`h-full antialiased ${caprasimo.variable} ${figtree.variable}`}
    >
      <body className="min-h-full">{children}</body>
    </html>
  );
}
