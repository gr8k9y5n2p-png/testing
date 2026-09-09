import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import type { FundEstimateView } from "../../data/types.ts";
import type { CompareIllustration, ComparePeriodOut, CompareResponse } from "./compare-types.ts";
import {
  COMPARE_DEFAULT_HOLDING_DOLLARS,
  COMPARE_SLOT_COUNT,
  compareTickersPath,
  buildCompareAnnualTable,
  compareSlotPlaceholder,
  emptyCompareSlots,
  filledCompareTickers,
  growthFundsFromSlots,
  padCompareSlots,
  parseCompareHoldingDollars,
  parseCompareQueryTickers,
  setCompareSlot,
  upcomingRowForCompareTicker,
  upcomingRowsFromCompareTickers,
} from "./compare-workspace.ts";

const here = dirname(fileURLToPath(import.meta.url));

function view(
  ticker: string,
  patch: Partial<FundEstimateView> = {},
): FundEstimateView {
  return {
    id: ticker.toLowerCase(),
    fundName: `${ticker} Fund`,
    ticker,
    cusip: "000000000",
    family: "American Funds",
    category: "Large Growth",
    shareClass: "Class A",
    nav: 41.22,
    estimatedDistributionAmount: 2.6,
    estimatedOrdinaryIncome: 0.5,
    estimatedCapitalGains: 2.1,
    estimatedDistributionPctNav: 6.4,
    publishedAt: "2026-09-05",
    asOfDate: "2026-08-29",
    recordDate: "2026-12-16",
    exDate: "2026-12-17",
    payableDate: "2026-12-18",
    publicationStage: "preliminary_estimate",
    bucket: "upcoming",
    paidHistory: [],
    distributionYear: 2026,
    categoryAveragePctNav: 6.4,
    vsCategoryPctNav: 0,
    ...patch,
  };
}

function side(
  label: string,
  matched: boolean,
  tax: number | null,
  dist: number | null,
): CompareIllustration {
  return {
    label,
    matched,
    holding_dollars: 10_000,
    totals: {
      distribution_dollars: dist,
      estimated_tax: tax,
      estimated_tax_dollars: tax,
      effective_tax_on_holding: tax == null ? null : tax / 10_000,
    },
  };
}

function period(
  year: number,
  left: CompareIllustration,
  right: CompareIllustration,
): ComparePeriodOut {
  return {
    year,
    left,
    right,
    deltas: {
      distribution_dollars: null,
      estimated_tax: null,
      effective_tax_on_holding: null,
    },
  };
}

function yoy(periods: ComparePeriodOut[]): CompareResponse {
  return {
    mode: "yoy",
    periods,
    summary: {
      normalized_holding_dollars: 10_000,
      total_tax_difference: 0,
      annualized_tax_drag_delta: 0,
      distribution_dollars_difference: 0,
      periods_compared: periods.length,
      common_inception: { from_year: 2022, to_year: 2026 },
    },
    notes: [],
  };
}

