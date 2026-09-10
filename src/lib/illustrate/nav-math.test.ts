import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { mapFundsApiItem } from "../../data/funds-list.ts";
import { aggregateDistributions, type DataDistribution } from "../../data/aggregate-distributions.ts";
import { mergeFundWithDistributions } from "../../data/hydrate-funds.ts";
import { paidHistoryViews, withPeerContext } from "../../data/queries.ts";
import { sortFunds } from "../format.ts";
import {
  fillNavPerShareInput,
  formatSoftPct,
  formatWeeklyNavLabel,
  historicalPctOfNav,
  parsePositiveNav,
  pctOfNavForFund,
  pctOfNavForUnpaidOrPaid,
  resolvePctOfNav,
  SOFT_DASH,
  upcomingDistDollars,
  upcomingPctOfNav,
  usesDistributionDayNav,
} from "./nav-math.ts";

const here = dirname(fileURLToPath(import.meta.url));

/** Live Data prints verified 2026-09-09 (PR #74). */
const ABALX_WEEKLY_NAV = 40.849998;
const ABALX_WEEKLY_AS_OF = "2026-09-08";
const ABALX_YE_NAV = 37.09;
const ABALX_YE_PER_SHARE = 2.125;
const HOLDING = 1_000_000;

function distRow(
  patch: Partial<DataDistribution> &
    Pick<DataDistribution, "id" | "estimate_type" | "amount" | "amount_unit">,
): DataDistribution {
  return {
    fund_family: "American Funds",
    fund_name: "American Balanced Fund",
    fund_identifier: "american-balanced-fund",
    ticker: "ABALX",
    cusip: "024071102",
    share_class: null,
    amount_min: null,
    amount_max: null,
    record_date: null,
    ex_date: null,
    payable_date: null,
    as_of: "2026-01-22",
    publication_stage: "final",
    ...patch,
  };
}

