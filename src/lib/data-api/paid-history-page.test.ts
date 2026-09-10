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
    assert.match(source, /publicationStage: "final"/);
    assert.match(source, /publicationStage: "paid"/);
    assert.match(source, /isFinalOrPaidRow/);
    assert.match(book, /isUpcomingFund/);
    assert.match(source, /pagePaidHistoryFunds/);
    assert.match(source, /loadPaidHistoryDistributionRows/);
    assert.match(source, /PAID_HISTORY_DATA_PAGE_SIZE = 200/);
    assert.doesNotMatch(source, /Math\.max\(finals\.total/);
    assert.doesNotMatch(source, /finals\.total|paids\.total/);
    assert.doesNotMatch(source, /DISTRIBUTION_MAX_PAGES/);
    assert.doesNotMatch(source, /preliminary_estimate/);
    assert.doesNotMatch(source, /updated_estimate/);
    assert.doesNotMatch(source, /SAMPLE_FUNDS|from ["']@\/data\/seed["']/);
    assert.match(dists, /loadDistributionPage/);
    assert.match(dists, /Never walks the book/);
    assert.match(dashboard, /paid_history/);
    assert.match(dashboard, /paidFunds/);
    assert.match(dashboard, /paidFacets/);
    assert.match(dashboard, /setPaidOffset\(0\)/);
    assert.match(table, /paidFunds \?\? funds/);
    assert.match(table, /page=\{paidPage\}/);
    assert.match(table, /All families/);
    assert.match(table, /All categories/);
    assert.match(table, /Paid History filters/);
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
