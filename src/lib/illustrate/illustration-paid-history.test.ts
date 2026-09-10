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
import { mergeFundWithDistributions, paidEventsForFund } from "../../data/hydrate-funds.ts";
import {
  illustrationPriorYearPaidEvents,
  priorPaidHistoryYear,
  withPeerContext,
} from "../../data/queries.ts";
import {
  illustrationPaidHistoryYear,
  illustrationPaidTypeRows,
} from "./illustration-paid-history.ts";

const here = dirname(fileURLToPath(import.meta.url));
const TODAY = "2026-09-10";
const NOW = new Date("2026-09-10T17:00:00Z");

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
    as_of: "2026-07-31",
    publication_stage: "preliminary_estimate",
  }),
  row({
    id: "fbgrx-ye-ltcg",
    ticker: "FBGRX",
    fund_name: "Blue Chip Growth",
    estimate_type: "long_term_capital_gains",
    amount: "5.073000",
    amount_unit: "per_share",
    record_date: "2025-09-12",
    ex_date: "2025-09-12",
    payable_date: "2025-09-15",
    as_of: "2025-12-31",
    publication_stage: "final",
    nav_on_distribution_day: "240.000000",
    nav_on_distribution_day_as_of: "2025-09-12",
  }),
  row({
    id: "fbgrx-ye-stcg",
    ticker: "FBGRX",
    fund_name: "Blue Chip Growth",
    estimate_type: "short_term_capital_gains",
    amount: "0.000000",
    amount_unit: "per_share",
    record_date: "2025-09-12",
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
    estimate_type: "long_term_capital_gains",
    amount: "3.536500",
    amount_unit: "per_share",
    record_date: "2026-06-16",
    ex_date: "2026-06-16",
    payable_date: "2026-06-17",
    as_of: "2026-07-08",
    publication_stage: "paid",
  }),
  row({
    id: "amcpx-ye-2025",
    ticker: "AMCPX",
    fund_name: "AMCAP Fund",
    fund_family: "American Funds",
    estimate_type: "long_term_capital_gains",
    amount: "2.125000",
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
  rows: DataDistribution[],
) {
  const catalog = mapFundsApiItem({
    ticker,
    fund_name: fundName,
    fund_family: family,
    has_estimate: true,
  });
  const aggregated = withPeerContext(aggregateDistributions(rows, TODAY))[0];
  return mergeFundWithDistributions(catalog, aggregated);
}

describe("Dollar Illustration prior-year Paid History", () => {
  it("uses the prior Chicago calendar year (2026 → 2025)", () => {
    assert.equal(priorPaidHistoryYear(NOW), 2025);
    assert.equal(illustrationPaidHistoryYear(NOW), 2025);
    assert.equal(
      priorPaidHistoryYear(new Date("2027-01-01T05:00:00Z")),
      2025,
      "year-end wipe follows America/Chicago, not UTC",
    );
    assert.equal(priorPaidHistoryYear(new Date("2027-01-01T07:00:00Z")), 2026);
  });

  it("lists FBGRX 2025 YE $5.073 / sh final and published $0 STCG", () => {
    const fund = hydrate("FBGRX", "Blue Chip Growth", "Fidelity", FBGRX_ROWS);
    const events = illustrationPriorYearPaidEvents(fund, NOW);
    assert.equal(events.length, 1);
    assert.ok(Math.abs(events[0]!.estimatedDistributionAmount - 5.073) < 1e-6);
    assert.equal(events[0]!.publicationStage, "final");
    assert.equal(events[0]!.exDate, "2025-09-12");
    assert.ok(
      (events[0]!.estimateTypeLines ?? []).some(
        (line) =>
          line.estimateType === "short_term_capital_gains" && line.amount === 0,
      ),
      "published $0 STCG stays on the 2025 final",
    );

    const rows = illustrationPaidTypeRows(fund, NOW);
    assert.equal(rows.length, 2);
    const ltcg = rows.find((row) => row.estimateType === "long_term_capital_gains");
    const stcg = rows.find((row) => row.estimateType === "short_term_capital_gains");
    assert.ok(ltcg);
    assert.ok(stcg);
    assert.ok(Math.abs((ltcg.perShare ?? NaN) - 5.073) < 1e-6);
    assert.equal(stcg.perShare, 0);
    assert.ok(ltcg.pctOfNav != null && Math.abs(ltcg.pctOfNav - (5.073 / 240) * 100) < 1e-6);
    assert.equal(stcg.pctOfNav, 0);
    assert.equal(ltcg.asOfDate, "2025-12-31");
    assert.equal(ltcg.recordDate, "2025-09-12");
    assert.equal(ltcg.exDate, "2025-09-12");
    assert.equal(
      rows.some((row) => Math.abs((row.perShare ?? 0) - 21.021) < 1e-6),
      false,
      "2026 unpaid prelim must not mix into Paid History",
    );
  });

  it("excludes AMCPX 2026 midyear paid and keeps only the 2025 final", () => {
    const fund = hydrate("AMCPX", "AMCAP Fund", "American Funds", AMCPX_ROWS);
    assert.ok(
      paidEventsForFund(fund).some(
        (event) => Math.abs(event.estimatedDistributionAmount - 3.5365) < 1e-6,
      ),
      "2026 midyear remains on the fund for Search Paid History",
    );
    const events = illustrationPriorYearPaidEvents(fund, NOW);
    assert.equal(events.length, 1);
    assert.ok(Math.abs(events[0]!.estimatedDistributionAmount - 2.125) < 1e-6);
    assert.equal(events[0]!.exDate, "2025-12-15");
    const rows = illustrationPaidTypeRows(fund, NOW);
    assert.equal(rows.length, 1);
    assert.ok(Math.abs((rows[0]!.perShare ?? NaN) - 2.125) < 1e-6);
    assert.equal(
      rows.some((row) => Math.abs((row.perShare ?? 0) - 3.5365) < 1e-6),
      false,
    );
  });

  it("does not invent unpublished estimate types and leaves missing % of NAV as null", () => {
    const fund = hydrate("AMCPX", "AMCAP Fund", "American Funds", [
      row({
        id: "amcpx-ye-only",
        ticker: "AMCPX",
        fund_name: "AMCAP Fund",
        fund_family: "American Funds",
        estimate_type: "long_term_capital_gains",
        amount: "2.125000",
        amount_unit: "per_share",
        record_date: "2025-12-12",
        ex_date: "2025-12-15",
        payable_date: "2025-12-16",
        as_of: "2025-12-31",
        publication_stage: "final",
      }),
    ]);
    const rows = illustrationPaidTypeRows(fund, NOW);
    assert.equal(rows.length, 1);
    assert.equal(rows[0]!.estimateType, "long_term_capital_gains");
    assert.equal(rows[0]!.pctOfNav, null, "no day NAV and no published % → never invent");
    assert.equal(
      rows.some((row) => row.estimateType === "ordinary_income"),
      false,
    );
  });

  it("mounts full-bleed under Holding + Estimated, not the right column", () => {
    const panel = readFileSync(
      join(here, "../../components/illustrate/IllustratePanel.tsx"),
      "utf8",
    );
    const paid = readFileSync(
      join(here, "../../components/illustrate/IllustrationPaidHistory.tsx"),
      "utf8",
    );
    const results = readFileSync(
      join(here, "../../components/illustrate/IllustrationResults.tsx"),
      "utf8",
    );
    assert.match(panel, /space-y-6/);
    assert.match(panel, /lg:grid-cols-12/);
    assert.match(panel, /<\/div>\s*<IllustrationPaidHistory/);
    assert.doesNotMatch(results, /IllustrationPaidHistory/);
    assert.doesNotMatch(results, /paidEventsForFund/);
    assert.match(paid, /w-full/);
    assert.match(paid, /illustrationPaidTypeRows/);
    assert.match(paid, /ILLUSTRATION_PAID_HISTORY_KICKER/);
    assert.match(paid, /ILLUSTRATION_PAID_HISTORY_DETAIL/);
    assert.match(paid, /fetchTickerDistributions/);
    assert.match(paid, /\/api\/funds/);
    assert.doesNotMatch(paid, /params\.set\("nav_only"/);
  });
});
