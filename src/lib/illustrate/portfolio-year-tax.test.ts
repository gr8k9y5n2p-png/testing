import assert from "node:assert/strict";
import { describe, it } from "node:test";
import type {
  PortfolioAllocationOut,
  PortfolioCompareResponse,
  PortfolioHoldingOut,
  PortfolioPeriodHoldingTax,
} from "./portfolio-compare-types.ts";
import { PORTFOLIO_COMPARE_YEARS, portfolioYearTaxRate } from "./portfolio-compare-years.ts";
import {
  calendarYearTaxTable,
  defaultPortfolioComparePeriods,
  ensurePortfolioComparePeriods,
  hasCalendarYearTax,
  periodHoldingTax,
} from "./portfolio-year-tax.ts";

function holding(
  patch: Partial<PortfolioHoldingOut> & { ticker: string },
): PortfolioHoldingOut {
  return {
    holding_index: 0,
    fund_identifier: patch.ticker,
    holding_dollars: 250_000,
    covered: true,
    warnings: [],
    ...patch,
  };
}

function emptyTotals() {
  return {
    distribution_dollars: 0,
    estimated_tax: 0,
    effective_tax_on_holding: 0,
  };
}

function allocation(
  label: string,
  holdings: PortfolioHoldingOut[],
): PortfolioAllocationOut {
  return {
    label,
    holdings,
    totals: emptyTotals(),
    coverage: {
      dollars_total: 1_000_000,
      dollars_covered: 1_000_000,
      dollars_uncovered: 0,
      coverage_pct: 100,
    },
    gaps: [],
    warnings: [],
  };
}

function tax(
  ticker: string,
  estimated_tax: number | null,
  matched = estimated_tax != null,
): PortfolioPeriodHoldingTax {
  return { ticker, matched, estimated_tax };
}

function resultForSmoke(): PortfolioCompareResponse {
  const years = [...PORTFOLIO_COMPARE_YEARS];
  const thick = (ticker: string, base: number) =>
    years.map((year, index) => tax(ticker, base + index * 25));
  return {
    current: allocation("Current Allocation", [
      holding({ ticker: "AGTHX" }),
      holding({ ticker: "DODIX", holding_index: 1 }),
      holding({ ticker: "AMCAP", holding_index: 2 }),
      holding({ ticker: "DODGX", holding_index: 3 }),
    ]),
    proposed: allocation("Proposed Allocation", [
      holding({ ticker: "AMCPX" }),
      holding({ ticker: "CGHM", holding_index: 1 }),
      holding({ ticker: "AGTHX", holding_index: 2 }),
      holding({ ticker: "AMCAP", holding_index: 3 }),
    ]),
    deltas: {
      estimated_tax: 1875,
      distribution_dollars: 0,
      effective_tax_on_holding: 0.0058,
      coverage_pct: 0,
    },
    summary: {
      normalized_book_dollars: 10_000,
      estimated_tax: 1875,
      distribution_dollars: 0,
      effective_tax_on_holding: 0.0058,
      coverage_pct: 0,
    },
    notes: [],
    periods: years.map((year, index) => ({
      year,
      current: [
        thick("AGTHX", 2050)[index],
        thick("DODIX", 3750)[index],
        thick("AMCAP", 4000)[index],
        thick("DODGX", 2600)[index],
      ],
      proposed: [
        thick("AMCPX", 4000)[index],
        tax("CGHM", null, false),
        thick("AGTHX", 2050)[index],
        thick("AMCAP", 4000)[index],
      ],
    })),
  };
}

describe("periodHoldingTax", () => {
  it("keeps unmatched years as N/A even when a zero is present", () => {
    assert.equal(periodHoldingTax(tax("CGHM", 0, false)), null);
    assert.equal(periodHoldingTax(tax("CGHM", null, false)), null);
  });

  it("keeps a matched published $0 as zero, not N/A", () => {
    assert.equal(periodHoldingTax(tax("DODIX", 0, true)), 0);
  });

  it("treats covered:false as N/A even when a zero is present", () => {
    assert.equal(
      periodHoldingTax({
        ticker: "CGHM",
        matched: true,
        estimated_tax: 0,
        covered: false,
      }),
      null,
    );
  });
});