describe("compare workspace slots", () => {
  it("starts with six empty slots", () => {
    assert.deepEqual(emptyCompareSlots(), ["", "", "", "", "", ""]);
  });

  it("numbers placeholders from Ticker 1 with no extra chrome", () => {
    assert.equal(compareSlotPlaceholder(0), "Ticker 1");
    assert.equal(compareSlotPlaceholder(1), "Ticker 2");
    assert.equal(compareSlotPlaceholder(COMPARE_SLOT_COUNT - 1), "Ticker 6");
  });

  it("prefills unique tickers into the first slots only", () => {
    assert.deepEqual(padCompareSlots(["amcpx", "AMCPX", "agthx"]), [
      "AMCPX",
      "AGTHX",
      "",
      "",
      "",
      "",
    ]);
  });

  it("rejects a duplicate ticker in another slot", () => {
    const slots = padCompareSlots(["AMCPX"]);
    assert.deepEqual(setCompareSlot(slots, 1, "amcpx"), slots);
    assert.deepEqual(setCompareSlot(slots, 1, "AGTHX")[1], "AGTHX");
  });

  it("reads tickers from compare query params and builds deep-links", () => {
    assert.deepEqual(parseCompareQueryTickers({ tickers: "agthx" }), ["AGTHX"]);
    assert.deepEqual(parseCompareQueryTickers({ tickers: "AGTHX,amcpx dodix" }), [
      "AGTHX",
      "AMCPX",
      "DODIX",
    ]);
    assert.deepEqual(parseCompareQueryTickers({ tickers: ["AMCPX", "AGTHX"] }), [
      "AMCPX",
      "AGTHX",
    ]);
    assert.deepEqual(parseCompareQueryTickers({ ticker: "agthx", left: "AMCPX" }), [
      "AGTHX",
      "AMCPX",
    ]);
    assert.deepEqual(parseCompareQueryTickers({ left: "AMCPX", right: "AGTHX" }), [
      "AMCPX",
      "AGTHX",
    ]);
    assert.deepEqual(parseCompareQueryTickers({ tickers: "AGTHX,AGTHX,AMCPX" }), [
      "AGTHX",
      "AMCPX",
    ]);
    assert.deepEqual(parseCompareQueryTickers({}), []);
    assert.equal(compareTickersPath(["agthx"]), "/compare?tickers=AGTHX");
    assert.equal(compareTickersPath(["AGTHX", "AMCPX"]), "/compare?tickers=AGTHX,AMCPX");
    assert.equal(compareTickersPath([]), "/compare");
  });
});

describe("compare shared holding", () => {
  it("defaults to $10,000 and parses the shared dollars-invested field", () => {
    assert.equal(COMPARE_DEFAULT_HOLDING_DOLLARS, 10_000);
    assert.equal(parseCompareHoldingDollars("25000"), 25_000);
    assert.equal(parseCompareHoldingDollars("25,000"), 25_000);
    assert.equal(parseCompareHoldingDollars("$5,000.50"), 5_000.5);
    assert.equal(parseCompareHoldingDollars("", 12_000), 12_000);
    assert.equal(parseCompareHoldingDollars("0"), 10_000);
    assert.equal(parseCompareHoldingDollars("abc", 8_000), 8_000);
  });
});

describe("compare workspace slots (filled)", () => {
  it("clears a slot and drops it from the filled list", () => {
    const slots = setCompareSlot(padCompareSlots(["AMCPX", "AGTHX"]), 0, "");
    assert.deepEqual(filledCompareTickers(slots), ["AGTHX"]);
  });

  it("one filled slot is enough; empty slots are ignored", () => {
    const slots = padCompareSlots(["amcpx"]);
    assert.deepEqual(filledCompareTickers(slots), ["AMCPX"]);
    assert.equal(slots.filter((slot) => slot === "").length, 5);

    const growth = growthFundsFromSlots(slots, [view("AMCPX")]);
    assert.equal(growth.length, 1);
    assert.equal(growth[0]?.ticker, "AMCPX");

    const tax = yoy([
      period(2025, side("AMCPX", true, 88, 210), side("AMCPX", true, 88, 210)),
    ]);
    const model = buildCompareAnnualTable([{ ticker: "AMCPX", tax }], [2025]);
    assert.equal(model.groups.length, 1);
    assert.equal(model.groups[0]?.ticker, "AMCPX");
    assert.equal(model.groups[0]?.rows.length, 2);

    const upcoming = upcomingRowsFromCompareTickers([
      {
        ticker: "AMCPX",
        fund: view("AMCPX"),
        upcoming: { dollars: 185, announced: true, asOf: "2026-08-29" },
      },
    ]);
    assert.equal(upcoming.length, 1);
    assert.equal(upcoming[0]?.ticker, "AMCPX");
    assert.equal(upcoming[0]?.available, true);
  });
});

