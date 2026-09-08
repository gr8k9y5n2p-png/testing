"use client";

import { useMemo } from "react";
import type { FundEstimateView } from "@/data/types";
import { PortfolioCompare } from "@/components/illustrate/PortfolioCompare";
import {
  exportToPdf,
  toPortfolioCompareExportModel,
} from "@/lib/illustrate/portfolio-compare-export";
import { PORTFOLIO_COMPARE_BOOK_DOLLARS } from "@/lib/illustrate/portfolio-compare-types";
import { UI_DEFAULT_TAX_RATES } from "@/lib/illustrate/types";

const HOMEPAGE_TAX_RATES = { state: UI_DEFAULT_TAX_RATES.state };

export function HomepagePortfolioCompare({
  funds,
}: {
  funds: FundEstimateView[];
}) {
  const catalog = useMemo(
    () =>
      funds.map((fund) => ({
        ticker: fund.ticker,
        fundName: fund.fundName,
        family: fund.family,
      })),
    [funds],
  );

  return (
    <section
      id="portfolio-compare"
      aria-label="Portfolio comparison"
      className="mt-4 scroll-mt-6 border-t border-line pt-10"
    >
      <PortfolioCompare
        funds={catalog}
        bookDollars={PORTFOLIO_COMPARE_BOOK_DOLLARS}
        taxRates={HOMEPAGE_TAX_RATES}
        // current/proposed omitted — GTM history-covered smoke books.
        headingAs="h2"
        onExport={(result, bookDollars) => {
          // Freemium gate stays stubbed on beta — export is available.
          exportToPdf(toPortfolioCompareExportModel(result, bookDollars));
        }}
      />
    </section>
  );
}
