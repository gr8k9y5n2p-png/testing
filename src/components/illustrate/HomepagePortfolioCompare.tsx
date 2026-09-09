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
        nav: fund.nav > 0 ? fund.nav : null,
      })),
    [funds],
  );

  return (
    <section id="portfolio-compare" aria-label="Portfolio comparison">
      <PortfolioCompare
        funds={catalog}
        bookDollars={PORTFOLIO_COMPARE_BOOK_DOLLARS}
        taxRates={HOMEPAGE_TAX_RATES}
        // current/proposed omitted — empty books; user path is + Add holding.
        headingAs="h1"
        onExport={(result, bookDollars) => {
          // Freemium gate stays stubbed on beta — export is available.
          exportToPdf(toPortfolioCompareExportModel(result, bookDollars));
        }}
      />
    </section>
  );
}
