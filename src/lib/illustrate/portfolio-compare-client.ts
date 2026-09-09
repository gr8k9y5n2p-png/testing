import { dataApiUrl, isRemoteDataApi } from "@/lib/data-api/config";
import { IllustrateRequestError } from "@/lib/illustrate/client";
import { userFacingIllustrateError } from "@/lib/illustrate/illustrate-error";
import {
  positiveNav,
  withPortfolioHoldingNav,
  type NavLookup,
} from "@/lib/illustrate/compare-request";
import {
  mockPortfolioCompareResponse,
  synthesizePortfolioCompare,
} from "@/lib/illustrate/portfolio-compare-fixture";
import { normalizePortfolioComparePeriods } from "@/lib/illustrate/portfolio-period-map";
import { ensurePortfolioComparePeriods } from "@/lib/illustrate/portfolio-year-tax";
import { seedFundNameLookup, seedNavLookup } from "@/lib/illustrate/seed-nav";
import type {
  PortfolioAllocationOut,
  PortfolioCompareRequest,
  PortfolioCompareResponse,
  PortfolioCompareSideIn,
  PortfolioCoverageOut,
  PortfolioDistributionRow,
  PortfolioGapOut,
  PortfolioHoldingOut,
  PortfolioTotalsOut,
  PortfolioUpcoming,
} from "@/lib/illustrate/portfolio-compare-types";

export function getPortfolioCompareEndpoint(): string {
  if (process.env.NEXT_PUBLIC_PORTFOLIO_COMPARE_URL?.trim()) {
    return process.env.NEXT_PUBLIC_PORTFOLIO_COMPARE_URL.replace(/\/$/, "");
  }
  return dataApiUrl("/illustrate/portfolio/compare");
}

export function isMockPortfolioCompareEndpoint(
  endpoint = getPortfolioCompareEndpoint(),
): boolean {
  return endpoint.startsWith("/");
}

