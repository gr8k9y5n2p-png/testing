import { emptyListRow, orderListRows, type ListRow } from "./rows.ts";

export const LIST_HYDRATE_MAX_ATTEMPTS = 3;

export const LIST_HYDRATE_BACKOFF_MS = [0, 400, 1200] as const;

export function needsListHydrate(
  row: ListRow | undefined,
  attempt: number,
  maxAttempts = LIST_HYDRATE_MAX_ATTEMPTS,
): boolean {
  if (attempt >= maxAttempts) return false;
  if (!row) return true;
  return (
    row.status === "loading" ||
    row.status === "not_found" ||
    row.status === "unavailable"
  );
}

export function listHydrateBackoffMs(
  attempt: number,
  schedule: readonly number[] = LIST_HYDRATE_BACKOFF_MS,
): number {
  return schedule[Math.min(Math.max(attempt, 0), schedule.length - 1)] ?? 0;
}

export function listRowsFromApiResponse(
  tickers: readonly string[],
  body: unknown,
  ok: boolean,
): ListRow[] {
  if (!ok) {
    throw new Error("lists hydrate failed");
  }
  const record = body && typeof body === "object" ? (body as { items?: unknown }) : null;
  const items = Array.isArray(record?.items) ? (record.items as ListRow[]) : [];
  return orderListRows(tickers, items);
}

export function listRowsAfterFailedHydrate(tickers: readonly string[]): ListRow[] {
  return tickers.map((ticker) => emptyListRow(ticker, "unavailable"));
}
