/** Advisor-facing copy when Data cannot convert a holding without NAV/shares. */
export const NEED_FUND_PRICE_COPY = "Need fund price to convert this holding.";

/** Soft path — enter NAV instead of treating a missing price as a hard crash. */
export const ENTER_NAV_COPY = "Enter NAV per share to convert $ / share amounts.";

export const ENTER_NAV_DETAIL =
  "Upcoming amounts stay undisclosed until Data can convert per_share rows. Enter a fund price — do not invent an estimate.";

/** Data API detail when a per_share snapshot is illustrated without NAV or shares. */
export const NAV_OR_SHARES_REQUIRED_DETAIL =
  "nav_per_share or shares is required when illustrating per_share distributions";

function asRecord(value: unknown): Record<string, unknown> | null {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null;
}

function truthyFlag(value: unknown): boolean {
  return value === true || value === "true" || value === 1;
}

function errorCode(value: unknown): string | undefined {
  return typeof value === "string" && value.trim() ? value.trim() : undefined;
}

/**
 * Map Data's nav/shares 422s to advisor copy. Keys `needs_nav_or_shares` /
 * `nav_required` win; otherwise match the locked detail string.
 */
export function userFacingIllustrateError(
  body: unknown,
  fallback: string,
): { message: string; code?: string } {
  const rec = asRecord(body) ?? {};
  const nested = asRecord(rec.detail);
  const code = errorCode(rec.code) ?? errorCode(nested?.code);
  const detail =
    typeof rec.detail === "string" && rec.detail.trim()
      ? rec.detail.trim()
      : typeof nested?.detail === "string" && nested.detail.trim()
        ? nested.detail.trim()
        : fallback;

  const flagged =
    truthyFlag(rec.needs_nav_or_shares) ||
    truthyFlag(rec.nav_required) ||
    truthyFlag(nested?.needs_nav_or_shares) ||
    truthyFlag(nested?.nav_required) ||
    code === "needs_nav_or_shares" ||
    code === "nav_required" ||
    detail.includes(NAV_OR_SHARES_REQUIRED_DETAIL) ||
    /nav_per_share is required when illustrating per_share/.test(detail);

  if (flagged) {
    return {
      message: NEED_FUND_PRICE_COPY,
      code: code ?? "needs_nav_or_shares",
    };
  }
  return { message: detail, code };
}

/** True when Data asked for NAV/shares. Soft-handle — never hard-crash the UI. */
export function isMissingNavError(error: unknown): boolean {
  const rec = asRecord(error);
  const code = errorCode(rec?.code) ?? "";
  const message = error instanceof Error ? error.message : "";
  return (
    code === "needs_nav_or_shares" ||
    code === "nav_required" ||
    message === NEED_FUND_PRICE_COPY ||
    message === ENTER_NAV_COPY ||
    message.includes(NAV_OR_SHARES_REQUIRED_DETAIL) ||
    /nav_per_share is required when illustrating per_share/.test(message)
  );
}
