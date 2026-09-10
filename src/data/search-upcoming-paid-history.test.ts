import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { aggregateDistributions, type DataDistribution } from "./aggregate-distributions.ts";
import { mapFundsApiItem } from "./funds-list.ts";
import {
  mergeFundWithDistributions,
  paidEventsForFund,
} from "./hydrate-funds.ts";
import {
  paidHistoryViews,
  paidHistoryYearOf,
  splitFundsByBucket,
  withPeerContext,
} from "./queries.ts";
import { isUpcomingFund } from "./distribution-bucket.ts";

const TODAY = "2026-09-10";

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
    as_of: "2026-07-31",
    publication_stage: "preliminary_estimate",
    ...patch,
  };
}

/** Live Data API FBGRX unpaid future prelim (as of 2026-09-10). */
const FBGRX_ROWS: DataDistribution[] = [
  row({
    id: "fbgrx-ltcg",
    ticker: "FBGRX",
    fund_name: "Blue Chip Growth",
    fund_family: "Fidelity",
    estimate_type: "long_term_capital_gains",
    amount: "21.021000",
    amount_unit: "per_share",
    ex_date: "2026-09-11",
    payable_date: "2026-09-14",
    as_of: "2026-07-31",
    publication_stage: "preliminary_estimate",
    nav_on_distribution_day: "312.260010",
  }),
  row({
    id: "fbgrx-stcg",
    ticker: "FBGRX",
    fund_name: "Blue Chip Growth",
    fund_family: "Fidelity",
    estimate_type: "short_term_capital_gains",
    amount: "0.000000",
    amount_unit: "per_share",
    ex_date: "2026-09-11",
    payable_date: "2026-09-14",
    as_of: "2026-07-31",
    publication_stage: "preliminary_estimate",
  }),
  row({
    id: "fbgrx-total",
    ticker: "FBGRX",
    fund_name: "Blue Chip Growth",
    fund_family: "Fidelity",
    estimate_type: "total",
    amount: "21.021000",
    amount_unit: "per_share",
    ex_date: "2026-09-11",
    payable_date: "2026-09-14",
    as_of: "2026-07-31",
    publication_stage: "preliminary_estimate",
  }),
  row({
    id: "fbgrx-tcg",
    ticker: "FBGRX",
    fund_name: "Blue Chip Growth",
    fund_family: "Fidelity",
    estimate_type: "total_capital_gains",
    amount: "7.080000",
    amount_unit: "percent_of_nav",
    ex_date: "2026-09-11",
    payable_date: "2026-09-14",
    as_of: "2026-07-31",
    publication_stage: "preliminary_estimate",
  }),
  row({
    id: "fbgrx-ye-final",
    ticker: "FBGRX",
    fund_name: "Blue Chip Growth",
    fund_family: "Fidelity",
    estimate_type: "long_term_capital_gains",
    amount: "5.073000",
    amount_unit: "per_share",
    ex_date: "2025-09-12",
    payable_date: "2025-09-15",
    as_of: "2025-12-31",
    publication_stage: "final",
  }),
];

const AMCPX_ROWS: DataDistribution[] = [
  row({
    id: "amcpx-ltcg-2026",
    ticker: "AMCPX",
    fund_name: "AMCAP Fund",
    fund_family: "American Funds",
    fund_identifier: "amcap-fund",
    estimate_type: "long_term_capital_gains",
    amount: "3.536500",
    amount_unit: "per_share",
    record_date: "2026-06-16",
    ex_date: "2026-06-16",
    payable_date: "2026-06-17",
    as_of: "2026-07-08",
    publication_stage: "paid",
  }),
];

const CGHM_ROWS: DataDistribution[] = [
  row({
    id: "cghm-lt",
    ticker: "CGHM",
    fund_name: "Capital Group Municipal High-Income ETF",
    fund_family: "American Funds",
    estimate_type: "long_term_capital_gains",
    amount: "0.003000",
    amount_unit: "per_share",
    record_date: "2026-06-29",
    ex_date: "2026-06-29",
    payable_date: "2026-06-30",
    as_of: "2026-07-08",
    publication_stage: "paid",
  }),
  row({
    id: "cghm-st",
    ticker: "CGHM",
    fund_name: "Capital Group Municipal High-Income ETF",
    fund_family: "American Funds",
    estimate_type: "short_term_capital_gains",
    amount: "0.016900",
    amount_unit: "per_share",
    record_date: "2026-06-29",
    ex_date: "2026-06-29",
    payable_date: "2026-06-30",
    as_of: "2026-07-08",
    publication_stage: "paid",
  }),
];

