import {
  lookupFund,
  PORTFOLIO_TICKER_RATES,
  ratesForTicker,
} from "@/lib/illustrate/portfolio-compare-catalog";
import type {
  PortfolioAllocationOut,
  PortfolioCompareRequest,
  PortfolioCompareResponse,
  PortfolioCompareSideIn,
  PortfolioDistributionRow,
  PortfolioFundOption,
  PortfolioGapOut,
  PortfolioHoldingIn,
  PortfolioHoldingOut,
} from "@/lib/illustrate/portfolio-compare-types";
import { PORTFOLIO_COMPARE_BOOK_DOLLARS } from "@/lib/illustrate/portfolio-compare-types";

const SUMMARY_HOLDING = 10_000;

function money(value: number): number {
  return Math.round(value * 100) / 100;
}

function rate(value: number): number {
  return Math.round(value * 1_000_000) / 1_000_000;
}

export function resolveHoldingDollars(
  holding: PortfolioHoldingIn,
  sideBook: number | null | undefined,
): number | null {
  if (holding.holding_dollars != null && holding.holding_dollars > 0) {
    return holding.holding_dollars;
  }
  if (holding.weight_pct == null || !(holding.weight_pct > 0)) return null;
  const book = sideBook ?? holding.book_dollars ?? null;
  if (book == null || !(book > 0)) return null;
  return (holding.weight_pct / 100) * book;
}

function tickerOf(holding: PortfolioHoldingIn): string {
  return (holding.ticker || holding.fund_identifier || "").trim().toUpperCase();
}

export function isPortfolioCompareRequestValid(body: PortfolioCompareRequest): string | null {
  if (!body.current?.holdings?.length) return "current.holdings is required";
  if (!body.proposed?.holdings?.length) return "proposed.holdings is required";

  for (const [sideName, side] of [
    ["current", body.current],
    ["proposed", body.proposed],
  ] as const) {
    for (const [index, holding] of side.holdings.entries()) {
      const hasLookup = Boolean(
        holding.ticker ||
          holding.fund_identifier ||
          holding.fund_name ||
          holding.distribution_ids?.length,
      );
      if (!hasLookup) {
        return `${sideName}.holdings[${index}] needs ticker and/or fund_identifier`;
      }
      const dollars = resolveHoldingDollars(holding, side.book_dollars);
      if (dollars == null || !(dollars > 0)) {
        return `${sideName}.holdings[${index}] needs holding_dollars, or weight_pct with book_dollars`;
      }
    }
  }
  return null;
}

function mockHoldingOut(
  holding: PortfolioHoldingIn,
  index: number,
  dollars: number,
  sideBook: number,
  funds: PortfolioFundOption[],
): PortfolioHoldingOut {
  const ticker = tickerOf(holding);
  const rates = ratesForTicker(ticker);
  const option = lookupFund(ticker, funds);
  const fundName =
    holding.fund_name || option?.fundName || rates.fundName || ticker;
  const family = holding.fund_family || option?.family || rates.family;
  const covered = Boolean(ticker) && (ticker in PORTFOLIO_TICKER_RATES || Boolean(option));
  const dist = money(dollars * rates.distRate);
  const upcomingTax = money(dist * rates.upcomingTaxRate);
  const tax = money(dollars * rates.taxDrag);
  const weightPct = sideBook > 0 ? (dollars / sideBook) * 100 : 0;
  const stage = rates.stage === "monthly" ? "monthly" : rates.stage;
  const yearEndDates =
    stage !== "monthly" && rates.asOf
      ? {
          record_date: addUtcDays(rates.asOf, 1),
          ex_date: addUtcDays(rates.asOf, 2),
          payable_date: addUtcDays(rates.asOf, 3),
        }
      : {
          record_date: null,
          ex_date: null,
          payable_date: null,
        };

  if (!covered) {
    return {
      holding_index: index,
      ticker: ticker || null,
      fund_identifier: ticker || null,
      fund_family: family || null,
      fund_name: fundName || null,
      holding_dollars: money(dollars),
      weight_pct: rate(weightPct),
      covered: false,
      warnings: [],
      gap_reason: family
        ? `${family} is not in the demo universe.`
        : "Ticker is not in the current universe.",
    };
  }

  return {
    holding_index: index,
    ticker,
    fund_identifier: ticker,
    fund_family: family || null,
    fund_name: fundName,
    holding_dollars: money(dollars),
    weight_pct: rate(weightPct),
    covered: true,
    publication_stage_used: stage,
    warnings: [],
    upcoming: {
      distribution_dollars: dist,
      estimated_tax: upcomingTax,
      as_of: rates.asOf,
      announced_date: rates.asOf,
      record_date: yearEndDates.record_date,
      ex_date: yearEndDates.ex_date,
      payable_date: yearEndDates.payable_date,
      publication_stage: stage,
    },
    distributions: mockDistributionEvents(dist, upcomingTax, rates.asOf, stage, yearEndDates),
    illustration: {
      totals: {
        distribution_dollars: dist,
        estimated_tax: tax,
        estimated_tax_dollars: tax,
        effective_tax_on_holding: dollars > 0 ? rate(tax / dollars) : 0,
      },
      components: [
        {
          distribution_dollars: dist,
          estimated_tax: upcomingTax,
          estimated_tax_dollars: upcomingTax,
          as_of: rates.asOf,
          announced_date: rates.asOf,
          record_date: yearEndDates.record_date,
          ex_date: yearEndDates.ex_date,
          payable_date: yearEndDates.payable_date,
          publication_stage: stage,
        },
      ],
    },
  };
}

