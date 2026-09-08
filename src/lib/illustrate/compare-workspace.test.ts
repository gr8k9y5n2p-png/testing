import assert from "node:assert/strict";
import { describe, it } from "node:test";
import type { FundEstimateView } from "../../data/types.ts";
import type { CompareIllustration, ComparePeriodOut, CompareResponse } from "./compare-types.ts";
import {
  buildCompareAnnualTable,
  emptyCompareSlots,
  filledCompareTickers,
  growthFundsFromSlots,
  padCompareSlots,
  setCompareSlot,
  upcomingRowForCompareTicker,
  upcomingRowsFromCompareTickers,
} from "./compare-workspace.ts";

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
  });
});