describe("compare annual table", () => {
  it("keeps unmatched years as N/A and matched published $0 as zero", () => {
    const tax = yoy([
      period(
        2024,
        side("AMCPX", true, 0, 0),
        side("AMCPX", true, 0, 0),
      ),
      period(
        2025,
        side("AMCPX", false, 0, 0),
        side("AMCPX", false, 0, 0),
      ),
    ]);
    const model = buildCompareAnnualTable([{ ticker: "AMCPX", tax }], [2025, 2024, 2023]);
    const taxRow = model.groups[0]?.rows.find((row) => row.kind === "tax");
    const distRow = model.groups[0]?.rows.find((row) => row.kind === "distribution");
    // YoY zip writes left onto year-1; unmatched 2025 stays N/A.
    assert.deepEqual(taxRow?.cells, [null, 0, 0]);
    assert.deepEqual(distRow?.cells, [null, 0, 0]);
  });

  it("does not invent a year when compare omitted that vintage pair", () => {
    const tax = yoy([
      period(2025, side("AGTHX", true, 88, 210), side("AGTHX", true, 88, 210)),
    ]);
    const model = buildCompareAnnualTable([{ ticker: "AGTHX", tax }], [2025, 2024, 2022]);
    assert.deepEqual(model.groups[0]?.rows[0]?.cells, [88, 88, null]);
    assert.deepEqual(model.groups[0]?.rows[1]?.cells, [210, 210, null]);
  });
});

