"use client";

import { useMemo, useRef } from "react";
import type { FundEstimateView } from "@/data/types";
import { PortfolioCompare, type PortfolioCompareHandle } from "@/components/illustrate/PortfolioCompare";
import { PortfolioSaveOpenActions } from "@/components/illustrate/PortfolioSaveOpenActions";
import { NoticeToast, useNoticeToast } from "@/components/NoticeToast";
import {
  exportToPdf,
  toPortfolioCompareExportModel,
} from "@/lib/illustrate/portfolio-compare-export";
import { WEBSITE_PORTFOLIO_HOLDINGS } from "@/lib/illustrate/portfolio-compare-mount";
import { PORTFOLIO_COMPARE_BOOK_DOLLARS } from "@/lib/illustrate/portfolio-compare-types";
import { UI_DEFAULT_TAX_RATES } from "@/lib/illustrate/types";

const HOMEPAGE_TAX_RATES = UI_DEFAULT_TAX_RATES;

export function HomepagePortfolioCompare({
  funds,
}: {
  funds: FundEstimateView[];
}) {
  const booksApiRef = useRef<PortfolioCompareHandle | null>(null);
  const { notice, onNotice, dismissNotice } = useNoticeToast();
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
    <section id="portfolio-compare" aria-label="Portfolios">
      <PortfolioCompare
        funds={catalog}
        bookDollars={PORTFOLIO_COMPARE_BOOK_DOLLARS}
        taxRates={HOMEPAGE_TAX_RATES}
        current={WEBSITE_PORTFOLIO_HOLDINGS}
        proposed={WEBSITE_PORTFOLIO_HOLDINGS}
        headingAs="h1"
        booksApiRef={booksApiRef}
        headerActions={
          <PortfolioSaveOpenActions
            booksApiRef={booksApiRef}
            onNotice={onNotice}
          />
        }
        onExport={(result, bookDollars) => {
          // Freemium gate stays stubbed on beta — export is available.
          exportToPdf(
            toPortfolioCompareExportModel(
              result,
              bookDollars,
              new Set(catalog.map((fund) => fund.ticker.toUpperCase())),
            ),
          );
        }}
      />
      <NoticeToast message={notice} onDismiss={dismissNotice} />
    </section>
  );
}
