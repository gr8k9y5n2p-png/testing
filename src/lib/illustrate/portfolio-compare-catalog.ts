import { PORTFOLIO_COMPARE_BOOK_DOLLARS } from "@/lib/illustrate/portfolio-compare-types";
import type {
  PortfolioFundOption,
  PortfolioHoldingDraft,
} from "@/lib/illustrate/portfolio-compare-types";

export type PortfolioTickerRates = {
  fundName: string;
  family: string;
  /** Decimal tax drag on holding (0.0042 = 0.42%). */
  taxDrag: number;
  /** Upcoming distribution as a decimal of holding dollars. */
  distRate: number;
  /** Effective tax on the upcoming distribution (0 = muni). */
  upcomingTaxRate: number;
  asOf: string | null;
  stage: string;
};

/**
 * Mock rates for ticker autocomplete + localhost fixture math.
 * Default smoke books are GTM’s history-covered set (funds with live
 * historical data for testing): Current AGTHX / DODIX / AMCAP / DODGX
 * and Proposed AMCPX / CGHM / AGTHX / AMCAP, 25% each at $1M.
 */
export const PORTFOLIO_TICKER_RATES: Record<string, PortfolioTickerRates> = {
  AGTHX: {
    fundName: "American Funds Growth Fund of America",
    family: "American Funds",
    taxDrag: 0.0068,
    distRate: 0.0194,
    upcomingTaxRate: 0.35,
    asOf: "2026-12-15",
    stage: "announced",
  },
  DODIX: {
    fundName: "Dodge & Cox Income Fund",
    family: "Dodge & Cox",
    taxDrag: 0.0048,
    distRate: 0.0084,
    upcomingTaxRate: 0.37,
    asOf: null,
    stage: "monthly",
  },
  AMCAP: {
    fundName: "AMCAP Fund",
    family: "American Funds",
    taxDrag: 0.0042,
    distRate: 0.0128,
    upcomingTaxRate: 0.35,
    asOf: "2026-12-15",
    stage: "announced",
  },
  DODGX: {
    fundName: "Dodge & Cox Stock Fund",
    family: "Dodge & Cox",
    taxDrag: 0.0056,
    distRate: 0.0162,
    upcomingTaxRate: 0.35,
    asOf: "2026-12-15",
    stage: "announced",
  },
  VIGAX: {
    fundName: "Vanguard Growth Index Fund",
    family: "Vanguard",
    taxDrag: 0.001,
    distRate: 0.0032,
    upcomingTaxRate: 0.2,
    asOf: "2026-12-15",
    stage: "announced",
  },
  AMCPX: {
    fundName: "AMCAP Fund",
    family: "American Funds",
    taxDrag: 0.0042,
    distRate: 0.0128,
    upcomingTaxRate: 0.35,
    asOf: "2026-12-15",
    stage: "announced",
  },
  CGHM: {
    fundName: "Capital Group Municipal High-Income ETF",
    family: "Capital Group",
    taxDrag: 0,
    distRate: 0.00168,
    upcomingTaxRate: 0,
    asOf: null,
    stage: "monthly",
  },
  TRBCX: {
    fundName: "T. Rowe Price Blue Chip Growth",
    family: "T. Rowe Price",
    taxDrag: 0.0038,
    distRate: 0.0111,
    upcomingTaxRate: 0.35,
    asOf: "2026-12-12",
    stage: "announced",
  },
  VFIAX: {
    fundName: "Vanguard 500 Index Fund",
    family: "Vanguard",
    taxDrag: 0.0008,
    distRate: 0.0024,
    upcomingTaxRate: 0.2,
    asOf: "2026-12-20",
    stage: "announced",
  },
  VBIAX: {
    fundName: "Vanguard Balanced Index Fund",
    family: "Vanguard",
    taxDrag: 0.0012,
    distRate: 0.0021,
    upcomingTaxRate: 0.2,
    asOf: "2026-12-20",
    stage: "announced",
  },
  FBGRX: {
    fundName: "Fidelity Blue Chip Growth Fund",
    family: "Fidelity",
    taxDrag: 0.0068,
    distRate: 0.0192,
    upcomingTaxRate: 0.35,
    asOf: "2026-12-12",
    stage: "announced",
  },
};

