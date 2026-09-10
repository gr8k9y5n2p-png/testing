import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { aggregateDistributions, type DataDistribution } from "../../data/aggregate-distributions.ts";
import { isUpcomingFund } from "../../data/distribution-bucket.ts";
import {
  filterPaidHistoryFunds,
  pagePaidHistoryFunds,
} from "../../data/paid-history-book.ts";
import {
  isTrustworthyFilteredRowTotal,
  loadPaidHistoryPage,
  paidHistoryCategoryParam,
  paidHistoryExDateWindow,
  shouldRetryPaidHistoryWithoutCategory,
  PAID_HISTORY_MAX_FETCH_ROUNDS,
  PAID_HISTORY_SOURCE_LIVE,
  PAID_HISTORY_SOURCE_PARTIAL,
  PAID_HISTORY_SOURCE_UNAVAILABLE,
  type PaidHistoryDataPage,
  type PaidHistoryFetchWindow,
} from "../../data/paid-history-walk.ts";
import { PAID_HISTORY_PAGE_SIZES } from "../../data/pagination.ts";
import { paidHistoryViews, withPeerContext } from "../../data/queries.ts";
import type { FundEstimateView } from "../../data/types.ts";

const here = dirname(fileURLToPath(import.meta.url));

function row(
  patch: Partial<DataDistribution> &
    Pick<DataDistribution, "id" | "ticker" | "estimate_type" | "amount" | "amount_unit">,
): DataDistribution {
  return {
    fund_family: patch.fund_family ?? "Fidelity",
    fund_name: patch.fund_name ?? patch.ticker,
    fund_identifier: patch.fund_identifier ?? patch.ticker,
    cusip: null,
    share_class: null,
    amount_min: null,
    amount_max: null,
    record_date: null,
    ex_date: null,
    payable_date: null,
    as_of: "2025-12-31",
    publication_stage: "final",
    ...patch,
  };
}

function paidFund(
  index: number,
  patch: Partial<FundEstimateView> = {},
): FundEstimateView {
  const n = String(index).padStart(2, "0");
  const year = patch.distributionYear ?? 2026;
  const asOf = patch.asOfDate ?? `${year}-06-15`;
  return {
    id: `fund-${n}`,
    fundName: patch.fundName ?? `Fund ${n}`,
    ticker: patch.ticker ?? `TIC${n}`,
    cusip: "000000000",
    family: patch.family ?? "American Funds",
    category: patch.category ?? "Large Growth",
    shareClass: "A",
    nav: 10,
    estimatedDistributionAmount: patch.estimatedDistributionAmount ?? 0.2,
    estimatedOrdinaryIncome: 0.1,
    estimatedCapitalGains: 0.1,
    estimatedDistributionPctNav: 2,
    publishedAt: asOf,
    asOfDate: asOf,
    recordDate: `${year}-06-12`,
    exDate: `${year}-06-15`,
    payableDate: `${year}-06-17`,
    publicationStage: "final",
    bucket: "paid",
    paidHistory: [],
    distributionYear: year,
    categoryAveragePctNav: 0,
    vsCategoryPctNav: 0,
    ...patch,
  };
}