describe("compare upcoming rows", () => {
  it("does not treat has_estimate-false YE as_of as Upcoming", () => {
    const row = upcomingRowForCompareTicker({
      ticker: "VFIAX",
      fund: view("VFIAX", {
        bucket: "upcoming",
        hasEstimate: false,
        publicationStage: null,
        asOfDate: "2025-12-24",
        publishedAt: "2025-12-24",
        recordDate: null,
        exDate: null,
        payableDate: null,
      }),
      upcoming: { dollars: null, announced: false, asOf: null },
      index: 0,
    });
    assert.equal(row.available, false);
    assert.equal(row.announcedDate, null);
    assert.equal(row.asOf, null);
    assert.equal(row.estimatedTax, null);
  });

  it("does not copy paid-history dates onto an unannounced ticker", () => {
    const paid = view("DODIX", {
      bucket: "paid_history",
      publicationStage: "paid",
      recordDate: "2024-12-16",
      exDate: "2024-12-17",
      payableDate: "2024-12-18",
    });
    const row = upcomingRowForCompareTicker({
      ticker: "DODIX",
      fund: paid,
      upcoming: { dollars: null, announced: false, asOf: null },
      index: 0,
    });
    assert.equal(row.available, false);
    assert.equal(row.recordDate, null);
    assert.equal(row.exDate, null);
    assert.equal(row.estimatedTax, null);
    assert.equal(row.distributionDollars, null);
  });

  it("keeps unpaid announced catalog dates and live upcoming tax dollars", () => {
    const row = upcomingRowForCompareTicker({
      ticker: "AMCPX",
      fund: view("AMCPX"),
      upcoming: {
        dollars: 185,
        announced: true,
        asOf: "2026-08-29",
        publicationStage: "preliminary_estimate",
      },
      index: 0,
    });
    assert.equal(row.available, true);
    assert.equal(row.estimatedTax, 185);
    assert.equal(row.recordDate, "2026-12-16");
    assert.equal(row.exDate, "2026-12-17");
    assert.equal(row.distributionDollars, null);
    assert.equal(row.pctOfNav, null);
    assert.equal(row.holdingDollars, null);
    assert.equal(row.navPerShare, 41.22);
  });

  it("never copies catalog Dist $ / % of NAV as manager prelims", () => {
    const source = readFileSync(join(here, "compare-workspace.ts"), "utf8");
    assert.match(source, /distributionDollars:\s*null/);
    assert.match(source, /pctOfNav:\s*null/);
    assert.doesNotMatch(source, /distributionDollars:\s*fund\??\./);
    assert.doesNotMatch(source, /pctOfNav:\s*fund\??\./);
    assert.doesNotMatch(source, /ticker === ["']ABALX["']/);
    const stage = readFileSync(join(here, "publication-stage.ts"), "utf8");
    assert.doesNotMatch(stage, /ticker === ["']ABALX["']/);
    assert.doesNotMatch(stage, /estimatedDistributionAmount/);
  });

  it("treats has_estimate-false finals as Undisclosed for every ticker, not only ABALX", () => {
    for (const ticker of ["ABALX", "VFIAX", "FXAIX", "DODIX"]) {
      const row = upcomingRowForCompareTicker({
        ticker,
        fund: view(ticker, {
          bucket: "paid",
          hasEstimate: false,
          publicationStage: "final",
          asOfDate: "2025-12-15",
          publishedAt: "2025-12-15",
          recordDate: "2025-12-16",
          exDate: "2025-12-17",
          payableDate: "2025-12-18",
          estimatedDistributionAmount: 1.25,
          estimatedDistributionPctNav: 2.4,
        }),
        upcoming: { dollars: null, announced: false, asOf: null },
        index: 0,
      });
      assert.equal(row.available, false, ticker);
      assert.equal(row.distributionDollars, null, ticker);
      assert.equal(row.pctOfNav, null, ticker);
      assert.equal(row.estimatedTax, null, ticker);
      assert.equal(row.recordDate, null, ticker);
    }
  });

  it("does not invent Dist $ or % of NAV from catalog prelims", () => {
    const row = upcomingRowForCompareTicker({
      ticker: "AMCPX",
      fund: view("AMCPX"),
      upcoming: {
        dollars: 185,
        announced: true,
        asOf: "2026-08-29",
        publicationStage: "preliminary_estimate",
      },
      holdingDollars: 10_000,
      index: 0,
    });
    assert.equal(row.holdingDollars, 10_000);
    assert.equal(row.distributionDollars, null);
    assert.equal(row.pctOfNav, null);
    assert.equal(row.navPerShare, 41.22);
    assert.equal(row.estimatedTax, 185);
  });
});

describe("Compare workspace Upcoming + NAV soft path", () => {
  it("surfaces Dist $ / % NAV / $ impact columns and prompts for missing NAV", () => {
    const workspace = readFileSync(
      join(here, "../../components/illustrate/CompareWorkspace.tsx"),
      "utf8",
    );
    const table = readFileSync(
      join(here, "../../components/illustrate/portfolio-compare/UpcomingTable.tsx"),
      "utf8",
    );
    const panel = readFileSync(
      join(here, "../../components/illustrate/IllustratePanel.tsx"),
      "utf8",
    );
    const results = readFileSync(
      join(here, "../../components/illustrate/IllustrationResults.tsx"),
      "utf8",
    );
    assert.match(workspace, /NeedFundPricePrompt/);
    assert.match(workspace, /isMissingNavError/);
    assert.match(workspace, /holdingDollars/);
    assert.match(table, /DIST_AMOUNT_COLUMN/);
    assert.match(table, /PCT_OF_NAV_COLUMN/);
    assert.match(table, /DOLLAR_IMPACT_COLUMN/);
    assert.match(table, /DistributionDateStrip/);
    assert.match(table, /showPayable=\{Boolean\(row\.payableDate\)\}/);
    assert.match(panel, /ENTER_NAV_COPY/);
    assert.match(panel, /isMissingNavError/);
    assert.match(results, /% of NAV/);
    assert.match(results, /\$ impact/);
    assert.doesNotMatch(results, /compact\n\s+showPayable=\{Boolean\(component\.payable_date\)\}/);
  });
});
