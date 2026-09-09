import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import {
  canComparePortfolioBooks,
  portfolioBookFilled,
} from "./portfolio-compare-books.ts";
import {
  EMPTY_BOOK_INVITE,
  PORTFOLIO_HEADING,
} from "./portfolio-compare-copy.ts";
import { isPortfolioCompareRequestValid } from "./portfolio-compare-request.ts";
import type {
  PortfolioAllocationOut,
  PortfolioCompareRequest,
  PortfolioCompareResponse,
  PortfolioHoldingOut,
} from "./portfolio-compare-types.ts";
import { PORTFOLIO_COMPARE_BOOK_DOLLARS } from "./portfolio-compare-types.ts";
import { PORTFOLIO_COMPARE_YEARS } from "./portfolio-compare-years.ts";
import { upcomingHoldingsForSide } from "./publication-stage.ts";
import { TAX_DRAG_NA_LABEL } from "./tax-drag-map.ts";
import { calendarYearTaxTable, hasCalendarYearTax } from "./portfolio-year-tax.ts";

const here = dirname(fileURLToPath(import.meta.url));

function read(relative: string): string {
  return readFileSync(join(here, relative), "utf8");
}

function book(
  ticker: string,
  label: string,
): PortfolioCompareRequest["current"] {
  return {
    label,
    book_dollars: PORTFOLIO_COMPARE_BOOK_DOLLARS,
    holdings: [
      {
        ticker,
        fund_identifier: ticker,
        weight_pct: 100,
        book_dollars: PORTFOLIO_COMPARE_BOOK_DOLLARS,
      },
    ],
  };
}

function emptyBook(label: string): PortfolioCompareRequest["current"] {
  return {
    label,
    book_dollars: PORTFOLIO_COMPARE_BOOK_DOLLARS,
    holdings: [],
  };
}

function holdingOut(
  ticker: string,
  patch: Partial<PortfolioHoldingOut> = {},
): PortfolioHoldingOut {
  return {
    holding_index: 0,
    ticker,
    fund_identifier: ticker,
    fund_name: ticker,
    holding_dollars: PORTFOLIO_COMPARE_BOOK_DOLLARS,
    weight_pct: 100,
    covered: true,
    warnings: [],
    upcoming: {
      publication_stage: "preliminary_estimate",
      distribution_dollars: 19_400,
      estimated_tax: 6_790,
      as_of: "2026-12-15",
      announced_date: "2026-12-15",
      record_date: "2026-12-16",
      ex_date: "2026-12-17",
      payable_date: "2026-12-18",
    },
    paid_history: [
      {
        publication_stage: "paid",
        distribution_dollars: 3_492,
        estimated_tax: 1_222,
        as_of: "2026-08-12",
        announced_date: "2026-08-12",
        record_date: "2026-08-14",
        ex_date: "2026-08-15",
        payable_date: "2026-08-18",
      },
    ],
    ...patch,
  };
}

function allocation(
  label: string,
  holdings: PortfolioHoldingOut[],
  tax = holdings.length ? 6_800 : 0,
): PortfolioAllocationOut {
  return {
    label,
    holdings,
    totals: {
      distribution_dollars: holdings.length ? 19_400 : 0,
      estimated_tax: tax,
      effective_tax_on_holding: holdings.length ? 0.0068 : 0,
    },
    coverage: {
      dollars_total: holdings.length ? PORTFOLIO_COMPARE_BOOK_DOLLARS : 0,
      dollars_covered: holdings.length ? PORTFOLIO_COMPARE_BOOK_DOLLARS : 0,
      dollars_uncovered: 0,
      coverage_pct: holdings.length ? 100 : 0,
    },
    gaps: [],
    warnings: [],
  };
}

function periodTax(ticker: string, estimated_tax: number) {
  return { ticker, matched: true as const, estimated_tax };
}

