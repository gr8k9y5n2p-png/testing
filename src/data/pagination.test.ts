import assert from "node:assert/strict";
import { test } from "node:test";
import { withPeerContext } from "./queries.ts";
import {
  FUND_PAGE_SIZE,
  PAID_HISTORY_PAGE_SIZE,
  PAID_HISTORY_PAGE_SIZE_MAX,
  clampPageOffset,
  clampPageSize,
  clampPaidHistoryPageSize,
  fundPageSearchParams,
  offsetToPage,
  paginateViews,
  parseFundPageQuery,
} from "./pagination.ts";
import type { FundEstimate } from "./types.ts";

function stubFund(index: number, patch: Partial<FundEstimate> = {}): FundEstimate {
  const n = String(index).padStart(2, "0");
  return {
    id: `fund-${n}`,
    fundName: patch.fundName ?? `Fund ${n}`,
    ticker: patch.ticker ?? `TIC${n}`,
    cusip: "000000000",
    family: patch.family ?? "American Funds",
    category: patch.category ?? "Large Growth",
    shareClass: "A",
    nav: 10,
    estimatedDistributionAmount: 0.2,
    estimatedOrdinaryIncome: 0.1,
    estimatedCapitalGains: 0.1,
    estimatedDistributionPctNav: patch.estimatedDistributionPctNav ?? index / 10,
    publishedAt: "2026-09-01",
    asOfDate: "2026-09-01",
    recordDate: "2026-12-12",
    exDate: "2026-12-15",
    payableDate: "2026-12-17",
    publicationStage: "preliminary_estimate",
    bucket: "upcoming",
    paidHistory: [],
    distributionYear: 2026,
    ...patch,
  };
}

test("default page size is 50 and clamps to 1–200", () => {
  assert.equal(FUND_PAGE_SIZE, 50);
  assert.equal(clampPageSize(undefined), 50);
  assert.equal(clampPageSize(0), 1);
  assert.equal(clampPageSize(500), 200);
});

test("Paid History page size clamps to 1–50", () => {
  assert.equal(PAID_HISTORY_PAGE_SIZE, 50);
  assert.equal(PAID_HISTORY_PAGE_SIZE_MAX, 50);
  assert.equal(clampPaidHistoryPageSize(undefined), 50);
  assert.equal(clampPaidHistoryPageSize(0), 1);
  assert.equal(clampPaidHistoryPageSize(1), 1);
  assert.equal(clampPaidHistoryPageSize(25), 25);
  assert.equal(clampPaidHistoryPageSize(200), 50);
});

test("paginateViews returns items + total for limit/offset", () => {
  const funds = withPeerContext(
    Array.from({ length: 120 }, (_, index) => stubFund(index + 1)),
  );
  const page = paginateViews(funds, {
    limit: 50,
    offset: 50,
    sort: "fundName",
    direction: "asc",
  });
  assert.equal(page.total, 120);
  assert.equal(page.limit, 50);
  assert.equal(page.offset, 50);
  assert.equal(page.items.length, 50);
  const firstPage = paginateViews(funds, {
    limit: 50,
    offset: 0,
    sort: "fundName",
    direction: "asc",
  });
  assert.notEqual(page.items[0]?.id, firstPage.items[0]?.id);
  assert.equal(
    new Set([...firstPage.items, ...page.items].map((fund) => fund.id)).size,
    100,
  );
});

test("paginateViews applies filters before slicing", () => {
  const funds = withPeerContext([
    stubFund(1, { family: "Vanguard", ticker: "VFIAX" }),
    stubFund(2, { family: "American Funds", ticker: "AMCPX" }),
    stubFund(3, { family: "Vanguard", ticker: "VTIAX" }),
  ]);
  const page = paginateViews(funds, { family: "Vanguard", limit: 50, offset: 0 });
  assert.equal(page.total, 2);
  assert.deepEqual(
    page.items.map((fund) => fund.ticker),
    ["VFIAX", "VTIAX"],
  );
});

test("clampPageOffset keeps a thin book on page 1 instead of an empty page 2", () => {
  assert.equal(clampPageOffset(0, 17, 50), 0);
  assert.equal(clampPageOffset(50, 17, 50), 0);
  assert.equal(clampPageOffset(50, 80, 50), 50);
  assert.equal(clampPageOffset(100, 80, 50), 50);
  assert.equal(clampPageOffset(0, 0, 50), 0);
});

