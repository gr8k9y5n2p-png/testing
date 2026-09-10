import assert from "node:assert/strict";
import { describe, it } from "node:test";
import type { FundEstimate, FundEstimateView, HighlightSets } from "./types.ts";
import {
  getHighlights,
  highlightsCalendarYear,
  HIGHLIGHTS_MIN_YEAR_PEERS,
  pickHighlightsCalendarYear,
  withPeerContext,
} from "./queries.ts";

function stub(patch: Partial<FundEstimate> & Pick<FundEstimate, "ticker">): FundEstimate {
  const asOfDate = patch.asOfDate ?? "2026-07-31";
  const year =
    patch.distributionYear ??
    Number((patch.exDate ?? patch.recordDate ?? asOfDate).slice(0, 4)) ??
    2026;
  const pct = patch.estimatedDistributionPctNav ?? 8;
  const nav = patch.nav ?? 10;
  const perShare = (pct / 100) * nav;
  return {
    id: `hl-${patch.ticker}`,
    fundName: patch.fundName ?? patch.ticker,
    ticker: patch.ticker,
    cusip: "000000000",
    family: patch.family ?? "Fidelity",
    category: patch.category ?? "Large Growth",
    shareClass: "A",
    nav,
    navOnDistributionDay: patch.navOnDistributionDay ?? nav,
    estimatedDistributionAmount: patch.estimatedDistributionAmount ?? perShare,
    estimatedOrdinaryIncome: perShare / 2,
    estimatedCapitalGains: perShare / 2,
    estimatedDistributionPctNav: pct,
    publishedAt: asOfDate,
    asOfDate,
    recordDate: patch.recordDate ?? (patch.exDate ? patch.exDate : `${year}-12-12`),
    exDate: patch.exDate === undefined ? `${year}-09-11` : patch.exDate,
    payableDate: patch.payableDate ?? (patch.exDate ? patch.exDate : `${year}-09-13`),
    publicationStage: patch.publicationStage ?? "updated_estimate",
    bucket: patch.bucket ?? "upcoming",
    paidHistory: patch.paidHistory ?? [],
    distributionYear: year,
    hasEstimate: patch.hasEstimate ?? true,
    ...patch,
  };
}

function julEquity(ticker: string, pct: number, extra: Partial<FundEstimate> = {}): FundEstimate {
  return stub({
    ticker,
    fundName: ticker,
    family: "Fidelity",
    category: extra.category ?? "Large Growth",
    asOfDate: "2026-07-31",
    recordDate: "2026-12-12",
    exDate: "2026-12-15",
    payableDate: "2026-12-17",
    distributionYear: 2026,
    estimatedDistributionPctNav: pct,
    ...extra,
  });
}

function decMuni(ticker: string, pct: number, extra: Partial<FundEstimate> = {}): FundEstimate {
  return stub({
    ticker,
    fundName: ticker,
    family: extra.family ?? "Dimensional",
    category: extra.category ?? "Muni National Intermediate",
    asOfDate: "2025-12-31",
    recordDate: extra.recordDate === undefined ? null : extra.recordDate,
    exDate: extra.exDate === undefined ? null : extra.exDate,
    payableDate: extra.payableDate === undefined ? null : extra.payableDate,
    distributionYear: 2025,
    estimatedDistributionPctNav: pct,
    ...extra,
  });
}

function allHighlightRows(highlights: HighlightSets): FundEstimateView[] {
  return [
    ...highlights.largest,
    ...highlights.mostRecent,
    ...highlights.aboveCategory,
    ...highlights.belowCategory,
  ];
}

function tickersOf(highlights: HighlightSets): string[] {
  return [...new Set(allHighlightRows(highlights).map((fund) => fund.ticker))];
}

const fidelityJul2026 = [
  julEquity("FCPGX", 17.34, { category: "Small Growth", fundName: "Small Cap Growth" }),
  julEquity("FVDFX", 14.94, { category: "Large Value", fundName: "Value Discovery" }),
  julEquity("FDOGFX", 12.0, { fundName: "Dividend Growth" }),
  julEquity("FBGRX", 8.1, { fundName: "Blue Chip Growth" }),
  julEquity("FCNTX", 7.9, { fundName: "Contrafund" }),
  julEquity("FBCVX", 20.45, { category: "Large Value", fundName: "Blue Chip Value" }),
];

const dimensionalDec2025 = [
  decMuni("DCIBEX", 1.0, {
    fundName: "California Intermediate-Term Municipal Bond Portfolio",
  }),
  decMuni("DFEAX", 6.4),
  decMuni("DFCMX", 6.2, {
    fundName: "California Short-Term Municipal Bond Portfolio",
  }),
  decMuni("DFCA", 6.5, { fundName: "California Municipal Bond ETF" }),
];

