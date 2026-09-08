import {
  PORTFOLIO_COMPARE_YEARS,
  type PortfolioComparePeriodIn,
} from "./portfolio-compare-years";
import type {
  PortfolioComparePeriodOut,
  PortfolioCompareResponse,
  PortfolioPeriodHoldingTax,
} from "./portfolio-compare-types";

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

export function calendarYearColumns(
  periods: PortfolioComparePeriodOut[] | null | undefined,
  fallback: readonly number[] = PORTFOLIO_COMPARE_YEARS,
): number[] {
  const fromPeriods = [
    ...new Set((periods ?? []).map((period) => period.year).filter((year) => year > 0)),
  ].sort((a, b) => a - b);
  if (fromPeriods.length) {
    const requested = [...fallback];
    const extra = fromPeriods.filter((year) => !requested.includes(year));
    return extra.length ? [...requested, ...extra] : requested.length ? requested : fromPeriods;
  }
  return [...fallback];
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

/** Unmatched / missing → null (N/A). Matched $0 stays 0. */
export function periodHoldingTax(holding: PortfolioPeriodHoldingTax): YearTaxCell {
  if (holding.matched === false) return null;
  return holding.estimated_tax;
}

function rowsForSide(
  result: PortfolioCompareResponse,
  side: "current" | "proposed",
  years: number[],
  lookup: Map<string, Map<number, YearTaxCell>>,
): YearTaxRow[] {
  const allocation = result[side];
  const sideLabel = side === "current" ? "Current" : "Proposed";
  return allocation.holdings.map((holding, index) => {
    const ticker = (holding.ticker || holding.fund_identifier || "—").toUpperCase();
    const byYear = lookup.get(ticker);
    return {
      key: `${side}-${holding.holding_index}-${ticker}-${index}`,
      side,
      sideLabel,
      ticker,
      fundName: holding.fund_name || ticker,
      cells: years.map((year) => {
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
