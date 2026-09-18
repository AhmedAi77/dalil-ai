import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Dalil AI | دليل — Your knowledge guide",
  description: "Ask your documents, keep the answers, and return to any conversation.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body>{children}</body>
    </html>
  );
}
