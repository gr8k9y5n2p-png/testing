"use client";

import { useRef } from "react";
import { PortfolioCompare, type PortfolioCompareHandle } from "@/components/illustrate/PortfolioCompare";
import { PortfolioSaveOpenActions } from "@/components/illustrate/PortfolioSaveOpenActions";
import { NoticeToast, useNoticeToast } from "@/components/NoticeToast";
import { catalogFunds } from "@/lib/illustrate/portfolio-compare-catalog";
import { universeTickersFromHoldings } from "@/lib/illustrate/portfolio-compare-identity";
import {
  exportToPdf,
  toPortfolioCompareExportModel,
} from "@/lib/illustrate/portfolio-compare-export";
import { WEBSITE_PORTFOLIO_HOLDINGS } from "@/lib/illustrate/portfolio-compare-mount";
import { PORTFOLIO_COMPARE_BOOK_DOLLARS } from "@/lib/illustrate/portfolio-compare-types";
import { UI_DEFAULT_TAX_RATES } from "@/lib/illustrate/types";

const HOMEPAGE_TAX_RATES = UI_DEFAULT_TAX_RATES;

export function HomepagePortfolioCompare() {
  const booksApiRef = useRef<PortfolioCompareHandle | null>(null);
  const { notice, onNotice, dismissNotice } = useNoticeToast();

  return (
    <section id="portfolio-compare" aria-label="Portfolios">
      <PortfolioCompare
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
          // Export stays available; the soft-wall blurs painted modules.
          const books = booksApiRef.current?.getBooks();
          exportToPdf(
            toPortfolioCompareExportModel(
              result,
              bookDollars,
              universeTickersFromHoldings(
                [...(books?.current ?? []), ...(books?.proposed ?? [])],
                catalogFunds().map((fund) => fund.ticker),
              ),
            ),
          );
        }}
      />
      <NoticeToast message={notice} onDismiss={dismissNotice} />
    </section>
  );
}