function resultFor(
  currentHoldings: PortfolioHoldingOut[],
  proposedHoldings: PortfolioHoldingOut[],
): PortfolioCompareResponse {
  const current = allocation("Current Allocation", currentHoldings, 6_800);
  const proposed = allocation("Proposed Allocation", proposedHoldings, 4_200);
  const years = [...PORTFOLIO_COMPARE_YEARS];
  return {
    current,
    proposed,
    deltas: {
      estimated_tax: proposed.totals.estimated_tax - current.totals.estimated_tax,
      distribution_dollars: 0,
      effective_tax_on_holding: 0,
      coverage_pct: 0,
    },
    summary: {
      normalized_book_dollars: 10_000,
      estimated_tax: proposed.totals.estimated_tax - current.totals.estimated_tax,
      distribution_dollars: 0,
      effective_tax_on_holding: 0,
      coverage_pct: 0,
    },
    notes: [],
    periods: years.map((year) => ({
      year,
      current: currentHoldings.map((row) =>
        periodTax(row.ticker || "—", 2_000 + year),
      ),
      proposed: proposedHoldings.map((row) =>
        periodTax(row.ticker || "—", 1_500 + year),
      ),
    })),
  };
}

describe("PortfolioCompare single-book fetch gate", () => {
  it("unlocks fetch when either book has a weighted holding", () => {
    const compare = read("../../components/illustrate/PortfolioCompare.tsx");
    assert.match(compare, /const currentFilled = currentApi\.length > 0/);
    assert.match(compare, /const proposedFilled = proposedApi\.length > 0/);
    assert.match(compare, /const canFetch = currentFilled \|\| proposedFilled/);
    assert.doesNotMatch(
      compare,
      /const canFetch = currentApi\.length > 0 && proposedApi\.length > 0/,
    );
    assert.doesNotMatch(compare, /on each side with \+ Add holding/);
    assert.match(compare, /Add at least one weighted holding with \+ Add holding/);
    assert.match(compare, /EmptyBookUpcoming/);
    assert.match(compare, /EMPTY_BOOK_INVITE/);
    const fixture = read("portfolio-compare-fixture.ts");
    const request = read("portfolio-compare-request.ts");
    const client = read("portfolio-compare-client.ts");
    assert.match(request, /current\.holdings or proposed\.holdings is required/);
    assert.doesNotMatch(request, /if \(!body\.current\?\.holdings\?\.length\)/);
    assert.match(fixture, /export \{ isPortfolioCompareRequestValid, resolveHoldingDollars \}/);
    assert.match(client, /request\.current\.holdings\.length > 0/);
    assert.match(client, /request\.proposed\.holdings\.length > 0/);
    assert.match(client, /mockIllustratePortfolioSide/);
  });

  it("titles Modules-owned UI Portfolio, not Portfolio comparison", () => {
    const compare = read("../../components/illustrate/PortfolioCompare.tsx");
    const homepage = read("../../components/illustrate/HomepagePortfolioCompare.tsx");
    const exported = read("portfolio-compare-export.ts");
    assert.match(compare, /PORTFOLIO_HEADING/);
    assert.doesNotMatch(compare, /Portfolio comparison/);
    assert.match(homepage, /aria-label="Portfolio"/);
    assert.doesNotMatch(homepage, /Portfolio comparison/);
    assert.match(exported, /title: PORTFOLIO_HEADING/);
    assert.doesNotMatch(exported, /title: "Portfolio comparison"/);
    assert.equal(PORTFOLIO_HEADING, "Portfolio");
  });
});

describe("single-book Current-only", () => {
  it("validates and illustrates Current without a Proposed book", () => {
    const request: PortfolioCompareRequest = {
      current: book("AGTHX", "Current Allocation"),
      proposed: emptyBook("Proposed Allocation"),
    };
    assert.equal(isPortfolioCompareRequestValid(request), null);

    const result = resultFor([holdingOut("AGTHX")], []);
    assert.equal(portfolioBookFilled(result.current), true);
    assert.equal(portfolioBookFilled(result.proposed), false);
    assert.equal(canComparePortfolioBooks(result), false);

    const upcoming = upcomingHoldingsForSide(result.current, "current");
    assert.ok(upcoming.length > 0, "Current Upcoming must come from the filled book");
    assert.equal(upcoming[0]?.ticker, "AGTHX");
    assert.equal(upcoming[0]?.available, true);
    assert.equal(upcoming.some((row) => row.bucket === "paid_history"), false);
    assert.equal(upcomingHoldingsForSide(result.proposed, "proposed").length, 0);

    const yearTax = calendarYearTaxTable(result);
    assert.equal(hasCalendarYearTax(yearTax), true);
    assert.equal(yearTax.current.length, 1);
    assert.equal(yearTax.current[0]?.ticker, "AGTHX");
    assert.ok(yearTax.current[0]?.cells.some((cell) => cell != null && cell > 0));
    assert.deepEqual(yearTax.proposed, []);
  });
});

