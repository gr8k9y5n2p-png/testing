import type { Metadata } from "next";
import type { ReactNode } from "react";
import { IBM_Plex_Mono, Source_Sans_3, Source_Serif_4 } from "next/font/google";
import { AppHeader } from "@/components/AppHeader";
import { AppFooter } from "@/components/AppFooter";
import { COPY } from "@/lib/copy";
import { publicOrigin } from "@/lib/hosts";
import "./globals.css";

const sourceSans = Source_Sans_3({
  variable: "--font-source-sans",
  subsets: ["latin"],
  display: "swap",
});

const sourceSerif = Source_Serif_4({
  variable: "--font-source-serif",
  subsets: ["latin"],
  display: "swap",
});

const plexMono = IBM_Plex_Mono({
  variable: "--font-plex-mono",
  subsets: ["latin"],
  weight: ["400", "500"],
  display: "swap",
});

const PUBLIC_ORIGIN = publicOrigin();

export const metadata: Metadata = {
  metadataBase: new URL(PUBLIC_ORIGIN),
  title: "Aftertax — taxable impact in dollars",
  description: `${COPY.hero} ${COPY.sub}`,
  alternates: { canonical: PUBLIC_ORIGIN },
  applicationName: "Aftertax",
  openGraph: {
    type: "website",
    url: PUBLIC_ORIGIN,
    siteName: "Aftertax",
    title: "Aftertax — taxable impact in dollars",
    description: `${COPY.hero} ${COPY.sub}`,
  },
  robots: PUBLIC_ORIGIN.includes("staging.")
    ? { index: false, follow: false }
    : { index: true, follow: true },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${sourceSans.variable} ${sourceSerif.variable} ${plexMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-paper text-ink font-sans">
        <AppHeader />
        <div className="flex-1">{children}</div>
        <AppFooter />
      </body>
    </html>
  );
}
