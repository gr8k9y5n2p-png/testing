/**
 * Compare / Portfolio TickerField matches: local catalog plus live
 * GET /api/funds hits. Same book Search uses — no heroes / has_estimate gate.
 */

export const TICKER_FIELD_MATCH_LIMIT = 8;

export type TickerSearchHit = {
  ticker: string;
  fundName: string;
  family?: string;
  nav?: number | null;
};

function positiveNav(value: unknown): number | null {
  const nav = typeof value === "number" ? value : Number(value);
  return Number.isFinite(nav) && nav > 0 ? nav : null;
}

/** Map a Website BFF /api/funds item. Do not drop has_estimate=false rows. */
export function toTickerFieldOption(item: unknown): TickerSearchHit | null {
  if (!item || typeof item !== "object") return null;
  const row = item as Record<string, unknown>;
  const ticker = String(row.ticker ?? "")
    .trim()
    .toUpperCase();
  if (!ticker) return null;
  const fundName =
    String(row.fundName ?? row.fund_name ?? "")
      .trim() || ticker;
  const family = String(row.family ?? row.fund_family ?? "").trim();
  return {
    ticker,
    fundName,
    family: family || undefined,
    nav: positiveNav(row.nav ?? row.nav_per_share),
  };
}

export function mergeTickerFieldOptions(
  local: readonly TickerSearchHit[],
  remote: readonly TickerSearchHit[],
): TickerSearchHit[] {
  const map = new Map<string, TickerSearchHit>();
  const order: string[] = [];
  for (const fund of [...remote, ...local]) {
    const ticker = fund.ticker.trim().toUpperCase();
    if (!ticker) continue;
    const prev = map.get(ticker);
    if (!prev) {
      map.set(ticker, { ...fund, ticker });
      order.push(ticker);
      continue;
    }
    map.set(ticker, {
      ticker,
      fundName: fund.fundName || prev.fundName,
      family: fund.family || prev.family,
      nav: fund.nav ?? prev.nav,
    });
  }
  return order.map((ticker) => map.get(ticker)!);
}

/**
 * Local substring hits plus every live /api/funds row for this query.
 * Remote rows are not re-filtered — the BFF already searched the full book.
 */
export function tickerFieldMatches(
  local: readonly TickerSearchHit[],
  remote: readonly TickerSearchHit[],
  query: string,
): TickerSearchHit[] {
  const q = query.trim().toLowerCase();
  if (!q) return [];
  const localHits = local.filter((fund) => {
    const haystack =
      `${fund.ticker} ${fund.fundName} ${fund.family ?? ""}`.toLowerCase();
    return haystack.includes(q);
  });
  return mergeTickerFieldOptions(localHits, remote).slice(
    0,
    TICKER_FIELD_MATCH_LIMIT,
  );
}