function num(value: unknown, fallback = 0): number {
  if (value == null || value === "") return fallback;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function numOrNull(value: unknown): number | null {
  if (value == null || value === "") return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" ? (value as Record<string, unknown>) : {};
}

function isoOrNull(value: unknown): string | null {
  if (value == null || value === "") return null;
  const day = String(value).trim().slice(0, 10);
  return /^\d{4}-\d{2}-\d{2}$/.test(day) ? day : String(value);
}

function normalizeDistributionRow(raw: unknown): PortfolioDistributionRow | null {
  if (raw == null || typeof raw !== "object") return null;
  const row = asRecord(raw);
  return {
    distribution_dollars: numOrNull(
      row.distribution_dollars ?? row.distributionDollars,
    ),
    estimated_tax: numOrNull(row.estimated_tax ?? row.estimated_tax_dollars),
    percent_of_nav: numOrNull(
      row.percent_of_nav ?? row.pct_of_nav ?? row.distribution_pct_nav,
    ),
    as_of: isoOrNull(row.as_of),
    announced_date: isoOrNull(row.announced_date ?? row.announcedDate),
    record_date: isoOrNull(row.record_date ?? row.recordDate),
    ex_date: isoOrNull(row.ex_date ?? row.exDate),
    payable_date: isoOrNull(row.payable_date ?? row.payableDate),
    publication_stage:
      row.publication_stage == null && row.stage == null
        ? null
        : String(row.publication_stage ?? row.stage),
  };
}

function normalizeUpcoming(raw: unknown): PortfolioUpcoming | PortfolioUpcoming[] | null | undefined {
  if (raw === undefined) return undefined;
  if (raw == null) return null;
  if (Array.isArray(raw)) {
    return raw
      .map((item) => normalizeDistributionRow(item))
      .filter((item): item is PortfolioDistributionRow => item != null);
  }
  return normalizeDistributionRow(raw);
}

function normalizeDistributionList(raw: unknown): PortfolioDistributionRow[] | undefined {
  if (raw == null) return undefined;
  if (!Array.isArray(raw)) return undefined;
  return raw
    .map((item) => normalizeDistributionRow(item))
    .filter((item): item is PortfolioDistributionRow => item != null);
}

export { normalizePortfolioComparePeriods } from "@/lib/illustrate/portfolio-period-map";

function withSideNav(
  side: PortfolioCompareSideIn,
  lookup: NavLookup,
): PortfolioCompareSideIn {
  const nameLookup = isRemoteDataApi() ? () => undefined : seedFundNameLookup;
  return {
    ...side,
    holdings: side.holdings.map((holding) =>
      withPortfolioHoldingNav(holding, lookup, nameLookup),
    ),
  };
}

/**
 * Calendar-year tax $ — send `periods: [{year:2021}…{year:2025}]`.
 * Attach search/seed `nav_per_share` (> 0 only) so per_share paid_history
 * rows are not dropped. Same pattern as fund compare #19.
 */
export function toPortfolioCompareRequestBody(
  request: PortfolioCompareRequest,
  lookup: NavLookup = seedNavLookup,
): Record<string, unknown> {
  const navLookup: NavLookup = isRemoteDataApi() ? () => undefined : lookup;
  const body: Record<string, unknown> = {
    current: withSideNav(request.current, navLookup),
    proposed: withSideNav(request.proposed, navLookup),
    tax_rates: request.tax_rates ?? {},
    combine_state_with_federal: request.combine_state_with_federal !== false,
    periods: ensurePortfolioComparePeriods(request.periods),
  };
  if (request.snapshot) body.snapshot = request.snapshot;
  return body;
}

function normalizeHolding(raw: unknown, index: number): PortfolioHoldingOut {
  const row = asRecord(raw);
  const illustrationRaw = row.illustration ? asRecord(row.illustration) : null;
  const totalsRaw = illustrationRaw ? asRecord(illustrationRaw.totals) : {};
  const components = Array.isArray(illustrationRaw?.components)
    ? illustrationRaw.components.map((item) => {
        const component = asRecord(item);
        return {
          distribution_dollars: numOrNull(component.distribution_dollars),
          estimated_tax: numOrNull(
            component.estimated_tax ?? component.estimated_tax_dollars,
          ),
          estimated_tax_dollars: numOrNull(
            component.estimated_tax_dollars ?? component.estimated_tax,
          ),
          as_of: isoOrNull(component.as_of),
          announced_date: isoOrNull(component.announced_date ?? component.announcedDate),
          record_date: isoOrNull(component.record_date ?? component.recordDate),
          ex_date: isoOrNull(component.ex_date ?? component.exDate),
          payable_date: isoOrNull(component.payable_date ?? component.payableDate),
          publication_stage:
            component.publication_stage == null
              ? null
              : String(component.publication_stage),
        };
      })
    : [];

  return {
    holding_index: num(row.holding_index, index),
    ticker: row.ticker == null ? null : String(row.ticker),
    fund_identifier: row.fund_identifier == null ? null : String(row.fund_identifier),
    fund_family: row.fund_family == null ? null : String(row.fund_family),
    fund_name: row.fund_name == null ? null : String(row.fund_name),
    holding_dollars: num(row.holding_dollars),
    weight_pct: numOrNull(row.weight_pct),
    covered: row.covered !== false && !row.gap_reason,
    publication_stage_used:
      row.publication_stage_used == null ? null : String(row.publication_stage_used),
    warnings: Array.isArray(row.warnings) ? row.warnings.map(String) : [],
    upcoming: normalizeUpcoming(
      Object.prototype.hasOwnProperty.call(row, "upcoming") ? row.upcoming : undefined,
    ),
    paid_history: Object.prototype.hasOwnProperty.call(row, "paid_history")
      ? normalizeUpcoming(row.paid_history) ?? []
      : undefined,
    distributions: normalizeDistributionList(row.distributions),
    history: normalizeDistributionList(row.history),
    gap_reason: row.gap_reason == null ? null : String(row.gap_reason),
    illustration: illustrationRaw
      ? {
          components,
          totals: {
            distribution_dollars: num(totalsRaw.distribution_dollars),
            estimated_tax: num(
              totalsRaw.estimated_tax ?? totalsRaw.estimated_tax_dollars,
            ),
            estimated_tax_dollars: num(
              totalsRaw.estimated_tax_dollars ?? totalsRaw.estimated_tax,
            ),
            effective_tax_on_holding: num(totalsRaw.effective_tax_on_holding),
          },
        }
      : null,
  };
}

function normalizeCoverage(raw: unknown): PortfolioCoverageOut {
  const row = asRecord(raw);
  return {
    dollars_total: num(row.dollars_total),
    dollars_covered: num(row.dollars_covered),
    dollars_uncovered: num(row.dollars_uncovered),
    coverage_pct: num(row.coverage_pct),
    holdings_covered: numOrNull(row.holdings_covered) ?? undefined,
    holdings_uncovered: numOrNull(row.holdings_uncovered) ?? undefined,
  };
}

function normalizeTotals(raw: unknown, holdings: PortfolioHoldingOut[]): PortfolioTotalsOut {
  const row = asRecord(raw);
  const estimatedTax = num(
    row.estimated_tax ?? row.estimated_tax_dollars,
    holdings
      .filter((holding) => holding.covered)
      .reduce(
        (sum, holding) => sum + (holding.illustration?.totals?.estimated_tax ?? 0),
        0,
      ),
  );
  const distributionDollars = num(
    row.distribution_dollars,
    holdings
      .filter((holding) => holding.covered)
      .reduce((sum, holding) => {
        const upcomingRows = Array.isArray(holding.upcoming)
          ? holding.upcoming
          : holding.upcoming
            ? [holding.upcoming]
            : [];
        const upcoming = upcomingRows.reduce<number | null>((total, item) => {
          const value = numOrNull(item.distribution_dollars);
          if (value == null) return total;
          return (total ?? 0) + value;
        }, null);
        const fromIllustration = holding.illustration?.totals?.distribution_dollars;
        return sum + (upcoming ?? fromIllustration ?? 0);
      }, 0),
  );
  const book = holdings.reduce((sum, holding) => sum + holding.holding_dollars, 0);
  return {
    distribution_dollars: distributionDollars,
    distribution_dollars_min: numOrNull(row.distribution_dollars_min),
    distribution_dollars_max: numOrNull(row.distribution_dollars_max),
    estimated_tax: estimatedTax,
    estimated_tax_dollars: num(row.estimated_tax_dollars ?? estimatedTax),
    estimated_tax_min: numOrNull(row.estimated_tax_min ?? row.estimated_tax_dollars_min),
    estimated_tax_max: numOrNull(row.estimated_tax_max ?? row.estimated_tax_dollars_max),
    federal_tax: numOrNull(row.federal_tax) ?? undefined,
    state_tax: numOrNull(row.state_tax) ?? undefined,
    effective_tax_on_holding: num(
      row.effective_tax_on_holding,
      book > 0 ? estimatedTax / book : 0,
    ),
  };
}

function normalizeGaps(raw: unknown): PortfolioGapOut[] {
  if (!Array.isArray(raw)) return [];
  return raw.map((item) => {
    const row = asRecord(item);
    return {
      holding_index: numOrNull(row.holding_index) ?? undefined,
      ticker: row.ticker == null ? null : String(row.ticker),
      fund_identifier: row.fund_identifier == null ? null : String(row.fund_identifier),
      fund_family: row.fund_family == null ? null : String(row.fund_family),
      fund_name: row.fund_name == null ? null : String(row.fund_name),
      holding_dollars: num(row.holding_dollars),
      reason: String(row.reason ?? ""),
    };
  });
}

export function normalizePortfolioAllocation(
  raw: unknown,
  fallbackLabel: string,
): PortfolioAllocationOut {
  const row = asRecord(raw);
  const holdingsRaw = Array.isArray(row.holdings) ? row.holdings : [];
  const holdings = holdingsRaw.map((item, index) => normalizeHolding(item, index));
  return {
    label: String(row.label ?? fallbackLabel),
    holdings,
    totals: normalizeTotals(row.totals, holdings),
    coverage: normalizeCoverage(row.coverage),
    gaps: normalizeGaps(row.gaps),
    warnings: [
      ...(Array.isArray(row.warnings) ? row.warnings : []),
      ...(Array.isArray(row.notes) ? row.notes : []),
    ].map(String),
    notes: Array.isArray(row.notes) ? row.notes.map(String) : [],
  };
}

export function normalizePortfolioCompareResponse(
  raw: Record<string, unknown>,
  source: "mock" | "live" = "live",
): PortfolioCompareResponse {
  const current = normalizePortfolioAllocation(raw.current, "Current Allocation");
  const proposed = normalizePortfolioAllocation(raw.proposed, "Proposed Allocation");
  const deltasRaw = asRecord(raw.deltas);
  const summaryRaw = asRecord(raw.summary);
  const notes = Array.isArray(raw.notes) ? raw.notes.map(String) : [];

  const estimatedTax = num(
    deltasRaw.estimated_tax ?? deltasRaw.estimated_tax_dollars,
    proposed.totals.estimated_tax - current.totals.estimated_tax,
  );
  const distributionDollars = num(
    deltasRaw.distribution_dollars,
    proposed.totals.distribution_dollars - current.totals.distribution_dollars,
  );
  const drag = num(
    deltasRaw.effective_tax_on_holding,
    proposed.totals.effective_tax_on_holding - current.totals.effective_tax_on_holding,
  );
  const coverage = num(
    deltasRaw.coverage_pct,
    proposed.coverage.coverage_pct - current.coverage.coverage_pct,
  );

  return {
    source,
    current,
    proposed,
    deltas: {
      estimated_tax: estimatedTax,
      distribution_dollars: distributionDollars,
      effective_tax_on_holding: drag,
      coverage_pct: coverage,
      estimated_tax_min: numOrNull(deltasRaw.estimated_tax_min),
      estimated_tax_max: numOrNull(deltasRaw.estimated_tax_max),
      distribution_dollars_min: numOrNull(deltasRaw.distribution_dollars_min),
      distribution_dollars_max: numOrNull(deltasRaw.distribution_dollars_max),
    },
    summary: {
      normalized_book_dollars: num(summaryRaw.normalized_book_dollars, 10_000),
      estimated_tax: num(summaryRaw.estimated_tax, estimatedTax),
      distribution_dollars: num(summaryRaw.distribution_dollars, distributionDollars),
      effective_tax_on_holding: num(summaryRaw.effective_tax_on_holding, drag),
      coverage_pct: num(summaryRaw.coverage_pct, coverage),
    },
    notes,
    periods: normalizePortfolioComparePeriods(raw.periods),
  };
}

function jsonPost(url: string, body: unknown, signal?: AbortSignal) {
  return fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify(body),
    signal,
  });
}

