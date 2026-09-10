import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { aggregateDistributions, type DataDistribution } from "../../data/aggregate-distributions.ts";
import { isUpcomingFund } from "../../data/distribution-bucket.ts";
import { paidHistoryViews, withPeerContext } from "../../data/queries.ts";

const here = dirname(fileURLToPath(import.meta.url));

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
    as_of: "2025-12-31",
    publication_stage: "final",
    ...patch,
  };
}

describe("Search Paid History year-book page", () => {
  it("pages GET /distributions finals/paid only — never walks the book or Upcoming", () => {
    const source = readFileSync(join(here, "paid-history-page.ts"), "utf8");
    const dists = readFileSync(join(here, "distributions.ts"), "utf8");
    const dashboard = readFileSync(join(here, "../../components/Dashboard.tsx"), "utf8");
    const table = readFileSync(join(here, "../../components/ResultsTable.tsx"), "utf8");
    assert.match(source, /publicationStage: "final"/);
    assert.match(source, /publicationStage: "paid"/);
    assert.match(source, /isFinalOrPaidRow/);
    assert.match(source, /isUpcomingFund/);
    assert.doesNotMatch(source, /DISTRIBUTION_MAX_PAGES/);
    assert.doesNotMatch(source, /preliminary_estimate/);
    assert.doesNotMatch(source, /updated_estimate/);
    assert.doesNotMatch(source, /SAMPLE_FUNDS|from ["']@\/data\/seed["']/);
    assert.match(dists, /loadDistributionPage/);
    assert.match(dists, /Never walks the book/);
    assert.match(dashboard, /paid_history/);
    assert.match(dashboard, /paidFunds/);
    assert.match(table, /paidFunds \?\? funds/);
    assert.match(table, /page=\{paidPage\}/);
  });

  it("keeps published $0 finals and drops Upcoming prelims from the year book", () => {
    const rows: DataDistribution[] = [
      row({
        id: "zero-stcg",
        ticker: "FXAIX",
        estimate_type: "short_term_capital_gains",
        amount: "0.000000",
        amount_unit: "per_share",
        ex_date: "2025-12-12",
        payable_date: "2025-12-15",
        publication_stage: "final",
        fund_family: "Fidelity",
        category: "Large Blend",
      }),
      row({
        id: "prelim",
        ticker: "FBGRX",
        estimate_type: "long_term_capital_gains",
        amount: "21.021000",
        amount_unit: "per_share",
        ex_date: "2026-09-11",
        as_of: "2026-07-31",
        publication_stage: "preliminary_estimate",
        fund_family: "Fidelity",
      }),
    ];
    const finalsOnly = rows.filter((item) => {
      const stage = (item.publication_stage ?? "").trim().toLowerCase();
      return stage === "final" || stage === "paid";
    });
    assert.equal(finalsOnly.length, 1);
    const funds = withPeerContext(aggregateDistributions(finalsOnly));
    assert.equal(funds.some((fund) => isUpcomingFund(fund)), false);
    const history = paidHistoryViews(funds, 2025);
    assert.ok(
      history.some(
        (fund) => fund.ticker === "FXAIX" && fund.estimatedDistributionAmount === 0,
      ),
      "published $0 final stays in Paid History",
    );
    assert.equal(
      history.some((fund) => fund.ticker === "FBGRX"),
      false,
      "Upcoming prelim must not enter Paid History",
    );
  });
});
