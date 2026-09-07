import type { Metadata } from "next";
import { PortfolioCompare } from "@/components/illustrate/PortfolioCompare";
import { getDistributionRepository } from "@/data";
import { COPY } from "@/lib/copy";

export const metadata: Metadata = {
  title: "Aftertax — portfolio comparison",
  description:
    "Current vs proposed allocation tax drag. Mount PortfolioCompare in the illustrate flow.",
  robots: { index: false, follow: false },
};

export default async function PortfolioCompareDemoPage() {
  const repository = await getDistributionRepository();
  const funds = (await repository.search()).map((fund) => ({
    ticker: fund.ticker,
    fundName: fund.fundName,
    family: fund.family,
  }));

  return (
    <main className="mx-auto w-full max-w-7xl px-4 pb-16 pt-8 sm:px-6 lg:px-8">
      <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-muted">
        Illustrate module
      </p>
      <p className="mt-2 max-w-2xl text-sm text-muted">
        Reusable module for Website Engineering. Drop{" "}
        <code className="font-mono text-[13px] text-ink">PortfolioCompare</code>{" "}
        into a page. This demo posts{" "}
        <code className="font-mono text-[13px] text-ink">
          POST /illustrate/portfolio/compare
        </code>{" "}
        and falls back to the sketch fixture when the Data API is unreachable. v1
        is a single snapshot — no YoY bars / no periods[].
      </p>

      <div className="mt-8">
        <PortfolioCompare funds={funds} />
      </div>

      <pre className="mt-10 overflow-auto rounded-lg border border-line bg-surface p-4 text-[12px] leading-relaxed text-muted">
        {`import { PortfolioCompare } from "@/components/illustrate";

<PortfolioCompare />

// Optional: pass book size, funds for autocomplete, or tax rates
<PortfolioCompare
  bookDollars={1_000_000}
  taxRates={{ state: 0.05 }}
  funds={funds}
/>`}
      </pre>

      <p className="mt-6 text-xs text-faint">{COPY.trust}</p>
    </main>
  );
}