function addUtcDays(iso: string, days: number): string {
  const date = new Date(`${iso}T00:00:00Z`);
  date.setUTCDate(date.getUTCDate() + days);
  return date.toISOString().slice(0, 10);
}

function mockDistributionEvents(
  dist: number,
  upcomingTax: number,
  asOf: string | null,
  stage: string,
  yearEndDates: {
    record_date: string | null;
    ex_date: string | null;
    payable_date: string | null;
  },
): PortfolioDistributionRow[] {
  const upcoming: PortfolioDistributionRow = {
    distribution_dollars: dist,
    estimated_tax: upcomingTax,
    as_of: asOf,
    announced_date: asOf,
    record_date: yearEndDates.record_date,
    ex_date: yearEndDates.ex_date,
    payable_date: yearEndDates.payable_date,
    publication_stage: stage,
  };
  if (stage === "monthly") return [upcoming];
  return [
    upcoming,
    {
      distribution_dollars: money(dist * 0.18),
      estimated_tax: money(upcomingTax * 0.18),
      as_of: "2026-08-12",
      announced_date: "2026-08-12",
      record_date: "2026-08-14",
      ex_date: "2026-08-15",
      payable_date: "2026-08-18",
      publication_stage: "paid",
    },
  ];
}

export function mockIllustratePortfolioSide(
  side: PortfolioCompareSideIn,
  fallbackLabel: string,
  funds: PortfolioFundOption[] = [],
): PortfolioAllocationOut {
  const book =
    side.book_dollars && side.book_dollars > 0
      ? side.book_dollars
      : PORTFOLIO_COMPARE_BOOK_DOLLARS;
  const holdings: PortfolioHoldingOut[] = [];
  const gaps: PortfolioGapOut[] = [];
  let coveredTax = 0;
  let coveredDist = 0;
  let dollarsCovered = 0;
  let dollarsUncovered = 0;
  let holdingsCovered = 0;
  let holdingsUncovered = 0;

  side.holdings.forEach((holding, index) => {
    const dollars = resolveHoldingDollars(holding, book);
    if (dollars == null || !(dollars > 0)) return;
    const out = mockHoldingOut(holding, index, dollars, book, funds);
    holdings.push(out);
    if (out.covered) {
      dollarsCovered += out.holding_dollars;
      holdingsCovered += 1;
      coveredTax += out.illustration?.totals?.estimated_tax ?? 0;
      coveredDist += (Array.isArray(out.upcoming) ? out.upcoming[0] : out.upcoming)
        ?.distribution_dollars ?? 0;
    } else {
      dollarsUncovered += out.holding_dollars;
      holdingsUncovered += 1;
      gaps.push({
        holding_index: index,
        ticker: out.ticker,
        fund_identifier: out.fund_identifier,
        fund_family: out.fund_family,
        fund_name: out.fund_name,
        holding_dollars: out.holding_dollars,
        reason: out.gap_reason ?? "Uncovered holding.",
      });
    }
  });

  const dollarsTotal = dollarsCovered + dollarsUncovered;
  const estimatedTax = money(coveredTax);
  const distributionDollars = money(coveredDist);
  const effective = dollarsCovered > 0 ? rate(estimatedTax / dollarsCovered) : 0;
  return {
    label: side.label?.trim() || fallbackLabel,
    holdings,
    totals: {
      distribution_dollars: distributionDollars,
      estimated_tax: estimatedTax,
      estimated_tax_dollars: estimatedTax,
      effective_tax_on_holding: effective,
    },
    coverage: {
      dollars_total: money(dollarsTotal),
      dollars_covered: money(dollarsCovered),
      dollars_uncovered: money(dollarsUncovered),
      coverage_pct: dollarsTotal ? rate((dollarsCovered / dollarsTotal) * 100) : 0,
      holdings_covered: holdingsCovered,
      holdings_uncovered: holdingsUncovered,
    },
    gaps,
    warnings: [
      "MOCK /illustrate/portfolio/compare — sample seed math, not the Data team service.",
    ],
    notes: [],
  };
}