test("paginateViews paid history total is the filtered fund count", () => {
  const funds = withPeerContext(
    Array.from({ length: 17 }, (_, index) =>
      stubFund(index + 1, { family: index < 5 ? "Fidelity" : "American Funds" }),
    ),
  );
  const thin = paginateViews(funds, {
    paidHistory: true,
    limit: 50,
    offset: 50,
  });
  assert.equal(thin.total, 17);
  assert.equal(thin.items.length, 17);
  assert.equal(thin.offset, 0);

  const fidelity = paginateViews(funds, {
    paidHistory: true,
    family: "Fidelity",
    limit: 50,
    offset: 0,
  });
  assert.equal(fidelity.total, 5);
  assert.equal(fidelity.items.length, 5);
});

test("empty filter result stays honest (total 0, no invented rows)", () => {
  const funds = withPeerContext([stubFund(1, { ticker: "AMCPX" })]);
  const page = paginateViews(funds, { query: "ZZZZZ", limit: 50, offset: 0 });
  assert.equal(page.total, 0);
  assert.equal(page.items.length, 0);
});

test("parseFundPageQuery and offsetToPage match the Data contract", () => {
  const query = parseFundPageQuery(
    new URLSearchParams("limit=50&offset=100&q=amc&sort=publishedAt&direction=desc"),
  );
  assert.equal(query.limit, 50);
  assert.equal(query.offset, 100);
  assert.equal(query.query, "amc");
  assert.equal(query.sort, "publishedAt");
  assert.equal(query.direction, "desc");

  const distShare = parseFundPageQuery(
    new URLSearchParams(
      "paid_history=1&sort=estimatedDistributionAmount&direction=desc",
    ),
  );
  assert.equal(distShare.sort, "estimatedDistributionAmount");
  assert.equal(distShare.direction, "desc");
  assert.equal(distShare.paidHistory, true);

  const pctNav = parseFundPageQuery(
    new URLSearchParams(
      "paid_history=1&sort=estimatedDistributionPctNav&direction=asc",
    ),
  );
  assert.equal(pctNav.sort, "estimatedDistributionPctNav");
  assert.equal(pctNav.direction, "asc");

  const exDiv = parseFundPageQuery(
    new URLSearchParams("sort=exDate&direction=desc"),
  );
  assert.equal(exDiv.sort, "exDate");
  assert.equal(
    parseFundPageQuery(new URLSearchParams("sort=asOfDate")).sort,
    "asOfDate",
  );
  assert.equal(
    parseFundPageQuery(new URLSearchParams("sort=recordDate")).sort,
    "recordDate",
  );
  assert.equal(
    parseFundPageQuery(new URLSearchParams("sort=payableDate")).sort,
    "payableDate",
  );
  assert.equal(offsetToPage(100, 50), 3);

  const params = fundPageSearchParams({ limit: 50, offset: 0 });
  assert.equal(params.get("limit"), "50");
  assert.equal(params.get("offset"), "0");
  assert.equal(params.get("page_size"), "50");
  assert.equal(params.get("page"), "1");

  const aliased = parseFundPageQuery(
    new URLSearchParams("page=3&page_size=50&fund_family=Vanguard&q=amc"),
  );
  assert.equal(aliased.limit, 50);
  assert.equal(aliased.offset, 100);
  assert.equal(aliased.family, "Vanguard");
  assert.equal(aliased.query, "amc");

  const navOnly = parseFundPageQuery(
    new URLSearchParams("q=FBGRX&limit=5&nav_only=1"),
  );
  assert.equal(navOnly.query, "FBGRX");
  assert.equal(navOnly.navOnly, true);

  const upcoming = parseFundPageQuery(new URLSearchParams("upcoming=1&limit=200"));
  assert.equal(upcoming.upcoming, true);
  const upcomingParams = fundPageSearchParams({ upcoming: true, limit: 200 });
  assert.equal(upcomingParams.get("upcoming"), "1");

  const paid = parseFundPageQuery(
    new URLSearchParams(
      "paid_history=1&limit=200&year=2025&fund_family=Vanguard&category=Large%20Blend",
    ),
  );
  assert.equal(paid.paidHistory, true);
  assert.equal(paid.limit, 50, "Paid History user window clamps to 1–50");
  assert.equal(paid.year, 2025);
  assert.equal(paid.family, "Vanguard");
  assert.equal(paid.category, "Large Blend");
  const paidParams = fundPageSearchParams({
    paidHistory: true,
    limit: 25,
    offset: 50,
    year: 2025,
    family: "Fidelity",
    category: "Large Growth",
  });
  assert.equal(paidParams.get("paid_history"), "1");
  assert.equal(paidParams.get("limit"), "25");
  assert.equal(paidParams.get("page_size"), "25");
  assert.equal(paidParams.get("page"), "3");
  assert.equal(paidParams.get("year"), "2025");
  assert.equal(paidParams.get("fund_family"), "Fidelity");
  assert.equal(paidParams.get("category"), "Large Growth");
});
