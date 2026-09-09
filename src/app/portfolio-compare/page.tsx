import type { Metadata } from "next";
import { PortfolioCompare } from "@/components/illustrate/PortfolioCompare";
import { getDistributionRepository } from "@/data";
import { COPY } from "@/lib/copy";
import { WEBSITE_PORTFOLIO_HOLDINGS } from "@/lib/illustrate/portfolio-compare-mount";

export const metadata: Metadata = {
  title: "Aftertax — Portfolio",
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
      <p
        data-print-hide
        className="text-[11px] font-semibold uppercase tracking-[0.16em] text-muted"
      >
        Illustrate module
      </p>
      <p data-print-hide className="mt-2 max-w-2xl text-sm text-muted">
        Reusable module for Website Engineering. Drop{" "}
        <code className="font-mono text-[13px] text-ink">PortfolioCompare</code>{" "}
        into a page. This demo posts{" "}
        <code className="font-mono text-[13px] text-ink">
          POST /illustrate/portfolio/compare
        </code>{" "}
        and falls back to the sketch fixture when the Data API is unreachable.
        Current and Proposed start empty — add tickers with + Add holding.
        Website mounts start Current / Proposed empty ($1M book stays).
        POSTs periods for calendar years 2021 through 2025. Calendar-year tax
        is the ticker × year matrix (2025–2021; unmatched / uncovered = N/A,
        never $0). Upcoming stays unpaid-announced. Paid History is not shown
        as a chronological list — historical tax lives in Calendar-year tax.
      </p>

      <div className="mt-8">
        <PortfolioCompare
          funds={funds}
          current={WEBSITE_PORTFOLIO_HOLDINGS}
          proposed={WEBSITE_PORTFOLIO_HOLDINGS}
        />
      </div>

      <pre
        data-print-hide
        className="mt-10 overflow-auto rounded-lg border border-line bg-surface p-4 text-[12px] leading-relaxed text-muted"
      >
        {`import {
  PortfolioCompare,
  exportToPdf,
  requestTicker,
  toPortfolioCompareExportModel,
} from "@/components/illustrate";
// or: import { requestTicker } from "@/lib/request-ticker";
// source: "web" | "search_miss" | "portfolio"
// await requestTicker({ ticker, note, source: "portfolio" });

<PortfolioCompare
  current={WEBSITE_PORTFOLIO_HOLDINGS}
  proposed={WEBSITE_PORTFOLIO_HOLDINGS}
/>

// Website wires the Export button + freemium gate, then:
exportToPdf(toPortfolioCompareExportModel(result, bookDollars));

// Website mounts pass empty books. Omit current/proposed to start empty
// (friends beta). Modules owns component smoke defaults.
<PortfolioCompare
  bookDollars={1_000_000}
  taxRates={{ state: 0.05 }}
  funds={funds}
  current={WEBSITE_PORTFOLIO_HOLDINGS}
  proposed={WEBSITE_PORTFOLIO_HOLDINGS}
/>`}
      </pre>

      <p data-print-hide className="mt-6 text-xs text-faint">
        {COPY.trust}
      </p>
    </main>
  );
}
