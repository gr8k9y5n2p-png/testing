import { illustrationComponentBucket } from "./illustration-upcoming.ts";
import {
  calendarYearFromUnknown,
  comparePeriodCalendarYear,
  illustrationIsUnmatched,
} from "./tax-drag-map.ts";
import type {
  CompareIllustration,
  CompareResponse,
} from "./compare-types.ts";
import {
  RATE_MAPPING,
  type IllustrationComponent,
  type TaxRates,
} from "./types.ts";

/** Data-named estimate_type keys. Do not invent aliases. */
export const GROWTH_TAX_ESTIMATE_TYPES = [
  "ordinary_income",
  "short_term_capital_gains",
  "long_term_capital_gains",
  "qualified_dividend",
  "special_dividend",
  "return_of_capital",
] as const;

export type GrowthTaxEstimateType = (typeof GROWTH_TAX_ESTIMATE_TYPES)[number];

export const GROWTH_TAX_TYPE_LABELS: Record<GrowthTaxEstimateType, string> = {
  ordinary_income: "Ordinary",
  short_term_capital_gains: "STCG",
  long_term_capital_gains: "LTCG",
  qualified_dividend: "QDI",
  special_dividend: "Special",
  return_of_capital: "ROC",
};

/** Muted Ledger Light stacks — not neon. LTCG is tax-more red. */
export const GROWTH_TAX_TYPE_COLORS: Record<GrowthTaxEstimateType, string> = {
  ordinary_income: "#1b7a72",
  short_term_capital_gains: "#8a6a4a",
  long_term_capital_gains: "#b42318",
  qualified_dividend: "#4a5d6b",
  special_dividend: "#0f7a4b",
  return_of_capital: "#a8b0aa",
};

export const GROWTH_TAX_EMPTY_LABEL = "—";
export const GROWTH_TAX_UNDISCLOSED_LABEL = "Undisc.";

export type GrowthTaxYearStatus = "paid" | "announced" | "empty";

export type GrowthTaxTypeAmounts = Record<GrowthTaxEstimateType, number | null>;

export type GrowthTaxFundYear = {
  ticker: string;
  year: number;
  status: GrowthTaxYearStatus;
  amounts: GrowthTaxTypeAmounts;
  total: number | null;
};

export type GrowthTaxFundSeries = {
  ticker: string;
  years: GrowthTaxFundYear[];
};

export type GrowthTaxByTypeModel = {
  years: number[];
  tickers: string[];
  series: GrowthTaxFundSeries[];
};

const TYPE_SET = new Set<string>(GROWTH_TAX_ESTIMATE_TYPES);

function emptyAmounts(): GrowthTaxTypeAmounts {
  return {
    ordinary_income: null,
    short_term_capital_gains: null,
    long_term_capital_gains: null,
    qualified_dividend: null,
    special_dividend: null,
    return_of_capital: null,
  };
}

