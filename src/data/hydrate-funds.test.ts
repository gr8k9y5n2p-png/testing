import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { aggregateDistributions, type DataDistribution } from "./aggregate-distributions.ts";
import { mapFundsApiItem } from "./funds-list.ts";
import {
  hideUpcomingAmounts,
  mergeFundLists,
  mergeFundWithDistributions,
  paidEventsForFund,
  preferFinalPaidEvents,
} from "./hydrate-funds.ts";
import { paidHistoryViews, splitFundsByBucket, withPeerContext } from "./queries.ts";

function row(
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

/** Live Cap Group YE LTCG for ABALX (Data API 2026-09-09). */
const ABALX_ROWS: DataDistribution[] = [
  row({
    id: "ltcg-2025",
    estimate_type: "long_term_capital_gains",
    amount: "2.125000",
    amount_unit: "per_share",
    record_date: "2025-12-15",
    ex_date: "2025-12-15",
    payable_date: "2025-12-16",
    as_of: "2026-01-22",
  }),
  row({
    id: "qd-2025",
    estimate_type: "qualified_dividend",
    amount: "41.940000",
    amount_unit: "percent",
  }),
  row({
    id: "special-2025",
    estimate_type: "special_dividend",
    amount: "0.340000",
    amount_unit: "per_share",
  }),
  row({
    id: "ltcg-2024",
    estimate_type: "long_term_capital_gains",
    amount: "1.748500",
    amount_unit: "per_share",
    record_date: "2024-12-16",
    ex_date: "2024-12-16",
    payable_date: "2024-12-17",
    as_of: "2025-01-22",
  }),
];

describe("Search hydrate from /distributions", () => {
  it("surfaces ABALX YE LTCG $2.125 in paid history, not Upcoming", () => {
    const catalog = mapFundsApiItem({
      ticker: "ABALX",
      fund_name: "American Balanced Fund",
      fund_family: "American Funds",
      fund_identifier: "american-balanced-fund",
      category: "Moderate Allocation",
      latest_as_of: "2026-01-22",
      has_estimate: false,
    });
    assert.equal(catalog.hasEstimate, false);
    assert.equal(catalog.estimatedDistributionAmount, 0);
    assert.equal(catalog.paidHistory.length, 0);

    const aggregated = withPeerContext(
      aggregateDistributions(ABALX_ROWS, "2026-09-09"),
    );
    assert.equal(aggregated.length, 1);
    assert.equal(aggregated[0].bucket, "paid");
    assert.equal(aggregated[0].estimatedDistributionAmount, 2.125);

    const merged = mergeFundWithDistributions(catalog, aggregated[0]);
    assert.equal(merged.ticker, "ABALX");
    assert.equal(merged.fundName, "American Balanced Fund");
    assert.equal(merged.hasEstimate, false);
    assert.equal(merged.bucket, "paid");
    assert.equal(merged.estimatedDistributionAmount, 2.125);
    assert.equal(hideUpcomingAmounts(merged), false);

    const { upcoming, paid } = splitFundsByBucket([merged]);
    assert.equal(upcoming.length, 0);
    assert.equal(paid.length, 1);

    const history = paidHistoryViews([merged]);
    assert.ok(
      history.some((fund) => Math.abs(fund.estimatedDistributionAmount - 2.125) < 1e-6),
      "paid history must list the $2.125/sh YE LTCG row",
    );
    assert.ok(
      paidEventsForFund(merged).some(
        (event) => Math.abs(event.estimatedDistributionAmount - 2.125) < 1e-6,
      ),
    );
  });

  it("does not invent Upcoming from future-dated finals when has_estimate is false", () => {
    const catalog = mapFundsApiItem({
      ticker: "ABALX",
      fund_name: "American Balanced Fund",
      fund_family: "American Funds",
      has_estimate: false,
    });
    const futureFinals: DataDistribution[] = [
      row({
        id: "ltcg-future",
        estimate_type: "long_term_capital_gains",
        amount: "2.125000",
        amount_unit: "per_share",
        publication_stage: "final",
        as_of: "2026-08-15",
        record_date: "2026-12-15",
        ex_date: "2026-12-15",
        payable_date: "2026-12-16",
      }),
    ];
    const aggregated = aggregateDistributions(futureFinals, "2026-09-09")[0];
    assert.equal(aggregated.bucket, "paid");
    const merged = mergeFundWithDistributions(catalog, aggregated);
    assert.equal(merged.bucket, "paid");
    assert.equal(merged.hasEstimate, false);
    assert.equal(merged.estimatedDistributionAmount, 2.125);
    assert.equal(splitFundsByBucket([merged]).upcoming.length, 0);
    assert.ok(
      paidHistoryViews([merged]).some(
        (fund) => Math.abs(fund.estimatedDistributionAmount - 2.125) < 1e-6,
      ),
    );
  });

  it("does not invent Upcoming from paid-only rows when has_estimate is false", () => {
    const catalog = mapFundsApiItem({
      ticker: "ABALX",
      fund_name: "American Balanced Fund",
      fund_family: "American Funds",
      has_estimate: false,
    });
    const aggregated = aggregateDistributions(ABALX_ROWS, "2026-09-09")[0];
    const merged = mergeFundWithDistributions(catalog, aggregated);
    assert.equal(merged.bucket, "paid");
    assert.equal(merged.hasEstimate, false);
    assert.equal(splitFundsByBucket([merged]).upcoming.length, 0);
  });

  it("does not leak FXAIX/VFIAX latest_as_of YE dates into Upcoming", () => {
    const catalogs = [
      mapFundsApiItem({
        ticker: "FXAIX",
        fund_name: "500 Index",
        fund_family: "Fidelity",
        latest_as_of: "2025-12-31",
        has_estimate: false,
      }),
      mapFundsApiItem({
        ticker: "VFIAX",
        fund_name: "500 Index Fund Admiral Shares",
        fund_family: "Vanguard",
        latest_as_of: "2025-12-24",
        has_estimate: false,
      }),
    ];
    for (const catalog of catalogs) {
      assert.equal(catalog.bucket, "paid");
      assert.equal(catalog.hasEstimate, false);
      const missing = mergeFundWithDistributions(catalog, null);
      assert.equal(missing.bucket, "paid");
      assert.equal(missing.hasEstimate, false);
      assert.equal(splitFundsByBucket([catalog, missing]).upcoming.length, 0);
      assert.equal(paidHistoryViews([catalog, missing]).length, 0);
    }
  });

  it("prefers a hydrated paid row over an unhydrated catalog duplicate", () => {
    const empty = mapFundsApiItem({
      ticker: "ABALX",
      fund_name: "American Balanced Fund",
      fund_family: "American Funds",
      latest_as_of: "2026-01-22",
      has_estimate: false,
    });
    const aggregated = withPeerContext(
      aggregateDistributions(ABALX_ROWS, "2026-09-09"),
    )[0];
    const hydrated = mergeFundWithDistributions(empty, aggregated);
    const merged = mergeFundLists([hydrated], [empty]);
    assert.equal(merged.length, 1);
    assert.equal(merged[0].estimatedDistributionAmount, 2.125);
    assert.equal(merged[0].bucket, "paid");
  });

  it("keeps an unpaid prelim in Upcoming and paid YE in history", () => {
    const rows: DataDistribution[] = [
      row({
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
      ABALX_ROWS[0],
    ];
    const catalog = mapFundsApiItem({
      ticker: "ABALX",
      fund_name: "American Balanced Fund",
      fund_family: "American Funds",
      has_estimate: true,
    });
    const aggregated = withPeerContext(aggregateDistributions(rows, "2026-09-09"))[0];
    const merged = mergeFundWithDistributions(catalog, aggregated);
    assert.equal(merged.bucket, "upcoming");
    assert.equal(merged.hasEstimate, true);
    assert.equal(merged.estimatedDistributionAmount, 3);
    assert.ok(
      merged.paidHistory.some(
        (event) => Math.abs(event.estimatedDistributionAmount - 2.125) < 1e-6,
      ),
    );
  });

  it("prefers YE finals over same-year prelim rows in Paid history", () => {
    const prelim = {
      asOfDate: "2025-10-01",
      recordDate: "2025-12-15",
      exDate: "2025-12-15",
      payableDate: "2025-12-16",
      publicationStage: "preliminary_estimate",
      estimatedDistributionAmount: 1.8,
      estimatedOrdinaryIncome: 0,
      estimatedCapitalGains: 1.8,
      estimatedDistributionPctNav: 0,
      distributionYear: 2025,
    };
    const final = {
      ...prelim,
      asOfDate: "2026-01-22",
      publicationStage: "final",
      estimatedDistributionAmount: 2.125,
      estimatedCapitalGains: 2.125,
      distributionYear: 2026,
    };
    const preferred = preferFinalPaidEvents([prelim, final]);
    assert.equal(preferred.length, 1);
    assert.equal(preferred[0].estimatedDistributionAmount, 2.125);
    assert.equal(preferred[0].publicationStage, "final");

    const catalog = mapFundsApiItem({
      ticker: "ABALX",
      fund_name: "American Balanced Fund",
      fund_family: "American Funds",
      has_estimate: false,
    });
    const merged = mergeFundWithDistributions(catalog, {
      ...aggregateDistributions(ABALX_ROWS, "2026-09-09")[0],
      paidHistory: [prelim, final],
    });
    const events = paidEventsForFund(merged);
    assert.ok(
      events.every(
        (event) =>
          (event.publicationStage ?? "").toLowerCase() !== "preliminary_estimate",
      ),
      "same-year prelim must not label Paid history when a final exists",
    );
    assert.ok(
      events.some((event) => Math.abs(event.estimatedDistributionAmount - 2.125) < 1e-6),
    );
    assert.ok(
      events.every((event) => event.estimatedDistributionAmount < 100),
      "Paid history stays per-share from /distributions, not illustration $",
    );
  });

  it("does not invent a $0 Paid history row from an unhydrated catalog", () => {
    const catalog = mapFundsApiItem({
      ticker: "ZZZZX",
      fund_name: "Unknown",
      fund_family: "Unknown",
      has_estimate: false,
    });
    assert.equal(paidEventsForFund(catalog).length, 0);
  });

  it("hides Upcoming $ amounts only — not paid history", () => {
    assert.equal(
      hideUpcomingAmounts({ bucket: "upcoming", hasEstimate: false }),
      true,
    );
    assert.equal(
      hideUpcomingAmounts({ bucket: "paid", hasEstimate: false }),
      false,
    );
    assert.equal(
      hideUpcomingAmounts({ bucket: "upcoming", hasEstimate: true }),
      false,
    );
  });
});
