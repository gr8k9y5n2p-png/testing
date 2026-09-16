"use client";

import { useMemo, useRef } from "react";
import type { FundEstimateView } from "@/data/types";
import { PortfolioCompare, type PortfolioCompareHandle } from "@/components/illustrate/PortfolioCompare";
import { SavedAssetActions } from "@/components/saved-assets/SavedAssetActions";
import {
  exportToPdf,
  toPortfolioCompareExportModel,
} from "@/lib/illustrate/portfolio-compare-export";
import { WEBSITE_PORTFOLIO_HOLDINGS } from "@/lib/illustrate/portfolio-compare-mount";
import { PORTFOLIO_COMPARE_BOOK_DOLLARS } from "@/lib/illustrate/portfolio-compare-types";
import { UI_DEFAULT_TAX_RATES } from "@/lib/illustrate/types";
import {
  parsePortfolioBooksPayload,
  toPortfolioAssetPayload,
} from "@/lib/saved-assets/payloads";

const HOMEPAGE_TAX_RATES = UI_DEFAULT_TAX_RATES;

export function HomepagePortfolioCompare({
  funds,
}: {
  funds: FundEstimateView[];
}) {
  const booksApiRef = useRef<PortfolioCompareHandle | null>(null);
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
          <SavedAssetActions
            type="portfolio"
            canSave={() => {
              const books = booksApiRef.current?.getBooks();
              return Boolean(
                books?.current.some((row) => row.ticker.trim()) ||
                  books?.proposed.some((row) => row.ticker.trim()),
              );
            }}
            getPayload={() =>
              toPortfolioAssetPayload(
                booksApiRef.current?.getBooks() ?? {
                  bookDollars: PORTFOLIO_COMPARE_BOOK_DOLLARS,
                  current: [],
                  proposed: [],
                  currentUnit: "pct",
                  proposedUnit: "pct",
                },
              )
            }
            onOpen={(asset) => {
              const books = parsePortfolioBooksPayload(asset.payload);
              if (!books) return;
              booksApiRef.current?.setBooks(books);
            }}
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
    </section>
  );
}
