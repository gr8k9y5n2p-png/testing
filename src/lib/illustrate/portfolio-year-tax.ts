import {
  PORTFOLIO_COMPARE_YEARS,
  type PortfolioComparePeriodIn,
} from "./portfolio-compare-years.ts";
import type {
  PortfolioComparePeriodOut,
  PortfolioCompareResponse,
  PortfolioPeriodHoldingTax,
} from "./portfolio-compare-types.ts";

export type YearTaxCell = number | null;

export type YearTaxRow = {
  key: string;
  side: "current" | "proposed";
  sideLabel: "Current" | "Proposed";
  ticker: string;
  fundName: string;
  cells: YearTaxCell[];
};

export type YearTaxTableModel = {
  years: number[];
  current: YearTaxRow[];
  proposed: YearTaxRow[];
};

/**
 * Always 2025 … 2021 (newest first), even when Data only returns 2021–2024.
 * Extra period years stay off the grid so the module does not grow a sixth column.
 */
export function calendarYearColumns(
  _periods?: PortfolioComparePeriodOut[] | null,
  fallback: readonly number[] = PORTFOLIO_COMPARE_YEARS,
): number[] {
  return [...fallback].sort((a, b) => b - a);
}

function taxLookup(
  periods: PortfolioComparePeriodOut[],
  side: "current" | "proposed",
): Map<string, Map<number, YearTaxCell>> {
  const byTicker = new Map<string, Map<number, YearTaxCell>>();
  for (const period of periods) {
    for (const holding of period[side]) {
      const ticker = holding.ticker.trim().toUpperCase();
      if (!ticker) continue;
      let byYear = byTicker.get(ticker);
      if (!byYear) {
        byYear = new Map();
        byTicker.set(ticker, byYear);
      }
      byYear.set(period.year, periodHoldingTax(holding));
    }
  }
  return byTicker;
}

/** Unmatched / uncovered / null totals → N/A. Published $0 stays 0. */
export function periodHoldingTax(holding: PortfolioPeriodHoldingTax): YearTaxCell {
  if (holding.matched === false) return null;
  if (holding.covered === false) return null;
  if (holding.gap_reason) return null;
  return holding.estimated_tax;
}

function uniqueHoldings(
  holdings: PortfolioCompareResponse["current"]["holdings"],
): PortfolioCompareResponse["current"]["holdings"] {
  const seen = new Set<string>();
  const unique: typeof holdings = [];
  for (const holding of holdings) {
    const ticker = (holding.ticker || holding.fund_identifier || "—").toUpperCase();
    if (seen.has(ticker)) continue;
    seen.add(ticker);
    unique.push(holding);
  }
  return unique;
}

function rowsForSide(
  result: PortfolioCompareResponse,
  side: "current" | "proposed",
  years: number[],
  lookup: Map<string, Map<number, YearTaxCell>>,
): YearTaxRow[] {
  const allocation = result[side];
  const sideLabel = side === "current" ? "Current" : "Proposed";
  return uniqueHoldings(allocation.holdings).map((holding, index) => {
    const ticker = (holding.ticker || holding.fund_identifier || "—").toUpperCase();
    const byYear = lookup.get(ticker);
    return {
      key: `${side}-${holding.holding_index}-${ticker}-${index}`,
      side,
      sideLabel,
      ticker,
      fundName: holding.fund_name || ticker,
      cells: years.map((year) => {
        if (holding.covered === false || holding.gap_reason) return null;
        if (!byYear || !byYear.has(year)) return null;
        const value = byYear.get(year);
        return value ?? null;
      }),
    };
  });
}

export function calendarYearTaxTable(
  result: PortfolioCompareResponse,
  years: readonly number[] = PORTFOLIO_COMPARE_YEARS,
): YearTaxTableModel {
  const columns = calendarYearColumns(result.periods, years);
  const periods = result.periods ?? [];
  return {
    years: columns,
    current: rowsForSide(result, "current", columns, taxLookup(periods, "current")),
    proposed: rowsForSide(result, "proposed", columns, taxLookup(periods, "proposed")),
  };
}

export function hasCalendarYearTax(model: YearTaxTableModel): boolean {
  return model.current.concat(model.proposed).some((row) =>
    row.cells.some((cell) => cell != null),
  );
}

export function defaultPortfolioComparePeriods(): PortfolioComparePeriodIn[] {
  return PORTFOLIO_COMPARE_YEARS.map((year) => ({ year }));
}

/** Always POST 2021–2025, even if a caller omitted 2025. */
export function ensurePortfolioComparePeriods(
  periods?: PortfolioComparePeriodIn[] | null,
): PortfolioComparePeriodIn[] {
  const byYear = new Map<number, PortfolioComparePeriodIn>();
  for (const period of periods ?? []) {
    if (period.year > 0) byYear.set(period.year, period);
  }
  for (const year of PORTFOLIO_COMPARE_YEARS) {
    if (!byYear.has(year)) byYear.set(year, { year });
  }
  return [...byYear.values()].sort((a, b) => a.year - b.year);
}