describe("Eric-locked NAV math", () => {
  it("computes upcoming Dist $ and % of NAV from weekly NAV", () => {
    const est = 3;
    assert.equal(
      upcomingDistDollars(est, HOLDING, ABALX_WEEKLY_NAV),
      est * (HOLDING / ABALX_WEEKLY_NAV),
    );
    assert.equal(
      upcomingPctOfNav(est, ABALX_WEEKLY_NAV),
      (est / ABALX_WEEKLY_NAV) * 100,
    );
  });

  it("locks FCPGX unpaid % of NAV to Dist $/share ÷ weekly NAV (16.9%)", () => {
    const fcpgx = upcomingPctOfNav(7.277, 42.94);
    assert.ok(fcpgx != null);
    assert.equal(Number(fcpgx.toFixed(1)), 16.9);
    assert.equal(
      Number(
        pctOfNavForUnpaidOrPaid({
          unpaid: true,
          perShare: 7.277,
          weeklyNav: 42.94,
          navOnDistributionDay: 37.09,
        })?.toFixed(1),
      ),
      16.9,
      "unpaid must ignore nav_on_distribution_day",
    );
  });

  it("uses dist-day NAV for paid % of NAV and never weekly", () => {
    const paid = pctOfNavForUnpaidOrPaid({
      unpaid: false,
      perShare: ABALX_YE_PER_SHARE,
      weeklyNav: ABALX_WEEKLY_NAV,
      navOnDistributionDay: ABALX_YE_NAV,
    });
    assert.ok(paid != null);
    assert.equal(Number(paid.toFixed(2)), 5.73);
    assert.notEqual(
      Number(paid.toFixed(2)),
      Number((((ABALX_YE_PER_SHARE / ABALX_WEEKLY_NAV) * 100).toFixed(2))),
    );
    assert.equal(
      pctOfNavForUnpaidOrPaid({
        unpaid: false,
        perShare: ABALX_YE_PER_SHARE,
        weeklyNav: ABALX_WEEKLY_NAV,
        navOnDistributionDay: null,
      }),
      null,
      "paid with no day NAV stays undisclosed — never fall back to weekly",
    );
  });

  it("computes historical % of NAV from dist-day NAV, never weekly", () => {
    const historical = historicalPctOfNav(ABALX_YE_PER_SHARE, ABALX_YE_NAV);
    assert.ok(historical != null);
    assert.equal(Number(historical.toFixed(6)), 5.729307);
    const wrongWeekly = historicalPctOfNav(ABALX_YE_PER_SHARE, ABALX_WEEKLY_NAV);
    assert.notEqual(Number(historical.toFixed(6)), Number(wrongWeekly?.toFixed(6)));
    assert.equal(
      resolvePctOfNav({
        perShare: ABALX_YE_PER_SHARE,
        weeklyNav: ABALX_WEEKLY_NAV,
        navOnDistributionDay: ABALX_YE_NAV,
        publicationStage: "final",
        exDate: "2025-12-15",
        today: "2026-09-09",
      }),
      historical,
    );
  });

  it("autofills $ / share from live weekly NAV and keeps a typed print", () => {
    assert.equal(fillNavPerShareInput("", 312.26001), "312.26001");
    assert.equal(fillNavPerShareInput("   ", 312.26001), "312.26001");
    assert.equal(fillNavPerShareInput("310", 312.26001), "310");
    assert.equal(fillNavPerShareInput("", 0), "");
    assert.equal(fillNavPerShareInput("", null), "");
  });

  it("soft-dashes when NAV or the estimate is missing — never invents", () => {
    assert.equal(upcomingPctOfNav(ABALX_YE_PER_SHARE, null), null);
    assert.equal(upcomingPctOfNav(null, ABALX_WEEKLY_NAV), null);
    assert.equal(historicalPctOfNav(ABALX_YE_PER_SHARE, null), null);
    assert.equal(upcomingDistDollars(2.125, HOLDING, 0), null);
    assert.equal(parsePositiveNav(null), null);
    assert.equal(parsePositiveNav(0), null);
    assert.equal(formatSoftPct(null), SOFT_DASH);
    assert.equal(formatWeeklyNavLabel({ nav: 0, navAsOf: null }), SOFT_DASH);
  });

  it("live Aftertax % is Dist $/share ÷ weekly NAV — ignores published percent_of_nav", () => {
    const fcpgxPerShare = 7.277;
    const fcpgxWeeklyNav = 42.94;
    const live = upcomingPctOfNav(fcpgxPerShare, fcpgxWeeklyNav);
    assert.ok(live != null);
    assert.equal(Number(live.toFixed(1)), 16.9);
    assert.equal(
      resolvePctOfNav({
        publishedPctNav: 7.08,
        perShare: fcpgxPerShare,
        weeklyNav: fcpgxWeeklyNav,
        publicationStage: "preliminary_estimate",
        exDate: "2026-12-15",
        today: "2026-09-10",
      }),
      live,
    );
    assert.equal(
      pctOfNavForFund(
        {
          estimatedDistributionAmount: fcpgxPerShare,
          publishedPctOfNav: 7.08,
          estimatedDistributionPctNav: 7.08,
          nav: fcpgxWeeklyNav,
          publicationStage: "preliminary_estimate",
          exDate: "2026-12-15",
        },
        "2026-09-10",
      ),
      live,
    );
    assert.equal(
      resolvePctOfNav({
        publishedPctNav: 1.28,
        perShare: ABALX_YE_PER_SHARE,
        weeklyNav: ABALX_WEEKLY_NAV,
        navOnDistributionDay: ABALX_YE_NAV,
        publicationStage: "final",
        exDate: "2025-12-15",
        today: "2026-09-09",
      }),
      historicalPctOfNav(ABALX_YE_PER_SHARE, ABALX_YE_NAV),
      "paid/final still uses dist-day NAV, not the published % character",
    );
  });
});

