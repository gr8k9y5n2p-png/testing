import type { Metadata } from "next";
import type { ReactNode } from "react";
import { cookies } from "next/headers";
import { IBM_Plex_Mono, Source_Sans_3, Source_Serif_4 } from "next/font/google";
import { AppHeader } from "@/components/AppHeader";
import { AppFooter } from "@/components/AppFooter";
import { AccountSessionProvider } from "@/components/AccountSession";
import { BillingProvider } from "@/components/BillingProvider";
import { FriendsBetaBanner } from "@/components/FriendsBetaBanner";
import { ACCOUNT_COOKIE, verifyAccountCookie } from "@/lib/account/session";
import { getAccountStore, toPublicAccount } from "@/lib/account/store";
import {
  FREEMIUM_COOKIE,
  mergeUsage,
  usageFromCookieValue,
} from "@/lib/billing/limits";
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

export default async function RootLayout({
  children,
}: Readonly<{
  children: ReactNode;
}>) {
  const jar = await cookies();
  const raw = jar.get(ACCOUNT_COOKIE)?.value;
  const accountId = verifyAccountCookie(raw);
  const row = accountId ? await getAccountStore().findById(accountId) : null;
  const initialAccount = row ? toPublicAccount(row) : null;
  const cookieUsage = usageFromCookieValue(jar.get(FREEMIUM_COOKIE)?.value);
  const initialUsage = row ? mergeUsage(row.usage, cookieUsage) : cookieUsage;

  return (
    <html
      lang="en"
      className={`${sourceSans.variable} ${sourceSerif.variable} ${plexMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-paper text-ink font-sans">
        <AccountSessionProvider initialAccount={initialAccount}>
          <BillingProvider initialUsage={initialUsage}>
            <AppHeader />
            <FriendsBetaBanner />
            <div className="flex-1">{children}</div>
            <AppFooter />
          </BillingProvider>
        </AccountSessionProvider>
      </body>
    </html>
  );
}