describe("portfolioYearTaxRate smoke coverage", () => {
  it("covers GTM thick tickers 2021–2025 and leaves CGHM unmatched", () => {
    for (const ticker of ["AGTHX", "AMCAP", "AMCPX", "DODGX", "DODIX"] as const) {
      for (const year of PORTFOLIO_COMPARE_YEARS) {
        assert.notEqual(
          portfolioYearTaxRate(ticker, year),
          null,
          `${ticker} ${year}`,
        );
      }
    }
    for (const year of PORTFOLIO_COMPARE_YEARS) {
      assert.equal(portfolioYearTaxRate("CGHM", year), null);
    }
  });
});

describe("calendar-year tax table", () => {
  it("sends 2021–2025 periods by default and fills a missing 2025", () => {
    assert.deepEqual(
      defaultPortfolioComparePeriods().map((period) => period.year),
      [2021, 2022, 2023, 2024, 2025],
    );
    assert.deepEqual(
      ensurePortfolioComparePeriods([{ year: 2021 }, { year: 2024 }]).map(
        (period) => period.year,
      ),
      [2021, 2022, 2023, 2024, 2025],
    );
  });

  it("fills AGTHX/AMCAP/AMCPX/DODGX and DODIX 2021–2025; CGHM is N/A", () => {
    const model = calendarYearTaxTable(resultForSmoke());
    assert.deepEqual(model.years, [2025, 2024, 2023, 2022, 2021]);
    assert.equal(hasCalendarYearTax(model), true);

    const byTicker = (side: "current" | "proposed", ticker: string) =>
      model[side].find((row) => row.ticker === ticker);

    for (const ticker of ["AGTHX", "AMCAP", "DODGX", "DODIX"] as const) {
      const row = byTicker("current", ticker);
      assert.ok(row, ticker);
      assert.equal(row?.cells.length, 5);
      assert.ok(row?.cells.every((cell) => cell != null && cell > 0), ticker);
    }
    const amcpx = byTicker("proposed", "AMCPX");
    assert.ok(amcpx?.cells.every((cell) => cell != null && cell > 0));

    const cghm = byTicker("proposed", "CGHM");
    assert.deepEqual(cghm?.cells, [null, null, null, null, null]);
  });

  it("does not invent $0 when a year is missing from periods", () => {
    const book = resultForSmoke();
    book.periods = [
      {
        year: 2024,
        current: [tax("AGTHX", 2400, true)],
        proposed: [tax("AMCPX", 3000, true)],
      },
    ];
    const model = calendarYearTaxTable(book);
    const agthx = model.current.find((row) => row.ticker === "AGTHX");
    assert.deepEqual(model.years, [2025, 2024, 2023, 2022, 2021]);
    assert.deepEqual(agthx?.cells, [null, 2400, null, null, null]);
    assert.equal(agthx?.cells.includes(0), false);
  });

  it("keeps a 2025 column when Data only returns 2021–2024", () => {
    const book = resultForSmoke();
    book.periods = (book.periods ?? []).filter((period) => period.year !== 2025);
    const model = calendarYearTaxTable(book);
    assert.deepEqual(model.years, [2025, 2024, 2023, 2022, 2021]);
    const agthx = model.current.find((row) => row.ticker === "AGTHX");
    assert.equal(agthx?.cells.length, 5);
    assert.equal(agthx?.cells[0], null);
    assert.ok(agthx?.cells.slice(1).every((cell) => cell != null && cell > 0));
  });

  it("keeps one row per ticker even when the book repeats a holding", () => {
    const book = resultForSmoke();
    book.proposed.holdings.push(holding({ ticker: "AMCPX", holding_index: 4 }));
    const model = calendarYearTaxTable(book);
    assert.equal(model.proposed.filter((row) => row.ticker === "AMCPX").length, 1);
  });

  it("treats uncovered holdings as N/A across years, never $0", () => {
    const book = resultForSmoke();
    book.proposed.holdings = book.proposed.holdings.map((holding) =>
      holding.ticker === "CGHM"
        ? { ...holding, covered: false, gap_reason: "no history" }
        : holding,
    );
    book.periods = [
      {
        year: 2024,
        current: [tax("AGTHX", 2400, true)],
        proposed: [tax("CGHM", 0, true)],
      },
    ];
    const model = calendarYearTaxTable(book);
    const cghm = model.proposed.find((row) => row.ticker === "CGHM");
    assert.deepEqual(cghm?.cells, [null, null, null, null, null]);
    assert.equal(cghm?.cells.includes(0), false);
  });
});
