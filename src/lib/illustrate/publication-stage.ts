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
  distributionDollars: number;
  estimatedTax: number | null;
  asOf: string | null;
  announcedDate: string | null;
  recordDate: string | null;
  exDate: string | null;
  payableDate: string | null;
  stage: string | null;
  bucket: DistributionBucket;
  heat: number;
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
 * Locked GTM split:
 * - Upcoming / announced: preliminary_estimate / updated_estimate (future-ish)
 * - Paid history: paid / final past rows
 * Past event-dated estimates stay out of Upcoming (Aug 2026 prelim ≠ live upcoming).
 */
export function publicationBucket(
  row: PortfolioDistributionRow,
  today = utcToday(),
): DistributionBucket | null {
  const stage = normalizePublicationStage(row.publication_stage);
  const event = eventDateOf(row);
  const pastEvent = event != null && event < today;

  if (PAID_HISTORY_STAGES.has(stage)) {
    return "paid_history";
  }
  if (UPCOMING_STAGES.has(stage)) {
    if (pastEvent) return null;
    return "upcoming";
  }
  if (!stage) {
    if (pastEvent) return null;
    return "upcoming";
  }
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
    Boolean(
      announcedDateOf(row) ||
        row.record_date ||
        row.ex_date ||
        row.payable_date ||
        row.publication_stage,
    )
  );
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

export function upcomingFromHolding(
  holding: PortfolioHoldingOut,
  today = utcToday(),
): PortfolioUpcoming | null {
  if (holding.upcoming === null) return null;

  if (holding.upcoming) {
    const rows = asDistributionRows(holding.upcoming)
      .map((row) => withStage(row, holding.publication_stage_used ?? null))
      .filter(hasDistributionSignal);
    return coalesceUpcomingRows(rows, today);
  }

  const illustration = holding.illustration;
  if (!illustration) return null;

  const components = illustration.components ?? [];
  const classified = components
    .map((row) =>
      withStage(
        {
          ...row,
          estimated_tax: row.estimated_tax ?? row.estimated_tax_dollars,
        },
        holding.publication_stage_used ?? null,
      ),
    )
    .filter((row) => publicationBucket(row, today) === "upcoming");
  if (classified.length) return coalesceUpcomingRows(classified, today);

  if (components.length) return null;

  const totals = illustration.totals;
  const candidate: PortfolioUpcoming = {
    distribution_dollars: num(totals?.distribution_dollars),
    estimated_tax: num(totals?.estimated_tax) ?? num(totals?.estimated_tax_dollars),
    as_of: null,
    publication_stage: holding.publication_stage_used ?? null,
  };
  if (!hasDistributionSignal(candidate)) return null;
  if (publicationBucket(candidate, today) !== "upcoming") return null;
  return candidate;
}

function tableEventsFromHolding(holding: PortfolioHoldingOut): PortfolioDistributionRow[] {
  const fallback = holding.publication_stage_used ?? null;
  const listed = [
    ...asDistributionRows(holding.distributions),
    ...asDistributionRows(holding.history),
  ]
    .map((row) => withStage(row, fallback))
    .filter(hasDistributionSignal);

  if (listed.length) return listed;

  if (holding.upcoming === null) return [];

  if (holding.upcoming) {
    return asDistributionRows(holding.upcoming)
      .map((row) => withStage(row, fallback))
      .filter(hasDistributionSignal);
  }

  return (holding.illustration?.components ?? [])
    .map((row) => withStage(row, fallback))
    .filter(hasDistributionSignal);
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

function rowsForSide(
  allocation: PortfolioAllocationOut,
  side: "current" | "proposed",
  bucket: DistributionBucket,
  today = utcToday(),
): UpcomingRow[] {
  return allocation.holdings.flatMap((holding, index) => {
    const ticker = (holding.ticker || holding.fund_identifier || "—").toUpperCase();
    return tableEventsFromHolding(holding).flatMap((event, eventIndex) => {
      if (publicationBucket(event, today) !== bucket) return [];
      const dist = num(event.distribution_dollars);
      if (dist == null) return [];
      return [
        {
          key: `${side}-${holding.holding_index}-${ticker}-${index}-${bucket}-${eventIndex}`,
          ticker,
          fundName: holding.fund_name || ticker,
          side,
          sideLabel: side === "current" ? "Current" : "Proposed",
          distributionDollars: dist,
          estimatedTax: num(event.estimated_tax),
          asOf: isoDate(event.as_of),
          announcedDate: announcedDateOf(event),
          recordDate: isoDate(event.record_date),
          exDate: isoDate(event.ex_date),
          payableDate: isoDate(event.payable_date),
          stage: event.publication_stage ?? holding.publication_stage_used ?? null,
          bucket,
          heat: 0,
        },
      ];
    });
  });
}

function sortDistributionRows(rows: UpcomingRow[], bucket: DistributionBucket): UpcomingRow[] {
  return [...rows].sort((a, b) => {
    if (bucket === "paid_history") {
      const aDate = a.payableDate ?? a.exDate ?? a.recordDate ?? a.announcedDate ?? "";
      const bDate = b.payableDate ?? b.exDate ?? b.recordDate ?? b.announcedDate ?? "";
      if (aDate !== bDate) return bDate.localeCompare(aDate);
    }
    return b.distributionDollars - a.distributionDollars;
  });
}

function withHeat(rows: UpcomingRow[]): UpcomingRow[] {
  const max = rows.reduce((peak, row) => Math.max(peak, row.distributionDollars), 0);
  return rows.map((row) => ({
    ...row,
    heat: max > 0 ? row.distributionDollars / max : 0,
  }));
}

/** Sort + heat within one allocation so Current and Proposed tables stay independent. */
export function upcomingRowsForSide(
  allocation: PortfolioAllocationOut,
  side: "current" | "proposed",
  today = utcToday(),
): UpcomingRow[] {
  return withHeat(
    sortDistributionRows(rowsForSide(allocation, side, "upcoming", today), "upcoming"),
  );
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

export function totalUpcomingTax(
  allocation: PortfolioAllocationOut,
  today = utcToday(),
): number {
  return allocation.holdings.reduce(
    (sum, holding) => sum + (num(upcomingFromHolding(holding, today)?.estimated_tax) ?? 0),
    0,
  );
}