describe("Search hydrate live NAV fields", () => {
  it("maps GET /funds weekly NAV for ABALX and keeps it off /distributions 0", () => {
    const catalog = mapFundsApiItem({
      ticker: "ABALX",
      fund_name: "American Balanced Fund",
      fund_family: "American Funds",
      fund_identifier: "american-balanced-fund",
      category: "Moderate Allocation",
      latest_as_of: "2026-01-22",
      has_estimate: false,
      nav_per_share: ABALX_WEEKLY_NAV,
      nav_as_of: ABALX_WEEKLY_AS_OF,
      nav_source: "yahoo_last_close",
    });
    assert.equal(catalog.nav, ABALX_WEEKLY_NAV);
    assert.equal(catalog.navAsOf, ABALX_WEEKLY_AS_OF);
    assert.equal(catalog.navSource, "yahoo_last_close");
    assert.match(formatWeeklyNavLabel(catalog), /\$40\.85/);
    assert.match(formatWeeklyNavLabel(catalog), /Sep 8, 2026/);

    const rows: DataDistribution[] = [
      distRow({
        id: "ltcg-2025",
        estimate_type: "long_term_capital_gains",
        amount: "2.125000",
        amount_unit: "per_share",
        record_date: "2025-12-15",
        ex_date: "2025-12-15",
        payable_date: "2025-12-16",
        nav_on_distribution_day: ABALX_YE_NAV,
        nav_on_distribution_day_as_of: "2025-12-15",
        nav_on_distribution_day_source: "yahoo_last_close",
      }),
    ];
    const aggregated = withPeerContext(aggregateDistributions(rows, "2026-09-09"))[0];
    const merged = mergeFundWithDistributions(catalog, aggregated);
    assert.equal(merged.nav, ABALX_WEEKLY_NAV, "weekly NAV stays from /funds");
    assert.equal(merged.navAsOf, ABALX_WEEKLY_AS_OF);
    assert.equal(merged.navOnDistributionDay, ABALX_YE_NAV);
    assert.equal(merged.navOnDistributionDayAsOf, "2025-12-15");

    const historical = pctOfNavForFund(merged, "2026-09-09");
    assert.ok(historical != null);
    assert.equal(Number(historical.toFixed(2)), 5.73);
    assert.notEqual(
      Number(historical.toFixed(2)),
      Number((((ABALX_YE_PER_SHARE / ABALX_WEEKLY_NAV) * 100).toFixed(2))),
      "must not divide YE $/share by today's weekly NAV",
    );

    const paid = paidHistoryViews([merged])[0];
    assert.ok(paid);
    assert.equal(Number(pctOfNavForFund(paid, "2026-09-09")?.toFixed(2)), 5.73);
  });

  it("uses weekly NAV for unpaid prelim % of NAV", () => {
    const catalog = mapFundsApiItem({
      ticker: "ABALX",
      fund_name: "American Balanced Fund",
      fund_family: "American Funds",
      has_estimate: true,
      nav_per_share: ABALX_WEEKLY_NAV,
      nav_as_of: ABALX_WEEKLY_AS_OF,
    });
    const rows: DataDistribution[] = [
      distRow({
        id: "prelim",
        estimate_type: "total_capital_gains",
        amount: "3.000000",
        amount_unit: "per_share",
        publication_stage: "preliminary_estimate",
        as_of: "2026-08-15",
        record_date: "2026-12-12",
        ex_date: "2026-12-15",
        payable_date: "2026-12-17",
      }),
    ];
    const merged = mergeFundWithDistributions(
      catalog,
      withPeerContext(aggregateDistributions(rows, "2026-09-09"))[0],
    );
    assert.equal(merged.bucket, "upcoming");
    assert.equal(
      Number(pctOfNavForFund(merged, "2026-09-09")?.toFixed(2)),
      Number((((3 / ABALX_WEEKLY_NAV) * 100).toFixed(2))),
    );
    assert.equal(usesDistributionDayNav(merged, "2026-09-09"), false);
  });

  it("Search and IllustrationResults read the shared helper — no invented NAV", () => {
    const table = readFileSync(
      join(here, "../../components/ResultsTable.tsx"),
      "utf8",
    );
    const results = readFileSync(
      join(here, "../../components/illustrate/IllustrationResults.tsx"),
      "utf8",
    );
    const panel = readFileSync(
      join(here, "../../components/illustrate/IllustratePanel.tsx"),
      "utf8",
    );
    const fundsList = readFileSync(join(here, "../../data/funds-list.ts"), "utf8");
    assert.match(table, /pctOfNavForFund/);
    assert.match(table, /formatSoftPct/);
    assert.match(results, /pctOfNavForFund/);
    assert.match(results, /historicalPctOfNav/);
    assert.match(results, /usesDistributionDayNav/);
    assert.match(results, /upcomingPctOfNav\(perShare, weekly\)/);
    assert.doesNotMatch(
      results,
      /if \(published != null\) return formatSoftPct\(published\)/,
    );
    assert.match(panel, /formatWeeklyNavLabel/);
    assert.match(panel, /EstimateLeadCard/);
    assert.match(panel, /Estimated \$ \/ share/);
    assert.match(panel, /Distribution % of NAV/);
    assert.match(panel, /illustrationFundCardTypeRows/);
    assert.match(panel, /overlayWeeklyNav/);
    assert.match(panel, /fillNavPerShareInput/);
    assert.match(panel, /\/api\/funds/);
    assert.match(panel, /nav_only/);
    assert.doesNotMatch(panel, /Weekly NAV/);
    assert.match(panel, /mock \? seedNavLookup/);
    assert.match(fundsList, /nav_per_share/);
    assert.match(fundsList, /parsePositiveNav/);

    const queries = readFileSync(join(here, "../../data/queries.ts"), "utf8");
    const format = readFileSync(join(here, "../format.ts"), "utf8");
    const compareCopy = readFileSync(
      join(here, "portfolio-compare-copy.ts"),
      "utf8",
    );
    const lists = readFileSync(join(here, "../lists/rows.ts"), "utf8");
    assert.doesNotMatch(queries, /pct \?\? fund\.estimatedDistributionPctNav/);
    assert.match(queries, /estimatedDistributionPctNav: pct \?\? 0/);
    assert.match(format, /aftertaxPctOfNavForSort/);
    assert.match(format, /case "estimatedDistributionPctNav"/);
    assert.doesNotMatch(compareCopy, /\?\?[\s\n]+row\.pctOfNav/);
    assert.match(lists, /upcomingPctOfNav\(distPerShare, nav\)/);
  });

  it("withPeerContext overwrites stored published % with Dist ÷ weekly NAV", () => {
    const [view] = withPeerContext([
      {
        id: "fcpgx",
        fundName: "Small Cap Growth",
        ticker: "FCPGX",
        cusip: "000000000",
        family: "Fidelity",
        category: "Small Growth",
        shareClass: "A",
        nav: 42.94,
        estimatedDistributionAmount: 7.277,
        estimatedOrdinaryIncome: 0,
        estimatedCapitalGains: 7.277,
        estimatedDistributionPctNav: 7.08,
        publishedPctOfNav: 7.08,
        publishedAt: "2026-07-31",
        asOfDate: "2026-07-31",
        recordDate: "2026-12-12",
        exDate: "2026-12-15",
        payableDate: "2026-12-17",
        publicationStage: "preliminary_estimate",
        bucket: "upcoming",
        paidHistory: [],
        distributionYear: 2026,
      },
    ]);
    assert.ok(view);
    assert.equal(Number(view.estimatedDistributionPctNav.toFixed(1)), 16.9);
    assert.ok(Math.abs(view.estimatedDistributionPctNav - (7.277 / 42.94) * 100) < 1e-9);
    assert.equal(
      sortFunds([view], "estimatedDistributionPctNav", "desc")[0]?.ticker,
      "FCPGX",
    );
  });
});
