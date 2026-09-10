import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import {
  aggregateDistributions,
  type DataDistribution,
} from "../../data/aggregate-distributions.ts";
import { mapFundsApiItem } from "../../data/funds-list.ts";
import { mergeFundWithDistributions } from "../../data/hydrate-funds.ts";
import { withPeerContext } from "../../data/queries.ts";
import {
  emptyEstimateTypes,
  listRowFromFund,
  upcomingEstimateTypeAmounts,
} from "./rows.ts";

const here = dirname(fileURLToPath(import.meta.url));
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

const FBGRX_ROWS: DataDistribution[] = [
  row({
    id: "fbgrx-ltcg",
    ticker: "FBGRX",
    fund_name: "Blue Chip Growth",
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
    estimate_type: "short_term_capital_gains",
    amount: "0.000000",
    amount_unit: "per_share",
    ex_date: "2026-09-11",
    payable_date: "2026-09-14",
  }),
  row({
    id: "fbgrx-total",
    ticker: "FBGRX",
    fund_name: "Blue Chip Growth",
    estimate_type: "total",
    amount: "21.021000",
    amount_unit: "per_share",
    ex_date: "2026-09-11",
    payable_date: "2026-09-14",
  }),
  row({
    id: "fbgrx-ye-final",
    ticker: "FBGRX",
    fund_name: "Blue Chip Growth",
    estimate_type: "long_term_capital_gains",
    amount: "5.073000",
    amount_unit: "per_share",
    ex_date: "2025-09-12",
    payable_date: "2025-09-15",
    as_of: "2025-12-31",
    publication_stage: "final",
  }),
];

const AGTHX_PAID_ROWS: DataDistribution[] = [
  row({
    id: "agthx-paid",
    ticker: "AGTHX",
    fund_name: "The Growth Fund of America",
    fund_family: "American Funds",
    estimate_type: "long_term_capital_gains",
    amount: "4.120000",
    amount_unit: "per_share",
    record_date: "2025-12-12",
    ex_date: "2025-12-15",
    payable_date: "2025-12-16",
    as_of: "2025-12-31",
    publication_stage: "final",
  }),
];

function hydrate(
  ticker: string,
  fundName: string,
  family: string,
  nav: number,
  rows: DataDistribution[],
) {
  const catalog = mapFundsApiItem({
    ticker,
    fund_name: fundName,
    fund_family: family,
    nav_per_share: nav,
    has_estimate: false,
  });
  const aggregated = withPeerContext(aggregateDistributions(rows, TODAY))[0];
  return mergeFundWithDistributions(catalog, aggregated);
}

