import { historicalPctOfNav, pctOfNavForUnpaidOrPaid } from "./nav-math.ts";
import {
  upcomingDistDollarsFromPerShare,
  upcomingPctOfNavFromPerShare,
  resolveUpcomingPerShare,
} from "./portfolio-compare-copy.ts";
import type {
  PortfolioAllocationOut,
  PortfolioDistributionRow,
  PortfolioHoldingOut,
  PortfolioUpcoming,
} from "./portfolio-compare-types";

export type DistributionBucket = "upcoming" | "paid_history";

export type UpcomingRow = {
  key: string;
  ticker: string;
  fundName: string;
  side: "current" | "proposed";
  sideLabel: string;
  /** Null when upcoming is undisclosed — never coerce to $0. */
  distributionDollars: number | null;
  distributionDollarsMin: number | null;
  distributionDollarsMax: number | null;
  /** Holding $ used to derive % of NAV. Null when unknown. */
  holdingDollars: number | null;
  /**
   * Upcoming: Dist $/share ÷ weekly nav_per_share.
   * Paid / historical: Dist $/share ÷ nav_on_distribution_day.
   * Never invent a manager rate from Dist $ / holding $ alone.
   */
  pctOfNav: number | null;
  /** Weekly NAV (`nav_per_share`). Upcoming % of NAV only. */
  navPerShare: number | null;
  navAsOf: string | null;
  /** Ex-day NAV. Paid / historical % of NAV only — never weekly. */
  navOnDistributionDay: number | null;
  /** Manager unpaid prelim $/share. Never invent. */
  distributionPerShare: number | null;
  ordinaryPerShare: number | null;
  capitalGainsPerShare: number | null;
  estimatedTax: number | null;
  asOf: string | null;
  announcedDate: string | null;
  recordDate: string | null;
  exDate: string | null;
  payableDate: string | null;
  stage: string | null;
  bucket: DistributionBucket;
  heat: number;
  /** False = empty/null upcoming for this fund (Awaiting Estimate, not $0). */
  available: boolean;
  covered: boolean;
  /** Catalog identity. False → Add to universe, not Awaiting Estimate. */
  inUniverse: boolean;
};