const DEFAULT_RATES: PortfolioTickerRates = {
  fundName: "",
  family: "",
  taxDrag: 0.003,
  distRate: 0.01,
  upcomingTaxRate: 0.3,
  asOf: "2026-12-15",
  stage: "announced",
};

export function ratesForTicker(ticker: string): PortfolioTickerRates {
  const key = ticker.trim().toUpperCase();
  return PORTFOLIO_TICKER_RATES[key] ?? { ...DEFAULT_RATES, fundName: key };
}

/** GTM history-covered Current book — 25% each. */
export const SMOKE_CURRENT_TICKERS = ["AGTHX", "DODIX", "AMCAP", "DODGX"] as const;
/** GTM history-covered Proposed book — 25% each. */
export const SMOKE_PROPOSED_TICKERS = ["AMCPX", "CGHM", "AGTHX", "AMCAP"] as const;
export const SMOKE_WEIGHT_PCT = 25;

export function draftHolding(
  ticker: string,
  weightPct: number,
  bookDollars: number,
  funds?: PortfolioFundOption[],
  id?: string,
): PortfolioHoldingDraft {
  const rates = ratesForTicker(ticker);
  const option = funds?.find((fund) => fund.ticker.toUpperCase() === ticker.toUpperCase());
  return {
    id: id ?? `${ticker.toUpperCase()}-${Math.round(weightPct * 100)}`,
    ticker: ticker.toUpperCase(),
    fundName: rates.fundName || option?.fundName || ticker.toUpperCase(),
    family: rates.family || option?.family,
    weightPct,
    holdingDollars: (weightPct / 100) * bookDollars,
  };
}

export function smokeCurrentHoldings(
  bookDollars = PORTFOLIO_COMPARE_BOOK_DOLLARS,
  funds?: PortfolioFundOption[],
): PortfolioHoldingDraft[] {
  return SMOKE_CURRENT_TICKERS.map((ticker) =>
    draftHolding(ticker, SMOKE_WEIGHT_PCT, bookDollars, funds, `current-${ticker}`),
  );
}

export function smokeProposedHoldings(
  bookDollars = PORTFOLIO_COMPARE_BOOK_DOLLARS,
  funds?: PortfolioFundOption[],
): PortfolioHoldingDraft[] {
  return SMOKE_PROPOSED_TICKERS.map((ticker) =>
    draftHolding(ticker, SMOKE_WEIGHT_PCT, bookDollars, funds, `proposed-${ticker}`),
  );
}

export function catalogFunds(extra: PortfolioFundOption[] = []): PortfolioFundOption[] {
  const fromRates: PortfolioFundOption[] = Object.entries(PORTFOLIO_TICKER_RATES).map(
    ([ticker, rates]) => ({
      ticker,
      fundName: rates.fundName,
      family: rates.family,
    }),
  );
  const byTicker = new Map<string, PortfolioFundOption>();
  for (const fund of [...fromRates, ...extra]) {
    const ticker = fund.ticker.trim().toUpperCase();
    if (!ticker) continue;
    const prev = byTicker.get(ticker);
    byTicker.set(ticker, {
      ticker,
      // Rates/catalog names win so the smoke book matches the locked sketch.
      fundName: prev?.fundName || fund.fundName || ticker,
      family: prev?.family || fund.family,
    });
  }
  return [...byTicker.values()].sort((a, b) => a.ticker.localeCompare(b.ticker));
}

export function lookupFund(
  ticker: string,
  funds: PortfolioFundOption[],
): PortfolioFundOption | undefined {
  const key = ticker.trim().toUpperCase();
  return funds.find((fund) => fund.ticker.toUpperCase() === key);
}
