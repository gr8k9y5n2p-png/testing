import { SAMPLE_FUNDS } from "@/data/seed";
import type { FundEstimate } from "@/data/types";
import { roundTo } from "@/data/queries";
import { distributionId } from "@/lib/illustrate/ids";
import {
  AMOUNT_UNITS,
  DEFAULT_TAX_RATES,
  RATE_MAPPING,
  type AmountUnit,
  type IllustrateRequest,
  type IllustrateResponse,
  type IllustrationComponent,
  type TaxRates,
} from "@/lib/illustrate/types";

/**
 * MOCK illustrate engine — server-side only.
 * Data team owns production math on POST /illustrate. This replica returns the
 * locked response shape from seeded estimates so the Aftertax UI is demoable.
 */

export type MockDistributionRow = {
  distribution_id: string;
  fund_id: string;
  fund_name: string;
  fund_family: string;
  ticker: string;
  estimate_type: string;
  amount_unit: AmountUnit;
  amount: number;
  amount_min: number | null;
  amount_max: number | null;
  publication_stage: string;
  as_of: string;
  record_date: string | null;
  ex_date: string | null;
  payable_date: string | null;
  nav_per_share: number;
};

function money(value: number): number {
  return Math.round(value * 100) / 100;
}

function rate(value: number): number {
  return Math.round(value * 1_000_000) / 1_000_000;
}

function mergeRates(incoming?: TaxRates): TaxRates {
  return {
    ordinary_income: incoming?.ordinary_income ?? DEFAULT_TAX_RATES.ordinary_income,
    long_term_capital_gains:
      incoming?.long_term_capital_gains ?? DEFAULT_TAX_RATES.long_term_capital_gains,
    short_term_capital_gains:
      incoming?.short_term_capital_gains ?? DEFAULT_TAX_RATES.short_term_capital_gains,
    qualified_dividend:
      incoming?.qualified_dividend ?? DEFAULT_TAX_RATES.qualified_dividend,
    state: incoming?.state ?? DEFAULT_TAX_RATES.state,
  };
}

function rowsForFund(fund: FundEstimate): MockDistributionRow[] {
  const ordinaryPct = roundTo((fund.estimatedOrdinaryIncome / fund.nav) * 100, 4);
  const ltcgPct = roundTo((fund.estimatedCapitalGains / fund.nav) * 100, 4);

  return [
    {
      distribution_id: distributionId(fund.id, "ordinary", AMOUNT_UNITS.percent_of_nav),
      fund_id: fund.id,
      fund_name: fund.fundName,
      fund_family: fund.family,
      ticker: fund.ticker,
      estimate_type: "ordinary_income",
      amount_unit: AMOUNT_UNITS.percent_of_nav,
      amount: ordinaryPct,
      amount_min: null,
      amount_max: null,
      publication_stage: fund.publicationStage ?? "preliminary_estimate",
      as_of: fund.asOfDate,
      record_date: fund.recordDate,
      ex_date: fund.exDate,
      payable_date: fund.payableDate,
      nav_per_share: fund.nav,
    },
    {
      distribution_id: distributionId(fund.id, "ltcg", AMOUNT_UNITS.percent_of_nav),
      fund_id: fund.id,
      fund_name: fund.fundName,
      fund_family: fund.family,
      ticker: fund.ticker,
      estimate_type: "long_term_capital_gains",
      amount_unit: AMOUNT_UNITS.percent_of_nav,
      amount: ltcgPct,
      amount_min: roundTo(ltcgPct * 0.8, 4),
      amount_max: roundTo(ltcgPct * 1.2, 4),
      publication_stage: fund.publicationStage ?? "preliminary_estimate",
      as_of: fund.asOfDate,
      record_date: fund.recordDate,
      ex_date: fund.exDate,
      payable_date: fund.payableDate,
      nav_per_share: fund.nav,
    },
    {
      distribution_id: distributionId(fund.id, "ordinary", AMOUNT_UNITS.per_share),
      fund_id: fund.id,
      fund_name: fund.fundName,
      fund_family: fund.family,
      ticker: fund.ticker,
      estimate_type: "ordinary_income",
      amount_unit: AMOUNT_UNITS.per_share,
      amount: fund.estimatedOrdinaryIncome,
      amount_min: null,
      amount_max: null,
      publication_stage: fund.publicationStage ?? "preliminary_estimate",
      as_of: fund.asOfDate,
      record_date: fund.recordDate,
      ex_date: fund.exDate,
      payable_date: fund.payableDate,
      nav_per_share: fund.nav,
    },
    {
      distribution_id: distributionId(fund.id, "ltcg", AMOUNT_UNITS.per_share),
      fund_id: fund.id,
      fund_name: fund.fundName,
      fund_family: fund.family,
      ticker: fund.ticker,
      estimate_type: "long_term_capital_gains",
      amount_unit: AMOUNT_UNITS.per_share,
      amount: fund.estimatedCapitalGains,
      amount_min: roundTo(fund.estimatedCapitalGains * 0.8, 4),
      amount_max: roundTo(fund.estimatedCapitalGains * 1.2, 4),
      publication_stage: fund.publicationStage ?? "preliminary_estimate",
      as_of: fund.asOfDate,
      record_date: fund.recordDate,
      ex_date: fund.exDate,
      payable_date: fund.payableDate,
      nav_per_share: fund.nav,
    },
  ];
}