function numericOrNull(value: unknown): number | null {
  if (value == null || value === "") return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function illustrationCalendarYear(illustration: CompareIllustration | null | undefined): number {
  if (!illustration) return 0;
  const extra = illustration as CompareIllustration & { year?: unknown; as_of?: unknown };
  const first = Array.isArray(illustration.components)
    ? (illustration.components[0] as { as_of?: unknown; ex_date?: unknown } | undefined)
    : undefined;
  return (
    calendarYearFromUnknown(extra.year) ||
    calendarYearFromUnknown(extra.as_of) ||
    calendarYearFromUnknown(illustration.label) ||
    calendarYearFromUnknown(first?.as_of) ||
    calendarYearFromUnknown(first?.ex_date)
  );
}

/**
 * Place each compare side onto **that illustration’s calendar year**.
 * YoY left/right vintages never share a column — never mix YE seasons
 * or market years when comparing funds. Missing years stay absent.
 */
export function illustrationsByCalendarYear(
  response: CompareResponse,
  side: "left" | "right" | "auto" = "auto",
): Map<number, CompareIllustration> {
  const byYear = new Map<number, CompareIllustration>();
  const write = (year: number, illustration: CompareIllustration | null | undefined) => {
    if (!Number.isFinite(year) || year <= 0 || !illustration) return;
    const prior = byYear.get(year);
    if (prior && !illustrationIsUnmatched(prior) && illustrationIsUnmatched(illustration)) {
      return;
    }
    byYear.set(year, illustration);
  };

  for (const period of response.periods) {
    const yoy = response.mode === "yoy";
    const periodYear = comparePeriodCalendarYear(period);
    if (yoy) {
      const olderFromLabel = illustrationCalendarYear(period.left);
      const newerFromLabel = illustrationCalendarYear(period.right);
      const calendarRow =
        periodYear > 0 &&
        ((olderFromLabel === 0 && newerFromLabel === 0) ||
          (olderFromLabel === periodYear && newerFromLabel === periodYear));
      if (calendarRow && side !== "auto") {
        write(periodYear, side === "right" ? period.right : period.left);
        continue;
      }
      if (calendarRow && olderFromLabel === periodYear && newerFromLabel === periodYear) {
        write(periodYear, period.right ?? period.left);
        continue;
      }
      const olderYear = olderFromLabel || (periodYear > 1 ? periodYear - 1 : 0);
      const newerYear = newerFromLabel || periodYear;
      if (olderYear > 0) write(olderYear, period.left);
      if (newerYear > 0) write(newerYear, period.right);
      continue;
    }
    if (side === "right") write(periodYear, period.right);
    else write(periodYear, period.left);
  }

  return byYear;
}

function asComponent(raw: unknown): IllustrationComponent | null {
  if (!raw || typeof raw !== "object") return null;
  const row = raw as Record<string, unknown>;
  const estimateType = String(row.estimate_type ?? "").trim();
  if (!estimateType) return null;
  return {
    distribution_id: String(row.distribution_id ?? ""),
    fund_name: String(row.fund_name ?? ""),
    estimate_type: estimateType,
    amount_unit: String(row.amount_unit ?? ""),
    publication_stage: row.publication_stage == null ? null : String(row.publication_stage),
    as_of: row.as_of == null ? null : String(row.as_of),
    record_date: row.record_date == null ? null : String(row.record_date),
    ex_date: row.ex_date == null ? null : String(row.ex_date),
    payable_date: row.payable_date == null ? null : String(row.payable_date),
    distribution_dollars: numericOrNull(row.distribution_dollars),
    distribution_dollars_min: numericOrNull(row.distribution_dollars_min),
    distribution_dollars_max: numericOrNull(row.distribution_dollars_max),
    rate_key: String(row.rate_key ?? row.federal_rate_key ?? "ordinary_income"),
    federal_rate: numericOrNull(row.federal_rate) ?? 0,
    state_rate: numericOrNull(row.state_rate) ?? 0,
    effective_rate: numericOrNull(row.effective_rate ?? row.applied_rate) ?? 0,
    estimated_tax_dollars: numericOrNull(
      row.estimated_tax_dollars ?? row.estimated_tax,
    ),
    estimated_tax_dollars_min: numericOrNull(
      row.estimated_tax_dollars_min ?? row.estimated_tax_min,
    ),
    estimated_tax_dollars_max: numericOrNull(
      row.estimated_tax_dollars_max ?? row.estimated_tax_max,
    ),
    notes: typeof row.notes === "string" ? row.notes : null,
  };
}

export function canonicalizeEstimateType(raw: string): GrowthTaxEstimateType | "skip" | "total_capital_gains" {
  const key = raw.trim().toLowerCase().replace(/[\s-]+/g, "_");
  if (key === "total_capital_gains") return "total_capital_gains";
  if (TYPE_SET.has(key)) return key as GrowthTaxEstimateType;
  return "skip";
}

/**
 * Tax $ for one component: API tax first, else Dist $ × the rate already
 * applied (component effective_rate, else locked user rates). ROC is not
 * taxed unless Data sent a tax figure. Never invent Dist $.
 */
export function taxDollarsFromComponent(
  component: Pick<
    IllustrationComponent,
    | "estimate_type"
    | "distribution_dollars"
    | "estimated_tax_dollars"
    | "effective_rate"
    | "federal_rate"
    | "state_rate"
    | "rate_key"
  >,
  rates?: TaxRates,
  combineState = true,
): number | null {
  const published = numericOrNull(component.estimated_tax_dollars);
  if (published != null) return published;

  const dist = numericOrNull(component.distribution_dollars);
  if (dist == null) return null;

  const kind = canonicalizeEstimateType(component.estimate_type);
  if (kind === "return_of_capital") return 0;

  const effective = numericOrNull(component.effective_rate);
  if (effective != null && effective > 0) return dist * effective;

  if (!rates) return null;
  const rateKey =
    (component.rate_key as keyof TaxRates | undefined) &&
    component.rate_key in rates
      ? (component.rate_key as keyof TaxRates)
      : (RATE_MAPPING[component.estimate_type] ?? "ordinary_income");
  const federal = rates[rateKey] ?? rates.ordinary_income;
  const state = combineState ? rates.state : 0;
  return dist * (federal + state);
}

function addAmount(amounts: GrowthTaxTypeAmounts, type: GrowthTaxEstimateType, value: number) {
  amounts[type] = (amounts[type] ?? 0) + value;
}

/**
 * Fold Data estimate_type rows onto the locked table keys.
 * Prefer STCG / LTCG component rows; `total_capital_gains` is only used
 * when those component rows are absent so stacks never double-count.
 */
export function foldEstimateTypeAmounts(
  components: Array<Pick<IllustrationComponent, "estimate_type"> & { tax: number | null }>,
): GrowthTaxTypeAmounts {
  const amounts = emptyAmounts();
  let totalCapitalGains: number | null = null;
  for (const row of components) {
    if (row.tax == null) continue;
    const kind = canonicalizeEstimateType(row.estimate_type);
    if (kind === "skip") continue;
    if (kind === "total_capital_gains") {
      totalCapitalGains = (totalCapitalGains ?? 0) + row.tax;
      continue;
    }
    addAmount(amounts, kind, row.tax);
  }
  const hasComponentGains =
    amounts.short_term_capital_gains != null || amounts.long_term_capital_gains != null;
  if (!hasComponentGains && totalCapitalGains != null) {
    amounts.long_term_capital_gains = totalCapitalGains;
  }
  return amounts;
}

function sumAmounts(amounts: GrowthTaxTypeAmounts): number | null {
  let total: number | null = null;
  for (const type of GROWTH_TAX_ESTIMATE_TYPES) {
    const value = amounts[type];
    if (value == null) continue;
    total = (total ?? 0) + value;
  }
  return total;
}

export function yearStatusFromComponents(
  components: IllustrationComponent[],
): GrowthTaxYearStatus {
  if (components.length === 0) return "empty";
  const announced = components.filter(
    (component) => illustrationComponentBucket(component) === "upcoming",
  );
  if (announced.length > 0) return "announced";
  return "paid";
}

/**
 * Historical years use paid components only. Announced unpaid years use
 * unpaid manager estimates only. Never promote paid finals into announced
 * and never invent a prelim row.
 */
export function selectComponentsForYear(
  components: IllustrationComponent[],
): { status: GrowthTaxYearStatus; used: IllustrationComponent[] } {
  if (components.length === 0) return { status: "empty", used: [] };
  const announced = components.filter(
    (component) => illustrationComponentBucket(component) === "upcoming",
  );
  if (announced.length > 0) return { status: "announced", used: announced };
  const paid = components.filter(
    (component) => illustrationComponentBucket(component) === "paid",
  );
  if (paid.length > 0) return { status: "paid", used: paid };
  return { status: "empty", used: [] };
}

export function growthTaxYearFromIllustration(
  ticker: string,
  year: number,
  illustration: CompareIllustration | null | undefined,
  rates?: TaxRates,
  combineState = true,
): GrowthTaxFundYear {
  const empty: GrowthTaxFundYear = {
    ticker,
    year,
    status: "empty",
    amounts: emptyAmounts(),
    total: null,
  };
  if (!illustration || illustrationIsUnmatched(illustration)) return empty;

  const parsed = (illustration.components ?? [])
    .map(asComponent)
    .filter((row): row is IllustrationComponent => row != null);
  const { status, used } = selectComponentsForYear(parsed);
  if (status === "empty") return empty;

  const amounts = foldEstimateTypeAmounts(
    used.map((component) => ({
      estimate_type: component.estimate_type,
      tax: taxDollarsFromComponent(component, rates, combineState),
    })),
  );
  return {
    ticker,
    year,
    status,
    amounts,
    total: sumAmounts(amounts),
  };
}

export function growthTaxSeriesFromCompare(
  ticker: string,
  response: CompareResponse | null,
  years: number[],
  side: "left" | "right" | "auto" = "auto",
  rates?: TaxRates,
  combineState = true,
): GrowthTaxFundSeries {
  const byYear = response ? illustrationsByCalendarYear(response, side) : new Map();
  return {
    ticker,
    years: years.map((year) =>
      growthTaxYearFromIllustration(ticker, year, byYear.get(year), rates, combineState),
    ),
  };
}

/** Same calendar-year columns for every fund — never mix YE seasons. */
export function buildGrowthTaxByTypeModel(
  rows: Array<{
    ticker: string;
    tax: CompareResponse | null;
    taxSide?: "left" | "right" | "auto";
  }>,
  years: number[],
  rates?: TaxRates,
  combineState = true,
): GrowthTaxByTypeModel {
  const tickers = rows.map((row) => row.ticker.trim().toUpperCase()).filter(Boolean);
  return {
    years,
    tickers,
    series: rows.map((row) =>
      growthTaxSeriesFromCompare(
        row.ticker.trim().toUpperCase(),
        row.tax,
        years,
        row.taxSide ?? "auto",
        rates,
        combineState,
      ),
    ),
  };
}

export function lightenHex(hex: string, amount = 0.32): string {
  const raw = hex.replace("#", "");
  if (raw.length !== 6) return hex;
  const mix = (channel: number) =>
    Math.round(channel + (255 - channel) * Math.min(1, Math.max(0, amount)));
  const r = mix(Number.parseInt(raw.slice(0, 2), 16));
  const g = mix(Number.parseInt(raw.slice(2, 4), 16));
  const b = mix(Number.parseInt(raw.slice(4, 6), 16));
  return `#${[r, g, b].map((value) => value.toString(16).padStart(2, "0")).join("")}`;
}

export function formatGrowthTaxCell(
  value: number | null,
  status: GrowthTaxYearStatus,
  kind: "type" | "total" = "type",
): string {
  if (value == null) {
    return status === "empty" && kind === "total"
      ? GROWTH_TAX_UNDISCLOSED_LABEL
      : GROWTH_TAX_EMPTY_LABEL;
  }
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(Math.round(value));
}