describe("Lists upcoming rows", () => {
  it("shows FBGRX unpaid prelim Dist $/sh ~$21.021 and typed LTCG — not the 2025 final", () => {
    const fund = hydrate("FBGRX", "Blue Chip Growth", "Fidelity", 248.12, FBGRX_ROWS);
    const list = listRowFromFund({
      ticker: "FBGRX",
      fund,
      distributionRows: FBGRX_ROWS,
      found: true,
      today: TODAY,
    });
    assert.equal(list.status, "upcoming");
    assert.ok(list.nav != null && Math.abs(list.nav - 248.12) < 1e-6);
    assert.ok(
      list.distPerShare != null && Math.abs(list.distPerShare - 21.021) < 1e-6,
    );
    assert.equal(list.asOfDate, "2026-07-31");
    assert.equal(list.exDate, "2026-09-11");
    assert.ok(
      list.estimateTypes.long_term_capital_gains != null &&
        Math.abs(list.estimateTypes.long_term_capital_gains - 21.021) < 1e-6,
    );
    assert.equal(list.estimateTypes.ordinary_income, null);
    assert.equal(list.estimateTypes.qualified_dividend, null);
    assert.notEqual(list.distPerShare, 5.073);
  });

  it("does not invent Upcoming from a paid-only fund — NAV can still show", () => {
    const fund = hydrate(
      "AGTHX",
      "The Growth Fund of America",
      "American Funds",
      88.42,
      AGTHX_PAID_ROWS,
    );
    const list = listRowFromFund({
      ticker: "AGTHX",
      fund,
      distributionRows: AGTHX_PAID_ROWS,
      found: true,
      today: TODAY,
    });
    assert.equal(list.status, "undisclosed");
    assert.ok(list.nav != null && Math.abs(list.nav - 88.42) < 1e-6);
    assert.equal(list.distPerShare, null);
    assert.equal(list.pctOfNav, null);
    assert.deepEqual(list.estimateTypes, emptyEstimateTypes());
    assert.equal(list.asOfDate, null);
    assert.equal(list.recordDate, null);
    assert.equal(list.exDate, null);
    assert.deepEqual(upcomingEstimateTypeAmounts(AGTHX_PAID_ROWS, TODAY), emptyEstimateTypes());
  });

  it("does not double Dist $/sh when ticker= and Upcoming snapshot rows are the same", () => {
    const list = listRowFromFund({
      ticker: "FBGRX",
      fund: null,
      distributionRows: [...FBGRX_ROWS, ...FBGRX_ROWS],
      found: true,
      today: TODAY,
    });
    // latest snapshot still groups one as_of|stage|ex key; amounts add.
    // BFF must dedupe before this helper — lock the helper to one snapshot sum.
    assert.ok(
      list.distPerShare != null && Math.abs(list.distPerShare - 21.021) < 1e-6,
    );
  });

  it("fills LTCG from upcoming estimateTypeLines when raw snapshot rows are missing", () => {
    const fund = hydrate("FBGRX", "Blue Chip Growth", "Fidelity", 312.26, FBGRX_ROWS);
    const list = listRowFromFund({
      ticker: "FBGRX",
      fund,
      distributionRows: [],
      found: true,
      today: TODAY,
    });
    assert.equal(list.status, "upcoming");
    assert.ok(
      list.estimateTypes.long_term_capital_gains != null &&
        Math.abs(list.estimateTypes.long_term_capital_gains - 21.021) < 1e-6,
    );
    assert.ok(
      list.distPerShare != null && Math.abs(list.distPerShare - 21.021) < 1e-6,
    );
  });

  it("keeps unknown tickers as not-found instead of dropping them", () => {
    const list = listRowFromFund({ ticker: "ZZZZZ", fund: null, found: false });
    assert.equal(list.status, "not_found");
    assert.equal(list.distPerShare, null);
    assert.equal(list.nav, null);
  });

  it("hydrates FBGRX from unpaid snapshots when identity is has_estimate:false / paid", () => {
    const identity = mapFundsApiItem({
      ticker: "FBGRX",
      fund_name: "Blue Chip Growth",
      fund_family: "Fidelity",
      nav_per_share: 312.26,
      has_estimate: false,
    });
    const fund = mergeFundWithDistributions(identity, null);
    assert.equal(fund.hasEstimate, false);
    assert.equal(fund.bucket, "paid");
    const list = listRowFromFund({
      ticker: "FBGRX",
      fund,
      distributionRows: FBGRX_ROWS,
      found: true,
      today: TODAY,
    });
    assert.equal(list.status, "upcoming");
    assert.ok(list.nav != null && Math.abs(list.nav - 312.26) < 1e-4);
    assert.ok(
      list.distPerShare != null && Math.abs(list.distPerShare - 21.021) < 1e-6,
    );
    assert.ok(list.pctOfNav != null && list.pctOfNav > 0);
    assert.equal(list.asOfDate, "2026-07-31");
    assert.equal(list.exDate, "2026-09-11");
    assert.ok(
      list.estimateTypes.long_term_capital_gains != null &&
        Math.abs(list.estimateTypes.long_term_capital_gains - 21.021) < 1e-6,
    );
    assert.equal(list.estimateTypes.short_term_capital_gains, 0);
    assert.equal(list.estimateTypes.ordinary_income, null);
    assert.equal(list.estimateTypes.qualified_dividend, null);
  });

  it("hydrates FBGRX columns from unpaid rows when catalog identity is missing", () => {
    const list = listRowFromFund({
      ticker: "FBGRX",
      fund: null,
      distributionRows: FBGRX_ROWS,
      found: true,
      today: TODAY,
    });
    assert.equal(list.status, "upcoming");
    assert.ok(list.nav != null && Math.abs(list.nav - 312.26001) < 1e-4);
    assert.ok(
      list.distPerShare != null && Math.abs(list.distPerShare - 21.021) < 1e-6,
    );
    assert.equal(list.asOfDate, "2026-07-31");
    assert.equal(list.exDate, "2026-09-11");
    assert.ok(
      list.estimateTypes.long_term_capital_gains != null &&
        Math.abs(list.estimateTypes.long_term_capital_gains - 21.021) < 1e-6,
    );
  });
});

describe("Lists chrome lock", () => {
  it("does not show MOCK banners and keeps Eric's column order", () => {
    const workspace = readFileSync(
      join(here, "../../components/lists/ListsWorkspace.tsx"),
      "utf8",
    );
    const page = readFileSync(join(here, "../../app/lists/page.tsx"), "utf8");
    const nav = readFileSync(join(here, "../../components/AppNav.tsx"), "utf8");
    assert.doesNotMatch(workspace, /MOCK/);
    assert.doesNotMatch(page, /MOCK/);
    assert.match(workspace, /LISTS_NAV_COLUMN/);
    assert.match(workspace, /LISTS_DIST_COLUMN/);
    assert.match(workspace, /LISTS_PCT_COLUMN/);
    assert.match(workspace, /LIST_ESTIMATE_TYPES/);
    assert.match(workspace, /LISTS_ANNOUNCED_COLUMN/);
    assert.match(workspace, /LISTS_RECORD_COLUMN/);
    assert.match(workspace, /LISTS_EX_COLUMN/);
    assert.match(workspace, /tickerSlotBorderClass/);
    assert.match(workspace, /history\.replaceState/);
    assert.doesNotMatch(workspace, /useRouter|router\.replace/);
    assert.match(workspace, /cache:\s*"no-store"/);
    assert.match(workspace, /needsListHydrate/);
    assert.match(workspace, /listRowsFromApiResponse/);
    assert.doesNotMatch(
      workspace,
      /return tickers\.map\(\(ticker\) => emptyListRow\(ticker, "not_found"\)\)/,
    );
    assert.match(nav, /label:\s*"Lists"/);
    assert.match(nav, /href:\s*"\/lists"/);
  });
});
