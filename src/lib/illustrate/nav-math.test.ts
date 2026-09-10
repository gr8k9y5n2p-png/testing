import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { mapFundsApiItem } from "../../data/funds-list.ts";
import { aggregateDistributions, type DataDistribution } from "../../data/aggregate-distributions.ts";
import { mergeFundWithDistributions } from "../../data/hydrate-funds.ts";
import { paidHistoryViews, withPeerContext } from "../../data/queries.ts";
import {
  formatSoftPct,
  formatWeeklyNavLabel,
  historicalPctOfNav,
  parsePositiveNav,
  pctOfNavForFund,
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

  it("leaves issuer-published percent_of_nav as-is", () => {
    assert.equal(
      resolvePctOfNav({
        publishedPctNav: 1.28,
        perShare: 2.125,
        weeklyNav: ABALX_WEEKLY_NAV,
        navOnDistributionDay: ABALX_YE_NAV,
        publicationStage: "final",
        exDate: "2025-12-15",
      }),
      1.28,
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
    assert.match(panel, /formatWeeklyNavLabel/);
    assert.match(panel, /EstimateLeadCard/);
    assert.match(panel, /Estimated \$ \/ share/);
    assert.match(panel, /Distribution % of NAV/);
    assert.match(panel, /Estimate types/);
    assert.match(panel, /overlayWeeklyNav/);
    assert.match(panel, /\/api\/funds/);
    assert.doesNotMatch(panel, /Weekly NAV/);
    assert.match(panel, /mock \? seedNavLookup/);
    assert.match(fundsList, /nav_per_share/);
    assert.match(fundsList, /parsePositiveNav/);
  });
});
