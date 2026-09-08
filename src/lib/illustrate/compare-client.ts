import { dataApiUrl } from "@/lib/data-api/config";
import { mockCompareResponse } from "@/lib/illustrate/compare-fixture";
import { toDataApiCompareBody } from "@/lib/illustrate/compare-request";
import { seedNavLookup } from "@/lib/illustrate/seed-nav";
import type {
  CompareRequest,
  CompareResponse,
} from "@/lib/illustrate/compare-types";
import { IllustrateRequestError } from "@/lib/illustrate/client";

export function getCompareEndpoint(): string {
  if (process.env.NEXT_PUBLIC_COMPARE_URL?.trim()) {
    return process.env.NEXT_PUBLIC_COMPARE_URL.replace(/\/$/, "");
  }
  return dataApiUrl("/illustrate/compare");
}

export function isMockCompareEndpoint(endpoint = getCompareEndpoint()): boolean {
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

function normalizeIllustration(raw: unknown, fallbackLabel: string) {
  const row = asRecord(raw);
  const totals = asRecord(row.totals);
  return {
    label: String(row.label ?? fallbackLabel),
    matched: row.matched !== false,
    holding_dollars: numOrNull(row.holding_dollars) ?? undefined,
    components: Array.isArray(row.components) ? row.components : [],
    totals: {
      distribution_dollars: num(totals.distribution_dollars),
      estimated_tax: num(totals.estimated_tax ?? totals.estimated_tax_dollars),
      estimated_tax_dollars: num(totals.estimated_tax_dollars ?? totals.estimated_tax),
      effective_tax_on_holding: num(totals.effective_tax_on_holding),
    },
    notes: Array.isArray(row.notes) ? row.notes.map(String) : [],
  };
}

function normalizeDeltas(raw: unknown) {
  const row = asRecord(raw);
  return {
    distribution_dollars: num(row.distribution_dollars),
    distribution_dollars_min: numOrNull(row.distribution_dollars_min),
    distribution_dollars_max: numOrNull(row.distribution_dollars_max),
    estimated_tax: num(row.estimated_tax ?? row.estimated_tax_dollars),
    estimated_tax_min: numOrNull(row.estimated_tax_min),
    estimated_tax_max: numOrNull(row.estimated_tax_max),
    federal_tax: num(row.federal_tax),
    state_tax: num(row.state_tax),
    effective_tax_on_holding: num(row.effective_tax_on_holding),
    effective_tax_on_holding_min: numOrNull(row.effective_tax_on_holding_min),
    effective_tax_on_holding_max: numOrNull(row.effective_tax_on_holding_max),
  };
}

export function normalizeCompareResponse(
  raw: Record<string, unknown>,
  source: "mock" | "live" = "live",
): CompareResponse {
  const periodsRaw = Array.isArray(raw.periods) ? raw.periods : [];
  const summaryRaw = asRecord(raw.summary);
  const inception = asRecord(summaryRaw.common_inception);
  const upcomingRaw = summaryRaw.upcoming_taxable_distribution;
  const upcoming =
    upcomingRaw && typeof upcomingRaw === "object"
      ? asRecord(upcomingRaw)
      : null;
  const notes = Array.isArray(raw.notes) ? raw.notes.map(String) : [];

  return {
    mode: raw.mode === "yoy" ? "yoy" : "fund_vs_fund",
    source,
    left: raw.left ? normalizeIllustration(raw.left, "Fund A") : null,
    right: raw.right ? normalizeIllustration(raw.right, "Fund B") : null,
    deltas: raw.deltas ? normalizeDeltas(raw.deltas) : null,
    periods: periodsRaw.map((item) => {
      const row = asRecord(item);
      return {
        year: num(row.year),
        as_of: row.as_of == null ? null : String(row.as_of),
        left: normalizeIllustration(row.left, "Fund A"),
        right: normalizeIllustration(row.right, "Fund B"),
        deltas: normalizeDeltas(row.deltas),
      };
    }),
    summary: {
      normalized_holding_dollars: num(
        summaryRaw.normalized_holding_dollars,
        10_000,
      ),
      total_tax_difference: num(summaryRaw.total_tax_difference),
      annualized_tax_drag_delta: num(summaryRaw.annualized_tax_drag_delta),
      distribution_dollars_difference: num(
        summaryRaw.distribution_dollars_difference,
      ),
      periods_compared: num(summaryRaw.periods_compared, periodsRaw.length),
      common_inception: {
        from_year: numOrNull(inception.from_year),
        to_year: numOrNull(inception.to_year),
        from_as_of: inception.from_as_of == null ? null : String(inception.from_as_of),
        to_as_of: inception.to_as_of == null ? null : String(inception.to_as_of),
      },
      upcoming_taxable_distribution: upcoming
        ? {
            left_dollars: numOrNull(upcoming.left_dollars),
            right_dollars: numOrNull(upcoming.right_dollars),
            delta_dollars: numOrNull(upcoming.delta_dollars),
            left_as_of:
              upcoming.left_as_of == null ? null : String(upcoming.left_as_of),
            right_as_of:
              upcoming.right_as_of == null ? null : String(upcoming.right_as_of),
            left_publication_stage:
              upcoming.left_publication_stage == null
                ? null
                : String(upcoming.left_publication_stage),
            right_publication_stage:
              upcoming.right_publication_stage == null
                ? null
                : String(upcoming.right_publication_stage),
          }
        : null,
    },
    notes,
  };
}

export async function postIllustrateCompare(
  request: CompareRequest,
  init?: { signal?: AbortSignal },
): Promise<CompareResponse> {
  const endpoint = getCompareEndpoint();
  const remote = !isMockCompareEndpoint(endpoint);
  const payload = toDataApiCompareBody(request, seedNavLookup);

  async function post(url: string) {
    return fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(payload),
      signal: init?.signal,
    });
  }

  let response: Response;
  let usedMock = !remote;
  try {
    response = await post(endpoint);
    if (remote && response.status >= 500) {
      response = await post("/api/illustrate/compare");
      usedMock = true;
    }
  } catch (error) {
    if (remote && !init?.signal?.aborted) {
      response = await post("/api/illustrate/compare");
      usedMock = true;
    } else if (!remote) {
      return mockCompareResponse(payload);
    } else {
      throw error;
    }
  }

  if (!response.ok) {
    let detail = `Compare failed (${response.status})`;
    let code: string | undefined;
    try {
      const body = (await response.json()) as { detail?: string; code?: string };
      if (body.detail) detail = body.detail;
      code = body.code;
    } catch {
      /* ignore */
    }
    throw new IllustrateRequestError(detail, response.status, code);
  }

  const raw = (await response.json()) as Record<string, unknown>;
  const source =
    usedMock || raw.source === "mock" || isMockCompareEndpoint(endpoint)
      ? "mock"
      : "live";
  return normalizeCompareResponse(raw, source);
}