function scaleToBook(value: number, book: number, common: number): number {
  if (!(book > 0)) return 0;
  return money(value * (common / book));
}

export function mockPortfolioCompareResponse(
  request: PortfolioCompareRequest,
  funds: PortfolioFundOption[] = [],
): PortfolioCompareResponse {
  const current = mockIllustratePortfolioSide(request.current, "Current Allocation", funds);
  const proposed = mockIllustratePortfolioSide(
    request.proposed,
    "Proposed Allocation",
    funds,
  );
  const estimatedTaxDelta = money(
    proposed.totals.estimated_tax - current.totals.estimated_tax,
  );
  const distDelta = money(
    proposed.totals.distribution_dollars - current.totals.distribution_dollars,
  );
  const dragDelta = rate(
    proposed.totals.effective_tax_on_holding - current.totals.effective_tax_on_holding,
  );
  const coverageDelta = rate(
    proposed.coverage.coverage_pct - current.coverage.coverage_pct,
  );
  const currentBook = current.coverage.dollars_total;
  const proposedBook = proposed.coverage.dollars_total;

  return {
    source: "mock",
    current,
    proposed,
    deltas: {
      estimated_tax: estimatedTaxDelta,
      distribution_dollars: distDelta,
      effective_tax_on_holding: dragDelta,
      coverage_pct: coverageDelta,
    },
    summary: {
      normalized_book_dollars: SUMMARY_HOLDING,
      estimated_tax: money(
        scaleToBook(proposed.totals.estimated_tax, proposedBook, SUMMARY_HOLDING) -
          scaleToBook(current.totals.estimated_tax, currentBook, SUMMARY_HOLDING),
      ),
      distribution_dollars: money(
        scaleToBook(proposed.totals.distribution_dollars, proposedBook, SUMMARY_HOLDING) -
          scaleToBook(current.totals.distribution_dollars, currentBook, SUMMARY_HOLDING),
      ),
      effective_tax_on_holding: dragDelta,
      coverage_pct: coverageDelta,
    },
    notes: [
      "Deltas are proposed − current on one shared snapshot. v1 has no periods[].",
      "Each side is a full POST /illustrate/portfolio result. Gaps stay on that side.",
      "MOCK /illustrate/portfolio/compare — sketch fixture so localhost still demos when the Data API is down.",
    ],
  };
}

export function synthesizePortfolioCompare(
  current: PortfolioAllocationOut,
  proposed: PortfolioAllocationOut,
  source: "mock" | "live" = "live",
): PortfolioCompareResponse {
  const estimatedTaxDelta = money(
    proposed.totals.estimated_tax - current.totals.estimated_tax,
  );
  const distDelta = money(
    proposed.totals.distribution_dollars - current.totals.distribution_dollars,
  );
  const dragDelta = rate(
    proposed.totals.effective_tax_on_holding - current.totals.effective_tax_on_holding,
  );
  const coverageDelta = rate(
    proposed.coverage.coverage_pct - current.coverage.coverage_pct,
  );
  return {
    source,
    current,
    proposed,
    deltas: {
      estimated_tax: estimatedTaxDelta,
      distribution_dollars: distDelta,
      effective_tax_on_holding: dragDelta,
      coverage_pct: coverageDelta,
    },
    summary: {
      normalized_book_dollars: SUMMARY_HOLDING,
      estimated_tax: estimatedTaxDelta,
      distribution_dollars: distDelta,
      effective_tax_on_holding: dragDelta,
      coverage_pct: coverageDelta,
    },
    notes: [
      "Synthesized from two POST /illustrate/portfolio calls (compare endpoint unavailable).",
      "Deltas are proposed − current. v1 has no periods[].",
    ],
  };
}