function hydrate(
  ticker: string,
  fundName: string,
  family: string,
  hasEstimate: boolean,
  rows: DataDistribution[],
) {
  const catalog = mapFundsApiItem({
    ticker,
    fund_name: fundName,
    fund_family: family,
    has_estimate: hasEstimate,
  });
  const aggregated = withPeerContext(aggregateDistributions(rows, TODAY))[0];
  return mergeFundWithDistributions(catalog, aggregated);
}

describe("Search Upcoming still-future unpaid prelims", () => {
  it("lists FBGRX LTCG $21.021 / sh prelim — not empty / undisclosed", () => {
    const fund = hydrate(
      "FBGRX",
      "Blue Chip Growth",
      "Fidelity",
      true,
      FBGRX_ROWS,
    );
    assert.equal(fund.bucket, "upcoming");
    assert.equal(fund.hasEstimate, true);
    assert.equal(fund.publicationStage, "preliminary_estimate");
    assert.equal(fund.asOfDate, "2026-07-31");
    assert.equal(fund.exDate, "2026-09-11");
    assert.equal(fund.payableDate, "2026-09-14");
    assert.ok(
      Math.abs(fund.estimatedDistributionAmount - 21.021) < 1e-6,
      `Dist $/sh should be 21.021, got ${fund.estimatedDistributionAmount}`,
    );
    assert.ok(
      fund.publishedPctOfNav != null && Math.abs(fund.publishedPctOfNav - 7.08) < 1e-6,
      "% NAV should keep the published 7.08 character",
    );
    assert.equal(isUpcomingFund(fund, TODAY), true);
    const { upcoming, paid } = splitFundsByBucket([fund]);
    assert.equal(upcoming.length, 1, "Upcoming must show FBGRX");
    assert.equal(paid.length, 0);
    assert.ok(
      paidHistoryViews([fund]).some(
        (row) => Math.abs(row.estimatedDistributionAmount - 5.073) < 1e-6,
      ),
      "2025 final stays in Paid history, not Upcoming",
    );
  });

  it("does not invent Upcoming from AMCPX/CGHM midyear paids", () => {
    const amcpx = hydrate("AMCPX", "AMCAP Fund", "American Funds", true, AMCPX_ROWS);
    const cghm = hydrate(
      "CGHM",
      "Capital Group Municipal High-Income ETF",
      "American Funds",
      false,
      CGHM_ROWS,
    );
    assert.equal(isUpcomingFund(amcpx, TODAY), false);
    assert.equal(isUpcomingFund(cghm, TODAY), false);
    assert.equal(splitFundsByBucket([amcpx, cghm]).upcoming.length, 0);
  });
});

describe("Search Paid history 2026 midyear paids", () => {
  it("lists AMCPX paid LTCG $3.5365 ex 2026-06-16", () => {
    const fund = hydrate("AMCPX", "AMCAP Fund", "American Funds", true, AMCPX_ROWS);
    assert.equal(fund.bucket, "paid");
    const history = paidHistoryViews([fund], 2026);
    assert.ok(
      history.some(
        (row) =>
          row.ticker === "AMCPX" &&
          Math.abs(row.estimatedDistributionAmount - 3.5365) < 1e-6 &&
          row.exDate === "2026-06-16",
      ),
      "AMCPX 2026 midyear paid must appear in Paid history",
    );
    assert.ok(paidEventsForFund(fund).some((event) => event.exDate === "2026-06-16"));
    assert.equal(paidHistoryYearOf(history[0]!), 2026);
  });

  it("lists CGHM paid LT $0.003 + ST $0.0169 ex 2026-06-29", () => {
    const fund = hydrate(
      "CGHM",
      "Capital Group Municipal High-Income ETF",
      "American Funds",
      false,
      CGHM_ROWS,
    );
    assert.equal(fund.bucket, "paid");
    const history = paidHistoryViews([fund], 2026);
    assert.ok(
      history.some(
        (row) =>
          row.ticker === "CGHM" &&
          Math.abs(row.estimatedDistributionAmount - 0.0199) < 1e-6 &&
          row.exDate === "2026-06-29",
      ),
      "CGHM combined 2026 midyear paid must appear",
    );
  });

  it("year toggle keeps 2025 FBGRX finals out of the 2026 Paid history window", () => {
    const fund = hydrate(
      "FBGRX",
      "Blue Chip Growth",
      "Fidelity",
      true,
      FBGRX_ROWS,
    );
    const y2026 = paidHistoryViews([fund], 2026);
    const y2025 = paidHistoryViews([fund], 2025);
    assert.equal(
      y2026.some((row) => Math.abs(row.estimatedDistributionAmount - 5.073) < 1e-6),
      false,
    );
    assert.ok(
      y2025.some((row) => Math.abs(row.estimatedDistributionAmount - 5.073) < 1e-6),
    );
  });
});