const ALL_ROWS: MockDistributionRow[] = SAMPLE_FUNDS.flatMap(rowsForFund);
const ROW_BY_ID = new Map(ALL_ROWS.map((row) => [row.distribution_id, row]));

export function listMockRowsForFund(
  fundId: string,
  unit: AmountUnit = AMOUNT_UNITS.percent_of_nav,
): MockDistributionRow[] {
  return ALL_ROWS.filter((row) => row.fund_id === fundId && row.amount_unit === unit);
}

export class IllustrateHttpError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly code?: string,
  ) {
    super(message);
  }
}

function distDollars(
  unit: AmountUnit,
  amount: number | null,
  holding: number,
  shares: number | null,
): number | null {
  if (amount == null) return null;
  if (unit === AMOUNT_UNITS.percent_of_nav) return holding * (amount / 100);
  if (unit === AMOUNT_UNITS.per_share) {
    if (shares == null) return null;
    return shares * amount;
  }
  return null;
}

function illustrateRow(
  row: MockDistributionRow,
  holding: number,
  shares: number | null,
  rates: TaxRates,
  combine: boolean,
): IllustrationComponent {
  const rateKey = RATE_MAPPING[row.estimate_type] ?? "ordinary_income";
  const federal = rates[rateKey];
  const state = rates.state;
  const effective = combine ? federal + state : federal;
  const dist = distDollars(row.amount_unit, row.amount, holding, shares);
  const distMin = distDollars(row.amount_unit, row.amount_min, holding, shares);
  const distMax = distDollars(row.amount_unit, row.amount_max, holding, shares);

  const taxOn = (dollars: number | null) =>
    dollars == null ? null : money(dollars * effective);

  return {
    distribution_id: row.distribution_id,
    fund_name: row.fund_name,
    estimate_type: row.estimate_type,
    amount_unit: row.amount_unit,
    publication_stage: row.publication_stage,
    as_of: row.as_of,
    record_date: row.record_date,
    ex_date: row.ex_date,
    payable_date: row.payable_date,
    distribution_dollars: dist == null ? null : money(dist),
    distribution_dollars_min: distMin == null ? null : money(distMin),
    distribution_dollars_max: distMax == null ? null : money(distMax),
    rate_key: rateKey,
    federal_rate: rate(federal),
    state_rate: rate(state),
    effective_rate: rate(effective),
    estimated_tax_dollars: taxOn(dist == null ? null : money(dist)),
    estimated_tax_dollars_min: taxOn(distMin == null ? null : money(distMin)),
    estimated_tax_dollars_max: taxOn(distMax == null ? null : money(distMax)),
    notes: null,
  };
}

