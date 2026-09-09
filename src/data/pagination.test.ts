import assert from "node:assert/strict";
import { test } from "node:test";
import { withPeerContext } from "./queries.ts";
import {
  FUND_PAGE_SIZE,
  clampPageSize,
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
});

test("parseFundPageQuery reads paid_year for Paid history as_of bounds", () => {
  const query = parseFundPageQuery(
    new URLSearchParams("limit=50&offset=0&paid_year=2025&sort=asOfDate&direction=desc"),
  );
  assert.equal(query.paidYear, 2025);
  assert.equal(query.sort, "asOfDate");
  assert.equal(query.direction, "desc");
});
