import type { Metadata } from "next";
import type { ReactNode } from "react";
import { IBM_Plex_Mono, Source_Sans_3, Source_Serif_4 } from "next/font/google";
import { AppHeader } from "@/components/AppHeader";
import { AppFooter } from "@/components/AppFooter";
import { COPY } from "@/lib/copy";
import { AFTERTAX_ORIGIN } from "@/lib/data-api/config";
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

export const metadata: Metadata = {
  metadataBase: new URL(AFTERTAX_ORIGIN),
  title: "Aftertax — taxable impact in dollars",
  description: `${COPY.hero} ${COPY.sub}`,
  alternates: { canonical: AFTERTAX_ORIGIN },
  applicationName: "Aftertax",
  openGraph: {
    type: "website",
    url: AFTERTAX_ORIGIN,
    siteName: "Aftertax",
    title: "Aftertax — taxable impact in dollars",
    description: `${COPY.hero} ${COPY.sub}`,
  },
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
