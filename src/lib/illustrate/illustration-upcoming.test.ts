import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import type { IllustrationComponent } from "./types.ts";
import { illustrationRequestNav, perShareNavError } from "./compare-request.ts";
import {
  illustrationComponentBucket,
  splitIllustrationComponents,
  upcomingEstimateTypeRows,
  upcomingIllustrationTotals,
} from "./illustration-upcoming.ts";

const here = dirname(fileURLToPath(import.meta.url));

function component(
  patch: Partial<IllustrationComponent> &
    Pick<IllustrationComponent, "distribution_id" | "estimate_type">,
): IllustrationComponent {
  return {
    fund_name: "American Balanced Fund",
    amount_unit: "per_share",
    publication_stage: "final",
    as_of: "2026-01-22",
    record_date: null,
    ex_date: null,
    payable_date: null,
    distribution_dollars: null,
    distribution_dollars_min: null,
    distribution_dollars_max: null,
    rate_key: "long_term_capital_gains",
    federal_rate: 0.2,
    state_rate: 0.05,
    effective_rate: 0.25,
    estimated_tax_dollars: null,
    estimated_tax_dollars_min: null,
    estimated_tax_dollars_max: null,
    notes: null,
    ...patch,
  };
}

/** Holding-scaled Dollar Illustration of live ABALX finals (no unpaid prelim). */
const ABALX_ILLUSTRATION: IllustrationComponent[] = [
  component({
    distribution_id: "ltcg-2025",
    estimate_type: "long_term_capital_gains",
    publication_stage: "final",
    as_of: "2026-01-22",
    record_date: "2025-12-15",
    ex_date: "2025-12-15",
    payable_date: "2025-12-16",
    distribution_dollars: 63_000,
    estimated_tax_dollars: 15_750,
  }),
  component({
    distribution_id: "qd-2025",
    estimate_type: "qualified_dividend",
    amount_unit: "percent",
    publication_stage: "final",
    as_of: "2026-01-22",
    distribution_dollars: 21_750,
    distribution_dollars_min: 17_400,
    distribution_dollars_max: 26_100,
    estimated_tax_dollars: 5_437.5,
    rate_key: "qualified_dividend",
  }),
  component({
    distribution_id: "special-2025",
    estimate_type: "special_dividend",
    publication_stage: "final",
    as_of: "2026-01-22",
    distribution_dollars: 10_080,
    estimated_tax_dollars: 4_233.6,
  }),
  component({
    distribution_id: "ltcg-2024",
    estimate_type: "long_term_capital_gains",
    publication_stage: "final",
    as_of: "2025-01-22",
    record_date: "2024-12-16",
    ex_date: "2024-12-16",
    payable_date: "2024-12-17",
    distribution_dollars: 51_820,
    estimated_tax_dollars: 12_955,
  }),
];