export function mockIllustrate(body: IllustrateRequest): IllustrateResponse {
  const holding = body.holding_dollars;
  if (!(holding > 0)) {
    throw new IllustrateHttpError("holding_dollars must be greater than 0", 422);
  }

  const hasIds = Boolean(body.distribution_ids?.length);
  const hasSelector = Boolean(
    body.selector?.fund_family || body.selector?.fund_identifier,
  );
  if (hasIds && hasSelector) {
    throw new IllustrateHttpError("provide distribution_ids or selector, not both", 422);
  }
  if (!hasIds && !hasSelector) {
    throw new IllustrateHttpError("provide distribution_ids or selector", 422);
  }

  let rows: MockDistributionRow[] = [];
  if (hasIds) {
    const missing: string[] = [];
    for (const id of body.distribution_ids ?? []) {
      const row = ROW_BY_ID.get(id);
      if (!row) missing.push(id);
      else rows.push(row);
    }
    if (missing.length) {
      throw new IllustrateHttpError(`Unknown distribution_ids: ${missing.join(", ")}`, 404);
    }
  } else {
    const identifier = body.selector?.fund_identifier?.toUpperCase();
    const family = body.selector?.fund_family?.toLowerCase();
    rows = ALL_ROWS.filter((row) => {
      if (row.amount_unit !== AMOUNT_UNITS.percent_of_nav) return false;
      if (identifier && row.ticker.toUpperCase() !== identifier) return false;
      if (family && row.fund_family.toLowerCase() !== family) return false;
      return true;
    });
    if (!rows.length) {
      throw new IllustrateHttpError("No distribution estimates matched the selector", 404);
    }
  }

  const stages = new Set(rows.map((row) => `${row.publication_stage}|${row.as_of}`));
  const warnings: string[] = [
    "MOCK /illustrate — sample seed math, not the Data team service. Set NEXT_PUBLIC_ILLUSTRATE_URL to swap.",
  ];
  if (stages.size > 1) {
    warnings.push(
      "Selected rows span more than one publication_stage / as_of snapshot. Prefer one snapshot to avoid double-counting.",
    );
  }

  const needsNav = rows.some((row) => row.amount_unit === AMOUNT_UNITS.per_share);
  const nav = body.nav_per_share ?? null;
  if (needsNav && !(nav != null && nav > 0)) {
    throw new IllustrateHttpError(
      "nav_per_share is required when illustrating per_share distributions",
      422,
      "nav_required",
    );
  }
  const shares = nav && nav > 0 ? holding / nav : null;

  const rates = mergeRates(body.tax_rates);
  const combine = body.combine_state_with_federal !== false;
  const components = rows.map((row) =>
    illustrateRow(row, holding, shares, rates, combine),
  );

  const included = components.filter((c) => c.distribution_dollars != null);
  const sum = (pick: (c: IllustrationComponent) => number | null) =>
    money(included.reduce((acc, c) => acc + (pick(c) ?? 0), 0));
  const hasRange = included.some(
    (c) => c.distribution_dollars_min != null || c.distribution_dollars_max != null,
  );

  if (rows.some((row) => row.fund_family !== "American Funds")) {
    warnings.push(
      "Coverage gap: live ingest today is Capital Group / American Funds. This illustration uses sample data and may understate book-level tax impact.",
    );
  }

  return {
    tax_rates_applied: rates,
    components,
    totals: {
      distribution_dollars: sum((c) => c.distribution_dollars),
      distribution_dollars_min: hasRange
        ? sum((c) => c.distribution_dollars_min ?? c.distribution_dollars)
        : null,
      distribution_dollars_max: hasRange
        ? sum((c) => c.distribution_dollars_max ?? c.distribution_dollars)
        : null,
      estimated_tax_dollars: sum((c) => c.estimated_tax_dollars),
      estimated_tax_dollars_min: hasRange
        ? sum((c) => c.estimated_tax_dollars_min ?? c.estimated_tax_dollars)
        : null,
      estimated_tax_dollars_max: hasRange
        ? sum((c) => c.estimated_tax_dollars_max ?? c.estimated_tax_dollars)
        : null,
    },
    warnings,
  };
}
