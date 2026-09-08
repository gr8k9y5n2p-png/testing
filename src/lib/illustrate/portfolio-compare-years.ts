/**
 * Calendar-year tax $ window for PortfolioCompare.
 * Import-free so Node tests can load it without `@/` aliases.
 */

/** Locked POST /illustrate/portfolio/compare `periods[]`. */
export const PORTFOLIO_COMPARE_YEARS = [2021, 2022, 2023, 2024, 2025] as const;

export const PORTFOLIO_COMPARE_PERIODS = PORTFOLIO_COMPARE_YEARS.map((year) => ({
  year,
}));

export type PortfolioComparePeriodIn = { year: number; as_of?: string | null };

/**
 * Decimal tax on holding for mock / smoke. `null` omitted years are unmatched (N/A).
 * CGHM has no pre-2026 history. AMCAP shares AMCPX.
 */
export const PORTFOLIO_YEAR_TAX_RATES: Record<string, Record<number, number>> = {
  AGTHX: {
    2021: 0.0082, 2022: 0.0071, 2023: 0.0118, 2024: 0.0096, 2025: 0.0088,
  },
  AMCPX: {
    2021: 0.016, 2022: 0.009, 2023: 0.014, 2024: 0.017, 2025: 0.012,
  },
  AMCAP: {
    2021: 0.016, 2022: 0.009, 2023: 0.014, 2024: 0.017, 2025: 0.012,
  },
  DODIX: {
    2021: 0.015, 2022: 0.014, 2023: 0.017, 2024: 0.02, 2025: 0.016,
  },
  DODGX: {
    2021: 0.0104, 2022: 0.0079, 2023: 0.0122, 2024: 0.0099, 2025: 0.0087,
  },
};

export function portfolioYearTaxRate(ticker: string, year: number): number | null {
  const key = ticker.trim().toUpperCase();
  const table = PORTFOLIO_YEAR_TAX_RATES[key];
  if (!table || !(year in table)) return null;
  return table[year];
}