describe("Dollar Illustration Upcoming gate", () => {
  it("keeps finals-only illustration (ABALX smoke fixture) out of Upcoming", () => {
    const fund = { hasEstimate: false as const };
    const { upcoming, paid } = splitIllustrationComponents(ABALX_ILLUSTRATION, fund);
    assert.equal(upcoming.length, 0);
    assert.equal(paid.length, 4);
    assert.equal(upcomingIllustrationTotals(upcoming), null);
    assert.equal(
      illustrationComponentBucket(
        {
          publication_stage: "final",
          as_of: "2026-12-15",
          record_date: "2026-12-15",
          ex_date: "2026-12-15",
          payable_date: "2026-12-16",
        },
        fund,
      ),
      "paid",
    );
  });

  it("does not use illustration totals when every component is final", () => {
    const { upcoming } = splitIllustrationComponents(ABALX_ILLUSTRATION);
    assert.equal(upcoming.length, 0);
    assert.equal(upcomingIllustrationTotals(upcoming), null);
  });

  it("sums only unpaid prelim components, not paid YE illustration math", () => {
    const prelim = component({
      distribution_id: "prelim",
      estimate_type: "total_capital_gains",
      publication_stage: "preliminary_estimate",
      as_of: "2026-08-15",
      record_date: "2026-12-12",
      ex_date: "2026-12-15",
      payable_date: "2026-12-17",
      distribution_dollars: 3_200,
      estimated_tax_dollars: 800,
    });
    const { upcoming, paid } = splitIllustrationComponents(
      [...ABALX_ILLUSTRATION, prelim],
      { hasEstimate: true },
    );
    assert.equal(upcoming.length, 1);
    assert.equal(paid.length, 4);
    const totals = upcomingIllustrationTotals(upcoming);
    assert.equal(totals?.distribution_dollars, 3_200);
    assert.equal(totals?.estimated_tax_dollars, 800);
  });

  it("Dollar Illustration $/share auto-attaches metadata NAV and only errors when missing", () => {
    const panel = readFileSync(
      join(here, "../../components/illustrate/IllustratePanel.tsx"),
      "utf8",
    );
    const seed = readFileSync(join(here, "../../data/seed.ts"), "utf8");
    assert.match(panel, /seedNavLookup/);
    assert.match(panel, /mock \? seedNavLookup/);
    assert.match(panel, /illustrationRequestNav/);
    assert.match(panel, /perShareNavError/);
    assert.match(seed, /ticker:\s*"ABALX"[\s\S]*?nav:\s*34\.52/);
    const seedLookup = (ticker: string) =>
      ticker.toUpperCase() === "ABALX" ? 34.52 : undefined;
    const attached = illustrationRequestNav("", "ABALX", 0, seedLookup);
    assert.equal(attached, 34.52);
    assert.equal(perShareNavError("per_share", attached), null);
  });

  it("IllustrationResults reads the unpaid-only helper instead of result.totals", () => {
    const source = readFileSync(join(here, "../../components/illustrate/IllustrationResults.tsx"), "utf8");
    assert.match(source, /splitIllustrationComponents/);
    assert.match(source, /upcomingIllustrationTotals/);
    assert.match(source, /upcomingEstimateTypeRows/);
    assert.match(source, /catalogUpcoming/);
    assert.match(source, /isUpcomingFund/);
    assert.doesNotMatch(source, /result\.totals/);
  });

  it("Dollar Illustration Paid History is full-bleed prior-year /distributions, not illustrate components", () => {
    const results = readFileSync(
      join(here, "../../components/illustrate/IllustrationResults.tsx"),
      "utf8",
    );
    const panel = readFileSync(
      join(here, "../../components/illustrate/IllustratePanel.tsx"),
      "utf8",
    );
    const paid = readFileSync(
      join(here, "../../components/illustrate/IllustrationPaidHistory.tsx"),
      "utf8",
    );
    assert.match(panel, /IllustrationPaidHistory/);
    assert.match(panel, /space-y-6/);
    assert.match(panel, /<\/div>\s*<IllustrationPaidHistory/);
    assert.doesNotMatch(results, /paidEventsForFund/);
    assert.doesNotMatch(results, /IllustrationPaidHistory/);
    assert.doesNotMatch(results, /paidComponents/);
    assert.doesNotMatch(results, /components=\{paid/);
    assert.match(paid, /illustrationPaidHistoryMatrix/);
    assert.match(paid, /Component/);
    assert.match(paid, /navOnly: false/);
    assert.doesNotMatch(paid, /Payable/);
  });

  it("still-future unpaid prelims with omitted illustrate stage stay Upcoming", () => {
    const fbgrx = component({
      distribution_id: "fbgrx-ltcg",
      estimate_type: "long_term_capital_gains",
      publication_stage: null,
      as_of: "2026-07-31",
      record_date: null,
      ex_date: "2026-09-11",
      payable_date: "2026-09-14",
      amount: 21.021,
      amount_unit: "per_share",
      distribution_dollars: 67_318.9,
      estimated_tax_dollars: 16_829.73,
    });
    const { upcoming, paid } = splitIllustrationComponents([fbgrx], {
      hasEstimate: true,
      bucket: "upcoming",
      publicationStage: "preliminary_estimate",
    });
    assert.equal(upcoming.length, 1);
    assert.equal(paid.length, 0);
    assert.equal(
      illustrationComponentBucket(fbgrx, {
        hasEstimate: true,
        bucket: "upcoming",
        publicationStage: "preliminary_estimate",
      }),
      "upcoming",
    );
  });

  it("does not force paid when catalog hasEstimate is stale but bucket is Upcoming", () => {
    const fbgrx = component({
      distribution_id: "fbgrx-ltcg",
      estimate_type: "long_term_capital_gains",
      publication_stage: null,
      as_of: "2026-07-31",
      record_date: null,
      ex_date: "2026-09-11",
      payable_date: "2026-09-14",
      amount: 21.021,
      amount_unit: "per_share",
      distribution_dollars: 67_318.9,
      estimated_tax_dollars: 16_829.73,
    });
    assert.equal(
      illustrationComponentBucket(fbgrx, {
        hasEstimate: false,
        bucket: "upcoming",
        publicationStage: "preliminary_estimate",
      }),
      "upcoming",
    );
  });

  it("coerces string illustrate dollars and does not double-count % NAV twins", () => {
    const ltcg = component({
      distribution_id: "fbgrx-ltcg",
      estimate_type: "long_term_capital_gains",
      publication_stage: "preliminary_estimate",
      as_of: "2026-07-31",
      ex_date: "2026-09-11",
      payable_date: "2026-09-14",
      amount: 21.021,
      amount_unit: "per_share",
      distribution_dollars: "67318.90" as unknown as number,
      estimated_tax_dollars: "16829.73" as unknown as number,
    });
    const total = component({
      distribution_id: "fbgrx-total",
      estimate_type: "total",
      publication_stage: "preliminary_estimate",
      as_of: "2026-07-31",
      ex_date: "2026-09-11",
      payable_date: "2026-09-14",
      amount: 21.021,
      amount_unit: "per_share",
      distribution_dollars: "67318.90" as unknown as number,
      estimated_tax_dollars: "16829.73" as unknown as number,
    });
    const pct = component({
      distribution_id: "fbgrx-tcg",
      estimate_type: "total_capital_gains",
      publication_stage: "preliminary_estimate",
      as_of: "2026-07-31",
      ex_date: "2026-09-11",
      payable_date: "2026-09-14",
      amount: 7.08,
      amount_unit: "percent_of_nav",
      distribution_dollars: "70800.00" as unknown as number,
      estimated_tax_dollars: "17700.00" as unknown as number,
    });
    const totals = upcomingIllustrationTotals([ltcg, total, pct]);
    assert.equal(totals?.distribution_dollars, 67_318.9);
    assert.equal(totals?.estimated_tax_dollars, 16_829.73);
  });

  it("keeps published $0 estimate types and does not invent unpublished ones", () => {
    const ltcg = component({
      distribution_id: "fbgrx-ltcg",
      estimate_type: "long_term_capital_gains",
      publication_stage: "preliminary_estimate",
      as_of: "2026-07-31",
      ex_date: "2026-09-11",
      payable_date: "2026-09-14",
      amount: 21.021,
      amount_unit: "per_share",
      distribution_dollars: 67_319,
      estimated_tax_dollars: 16_830,
    });
    const rows = upcomingEstimateTypeRows([ltcg], {
      publicationStage: "preliminary_estimate",
      asOfDate: "2026-07-31",
      exDate: "2026-09-11",
      payableDate: "2026-09-14",
      estimateTypeLines: [
        {
          estimateType: "long_term_capital_gains",
          amount: 21.021,
          amountUnit: "per_share",
        },
        {
          estimateType: "short_term_capital_gains",
          amount: 0,
          amountUnit: "per_share",
        },
      ],
    });
    assert.equal(rows.length, 2);
    const stcg = rows.find((row) => row.estimate_type === "short_term_capital_gains");
    assert.ok(stcg);
    assert.equal(stcg.amount, 0);
    assert.equal(stcg.distribution_dollars, 0);
    assert.equal(
      rows.some((row) => row.estimate_type === "ordinary_income"),
      false,
      "unpublished types stay off the table — never invent $0",
    );
    const panel = readFileSync(
      join(here, "../../components/illustrate/IllustratePanel.tsx"),
      "utf8",
    );
    assert.doesNotMatch(panel, /PortfolioCoverageCard/);
    assert.doesNotMatch(panel, /postIllustratePortfolio/);
  });
});
