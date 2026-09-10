import type { GrowthFundInput } from "@/components/illustrate/GrowthAndTaxDragModule";
import type { FundEstimateView } from "@/data/types";

/** Search-tab Upcoming + dollar illustration (`IllustratePanel`). */
export const FUND_HISTORY_HASH = "illustrate";

/**
 * Empty initial series for GrowthAndTaxDragModule consumers (Compare /
 * /growth-tax). Search no longer mounts that module.
 */
export const HOMEPAGE_GROWTH_FUNDS: GrowthFundInput[] = [];

/**
 * Deep-link into Search for a ticker's Upcoming / announced estimates and
 * dollar illustration. Historical paid distributions and Growth & tax drag
 * live on Compare / Portfolio / `/growth-tax`, not the Search homepage.
 */
export function fundHistoryPath(ticker: string): string {
  const key = normalizeTicker(ticker);
  if (!key) return `/#${FUND_HISTORY_HASH}`;
  return `/?ticker=${encodeURIComponent(key)}#${FUND_HISTORY_HASH}`;
}

export function normalizeTicker(value: string | null | undefined): string {
  return value?.trim().toUpperCase() ?? "";
}

export function firstSearchParam(
  value: string | string[] | undefined,
): string | undefined {
  const raw = Array.isArray(value) ? value[0] : value;
  const ticker = normalizeTicker(raw);
  return ticker || undefined;
}

/** Exact ticker, then share-class / product-name alias (AMCAP → AMCPX). */
export function resolveFundView(
  funds: FundEstimateView[],
  ticker: string,
): FundEstimateView | undefined {
  const key = normalizeTicker(ticker);
  if (!key) return undefined;

  const exact = funds.find((fund) => fund.ticker.toUpperCase() === key);
  if (exact) return exact;

  return funds.find((fund) => {
    const name = fund.fundName.toUpperCase();
    const words = name.split(/[^A-Z0-9]+/).filter(Boolean);
    return words.includes(key) || name.includes(key);
  });
}

export function growthFundFromTicker(
  ticker: string,
  funds: FundEstimateView[] = [],
): GrowthFundInput | undefined {
  const key = normalizeTicker(ticker);
  if (!key) return undefined;
  const match = resolveFundView(funds, key);
  const resolved = match?.ticker ?? key;
  return {
    ticker: resolved,
    label: resolved,
    fundIdentifier: resolved,
    fundFamily: match?.family,
    fundName: match?.fundName,
    navPerShare: match && match.nav > 0 ? match.nav : undefined,
  };
}