function toPortfolioIllustrateBody(side: PortfolioCompareSideIn) {
  const book = side.book_dollars;
  return {
    holdings: side.holdings.map((holding) => {
      const weight = holding.weight_pct;
      const dollars =
        holding.holding_dollars ??
        (weight != null && book
          ? (weight / 100) * book
          : holding.holding_dollars);
      return {
        ticker: holding.ticker,
        fund_family: holding.fund_family,
        fund_identifier: holding.fund_identifier ?? holding.ticker,
        fund_name: holding.fund_name,
        holding_dollars: dollars,
        weight_pct: dollars ? undefined : weight,
        book_dollars: book,
        ...(positiveNav(holding.nav_per_share) != null
          ? { nav_per_share: positiveNav(holding.nav_per_share) }
          : {}),
        ...(positiveNav(holding.shares) != null
          ? { shares: positiveNav(holding.shares) }
          : {}),
        distribution_ids: holding.distribution_ids,
      };
    }),
  };
}

async function postPortfolioSide(
  side: PortfolioCompareSideIn,
  taxRates: PortfolioCompareRequest["tax_rates"],
  combine: boolean | undefined,
  signal?: AbortSignal,
): Promise<PortfolioAllocationOut | null> {
  const endpoint = dataApiUrl("/illustrate/portfolio");
  const body = {
    ...toPortfolioIllustrateBody(side),
    tax_rates: taxRates ?? {},
    combine_state_with_federal: combine !== false,
  };

  async function post(url: string) {
    return jsonPost(url, body, signal);
  }

  let response: Response;
  try {
    response = await post(endpoint);
    if (isRemoteDataApi() && (response.status >= 500 || response.status === 404)) {
      return null;
    }
  } catch (error) {
    if (isRemoteDataApi()) return null;
    throw error;
  }

  if (!response.ok) return null;
  const raw = (await response.json()) as Record<string, unknown>;
  if (!Array.isArray(raw.holdings) && raw.totals == null) return null;
  return normalizePortfolioAllocation(
    { ...raw, label: side.label },
    side.label || "Allocation",
  );
}

