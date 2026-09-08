import {
  PORTFOLIO_COMPARE_YEARS,
  type PortfolioComparePeriodIn,
} from "./portfolio-compare-years.ts";
import type {
  PortfolioComparePeriodOut,
  PortfolioCompareResponse,
  PortfolioHoldingOut,
  PortfolioPeriodHoldingTax,
} from "./portfolio-compare-types.ts";

/** Share-class aliases so AMCAP period rows still fill an AMCPX holding (and vice versa). */
const TICKER_PERIOD_ALIASES: Record<string, string> = {
  AMCAP: "AMCPX",
  AMCPX: "AMCAP",
};

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

type PeriodTaxLookup = {
  byTicker: Map<string, Map<number, YearTaxCell>>;
  byIndex: Map<number, Map<number, YearTaxCell>>;
};

function tickerAliases(ticker: string): string[] {
  const key = ticker.trim().toUpperCase();
  if (!key) return [];
  const alias = TICKER_PERIOD_ALIASES[key];
  return [key, alias].filter(
    (value, index, list): value is string => Boolean(value) && list.indexOf(value) === index,
  );
}

function taxLookup(
  periods: PortfolioComparePeriodOut[],
  side: "current" | "proposed",
): PeriodTaxLookup {
  const byTicker = new Map<string, Map<number, YearTaxCell>>();
  const byIndex = new Map<number, Map<number, YearTaxCell>>();
  for (const period of periods) {
    for (const holding of period[side]) {
      const cell = periodHoldingTax(holding);
      const ticker = holding.ticker.trim().toUpperCase();
      if (ticker) {
        let byYear = byTicker.get(ticker);
        if (!byYear) {
          byYear = new Map();
          byTicker.set(ticker, byYear);
        }
        byYear.set(period.year, cell);
      }
      if (holding.holding_index != null) {
        let byYear = byIndex.get(holding.holding_index);
        if (!byYear) {
          byYear = new Map();
          byIndex.set(holding.holding_index, byYear);
        }
        byYear.set(period.year, cell);
      }
    }
  }
  return { byTicker, byIndex };
}

function yearCellsForHolding(
  holding: PortfolioHoldingOut,
  years: number[],
  lookup: PeriodTaxLookup,
): YearTaxCell[] {
  const ticker = (holding.ticker || holding.fund_identifier || "—").toUpperCase();
  const aliases = tickerAliases(ticker);
  const byTicker = aliases
    .map((key) => lookup.byTicker.get(key))
    .find((map) => map != null);
  const byIndex =
    holding.holding_index != null ? lookup.byIndex.get(holding.holding_index) : undefined;
  const byYear = byTicker ?? byIndex;
  return years.map((year) => {
    if (!byYear || !byYear.has(year)) return null;
    return byYear.get(year) ?? null;
  });
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
  lookup: PeriodTaxLookup,
): YearTaxRow[] {
  const allocation = result[side];
  const sideLabel = side === "current" ? "Current" : "Proposed";
  return uniqueHoldings(allocation.holdings).map((holding, index) => {
    const ticker = (holding.ticker || holding.fund_identifier || "—").toUpperCase();
    return {
      key: `${side}-${holding.holding_index}-${ticker}-${index}`,
      side,
      sideLabel,
      ticker,
      fundName: holding.fund_name || ticker,
      // Period matched/unmatched wins. Holding-level covered is the upcoming
      // snapshot, not calendar-year tax — Search already proves AGTHX history.
      cells: yearCellsForHolding(holding, years, lookup),
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
