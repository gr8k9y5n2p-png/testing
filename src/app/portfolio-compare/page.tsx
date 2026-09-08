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
        Defaults are GTM’s history-covered smoke books (Current AGTHX / DODIX /
        AMCAP / DODGX, Proposed AMCPX / CGHM / AGTHX / AMCAP, 25% each at $1M).
        POSTs periods for calendar years 2021 through 2025. Calendar-year tax
        is the ticker × year matrix (2025–2021; unmatched / uncovered = N/A,
        never $0). Upcoming stays unpaid-announced; Paid History is
        `paid_history[]` only.
      </p>

      <div className="mt-8">
        <PortfolioCompare funds={funds} />
      </div>

      <pre
        data-print-hide
        className="mt-10 overflow-auto rounded-lg border border-line bg-surface p-4 text-[12px] leading-relaxed text-muted"
      >
        {`import {
  PortfolioCompare,
  exportToPdf,
  toPortfolioCompareExportModel,
} from "@/components/illustrate";

<PortfolioCompare />

// Website wires the Export button + freemium gate, then:
exportToPdf(toPortfolioCompareExportModel(result, bookDollars));

// Optional: pass book size, funds for autocomplete, or tax rates.
// Omit current/proposed to use GTM history-covered smoke books.
<PortfolioCompare
  bookDollars={1_000_000}
  taxRates={{ state: 0.05 }}
  funds={funds}
/>`}
      </pre>

      <p data-print-hide className="mt-6 text-xs text-faint">
        {COPY.trust}
      </p>
    </main>
  );
}