export async function postIllustratePortfolioCompare(
  request: PortfolioCompareRequest,
  init?: { signal?: AbortSignal },
): Promise<PortfolioCompareResponse> {
  const endpoint = getPortfolioCompareEndpoint();
  const remote = !isMockPortfolioCompareEndpoint(endpoint);

  let response: Response | undefined;
  try {
    response = await jsonPost(endpoint, toPortfolioCompareRequestBody(request), init?.signal);
    if (remote && (response.status >= 500 || response.status === 404)) {
      response = undefined;
    }
  } catch (error) {
    if (!remote) {
      return mockPortfolioCompareResponse(request);
    }
    if (init?.signal?.aborted) throw error;
    response = undefined;
  }

  if (response?.ok) {
    const raw = (await response.json()) as Record<string, unknown>;
    const source =
      !remote || raw.source === "mock" || isMockPortfolioCompareEndpoint(endpoint)
        ? "mock"
        : "live";
    return normalizePortfolioCompareResponse(raw, source);
  }

  if (response && response.status >= 400 && response.status < 500 && response.status !== 404) {
    let mapped = userFacingIllustrateError(
      null,
      `Portfolio compare failed (${response.status})`,
    );
    try {
      const body = (await response.json()) as Record<string, unknown>;
      mapped = userFacingIllustrateError(
        body,
        typeof body.detail === "string" && body.detail
          ? body.detail
          : mapped.message,
      );
    } catch {
      /* ignore */
    }
    throw new IllustrateRequestError(mapped.message, response.status, mapped.code);
  }

  try {
    const [current, proposed] = await Promise.all([
      postPortfolioSide(
        request.current,
        request.tax_rates,
        request.combine_state_with_federal,
        init?.signal,
      ),
      postPortfolioSide(
        request.proposed,
        request.tax_rates,
        request.combine_state_with_federal,
        init?.signal,
      ),
    ]);
    if (
      current &&
      proposed &&
      (current.holdings.length > 0 || proposed.holdings.length > 0) &&
      (current.totals.estimated_tax > 0 ||
        proposed.totals.estimated_tax > 0 ||
        current.holdings.some((holding) => holding.illustration || holding.upcoming))
    ) {
      return synthesizePortfolioCompare(current, proposed, remote ? "live" : "mock");
    }
  } catch (error) {
    if (init?.signal?.aborted) throw error;
  }

  if (!remote) {
    return mockPortfolioCompareResponse(request);
  }

  throw new IllustrateRequestError(
    "Portfolio compare is unavailable from the Data API.",
    response?.status ?? 503,
  );
}
