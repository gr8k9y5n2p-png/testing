import type { Metadata } from "next";
import { Disclaimer } from "@/components/Disclaimer";
import { HomepagePortfolioCompare } from "@/components/illustrate/HomepagePortfolioCompare";
import { COPY } from "@/lib/copy";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Aftertax — Portfolios",
  description: `${COPY.sub} Current vs proposed books, tax impact, and holdings.`,
};

export default function PortfolioPage() {
  // Do not wait on the unpaid-announce catalog dump. Portfolios hydrates
  // identity per confirmed ticker (thin /funds/lookup + /funds?q=).
  return (
    <main className="mx-auto w-full max-w-7xl px-4 pb-16 pt-6 sm:px-6 lg:px-8">
      <HomepagePortfolioCompare />
      <Disclaimer className="mt-8 text-xs leading-relaxed text-muted" />
    </main>
  );
}