describe("single-book Proposed-only", () => {
  it("validates and illustrates Proposed without a Current book", () => {
    const request: PortfolioCompareRequest = {
      current: emptyBook("Current Allocation"),
      proposed: book("AMCPX", "Proposed Allocation"),
    };
    assert.equal(isPortfolioCompareRequestValid(request), null);

    const result = resultFor([], [holdingOut("AMCPX")]);
    assert.equal(portfolioBookFilled(result.proposed), true);
    assert.equal(portfolioBookFilled(result.current), false);
    assert.equal(canComparePortfolioBooks(result), false);

    const upcoming = upcomingHoldingsForSide(result.proposed, "proposed");
    assert.ok(upcoming.length > 0, "Proposed Upcoming must come from the filled book");
    assert.equal(upcoming[0]?.ticker, "AMCPX");
    assert.equal(upcoming[0]?.available, true);
    assert.equal(upcoming.some((row) => row.bucket === "paid_history"), false);
    assert.equal(upcomingHoldingsForSide(result.current, "current").length, 0);

    const yearTax = calendarYearTaxTable(result);
    assert.equal(hasCalendarYearTax(yearTax), true);
    assert.equal(yearTax.proposed.length, 1);
    assert.equal(yearTax.proposed[0]?.ticker, "AMCPX");
    assert.ok(yearTax.proposed[0]?.cells.some((cell) => cell != null && cell > 0));
    assert.deepEqual(yearTax.current, []);
  });
});

describe("single-book still compares two filled books", () => {
  it("keeps proposed − current deltas when both books have holdings", () => {
    const request: PortfolioCompareRequest = {
      current: book("AGTHX", "Current Allocation"),
      proposed: book("AMCPX", "Proposed Allocation"),
    };
    assert.equal(isPortfolioCompareRequestValid(request), null);

    const result = resultFor([holdingOut("AGTHX")], [holdingOut("AMCPX")]);
    assert.equal(canComparePortfolioBooks(result), true);
    assert.equal(result.current.holdings.length, 1);
    assert.equal(result.proposed.holdings.length, 1);
    assert.equal(
      result.deltas.estimated_tax,
      result.proposed.totals.estimated_tax - result.current.totals.estimated_tax,
    );

    const yearTax = calendarYearTaxTable(result);
    assert.equal(yearTax.current[0]?.ticker, "AGTHX");
    assert.equal(yearTax.proposed[0]?.ticker, "AMCPX");
    assert.equal(upcomingHoldingsForSide(result.current, "current")[0]?.ticker, "AGTHX");
    assert.equal(upcomingHoldingsForSide(result.proposed, "proposed")[0]?.ticker, "AMCPX");
  });

  it("still rejects two empty books", () => {
    assert.equal(
      isPortfolioCompareRequestValid({
        current: emptyBook("Current Allocation"),
        proposed: emptyBook("Proposed Allocation"),
      }),
      "current.holdings or proposed.holdings is required",
    );
  });
});

describe("single-book empty-opposite copy", () => {
  it("invites Add holding on the empty book instead of inventing Upcoming", () => {
    const compare = read("../../components/illustrate/PortfolioCompare.tsx");
    const strip = read("../../components/illustrate/portfolio-compare/SummaryStrip.tsx");
    const exported = read("portfolio-compare-export.ts");
    assert.match(compare, /EMPTY_BOOK_INVITE/);
    assert.equal(EMPTY_BOOK_INVITE, "No holdings yet — use + Add holding to start.");
    assert.notEqual(EMPTY_BOOK_INVITE, "Not available / undisclosed");
    assert.match(strip, /canComparePortfolioBooks/);
    assert.match(strip, /TAX_DRAG_NA_LABEL/);
    assert.match(strip, /SINGLE_BOOK_DELTA_DETAIL/);
    assert.match(exported, /SINGLE_BOOK_DELTA_DETAIL/);
    assert.equal(TAX_DRAG_NA_LABEL, "N/A");
  });
});