describe("Highlights same-year unpaid announced peers", () => {
  it("reads the market year from ex/record before as_of", () => {
    assert.equal(
      highlightsCalendarYear(
        julEquity("FCPGX", 17.34, { asOfDate: "2025-12-31", exDate: "2026-09-11" }),
      ),
      2026,
    );
    assert.equal(highlightsCalendarYear(decMuni("DCIBEX", 1.0)), 2025);
  });

  it("prefers the latest year that has enough unpaid announced peers", () => {
    const year = pickHighlightsCalendarYear(
      withPeerContext([...fidelityJul2026, ...dimensionalDec2025]),
    );
    assert.equal(year, 2026);
    assert.ok(fidelityJul2026.length >= HIGHLIGHTS_MIN_YEAR_PEERS);
  });

  it("does not put Dec YE munis beside Jul YE equity in Versus Category", () => {
    const highlights = getHighlights(
      withPeerContext([...fidelityJul2026, ...dimensionalDec2025]),
    );
    const versus = [...highlights.aboveCategory, ...highlights.belowCategory];
    const versusTickers = versus.map((fund) => fund.ticker);
    const versusYears = new Set(versus.map(highlightsCalendarYear));

    assert.equal(versusTickers.includes("DCIBEX"), false);
    assert.equal(versusTickers.includes("DFCMX"), false);
    assert.equal(versusTickers.includes("DFCA"), false);
    assert.ok(versusYears.size <= 1);
    if (versusYears.size === 1) assert.deepEqual([...versusYears], [2026]);

    for (const fund of allHighlightRows(highlights)) {
      assert.equal(highlightsCalendarYear(fund), 2026, fund.ticker);
      assert.equal(fund.bucket, "upcoming", fund.ticker);
    }
    assert.ok(tickersOf(highlights).includes("FCPGX"));
    assert.ok(tickersOf(highlights).includes("FBCVX"));
  });

  it("drops prior-year category outliers when the latest year has enough peers", () => {
    const clustered2026 = [
      julEquity("FBGRX", 10.0),
      julEquity("FCNTX", 10.05),
      julEquity("FXAIX", 9.95),
    ];
    const highlights = getHighlights(
      withPeerContext([...clustered2026, ...dimensionalDec2025]),
    );
    assert.equal(highlights.aboveCategory.length, 0);
    assert.equal(highlights.belowCategory.length, 0);
    assert.equal(tickersOf(highlights).includes("DCIBEX"), false);
    assert.ok(highlights.largest.every((fund) => highlightsCalendarYear(fund) === 2026));
    assert.ok(highlights.mostRecent.every((fund) => highlightsCalendarYear(fund) === 2026));
  });

  it("never mixes paid history into any Highlights module", () => {
    const paid = stub({
      ticker: "AGTHX",
      fundName: "Growth Fund of America",
      family: "American Funds",
      category: "Large Growth",
      asOfDate: "2026-01-22",
      recordDate: "2025-12-15",
      exDate: "2025-12-15",
      payableDate: "2025-12-16",
      publicationStage: "final",
      bucket: "paid",
      hasEstimate: false,
      distributionYear: 2025,
      estimatedDistributionPctNav: 30,
    });
    const highlights = getHighlights(withPeerContext([...fidelityJul2026, paid]));
    assert.equal(tickersOf(highlights).includes("AGTHX"), false);
    assert.ok(allHighlightRows(highlights).every((fund) => fund.bucket === "upcoming"));
    assert.ok(allHighlightRows(highlights).every((fund) => fund.hasEstimate !== false));
  });

  it("soft-empties when no calendar year has enough unpaid announced peers", () => {
    const highlights = getHighlights(
      withPeerContext([
        julEquity("FCPGX", 17.34),
        decMuni("DCIBEX", 1.0),
      ]),
    );
    assert.deepEqual(highlights, {
      mostRecent: [],
      largest: [],
      aboveCategory: [],
      belowCategory: [],
    });
  });

  it("uses the older year when it is the only bucket with enough unpaid peers", () => {
    const highlights = getHighlights(
      withPeerContext([julEquity("FCPGX", 17.34), ...dimensionalDec2025]),
    );
    for (const fund of allHighlightRows(highlights)) {
      assert.equal(highlightsCalendarYear(fund), 2025, fund.ticker);
    }
    assert.equal(tickersOf(highlights).includes("FCPGX"), false);
    assert.ok(tickersOf(highlights).includes("DCIBEX"));
  });

  it("recomputes Versus Category deltas on unpaid same-year peers only", () => {
    const paidPeer = stub({
      ticker: "ANWPX",
      fundName: "New Perspective paid YE",
      category: "Large Growth",
      asOfDate: "2026-01-10",
      recordDate: "2025-12-12",
      exDate: "2025-12-15",
      payableDate: "2025-12-17",
      publicationStage: "final",
      bucket: "paid",
      hasEstimate: false,
      distributionYear: 2026,
      estimatedDistributionPctNav: 0.5,
    });
    const unpaid = [
      julEquity("FBGRX", 10.0),
      julEquity("FCNTX", 10.2),
      julEquity("FXAIX", 9.8),
    ];
    const mixed = withPeerContext([...unpaid, paidPeer]);
    const paidInflated = mixed.find((fund) => fund.ticker === "FBGRX");
    assert.ok(paidInflated);
    // Paid 1% NAV in the same year/category would pull the mixed average down.
    assert.ok(paidInflated.vsCategoryPctNav > 2.25);

    const highlights = getHighlights(mixed);
    assert.equal(highlights.aboveCategory.length, 0);
    assert.equal(highlights.belowCategory.length, 0);
    assert.equal(tickersOf(highlights).includes("ANWPX"), false);
  });
});
