export type CompareFundPick = {
  id: string;
  ticker: string;
  category?: string;
  family?: string;
};

export function findFundByTicker<T extends { ticker: string }>(
  funds: T[],
  ticker?: string | null,
): T | null {
  const key = ticker?.trim().toUpperCase();
  if (!key) return null;
  return funds.find((fund) => fund.ticker.toUpperCase() === key) ?? null;
}

export function defaultComparePeer<T extends CompareFundPick>(
  selected: T,
  funds: T[],
): T | null {
  const others = funds.filter(
    (fund) => fund.id !== selected.id && fund.ticker !== selected.ticker,
  );
  const sameCategoryOtherFamily = others.find(
    (fund) =>
      fund.category === selected.category && fund.family !== selected.family,
  );
  if (sameCategoryOtherFamily) return sameCategoryOtherFamily;
  return others[0] ?? null;
}
