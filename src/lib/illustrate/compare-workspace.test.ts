import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import type { FundEstimateView } from "../../data/types.ts";
import {
  COMPARE_DEFAULT_COMBINE_STATE,
  COMPARE_DEFAULT_HOLDING_DOLLARS,
  COMPARE_DEFAULT_TAX_RATES,
  COMPARE_SLOT_COUNT,
  compareTickersPath,
  compareInputsMatch,
  compareSlotPlaceholder,
  emptyCompareSlots,
  filledCompareTickers,
  growthFundsFromSlots,
  padCompareSlots,
  parseCompareHoldingDollars,
  parseCompareQueryTickers,
  setCompareSlot,
  taxRatesEqual,
  upcomingRowForCompareTicker,
  upcomingRowsFromCompareTickers,
} from "./compare-workspace.ts";
import { UI_DEFAULT_TAX_RATES } from "./types.ts";

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

describe("compare shared tax rates", () => {
  it("defaults to the locked Dollar Illustration top-bracket set", () => {
    assert.deepEqual(COMPARE_DEFAULT_TAX_RATES, UI_DEFAULT_TAX_RATES);
    assert.equal(COMPARE_DEFAULT_COMBINE_STATE, true);
    assert.equal(UI_DEFAULT_TAX_RATES.ordinary_income, 0.37);
    assert.equal(UI_DEFAULT_TAX_RATES.long_term_capital_gains, 0.2);
    assert.equal(UI_DEFAULT_TAX_RATES.short_term_capital_gains, 0.37);
    assert.equal(UI_DEFAULT_TAX_RATES.qualified_dividend, 0.2);
    assert.equal(UI_DEFAULT_TAX_RATES.state, 0.05);
    assert.equal(taxRatesEqual(COMPARE_DEFAULT_TAX_RATES, UI_DEFAULT_TAX_RATES), true);
    assert.equal(
      taxRatesEqual(COMPARE_DEFAULT_TAX_RATES, { ...UI_DEFAULT_TAX_RATES, state: 0 }),
      false,
    );
  });

  it("treats a rate or holding edit as a stale calendar-year fetch", () => {
    const loaded = {
      holdingDollars: 10_000,
      taxRates: UI_DEFAULT_TAX_RATES,
      combine: true,
    };
    assert.equal(
      compareInputsMatch(loaded, 10_000, UI_DEFAULT_TAX_RATES, true),
      true,
    );
    assert.equal(
      compareInputsMatch(loaded, 25_000, UI_DEFAULT_TAX_RATES, true),
      false,
    );
    assert.equal(
      compareInputsMatch(
        loaded,
        10_000,
        { ...UI_DEFAULT_TAX_RATES, ordinary_income: 0.24 },
        true,
      ),
      false,
    );
    assert.equal(
      compareInputsMatch(loaded, 10_000, UI_DEFAULT_TAX_RATES, false),
      false,
    );
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
    assert.equal(row.distributionPerShare, null);
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
    assert.equal(row.distributionPerShare, 2.6);
    assert.equal(row.distributionDollars, null);
    assert.ok(row.pctOfNav != null);
    assert.equal(Number(row.pctOfNav?.toFixed(2)), 6.31);
    assert.equal(row.holdingDollars, null);
    assert.equal(row.navPerShare, 41.22);
  });

  it("uses unpaid manager $/share only and never copies paid/final catalog amounts", () => {
    const source = readFileSync(join(here, "compare-workspace.ts"), "utf8");
    assert.match(source, /catalogUpcoming && fund && Number.isFinite\(fund\.estimatedDistributionAmount\)/);
    assert.match(source, /upcomingPctOfNavFromPerShare/);
    assert.match(source, /Do not use `isUpcomingFund`/);
    assert.doesNotMatch(source, /!isUpcomingFund\(fund\)/);
    assert.doesNotMatch(source, /estimatedDistributionPctNav/);
    assert.doesNotMatch(source, /ticker === ["'][A-Z0-9]+["']/);
    const stage = readFileSync(join(here, "publication-stage.ts"), "utf8");
    assert.match(stage, /pctOfNavForUnpaidOrPaid/);
    assert.match(stage, /nav_on_distribution_day/);
    assert.doesNotMatch(stage, /ticker === ["'][A-Z0-9]+["']/);
  });

  it("treats has_estimate-false finals as Awaiting Estimate for every in-universe ticker, not only ABALX", () => {
    for (const ticker of ["ABALX", "VFIAX", "FXAIX", "DODIX", "ZZZZX"]) {
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
      assert.equal(row.inUniverse, true, ticker);
      assert.equal(row.distributionDollars, null, ticker);
      assert.equal(row.distributionPerShare, null, ticker);
      assert.equal(row.pctOfNav, null, ticker);
      assert.equal(row.estimatedTax, null, ticker);
      assert.equal(row.recordDate, null, ticker);
    }
  });

  it("marks a Compare ticker with no catalog fund as not in universe", () => {
    const row = upcomingRowForCompareTicker({
      ticker: "ZZZZY",
      fund: null,
      upcoming: { dollars: null, announced: false, asOf: null },
      index: 0,
    });
    assert.equal(row.available, false);
    assert.equal(row.inUniverse, false);
    assert.equal(row.distributionDollars, null);
    assert.equal(row.estimatedTax, null);
  });

  it("builds Upcoming rows from filled slots before tax loads", () => {
    const rows = upcomingRowsFromCompareTickers([
      { ticker: "ZZZZY", fund: null, upcoming: null },
    ]);
    assert.equal(rows.length, 1);
    assert.equal(rows[0]?.ticker, "ZZZZY");
    assert.equal(rows[0]?.inUniverse, false);
    assert.equal(rows[0]?.available, false);
  });

  it("moves catalog Upcoming to Paid History when ex-date has passed, including $0", () => {
    const afterEx = upcomingRowForCompareTicker({
      ticker: "ZEROX",
      fund: view("ZEROX", {
        estimatedDistributionAmount: 0,
        estimatedOrdinaryIncome: 0,
        estimatedCapitalGains: 0,
        estimatedDistributionPctNav: 0,
        hasEstimate: false,
        bucket: "paid",
        recordDate: "2026-09-01",
        exDate: "2026-09-02",
        payableDate: "2026-12-18",
      }),
      upcoming: {
        dollars: 0,
        announced: true,
        asOf: "2026-08-12",
        publicationStage: "preliminary_estimate",
      },
      index: 0,
    });
    assert.equal(afterEx.available, false);
    assert.equal(afterEx.distributionPerShare, null);
    assert.equal(afterEx.recordDate, null);

    const beforeEx = upcomingRowForCompareTicker({
      ticker: "ZEROX",
      fund: view("ZEROX", {
        estimatedDistributionAmount: 0,
        estimatedOrdinaryIncome: 0,
        estimatedCapitalGains: 0,
        estimatedDistributionPctNav: 0,
        hasEstimate: false,
        bucket: "paid",
        recordDate: "2026-09-01",
        exDate: "2026-09-15",
        payableDate: "2026-12-18",
      }),
      upcoming: { dollars: null, announced: false, asOf: null },
      holdingDollars: 10_000,
      index: 0,
    });
    assert.equal(beforeEx.available, true);
    assert.equal(beforeEx.distributionPerShare, 0);
    assert.equal(beforeEx.exDate, "2026-09-15");
  });

  it("keeps unpaid manager-announced $0 after hydrate treats zeros as not Upcoming", () => {
    const row = upcomingRowForCompareTicker({
      ticker: "ZEROX",
      fund: view("ZEROX", {
        estimatedDistributionAmount: 0,
        estimatedOrdinaryIncome: 0,
        estimatedCapitalGains: 0,
        estimatedDistributionPctNav: 0,
        hasEstimate: false,
        bucket: "paid",
      }),
      upcoming: { dollars: null, announced: false, asOf: null },
      holdingDollars: 10_000,
      index: 0,
    });
    assert.equal(row.available, true);
    assert.equal(row.distributionPerShare, 0);
    assert.equal(row.distributionDollars, 0);
    assert.equal(row.pctOfNav, 0);
    assert.equal(row.recordDate, "2026-12-16");
    assert.equal(row.exDate, "2026-12-17");
    assert.equal(row.ordinaryPerShare, 0);
    assert.equal(row.capitalGainsPerShare, 0);
  });

  it("locks FCPGX Upcoming % of NAV to Dist $/share ÷ weekly NAV", () => {
    const row = upcomingRowForCompareTicker({
      ticker: "FCPGX",
      fund: view("FCPGX", {
        estimatedDistributionAmount: 7.277,
        estimatedDistributionPctNav: 12,
        nav: 42.94,
        navOnDistributionDay: 37.09,
        publicationStage: "preliminary_estimate",
        bucket: "upcoming",
      }),
      upcoming: {
        dollars: 185,
        announced: true,
        asOf: "2026-08-29",
        publicationStage: "preliminary_estimate",
      },
      index: 0,
    });
    assert.equal(row.available, true);
    assert.equal(row.bucket, "upcoming");
    assert.equal(row.distributionPerShare, 7.277);
    assert.equal(row.navPerShare, 42.94);
    assert.equal(row.navOnDistributionDay, null);
    assert.equal(Number(row.pctOfNav?.toFixed(1)), 16.9);
    assert.notEqual(
      Number(row.pctOfNav?.toFixed(1)),
      Number((((7.277 / 37.09) * 100).toFixed(1))),
      "Upcoming must not use nav_on_distribution_day",
    );
    assert.notEqual(Number(row.pctOfNav?.toFixed(1)), 12, "never manager percent_of_nav");
  });

  it("computes Dist $ and % of NAV from unpaid $/share ÷ weekly NAV", () => {
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
    assert.equal(row.distributionPerShare, 2.6);
    assert.equal(row.navPerShare, 41.22);
    assert.ok(row.distributionDollars != null);
    assert.equal(Math.round(row.distributionDollars ?? 0), Math.round(2.6 * (10_000 / 41.22)));
    assert.equal(Number(row.pctOfNav?.toFixed(2)), 6.31);
    assert.equal(row.estimatedTax, 185);
  });
});

describe("Compare workspace Upcoming + NAV soft path", () => {
  it("locks Upcoming / Announced six columns and prompts for missing NAV", () => {
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
    assert.doesNotMatch(workspace, /CompareAnnualTable/);
    assert.doesNotMatch(workspace, /Calendar-year history is unavailable/);
    assert.doesNotMatch(workspace, /Calendar-year tax & distributions/);
    assert.match(table, /DIST_AMOUNT_COLUMN/);
    assert.match(table, /PCT_OF_NAV_COLUMN/);
    assert.match(table, /DOLLAR_IMPACT_COLUMN/);
    assert.match(table, /ANNOUNCED_COLUMN/);
    assert.match(table, /RECORD_COLUMN/);
    assert.match(table, /EX_COLUMN/);
    assert.match(table, /taxRates/);
    assert.match(table, /combineStateWithFederal/);
    assert.doesNotMatch(table, /DistributionDateStrip/);
    assert.doesNotMatch(table, /showPayable/);
    assert.match(panel, /illustrationRequestNav/);
    assert.match(panel, /perShareNavError/);
    assert.match(panel, /isMissingNavError/);
    assert.match(results, /% of NAV/);
    assert.match(results, /\$ impact/);
    assert.doesNotMatch(results, /compact\n\s+showPayable=\{Boolean\(component\.payable_date\)\}/);
  });

  it("wires editable Dollar Illustration rates into Compare fetches", () => {
    const workspace = readFileSync(
      join(here, "../../components/illustrate/CompareWorkspace.tsx"),
      "utf8",
    );
    const fields = readFileSync(
      join(here, "../../components/illustrate/TaxRateFields.tsx"),
      "utf8",
    );
    const request = readFileSync(join(here, "compare-request.ts"), "utf8");
    const load = readFileSync(join(here, "growth-tax-load.ts"), "utf8");
    const growth = readFileSync(
      join(here, "../../components/illustrate/GrowthAndTaxDragModule.tsx"),
      "utf8",
    );
    assert.match(workspace, /TaxRateFields/);
    assert.match(workspace, /COMPARE_DEFAULT_TAX_RATES/);
    assert.match(workspace, /taxRates/);
    assert.match(workspace, /combineStateWithFederal/);
    assert.match(workspace, /<TaxRateFields[\s\S]*compact/);
    assert.doesNotMatch(workspace, /tax_rates:\s*\{\}/);
    assert.doesNotMatch(request, /tax_rates:\s*\{\}/);
    assert.doesNotMatch(load, /tax_rates:\s*\{\}/);
    const rail = readFileSync(
      join(here, "../../components/illustrate/FundCompareRail.tsx"),
      "utf8",
    );
    const homepage = readFileSync(
      join(here, "../../components/illustrate/HomepagePortfolioCompare.tsx"),
      "utf8",
    );
    const card = readFileSync(
      join(here, "../../components/illustrate/FundTaxDeltaCompare.tsx"),
      "utf8",
    );
    assert.doesNotMatch(rail, /\{ state: UI_DEFAULT_TAX_RATES\.state \}/);
    assert.doesNotMatch(homepage, /\{ state: UI_DEFAULT_TAX_RATES\.state \}/);
    assert.doesNotMatch(card, /tax_rates: next\.taxRates \?\? \{\}/);
    const fundDemo = readFileSync(join(here, "../../app/fund-compare/page.tsx"), "utf8");
    const portfolioDemo = readFileSync(
      join(here, "../../app/portfolio-compare/page.tsx"),
      "utf8",
    );
    assert.doesNotMatch(fundDemo, /taxRates=\{\{ state:/);
    assert.doesNotMatch(portfolioDemo, /taxRates=\{\{ state:/);
    assert.match(card, /compareTaxRequestFields/);
    assert.match(growth, /taxRates/);
    assert.match(growth, /combineStateWithFederal/);
    assert.match(fields, /Federal ordinary income/);
    assert.match(fields, /Federal LTCG/);
    assert.match(fields, /Federal STCG/);
    assert.match(fields, /Qualified dividend \(QDI\)/);
    assert.match(fields, /label="State"/);
    assert.match(fields, /Combine state with federal \(effective rate = federal \+ state\)/);
  });

  it("does not mount Compare pair-Δ / Delta Strip chrome", () => {
    const workspace = readFileSync(
      join(here, "../../components/illustrate/CompareWorkspace.tsx"),
      "utf8",
    );
    const barrel = readFileSync(
      join(here, "../../components/illustrate/index.ts"),
      "utf8",
    );
    assert.doesNotMatch(workspace, /CompareDeltaStrip/);
    assert.doesNotMatch(workspace, /showCompareDeltaStrip/);
    assert.doesNotMatch(workspace, /reservedDeltaStrip/);
    assert.doesNotMatch(workspace, /deltaStripFrom/);
    assert.doesNotMatch(workspace, /pair Δ/);
    assert.doesNotMatch(workspace, /never invent \$0/);
    assert.doesNotMatch(workspace, /DELTA STRIP/i);
    assert.match(workspace, /GrowthAndTaxDragModule/);
    assert.match(workspace, /UpcomingTable/);
    assert.doesNotMatch(barrel, /CompareDeltaStrip/);
  });
});
