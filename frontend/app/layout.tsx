import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "Workisto",
  description: "Find and book local service providers.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full">{children}</body>
    </html>
  );
}
