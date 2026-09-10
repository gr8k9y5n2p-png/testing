import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { aggregateDistributions, type DataDistribution } from "./aggregate-distributions.ts";
import { mapFundsApiItem } from "./funds-list.ts";
import {
  hideUpcomingAmounts,
  mergeFundWithDistributions,
} from "./hydrate-funds.ts";
import {
  getHighlights,
  paidHistoryViews,
  splitFundsByBucket,
  withPeerContext,
} from "./queries.ts";
import {
  illustrationComponentBucket,
  splitIllustrationComponents,
  upcomingIllustrationTotals,
} from "../lib/illustrate/illustration-upcoming.ts";
import { isUpcomingFund } from "./distribution-bucket.ts";

const here = dirname(fileURLToPath(import.meta.url));

function finalRow(
  ticker: string,
  patch: Partial<DataDistribution> &
    Pick<DataDistribution, "id" | "estimate_type" | "amount" | "amount_unit">,
): DataDistribution {
  return {
    fund_family: "American Funds",
    fund_name: `${ticker} Fund`,
    fund_identifier: ticker.toLowerCase(),
    ticker,
    cusip: null,
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

/** Live ABALX smoke fixture: has_estimate false, finals only. */
const ABALX_FINALS: DataDistribution[] = [
  finalRow("ABALX", {
    id: "abalx-ltcg",
    estimate_type: "long_term_capital_gains",
    amount: "2.125000",
    amount_unit: "per_share",
    record_date: "2025-12-15",
    ex_date: "2025-12-15",
    payable_date: "2025-12-16",
  }),
  finalRow("ABALX", {
    id: "abalx-special",
    estimate_type: "special_dividend",
    amount: "0.340000",
    amount_unit: "per_share",
  }),
];

/** Second finals-only fund so the rule cannot be an ABALX special case. */
const AMECX_FINALS: DataDistribution[] = [
  finalRow("AMECX", {
    id: "amecx-ltcg",
    estimate_type: "long_term_capital_gains",
    amount: "1.500000",
    amount_unit: "per_share",
    record_date: "2025-12-16",
    ex_date: "2025-12-16",
    payable_date: "2025-12-17",
  }),
];

function hydrateFinalsOnly(
  ticker: string,
  fundName: string,
  rows: DataDistribution[],
) {
  const catalog = mapFundsApiItem({
    ticker,
    fund_name: fundName,
    fund_family: "American Funds",
    has_estimate: false,
  });
  const aggregated = withPeerContext(
    aggregateDistributions(rows, "2026-09-09"),
  )[0];
  return mergeFundWithDistributions(catalog, aggregated);
}

describe("universe Upcoming / Fund Manager Estimated Distributions", () => {
  it("keeps AllianceBernstein catalog $0 / past announced rows out of Search Upcoming", () => {
    const today = "2026-09-09";
    const catalogs = [
      mapFundsApiItem({
        ticker: null,
        fund_name: "AB All Market Total Return Portfolio",
        fund_family: "AllianceBernstein",
        latest_as_of: "2025-10-31",
        has_estimate: true,
      }),
      mapFundsApiItem({
        ticker: null,
        fund_name: "AB Global Real Estate Investment Fund",
        fund_family: "AllianceBernstein",
        latest_as_of: "2023-10-31",
        has_estimate: true,
      }),
    ];
    const staleZero: DataDistribution[] = [
      {
        id: "ab-re-2023",
        fund_family: "AllianceBernstein",
        fund_name: "AB Global Real Estate Investment Fund",
        fund_identifier: "ab-global-real-estate-investment-fund",
        ticker: null,
        cusip: null,
        share_class: null,
        estimate_type: "total_capital_gains",
        amount: "0",
        amount_min: null,
        amount_max: null,
        amount_unit: "per_share",
        record_date: null,
        ex_date: null,
        payable_date: null,
        as_of: "2023-10-31",
        publication_stage: "updated_estimate",
      },
    ];
    const realEstate = mergeFundWithDistributions(
      catalogs[1],
      withPeerContext(aggregateDistributions(staleZero, today))[0],
    );
    const book = [...catalogs.map((fund) => mergeFundWithDistributions(fund, null)), realEstate];
    const { upcoming, paid } = splitFundsByBucket(book);
    assert.equal(upcoming.length, 0, "Search Upcoming must not list stale $0 AB rows");
    assert.ok(paid.length >= 1);
    const highlights = getHighlights(book);
    assert.equal(highlights.mostRecent.length, 0);
    assert.equal(highlights.largest.length, 0);
    for (const fund of book) {
      assert.equal(isUpcomingFund(fund, today), false, fund.fundName);
    }
  });

  it("treats every has_estimate:false + finals-only fund as Undisclosed Upcoming", () => {
    const abalx = hydrateFinalsOnly("ABALX", "American Balanced Fund", ABALX_FINALS);
    const amecx = hydrateFinalsOnly(
      "AMECX",
      "The Income Fund of America",
      AMECX_FINALS,
    );

    for (const fund of [abalx, amecx]) {
      assert.equal(fund.hasEstimate, false, `${fund.ticker} hasEstimate`);
      assert.equal(fund.bucket, "paid", `${fund.ticker} bucket`);
      assert.equal(isUpcomingFund(fund), false, `${fund.ticker} isUpcomingFund`);
      assert.equal(hideUpcomingAmounts(fund), false, `${fund.ticker} paid $ visible`);
      const { upcoming, paid } = splitFundsByBucket([fund]);
      assert.equal(upcoming.length, 0, `${fund.ticker} Search Upcoming`);
      assert.equal(paid.length, 1, `${fund.ticker} Paid history`);
    }

    assert.ok(
      paidHistoryViews([abalx]).some(
        (row) => Math.abs(row.estimatedDistributionAmount - 2.125) < 1e-6,
      ),
      "ABALX paid history keeps $2.125/sh finals",
    );
    assert.ok(
      paidHistoryViews([amecx]).some(
        (row) => Math.abs(row.estimatedDistributionAmount - 1.5) < 1e-6,
      ),
      "AMECX paid history keeps finals",
    );

    const highlights = getHighlights([abalx, amecx]);
    assert.equal(highlights.mostRecent.length, 0);
    assert.equal(highlights.largest.length, 0);
  });

  it("does not invent Dollar Illustration Upcoming from finals for any such fund", () => {
    for (const ticker of ["ABALX", "AMECX"] as const) {
      const { upcoming } = splitIllustrationComponents(
        [
          {
            distribution_id: `${ticker}-final`,
            fund_name: ticker,
            estimate_type: "long_term_capital_gains",
            amount_unit: "per_share",
            publication_stage: "final",
            as_of: "2026-08-29",
            record_date: "2026-12-12",
            ex_date: "2026-12-15",
            payable_date: "2026-12-17",
            distribution_dollars: 15_750,
            distribution_dollars_min: 17_400,
            distribution_dollars_max: 26_100,
            rate_key: "ordinary_income",
            federal_rate: 0.37,
            state_rate: 0.05,
            effective_rate: 0.42,
            estimated_tax_dollars: 15_750,
            estimated_tax_dollars_min: null,
            estimated_tax_dollars_max: null,
            notes: null,
          },
        ],
        { hasEstimate: false },
      );
      assert.equal(upcoming.length, 0, `${ticker} illustration Upcoming`);
      assert.equal(upcomingIllustrationTotals(upcoming), null);
      assert.equal(
        illustrationComponentBucket(
          {
            publication_stage: "final",
            as_of: "2026-08-29",
            record_date: "2026-12-12",
            ex_date: "2026-12-15",
            payable_date: "2026-12-17",
          },
          { hasEstimate: false },
        ),
        "paid",
      );
    }
  });

  it("Search / detail / badge surfaces share the classifier — no ticker allowlist", () => {
    const files = [
      "distribution-bucket.ts",
      "hydrate-funds.ts",
      "../components/ResultsTable.tsx",
      "../components/DeltaBadge.tsx",
      "../components/HighlightCard.tsx",
      "../components/illustrate/IllustrationResults.tsx",
      "../components/illustrate/IllustrationPaidHistory.tsx",
      "../components/illustrate/FundPicker.tsx",
      "../lib/illustrate/illustration-upcoming.ts",
      "../lib/illustrate/publication-stage.ts",
    ];
    for (const relative of files) {
      const source = readFileSync(join(here, relative), "utf8");
      assert.doesNotMatch(
        source,
        /ticker\s*===?\s*["']ABALX["']|ABALX\s*===/,
        `${relative} must not special-case ABALX`,
      );
    }
    const table = readFileSync(join(here, "../components/ResultsTable.tsx"), "utf8");
    const highlights = readFileSync(join(here, "queries.ts"), "utf8");
    const badges = readFileSync(join(here, "../components/DeltaBadge.tsx"), "utf8");
    const results = readFileSync(
      join(here, "../components/illustrate/IllustrationResults.tsx"),
      "utf8",
    );
    const paid = readFileSync(
      join(here, "../components/illustrate/IllustrationPaidHistory.tsx"),
      "utf8",
    );
    const panel = readFileSync(
      join(here, "../components/illustrate/IllustratePanel.tsx"),
      "utf8",
    );
    const bucket = readFileSync(join(here, "distribution-bucket.ts"), "utf8");
    const catalog = readFileSync(join(here, "funds-list.ts"), "utf8");
    assert.match(table, /splitFundsByBucket/);
    assert.match(table, /SEARCH_PAID_HISTORY_HEADING/);
    assert.match(table, /showHeading/);
    assert.match(table, /paidHistoryViews/);
    assert.match(highlights, /buildSearchTableFunds/);
    assert.match(highlights, /splitFundsByBucket/);
    assert.match(highlights, /pickHighlightsCalendarYear/);
    assert.match(highlights, /highlightsCalendarYear/);
    assert.match(highlights, /withPeerContext\(scoped\)/);
    assert.match(badges, /hideUpcomingAmounts/);
    assert.doesNotMatch(results, /paidEventsForFund/);
    assert.doesNotMatch(results, /paidComponents/);
    assert.match(panel, /IllustrationPaidHistory/);
    assert.match(paid, /illustrationPaidTypeRows/);
    assert.match(paid, /SEARCH_PAID_HISTORY_HEADING/);
    assert.match(bucket, /hasDisclosedUpcomingAmount/);
    assert.match(bucket, /isStaleAnnouncedOnly/);
    assert.match(catalog, /never invent an/);
  });
});
