import type { Metadata } from "next";
import { IBM_Plex_Sans_Condensed } from "next/font/google";
import "./globals.css";

const plex = IBM_Plex_Sans_Condensed({ subsets: ["latin"], weight: ["400", "500", "600", "700"], variable: "--font-plex" });
const site = process.env.SITE_URL ?? "http://localhost:3000";
const description =
  "A two-player hedge-fund crisis game on a real double-entry engine: survive a borrow recall, a margin shock and an investor redemption without touching investor money for payroll.";

export const metadata: Metadata = {
  metadataBase: new URL(site),
  title: { default: "FundForge: a two-partner hedge-fund crisis game", template: "%s | FundForge" },
  description,
  openGraph: { title: "FundForge", description, type: "website", url: "/" },
  twitter: { card: "summary_large_image", title: "FundForge", description },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={plex.variable}>
      <body>{children}</body>
    </html>
  );
}