describe("Search Paid History year-book page", () => {
  it("pages GET /distributions finals/paid by funds — never Upcoming, never a row total", () => {
    const source = readFileSync(join(here, "paid-history-page.ts"), "utf8");
    const book = readFileSync(join(here, "../../data/paid-history-book.ts"), "utf8");
    const dists = readFileSync(join(here, "distributions.ts"), "utf8");
    const dashboard = readFileSync(join(here, "../../components/Dashboard.tsx"), "utf8");
    const table = readFileSync(join(here, "../../components/ResultsTable.tsx"), "utf8");
    const walk = readFileSync(join(here, "../../data/paid-history-walk.ts"), "utf8");
    assert.match(source, /publicationStage: "final"/);
    assert.match(source, /publicationStage: "paid"/);
    assert.match(source, /isFinalOrPaidRow/);
    assert.match(book, /isUpcomingFund/);
    assert.match(source, /pagePaidHistoryFunds/);
    assert.match(source, /paidHistorySort/);
    assert.match(book, /sortFunds/);
    assert.match(book, /estimatedDistributionAmount|paidHistorySort/);
    assert.doesNotMatch(dists, /params\.set\("sort"/);
    assert.doesNotMatch(dists, /params\.set\("order"/);
    assert.match(source, /loadPaidHistoryPage/);
    assert.match(source, /fundFamily: query\.family/);
    assert.match(source, /paidHistoryCategoryParam/);
    assert.match(source, /shouldRetryPaidHistoryWithoutCategory/);
    assert.match(source, /exDateFrom/);
    assert.match(source, /exDateTo/);
    assert.match(source, /limit: window\.limit/);
    assert.match(source, /offset: window\.offset/);
    assert.match(walk, /ex_date_from/);
    assert.match(walk, /ex_date_to/);
    assert.match(walk, /PAID_HISTORY_MAX_FETCH_ROUNDS = 2/);
    assert.match(walk, /PAID_HISTORY_BUDGET_MS = 8_000/);
    assert.equal(PAID_HISTORY_MAX_FETCH_ROUNDS, 2);
    assert.doesNotMatch(walk, /PAID_HISTORY_WALK_MAX_PAGES/);
    assert.doesNotMatch(walk, /PAID_HISTORY_MAX_DATA_PAGES/);
    assert.doesNotMatch(walk, /WALK_BATCH/);
    assert.doesNotMatch(walk, /page_size=200 until short/);
    assert.doesNotMatch(source, /loadPaidHistoryDistributionRows/);
    assert.doesNotMatch(source, /year: query\.year/);
    assert.doesNotMatch(source, /DISTRIBUTION_MAX_PAGES/);
    assert.doesNotMatch(source, /preliminary_estimate/);
    assert.doesNotMatch(source, /updated_estimate/);
    assert.doesNotMatch(source, /SAMPLE_FUNDS|from ["']@\/data\/seed["']/);
    assert.match(dists, /ex_date_to/);
    assert.match(dists, /params\.set\("limit"/);
    assert.match(dists, /params\.set\("offset"/);
    assert.match(dists, /params\.set\("category"/);
    assert.doesNotMatch(dists, /fund_category/);
    assert.match(dists, /loadDistributionPage/);
    assert.match(dists, /Never walks the book/);
    assert.match(dashboard, /paid_history/);
    assert.match(dashboard, /paidFunds/);
    assert.match(dashboard, /paidFacets/);
    assert.match(dashboard, /setPaidOffset\(0\)/);
    assert.match(dashboard, /sort: sortKey/);
    assert.match(dashboard, /direction: sortDirection/);
    assert.match(source, /no order\/sort param/);
    assert.match(table, /paidFunds \?\? funds/);
    assert.match(table, /page=\{paidPage\}/);
    assert.match(table, /All families/);
    assert.match(table, /All categories/);
    assert.match(table, /Paid History filters/);
    assert.match(table, /column="estimatedDistributionAmount"/);
    assert.match(table, /currently displayed Paid History rows/);
  });

  it("keeps published $0 finals and drops Upcoming prelims from the year book", () => {
    const rows: DataDistribution[] = [
      row({
        id: "zero-stcg",
        ticker: "FXAIX",
        estimate_type: "short_term_capital_gains",
        amount: "0.000000",
        amount_unit: "per_share",
        ex_date: "2025-12-12",
        payable_date: "2025-12-15",
        publication_stage: "final",
        fund_family: "Fidelity",
        category: "Large Blend",
      }),
      row({
        id: "prelim",
        ticker: "FBGRX",
        estimate_type: "long_term_capital_gains",
        amount: "21.021000",
        amount_unit: "per_share",
        ex_date: "2026-09-11",
        as_of: "2026-07-31",
        publication_stage: "preliminary_estimate",
        fund_family: "Fidelity",
      }),
    ];
    const finalsOnly = rows.filter((item) => {
      const stage = (item.publication_stage ?? "").trim().toLowerCase();
      return stage === "final" || stage === "paid";
    });
    assert.equal(finalsOnly.length, 1);
    const funds = withPeerContext(aggregateDistributions(finalsOnly));
    assert.equal(funds.some((fund) => isUpcomingFund(fund)), false);
    const history = paidHistoryViews(funds, 2025);
    assert.ok(
      history.some(
        (fund) => fund.ticker === "FXAIX" && fund.estimatedDistributionAmount === 0,
      ),
      "published $0 final stays in Paid History",
    );
    assert.equal(
      history.some((fund) => fund.ticker === "FBGRX"),
      false,
      "Upcoming prelim must not enter Paid History",
    );
  });

  it("year=2026 page 2 is not empty when the filtered book fits on page 1", () => {
    const funds = Array.from({ length: 17 }, (_, index) =>
      paidFund(index + 1, { distributionYear: 2026 }),
    );
    const page1 = pagePaidHistoryFunds(funds, {
      year: 2026,
      limit: 50,
      offset: 0,
    });
    assert.equal(page1.total, 17);
    assert.equal(page1.items.length, 17);
    assert.equal(page1.offset, 0);
    assert.equal(Math.ceil(page1.total / page1.limit), 1);

    const page2 = pagePaidHistoryFunds(funds, {
      year: 2026,
      limit: 50,
      offset: 50,
    });
    assert.equal(page2.total, 17, "total matches the filtered fund count");
    assert.equal(page2.items.length, 17, "page 2 clamps back onto the year book");
    assert.equal(page2.offset, 0);
    assert.deepEqual(
      page2.items.map((fund) => fund.ticker),
      page1.items.map((fund) => fund.ticker),
    );
  });

  it("total matches the Family / Category filtered fund count", () => {
    const funds = [
      paidFund(1, { ticker: "FXAIX", family: "Fidelity", category: "Large Blend" }),
      paidFund(2, { ticker: "FBGRX", family: "Fidelity", category: "Large Growth" }),
      paidFund(3, { ticker: "AMCPX", family: "American Funds", category: "Large Growth" }),
      paidFund(4, {
        ticker: "FBGRX-UP",
        family: "Fidelity",
        category: "Large Growth",
        bucket: "upcoming",
        publicationStage: "preliminary_estimate",
        exDate: "2026-12-15",
        payableDate: "2026-12-17",
        asOfDate: "2026-07-31",
        estimatedDistributionAmount: 21,
      }),
    ];
    const fidelity = pagePaidHistoryFunds(funds, {
      year: 2026,
      family: "Fidelity",
      limit: 50,
      offset: 0,
    });
    assert.equal(fidelity.total, 2);
    assert.deepEqual(
      fidelity.items.map((fund) => fund.ticker),
      ["FXAIX", "FBGRX"],
    );

    const growth = pagePaidHistoryFunds(funds, {
      year: 2026,
      category: "Large Growth",
      limit: 50,
      offset: 0,
    });
    assert.equal(growth.total, 2);
    assert.deepEqual(
      growth.items.map((fund) => fund.ticker),
      ["FBGRX", "AMCPX"],
    );

    const both = pagePaidHistoryFunds(funds, {
      year: 2026,
      family: "Fidelity",
      category: "Large Growth",
      limit: 50,
      offset: 0,
    });
    assert.equal(both.total, 1);
    assert.equal(both.items[0]?.ticker, "FBGRX");
    assert.equal(
      filterPaidHistoryFunds(funds, { year: 2026, family: "Fidelity" }).some(
        (fund) => fund.ticker === "FBGRX-UP",
      ),
      false,
    );
  });

  it("sorts the current Paid History window by Dist $/Share desc then asc", () => {
    const funds = [
      paidFund(1, { ticker: "LOW", estimatedDistributionAmount: 0.19 }),
      paidFund(2, { ticker: "HIGH", estimatedDistributionAmount: 21.021 }),
      paidFund(3, { ticker: "MID", estimatedDistributionAmount: 2.5 }),
    ];
    const highest = pagePaidHistoryFunds(funds, {
      year: 2026,
      limit: 50,
      offset: 0,
      sort: "estimatedDistributionAmount",
      direction: "desc",
    });
    assert.equal(highest.total, 3, "sort does not change the filtered total");
    assert.deepEqual(
      highest.items.map((fund) => fund.ticker),
      ["HIGH", "MID", "LOW"],
    );
    assert.ok(
      highest.items[0]!.estimatedDistributionAmount >
        highest.items[1]!.estimatedDistributionAmount,
    );
    assert.ok(
      highest.items[1]!.estimatedDistributionAmount >
        highest.items[2]!.estimatedDistributionAmount,
    );

    const lowest = pagePaidHistoryFunds(funds, {
      year: 2026,
      limit: 50,
      offset: 0,
      sort: "estimatedDistributionAmount",
      direction: "asc",
    });
    assert.equal(lowest.total, 3);
    assert.deepEqual(
      lowest.items.map((fund) => fund.ticker),
      ["LOW", "MID", "HIGH"],
    );
  });

  it("keeps Family / Category / year filters while Dist $/Share sorting", () => {
    const funds = [
      paidFund(1, {
        ticker: "FXAIX",
        family: "Fidelity",
        category: "Large Blend",
        estimatedDistributionAmount: 0.5,
      }),
      paidFund(2, {
        ticker: "FBGRX",
        family: "Fidelity",
        category: "Large Growth",
        estimatedDistributionAmount: 21.021,
      }),
      paidFund(3, {
        ticker: "AMCPX",
        family: "American Funds",
        category: "Large Growth",
        estimatedDistributionAmount: 5.0,
      }),
    ];
    const fidelityHighest = pagePaidHistoryFunds(funds, {
      year: 2026,
      family: "Fidelity",
      sort: "estimatedDistributionAmount",
      direction: "desc",
      limit: 50,
      offset: 0,
    });
    assert.equal(fidelityHighest.total, 2);
    assert.deepEqual(
      fidelityHighest.items.map((fund) => fund.ticker),
      ["FBGRX", "FXAIX"],
    );

    const growthLowest = pagePaidHistoryFunds(funds, {
      year: 2026,
      category: "Large Growth",
      sort: "estimatedDistributionAmount",
      direction: "asc",
      limit: 50,
      offset: 0,
    });
    assert.equal(growthLowest.total, 2);
    assert.deepEqual(
      growthLowest.items.map((fund) => fund.ticker),
      ["AMCPX", "FBGRX"],
    );
  });

  it("page sizes 1/10/25/50 are fund windows, not distribution-row windows", () => {
    const funds = Array.from({ length: 40 }, (_, index) =>
      paidFund(index + 1, { distributionYear: 2026 }),
    );
    for (const size of PAID_HISTORY_PAGE_SIZES) {
      const page = pagePaidHistoryFunds(funds, {
        year: 2026,
        limit: size,
        offset: 0,
      });
      assert.equal(page.limit, size);
      assert.equal(page.total, 40, "total stays the filtered fund count");
      assert.equal(page.items.length, Math.min(size, 40));
      assert.equal(
        new Set(page.items.map((fund) => fund.ticker)).size,
        page.items.length,
        "one row per fund",
      );
    }

    const page2of10 = pagePaidHistoryFunds(funds, {
      year: 2026,
      limit: 10,
      offset: 10,
    });
    assert.equal(page2of10.items.length, 10);
    assert.equal(page2of10.total, 40);
    assert.equal(page2of10.offset, 10);
    assert.notEqual(page2of10.items[0]?.ticker, funds[0]?.ticker);
  });
});

function finalRow(
  ticker: string,
  year: number,
  extras: Partial<DataDistribution> = {},
): DataDistribution {
  return row({
    id: `${ticker}-${year}`,
    ticker,
    fund_identifier: ticker,
    fund_name: ticker,
    estimate_type: "long_term_capital_gains",
    amount: "0.250000",
    amount_unit: "per_share",
    as_of: `${year}-12-15`,
    ex_date: `${year}-12-12`,
    payable_date: `${year}-12-15`,
    publication_stage: "final",
    fund_family: extras.fund_family ?? "Fidelity",
    category: extras.category ?? "Large Blend",
    ...extras,
  });
}

function dataPage(
  rows: DataDistribution[],
  patch: Partial<PaidHistoryDataPage> = {},
): PaidHistoryDataPage {
  return {
    rows,
    failed: false,
    filteredTotal: rows.length,
    ...patch,
  };
}

describe("Paid History year-window paging", () => {
  it("does not walk page_size=200 until short — at most two Data rounds", () => {
    const walk = readFileSync(join(here, "../../data/paid-history-walk.ts"), "utf8");
    assert.match(walk, /PAID_HISTORY_MAX_FETCH_ROUNDS = 2/);
    assert.match(walk, /deadline/);
    assert.equal(PAID_HISTORY_MAX_FETCH_ROUNDS, 2);
    assert.doesNotMatch(walk, /for \(let page = 1/);
    assert.doesNotMatch(walk, /while \(true\)/);
    assert.doesNotMatch(walk, /page_size=200/);
  });

  it("maps a calendar year to ex_date_from / ex_date_to", () => {
    assert.deepEqual(paidHistoryExDateWindow(2026), {
      exDateFrom: "2026-01-01",
      exDateTo: "2026-12-31",
    });
    assert.deepEqual(paidHistoryExDateWindow(2025), {
      exDateFrom: "2025-01-01",
      exDateTo: "2025-12-31",
    });
    assert.deepEqual(paidHistoryExDateWindow(undefined), {});
  });

  it("year=2026 page 2 clamps to page 1 with rows when the filtered book fits", async () => {
    const rows = Array.from({ length: 17 }, (_, index) =>
      finalRow(`T${String(index + 1).padStart(2, "0")}`, 2026),
    );
    const offsets: number[] = [];
    const fetchPage = async (
      _query: unknown,
      window: PaidHistoryFetchWindow,
    ) => {
      offsets.push(window.offset);
      if (window.offset >= 17) {
        return dataPage([], { filteredTotal: 17 });
      }
      return dataPage(rows, { filteredTotal: 17 });
    };

    const page2 = await loadPaidHistoryPage(
      { year: 2026, limit: 50, offset: 50 },
      { fetchPage },
    );
    assert.ok(offsets.length <= PAID_HISTORY_MAX_FETCH_ROUNDS);
    assert.deepEqual(offsets, [50, 0]);
    assert.equal(page2.total, 17);
    assert.equal(page2.items.length, 17, "page 2 clamps back onto the year book");
    assert.equal(page2.offset, 0);
    assert.equal(page2.hasMore, false);
    assert.equal(page2.sourceLabel, PAID_HISTORY_SOURCE_LIVE);
    assert.ok(page2.items.some((fund) => fund.ticker === "T01"));
  });

  it("dense-year path uses the year-window filtered total and one Data fetch", async () => {
    const calls: number[] = [];
    const fetchPage = async (
      _query: unknown,
      window: PaidHistoryFetchWindow,
    ) => {
      calls.push(window.offset);
      const rows = Array.from({ length: window.limit }, (_, index) =>
        finalRow(
          `D${String(window.offset + index).padStart(4, "0")}`,
          2025,
        ),
      );
      return dataPage(rows, { filteredTotal: 800 });
    };

    const page1 = await loadPaidHistoryPage(
      { year: 2025, limit: 50, offset: 0 },
      { fetchPage },
    );
    assert.equal(calls.length, 1, "no walk — one year-window page");
    assert.ok(calls.length < 100, "must not attempt 100+ Data calls");
    assert.equal(page1.items.length, 50);
    assert.equal(page1.total, 800, "pager uses the filtered Data total");
    assert.equal(page1.hasMore, true);
    assert.notEqual(Math.ceil(page1.total / page1.limit), 511);
    assert.equal(page1.sourceLabel, PAID_HISTORY_SOURCE_PARTIAL);

    const page2 = await loadPaidHistoryPage(
      { year: 2025, limit: 50, offset: 50 },
      { fetchPage },
    );
    assert.equal(page2.items.length, 50);
    assert.equal(page2.offset, 50);
    assert.equal(page2.total, 800);
    assert.notEqual(page2.items[0]?.ticker, page1.items[0]?.ticker);
    assert.equal(page2.hasMore, true);
  });

  it("sorts the fetched year-window funds by Dist $/Share without a book walk", async () => {
    const rows = [
      finalRow("LOW", 2026, { amount: "0.190000" }),
      finalRow("HIGH", 2026, { amount: "21.021000" }),
      finalRow("MID", 2026, { amount: "2.500000" }),
    ];
    const calls: number[] = [];
    const fetchPage = async (
      _query: unknown,
      window: PaidHistoryFetchWindow,
    ) => {
      calls.push(window.offset);
      return dataPage(rows, { filteredTotal: 3 });
    };

    const highest = await loadPaidHistoryPage(
      {
        year: 2026,
        limit: 50,
        offset: 0,
        sort: "estimatedDistributionAmount",
        direction: "desc",
      },
      { fetchPage },
    );
    assert.equal(calls.length, 1, "sort must not walk extra Data pages");
    assert.equal(highest.total, 3);
    assert.deepEqual(
      highest.items.map((fund) => fund.ticker),
      ["HIGH", "MID", "LOW"],
    );

    const lowest = await loadPaidHistoryPage(
      {
        year: 2026,
        limit: 50,
        offset: 0,
        sort: "estimatedDistributionAmount",
        direction: "asc",
      },
      { fetchPage },
    );
    assert.equal(calls.length, 2);
    assert.deepEqual(
      lowest.items.map((fund) => fund.ticker),
      ["LOW", "MID", "HIGH"],
    );
  });

  it("ignores an unfiltered global row total on a thin year page", () => {
    assert.equal(isTrustworthyFilteredRowTotal(17, 50, 25515, 0), false);
    assert.equal(isTrustworthyFilteredRowTotal(17, 50, 17, 0), true);
    assert.equal(isTrustworthyFilteredRowTotal(50, 50, 800, 0), true);
  });

  it("502 / timeout returns honest empty and does not hang", async () => {
    const failed = await loadPaidHistoryPage(
      { year: 2026, limit: 50, offset: 0 },
      { fetchPage: async () => ({ rows: [], failed: true }) },
    );
    assert.equal(failed.items.length, 0);
    assert.equal(failed.total, 0);
    assert.equal(failed.sourceLabel, PAID_HISTORY_SOURCE_UNAVAILABLE);

    const timedOut = await loadPaidHistoryPage(
      { year: 2026, limit: 50, offset: 0 },
      {
        fetchPage: async () => {
          const error = new Error("aborted");
          error.name = "AbortError";
          throw error;
        },
      },
    );
    assert.equal(timedOut.items.length, 0);
    assert.equal(timedOut.sourceLabel, PAID_HISTORY_SOURCE_UNAVAILABLE);
  });

  it("passes Family as fund_family and Category through on the year window", async () => {
    const seen: Array<{
      year?: number;
      family?: string;
      category?: string;
      limit: number;
      offset: number;
    }> = [];
    await loadPaidHistoryPage(
      {
        year: 2026,
        family: "Fidelity",
        category: "Large Growth",
        limit: 50,
        offset: 0,
      },
      {
        fetchPage: async (query, window) => {
          seen.push({
            year: query.year,
            family: query.family,
            category: query.category,
            limit: window.limit,
            offset: window.offset,
          });
          return dataPage([
            finalRow("FBGRX", 2026, {
              fund_family: "Fidelity",
              category: "Large Growth",
            }),
          ]);
        },
      },
    );
    assert.deepEqual(seen, [
      {
        year: 2026,
        family: "Fidelity",
        category: "Large Growth",
        limit: 50,
        offset: 0,
      },
    ]);
    assert.deepEqual(paidHistoryExDateWindow(seen[0]?.year), {
      exDateFrom: "2026-01-01",
      exDateTo: "2026-12-31",
    });
  });

  it("wires Category as the Data category param and retries once on 400", () => {
    assert.equal(paidHistoryCategoryParam("Large Blend"), "Large Blend");
    assert.equal(paidHistoryCategoryParam("  Large Growth  "), "Large Growth");
    assert.equal(paidHistoryCategoryParam(""), undefined);
    assert.equal(paidHistoryCategoryParam(undefined), undefined);
    assert.equal(
      shouldRetryPaidHistoryWithoutCategory("Large Blend", [400, 200]),
      true,
    );
    assert.equal(
      shouldRetryPaidHistoryWithoutCategory("Large Blend", [200, 200]),
      false,
    );
    assert.equal(shouldRetryPaidHistoryWithoutCategory(undefined, [400]), false);
    const source = readFileSync(join(here, "paid-history-page.ts"), "utf8");
    assert.match(source, /loadPair\(undefined\)/);
    assert.match(source, /categoryFilter/);
  });

  it("does not drop funds when Category is selected but Data rows have no category", async () => {
    const result = await loadPaidHistoryPage(
      { year: 2026, category: "Large Growth", limit: 50, offset: 0 },
      {
        fetchPage: async () =>
          dataPage([
            finalRow("MFEGX", 2026, { category: null, fund_category: null }),
          ]),
      },
    );
    assert.equal(result.items.length, 1);
    assert.equal(result.items[0]?.ticker, "MFEGX");
  });
});
