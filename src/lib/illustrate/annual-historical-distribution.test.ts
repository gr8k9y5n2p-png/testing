import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { aggregateDistributions, type DataDistribution } from "../../data/aggregate-distributions.ts";
import { mapFundsApiItem } from "../../data/funds-list.ts";
import { mergeFundWithDistributions } from "../../data/hydrate-funds.ts";
import { withPeerContext } from "../../data/queries.ts";
import {
  annualHistoricalDistributionBars,
  formatAnnualHistoricalBar,
} from "./annual-historical-distribution.ts";

const here = dirname(fileURLToPath(import.meta.url));

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

/** Live Cap Group YE rows for ABALX (Data API 2026-09-09). Finals only. */
const ABALX_ROWS: DataDistribution[] = [
  row({
    id: "ltcg-2025",
    estimate_type: "long_term_capital_gains",
    amount: "2.125000",
    amount_unit: "per_share",
    record_date: "2025-12-15",
    ex_date: "2025-12-15",
    payable_date: "2025-12-16",
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

function hydrateAbalx() {
  const catalog = mapFundsApiItem({
    ticker: "ABALX",
    fund_name: "American Balanced Fund",
    fund_family: "American Funds",
    fund_identifier: "american-balanced-fund",
    category: "Moderate Allocation",
    latest_as_of: "2026-01-22",
    has_estimate: false,
  });
  const aggregated = withPeerContext(
    aggregateDistributions(ABALX_ROWS, "2026-09-09"),
  )[0];
  return mergeFundWithDistributions(catalog, aggregated);
}

describe("annual historical distribution bars", () => {
  it("charts ABALX finals as green-only and never invents a red estimate", () => {
    const fund = hydrateAbalx();
    assert.equal(fund.hasEstimate, false);
    const bars = annualHistoricalDistributionBars(fund);
    assert.ok(bars.length >= 2);
    assert.equal(
      bars.some((bar) => bar.tone === "estimate"),
      false,
    );
    assert.ok(bars.every((bar) => bar.tone === "paid"));
    const y2026 = bars.find((bar) => bar.year === 2026);
    assert.ok(y2026);
    assert.ok(Math.abs(y2026.value - 2.465) < 1e-6, "2.125 YE + 0.34 special");
    const y2025 = bars.find((bar) => bar.year === 2025);
    assert.ok(y2025);
    assert.ok(Math.abs(y2025.value - 1.7485) < 1e-6);
  });

  it("does not invent a red bar from paid-only rows or illustration totals", () => {
    const fund = hydrateAbalx();
    assert.deepEqual(
      annualHistoricalDistributionBars({
        ...fund,
        estimatedDistributionAmount: 99,
        hasEstimate: false,
        bucket: "paid",
      }).map((bar) => bar.tone),
      ["paid", "paid"],
    );
    assert.deepEqual(annualHistoricalDistributionBars(null), []);
    assert.deepEqual(annualHistoricalDistributionBars(undefined), []);
  });

  it("adds a red bar only for live unpaid prelim / manager announced", () => {
    const rows: DataDistribution[] = [
      row({
        id: "prelim",
        ticker: "FBGRX",
        fund_name: "Blue Chip Growth",
        fund_identifier: "fbgrx",
        fund_family: "Fidelity",
        estimate_type: "long_term_capital_gains",
        amount: "21.021000",
        amount_unit: "per_share",
        publication_stage: "preliminary_estimate",
        as_of: "2026-07-31",
        ex_date: "2026-09-11",
        payable_date: "2026-09-14",
      }),
      row({
        id: "paid-2025",
        ticker: "FBGRX",
        fund_name: "Blue Chip Growth",
        fund_identifier: "fbgrx",
        fund_family: "Fidelity",
        estimate_type: "long_term_capital_gains",
        amount: "5.073000",
        amount_unit: "per_share",
        publication_stage: "final",
        as_of: "2025-12-31",
        ex_date: "2025-09-12",
        payable_date: "2025-09-15",
      }),
    ];
    const catalog = mapFundsApiItem({
      ticker: "FBGRX",
      fund_name: "Blue Chip Growth",
      fund_family: "Fidelity",
      has_estimate: true,
    });
    const aggregated = withPeerContext(aggregateDistributions(rows, "2026-09-09"))[0];
    const merged = mergeFundWithDistributions(catalog, aggregated);
    assert.equal(merged.bucket, "upcoming");
    assert.equal(merged.hasEstimate, true);

    const bars = annualHistoricalDistributionBars(merged);
    const estimate = bars.find((bar) => bar.tone === "estimate");
    const paid = bars.filter((bar) => bar.tone === "paid");
    assert.ok(estimate);
    assert.equal(estimate.year, 2026);
    assert.ok(Math.abs(estimate.value - 21.021) < 1e-6);
    assert.equal(paid.length, 1);
    assert.equal(paid[0]?.year, 2025);
    assert.ok(Math.abs((paid[0]?.value ?? 0) - 5.073) < 1e-6);
    assert.equal(
      bars.some((bar) => bar.year === 2026 && bar.tone === "paid"),
      false,
    );
  });

  it("formats bars as $ / share to four decimals", () => {
    assert.equal(formatAnnualHistoricalBar(2.125), "$2.1250");
    assert.equal(formatAnnualHistoricalBar(1.7485), "$1.7485");
  });

  it("IllustrationResults mounts YoYTaxChart between Upcoming and Paid history", () => {
    const results = readFileSync(
      join(here, "../../components/illustrate/IllustrationResults.tsx"),
      "utf8",
    );
    assert.match(results, /annualHistoricalDistributionBars/);
    assert.match(results, /YoYTaxChart/);
    assert.match(results, /Annual historical distribution/);
    const upcomingIdx = results.indexOf("Upcoming / announced");
    const chartIdx = results.indexOf("Annual historical distribution");
    const paidIdx = results.indexOf('heading="Paid history"');
    assert.ok(upcomingIdx > 0 && chartIdx > upcomingIdx && paidIdx > chartIdx);
  });
});