function num(value: unknown): number | null {
  if (value == null || value === "") return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

export function utcToday(now = new Date()): string {
  return now.toISOString().slice(0, 10);
}

function isoDate(value: string | null | undefined): string | null {
  if (value == null) return null;
  const trimmed = String(value).trim();
  if (!trimmed) return null;
  const day = trimmed.slice(0, 10);
  return /^\d{4}-\d{2}-\d{2}$/.test(day) ? day : null;
}

/** Announced date: announced_date, else as_of. Never synthesize a calendar day. */
export function announcedDateOf(
  row: Pick<PortfolioDistributionRow, "announced_date" | "as_of">,
): string | null {
  return isoDate(row.announced_date) ?? isoDate(row.as_of);
}

/** Event date for future-ish checks. as_of is announcement, not an event date. */
export function eventDateOf(
  row: Pick<PortfolioDistributionRow, "payable_date" | "ex_date" | "record_date">,
): string | null {
  return isoDate(row.payable_date) ?? isoDate(row.ex_date) ?? isoDate(row.record_date);
}

/**
 * Data paid_history sort key: record, else ex, else payable.
 * Null dates stay null — never invent a day.
 */
export function paidHistoryDateOf(
  row: Pick<PortfolioDistributionRow, "record_date" | "ex_date" | "payable_date">,
): string | null {
  return isoDate(row.record_date) ?? isoDate(row.ex_date) ?? isoDate(row.payable_date);
}

/**
 * Compare / Portfolio Upcoming → Paid History cutover: ex-date, else record,
 * else payable. Unpaid announced moves as soon as ex-date passes — do not
 * wait for payable. Null dates stay null — never invent a day.
 */
export function upcomingCutoverDateOf(
  row: Pick<PortfolioDistributionRow, "ex_date" | "record_date" | "payable_date">,
): string | null {
  return isoDate(row.ex_date) ?? isoDate(row.record_date) ?? isoDate(row.payable_date);
}

export function normalizePublicationStage(
  stage: string | null | undefined,
): string {
  return (stage ?? "").trim().toLowerCase();
}

const UPCOMING_STAGES = new Set([
  "preliminary_estimate",
  "updated_estimate",
  "preliminary",
  "updated",
  "announced",
  "monthly",
]);

const PAID_HISTORY_STAGES = new Set(["paid", "final"]);

export function isUpcomingPublicationStage(stage: string | null | undefined): boolean {
  return UPCOMING_STAGES.has(normalizePublicationStage(stage));
}

export function isPaidHistoryPublicationStage(
  stage: string | null | undefined,
): boolean {
  return PAID_HISTORY_STAGES.has(normalizePublicationStage(stage));
}

/**
 * Ex-date (else record, else payable) already past. as_of is announcement and
 * does not make a preliminary/updated row paid. Past `final` falls back to as_of.
 * Do not wait for payable when ex-date has passed.
 */
function isPastPaidEvent(row: PortfolioDistributionRow, today = utcToday()): boolean {
  const stage = normalizePublicationStage(row.publication_stage);
  const event = upcomingCutoverDateOf(row);
  const cutoff = event ?? (stage === "final" ? isoDate(row.as_of) : null);
  return cutoff != null && cutoff < today;
}

/**
 * Locked split vs Data `paid_history[]` / unpaid `upcoming`:
 * Upcoming = unpaid prelim/estimate only (not `final`).
 * If ex-date (else record, else payable) is already past, the row is Paid
 * history even when publication_stage is still preliminary_estimate /
 * updated_estimate. Do not wait for payable. as_of is announcement only —
 * never invent a day. Never invent Upcoming from paid/final YE history or
 * illustration / tax-on-holding math.
 */
export function publicationBucket(
  row: PortfolioDistributionRow,
  today = utcToday(),
): DistributionBucket | null {
  const stage = normalizePublicationStage(row.publication_stage);
  if (
    isPaidHistoryPublicationStage(stage) ||
    isPastPaidEvent(row, today)
  ) {
    return "paid_history";
  }
  if (isUpcomingPublicationStage(stage)) return "upcoming";
  // latest_as_of / identity-only — never invent Upcoming from paid YE dates.
  return null;
}

function asDistributionRows(
  value: PortfolioDistributionRow | PortfolioDistributionRow[] | null | undefined,
): PortfolioDistributionRow[] {
  if (value == null) return [];
  return Array.isArray(value) ? value : [value];
}

function withStage(
  row: PortfolioDistributionRow,
  fallbackStage: string | null,
): PortfolioDistributionRow {
  return {
    ...row,
    as_of: isoDate(row.as_of),
    announced_date: isoDate(row.announced_date),
    record_date: isoDate(row.record_date),
    ex_date: isoDate(row.ex_date),
    payable_date: isoDate(row.payable_date),
    publication_stage: row.publication_stage ?? fallbackStage,
  };
}

function hasDistributionSignal(row: PortfolioDistributionRow): boolean {
  return (
    num(row.distribution_dollars) != null ||
    num(row.estimated_tax) != null ||
    num(row.percent_of_nav) != null ||
    num(row.per_share) != null ||
    num(row.amount) != null ||
    Boolean(
      announcedDateOf(row) ||
        row.record_date ||
        row.ex_date ||
        row.payable_date ||
        row.publication_stage,
    )
  );
}

/**
 * Issuer-published % of NAV only. Dist $ / holding $ is not a published rate —
 * never invent % of NAV for any ticker.
 */
export function pctOfNavFromDist(
  _distributionDollars: number | null,
  _holdingDollars: number | null | undefined,
  explicit?: number | null,
): number | null {
  if (explicit != null && Number.isFinite(explicit)) return explicit;
  return null;
}

function coalesceUpcomingRows(
  rows: PortfolioDistributionRow[],
  today = utcToday(),
): PortfolioUpcoming | null {
  const upcoming = rows.filter((row) => publicationBucket(row, today) === "upcoming");
  if (!upcoming.length) return null;
  if (upcoming.length === 1) return upcoming[0];
  const dist = upcoming.reduce((sum, row) => sum + (num(row.distribution_dollars) ?? 0), 0);
  const taxes = upcoming.map((row) => num(row.estimated_tax));
  const tax = taxes.every((value) => value == null)
    ? null
    : taxes.reduce<number>((sum, value) => sum + (value ?? 0), 0);
  return {
    ...upcoming[0],
    distribution_dollars: dist,
    estimated_tax: tax,
  };
}

/**
 * Upcoming $ only from non-null unpaid `holdings[].upcoming`.
 * Omitted / null / paid / historical illustration totals → Awaiting Estimate
 * when the ticker is in universe (Add to universe when it is not).
 * Never invent Fund Manager Estimated Distributions for any ticker
 * (ABALX is an example, not a special case).
 */
export function upcomingFromHolding(
  holding: PortfolioHoldingOut,
  today = utcToday(),
): PortfolioUpcoming | null {
  if (holding.upcoming == null) return null;

  const rows = asDistributionRows(holding.upcoming)
    .map((row) => withStage(row, holding.publication_stage_used ?? null))
    .filter(hasDistributionSignal);
  return coalesceUpcomingRows(rows, today);
}

/**
 * Unpaid announced rows only. Omitted or `upcoming: null` is Awaiting
 * Estimate in-universe — do not derive from illustration, distributions,
 * history, or annual tax.
 */
function upcomingEventsFromHolding(
  holding: PortfolioHoldingOut,
  today = utcToday(),
): PortfolioDistributionRow[] {
  if (holding.upcoming == null) return [];
  return asDistributionRows(holding.upcoming)
    .map((row) => withStage(row, holding.publication_stage_used ?? null))
    .filter(hasDistributionSignal)
    .filter((event) => publicationBucket(event, today) === "upcoming");
}

/** Data `paid_history[]` cap. Newest-first after that is dropped. */
export const PAID_HISTORY_CAP = 12;

function paidHistorySortKey(row: PortfolioDistributionRow): string | null {
  return paidHistoryDateOf(row) ?? announcedDateOf(row);
}

/**
 * Paid History is `holdings[].paid_history[]` only. Same fields as upcoming.
 * Data sends newest-first, cap 12. Never derive from illustration, distributions,
 * history, or `upcoming` (including `upcoming: null`).
 */
function paidHistoryEventsFromHolding(
  holding: PortfolioHoldingOut,
): PortfolioDistributionRow[] {
  const fallback = holding.publication_stage_used ?? null;
  const rows = asDistributionRows(holding.paid_history)
    .map((row) => withStage(row, fallback))
    .filter(hasDistributionSignal);
  return [...rows]
    .sort((a, b) => {
      const aDate = paidHistorySortKey(a);
      const bDate = paidHistorySortKey(b);
      if (!aDate && !bDate) {
        return (num(b.distribution_dollars) ?? 0) - (num(a.distribution_dollars) ?? 0);
      }
      if (!aDate) return 1;
      if (!bDate) return -1;
      if (aDate !== bDate) return bDate.localeCompare(aDate);
      return (num(b.distribution_dollars) ?? 0) - (num(a.distribution_dollars) ?? 0);
    })
    .slice(0, PAID_HISTORY_CAP);
}

const STAGE_LABELS: Record<string, string> = {
  announced: "announced",
  monthly: "next",
  preliminary: "announced",
  preliminary_estimate: "announced",
  updated_estimate: "updated",
  updated: "updated",
  final: "final",
  paid: "paid",
};

export function formatStageLabel(stage: string | null): string {
  const stageKey = (stage ?? "").trim().toLowerCase();
  if (!stageKey) return "—";
  if (stageKey === "monthly") return "monthly";
  return STAGE_LABELS[stageKey] ?? stageKey.replace(/_/g, " ");
}

export function formatAsOfStage(asOf: string | null, stage: string | null): string {
  const stageKey = (stage ?? "").trim().toLowerCase();
  const stageLabel = formatStageLabel(stage);

  if (stageKey === "monthly") {
    return "Est. monthly · next";
  }

  let month = "";
  if (asOf) {
    const date = new Date(`${asOf}T00:00:00Z`);
    if (!Number.isNaN(date.getTime())) {
      month = date.toLocaleString("en-US", { month: "short", timeZone: "UTC" });
    }
  }

  if (month && stageLabel !== "—") return `Est. ${month} · ${stageLabel}`;
  if (month) return `Est. ${month}`;
  if (stageLabel !== "—") return stageLabel;
  return "—";
}

function holdingTicker(
  holding: Pick<PortfolioHoldingOut, "ticker" | "fund_identifier">,
): string {
  return (holding.ticker || holding.fund_identifier || "—").toUpperCase();
}

/**
 * Catalog membership for empty Upcoming copy.
 * Prefer Awaiting Estimate unless the ticker is known to be outside the universe.
 */
export function holdingInUniverse(
  holding: Pick<PortfolioHoldingOut, "ticker" | "fund_identifier">,
  universeTickers?: ReadonlySet<string>,
): boolean {
  if (!universeTickers) return true;
  return universeTickers.has(holdingTicker(holding));
}

function toTableRow(
  holding: PortfolioHoldingOut,
  side: "current" | "proposed",
  index: number,
  event: PortfolioDistributionRow,
  eventIndex: number,
  bucket: DistributionBucket,
  universeTickers?: ReadonlySet<string>,
): UpcomingRow | null {
  if (!hasDistributionSignal(event)) return null;
  const dist = num(event.distribution_dollars);
  const holdingDollars = num(holding.holding_dollars);
  const ticker = holdingTicker(holding);
  const weeklyNav =
    num(event.nav_per_share) ??
    num(holding.nav_per_share);
  const navOnDistributionDay = num(event.nav_on_distribution_day);
  const perShare =
    num(event.per_share) ??
    (event.amount_unit === "per_share" ? num(event.amount) : null);
  const paid = bucket === "paid_history";
  // Paid % of NAV must not back out $/share from Dist $ ÷ weekly shares.
  const resolvedPerShare = paid
    ? perShare
    : resolveUpcomingPerShare({
        distributionPerShare: perShare,
        distributionDollars: dist,
        holdingDollars,
        navPerShare: weeklyNav,
      });
  return {
    key: `${side}-${holding.holding_index}-${ticker}-${index}-${bucket}-${eventIndex}`,
    ticker,
    fundName: holding.fund_name || ticker,
    side,
    sideLabel: side === "current" ? "Current" : "Proposed",
    distributionDollars: paid
      ? dist
      : dist ?? upcomingDistDollarsFromPerShare(resolvedPerShare, holdingDollars, weeklyNav),
    distributionDollarsMin: num(event.distribution_dollars_min),
    distributionDollarsMax: num(event.distribution_dollars_max),
    holdingDollars,
    pctOfNav: pctOfNavForUnpaidOrPaid({
      unpaid: !paid,
      perShare: resolvedPerShare,
      weeklyNav,
      navOnDistributionDay,
    }),
    navPerShare: weeklyNav,
    navAsOf: isoDate(event.nav_as_of) ?? isoDate(holding.nav_as_of),
    navOnDistributionDay,
    distributionPerShare: resolvedPerShare,
    ordinaryPerShare: null,
    capitalGainsPerShare: null,
    estimatedTax: num(event.estimated_tax),
    asOf: isoDate(event.as_of),
    announcedDate: announcedDateOf(event),
    recordDate: isoDate(event.record_date),
    exDate: isoDate(event.ex_date),
    payableDate: isoDate(event.payable_date),
    stage: event.publication_stage ?? holding.publication_stage_used ?? null,
    bucket,
    heat: 0,
    available: true,
    covered: holding.covered !== false && !holding.gap_reason,
    inUniverse: holdingInUniverse(holding, universeTickers),
  };
}

function emptyUpcomingRow(
  holding: PortfolioHoldingOut,
  side: "current" | "proposed",
  index: number,
  universeTickers?: ReadonlySet<string>,
): UpcomingRow {
  const ticker = holdingTicker(holding);
  return {
    key: `${side}-${holding.holding_index}-${ticker}-${index}-upcoming-empty`,
    ticker,
    fundName: holding.fund_name || ticker,
    side,
    sideLabel: side === "current" ? "Current" : "Proposed",
    distributionDollars: null,
    distributionDollarsMin: null,
    distributionDollarsMax: null,
    holdingDollars: num(holding.holding_dollars),
    pctOfNav: null,
    navPerShare: num(holding.nav_per_share),
    navAsOf: isoDate(holding.nav_as_of),
    navOnDistributionDay: null,
    distributionPerShare: null,
    ordinaryPerShare: null,
    capitalGainsPerShare: null,
    estimatedTax: null,
    asOf: null,
    announcedDate: null,
    recordDate: null,
    exDate: null,
    payableDate: null,
    stage: null,
    bucket: "upcoming",
    heat: 0,
    available: false,
    covered: holding.covered !== false && !holding.gap_reason,
    inUniverse: holdingInUniverse(holding, universeTickers),
  };
}

function rowsForSide(
  allocation: PortfolioAllocationOut,
  side: "current" | "proposed",
  bucket: DistributionBucket,
  today = utcToday(),
  universeTickers?: ReadonlySet<string>,
): UpcomingRow[] {
  return allocation.holdings.flatMap((holding, index) => {
    const events =
      bucket === "paid_history"
        ? paidHistoryEventsFromHolding(holding)
        : upcomingEventsFromHolding(holding, today);
    return events.flatMap((event, eventIndex) => {
      const row = toTableRow(
        holding,
        side,
        index,
        event,
        eventIndex,
        bucket,
        universeTickers,
      );
      return row ? [row] : [];
    });
  });
}

function paidHistorySortDate(row: UpcomingRow): string | null {
  return row.recordDate ?? row.exDate ?? row.payableDate ?? row.asOf ?? row.announcedDate;
}

function sortDistributionRows(rows: UpcomingRow[], bucket: DistributionBucket): UpcomingRow[] {
  return [...rows].sort((a, b) => {
    if (bucket === "paid_history") {
      const aDate = paidHistorySortDate(a);
      const bDate = paidHistorySortDate(b);
      if (!aDate && !bDate) {
        return (b.distributionDollars ?? 0) - (a.distributionDollars ?? 0);
      }
      if (!aDate) return 1;
      if (!bDate) return -1;
      if (aDate !== bDate) return bDate.localeCompare(aDate);
    }
    return (b.distributionDollars ?? 0) - (a.distributionDollars ?? 0);
  });
}

function withHeat(rows: UpcomingRow[]): UpcomingRow[] {
  const max = rows.reduce(
    (peak, row) =>
      row.available ? Math.max(peak, row.distributionDollars ?? 0) : peak,
    0,
  );
  return rows.map((row) => ({
    ...row,
    heat:
      row.available && max > 0 && row.distributionDollars != null
        ? row.distributionDollars / max
        : 0,
  }));
}

/** Sort + heat within one allocation so Current and Proposed tables stay independent. */
export function upcomingRowsForSide(
  allocation: PortfolioAllocationOut,
  side: "current" | "proposed",
  today = utcToday(),
  universeTickers?: ReadonlySet<string>,
): UpcomingRow[] {
  return withHeat(
    sortDistributionRows(
      rowsForSide(allocation, side, "upcoming", today, universeTickers),
      "upcoming",
    ),
  );
}

/**
 * One row per Current/Proposed holding for the Upcoming module.
 * Extra unpaid events on the same fund collapse to the first row.
 * Empty/null upcoming is Awaiting Estimate in-universe — never $0.
 */
export function upcomingHoldingsForSide(
  allocation: PortfolioAllocationOut,
  side: "current" | "proposed",
  today = utcToday(),
  universeTickers?: ReadonlySet<string>,
): UpcomingRow[] {
  const rows = allocation.holdings.flatMap((holding, index) => {
    const events = upcomingEventsFromHolding(holding, today);
    const eventRows = events.flatMap((event, eventIndex) => {
      const row = toTableRow(
        holding,
        side,
        index,
        event,
        eventIndex,
        "upcoming",
        universeTickers,
      );
      return row ? [row] : [];
    });
    if (eventRows.length) return [eventRows[0]];
    return [emptyUpcomingRow(holding, side, index, universeTickers)];
  });
  return withHeat(rows);
}

/** Paid / final past rows. Kept off the upcoming path. */
export function paidHistoryRowsForSide(
  allocation: PortfolioAllocationOut,
  side: "current" | "proposed",
  today = utcToday(),
): UpcomingRow[] {
  return withHeat(
    sortDistributionRows(
      rowsForSide(allocation, side, "paid_history", today),
      "paid_history",
    ),
  );
}

export function distributionHasPayable(rows: UpcomingRow[]): boolean {
  return rows.some((row) => row.payableDate != null);
}

/**
 * Sum of unpaid announced tax. Null estimated_tax is skipped (not $0).
 * No upcoming rows → 0; the UI uses `hasUpcoming` so a miss is undisclosed.
 */
/** Attach known weekly NAV for unpaid Upcoming. Never rewrite paid/historical %. */
export function withUpcomingNav(
  rows: UpcomingRow[],
  navByTicker: Record<string, number | null | undefined> | Map<string, number | null | undefined>,
): UpcomingRow[] {
  const lookup =
    navByTicker instanceof Map
      ? navByTicker
      : new Map(Object.entries(navByTicker));
  return rows.map((row) => {
    if (row.bucket === "paid_history") {
      return {
        ...row,
        pctOfNav: historicalPctOfNav(
          row.distributionPerShare,
          row.navOnDistributionDay,
        ),
      };
    }
    const lookedUp = lookup.get(row.ticker) ?? lookup.get(row.ticker.toUpperCase());
    const nav =
      row.navPerShare != null && row.navPerShare > 0
        ? row.navPerShare
        : lookedUp != null && lookedUp > 0
          ? lookedUp
          : row.navPerShare;
    const perShare = resolveUpcomingPerShare({
      distributionPerShare: row.distributionPerShare,
      distributionDollars: row.distributionDollars,
      holdingDollars: row.holdingDollars,
      navPerShare: nav,
    });
    return {
      ...row,
      navPerShare: nav,
      distributionPerShare: perShare,
      pctOfNav: upcomingPctOfNavFromPerShare(perShare, nav),
      distributionDollars:
        row.distributionDollars ??
        upcomingDistDollarsFromPerShare(perShare, row.holdingDollars, nav),
    };
  });
}

export function totalUpcomingTax(
  allocation: PortfolioAllocationOut,
  today = utcToday(),
): number {
  return allocation.holdings.reduce((sum, holding) => {
    const upcoming = upcomingFromHolding(holding, today);
    if (!upcoming) return sum;
    const tax = num(upcoming.estimated_tax);
    return tax == null ? sum : sum + tax;
  }, 0);
}
