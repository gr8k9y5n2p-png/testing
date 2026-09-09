import {
  getIllustrateEndpoint,
  isMockIllustrateEndpoint,
} from "@/lib/data-api/config";
import {
  toDataApiIllustrateBody,
  userFacingIllustrateError,
} from "@/lib/illustrate/illustrate-request";
import { userFacingNotes } from "@/lib/illustrate/user-facing-notes";
import type {
  IllustrateErrorBody,
  IllustrateRequest,
  IllustrateResponse,
  IllustrationComponent,
  TaxRates,
} from "@/lib/illustrate/types";

export {
  getIllustrateEndpoint,
  isMockIllustrateEndpoint as isMockIllustrate,
} from "@/lib/data-api/config";

export {
  ENTER_NAV_COPY,
  ENTER_NAV_DETAIL,
  NEED_FUND_PRICE_COPY,
  NAV_OR_SHARES_REQUIRED_DETAIL,
  isMissingNavError,
  toDataApiIllustrateBody,
  userFacingIllustrateError,
} from "@/lib/illustrate/illustrate-request";

export class IllustrateRequestError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly code?: string,
  ) {
    super(message);
  }
}

function num(value: unknown): number | null {
  if (value == null || value === "") return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function requiredNum(value: unknown, fallback = 0): number {
  return num(value) ?? fallback;
}

/**
 * POSTs the locked request JSON. UI field is `selector`.
 * PR #2 FastAPI expects `selectors` — both are sent to the Data API.
 * Inbound responses are coerced into the locked UI shape (`estimated_tax_dollars`,
 * `warnings`, `tax_rates_applied`) from older aliases (`estimated_tax`, `notes`, `tax_rates`).
 */
export function normalizeIllustrateResponse(raw: Record<string, unknown>): IllustrateResponse {
  const componentsRaw = Array.isArray(raw.components) ? raw.components : [];
  const components: IllustrationComponent[] = componentsRaw.map((item) => {
    const row = item as Record<string, unknown>;
    return {
      distribution_id: String(row.distribution_id ?? ""),
      fund_name: String(row.fund_name ?? ""),
      estimate_type: String(row.estimate_type ?? ""),
      amount_unit: String(row.amount_unit ?? ""),
      publication_stage:
        row.publication_stage == null ? null : String(row.publication_stage),
      as_of: row.as_of == null ? null : String(row.as_of),
      record_date: row.record_date == null ? null : String(row.record_date),
      ex_date: row.ex_date == null ? null : String(row.ex_date),
      payable_date: row.payable_date == null ? null : String(row.payable_date),
      distribution_dollars: num(row.distribution_dollars),
      distribution_dollars_min: num(row.distribution_dollars_min),
      distribution_dollars_max: num(row.distribution_dollars_max),
      rate_key: String(row.rate_key ?? row.federal_rate_key ?? "ordinary_income"),
      federal_rate: requiredNum(row.federal_rate),
      state_rate: requiredNum(row.state_rate),
      effective_rate: requiredNum(row.effective_rate ?? row.applied_rate),
      estimated_tax_dollars: num(row.estimated_tax_dollars ?? row.estimated_tax),
      estimated_tax_dollars_min: num(
        row.estimated_tax_dollars_min ?? row.estimated_tax_min,
      ),
      estimated_tax_dollars_max: num(
        row.estimated_tax_dollars_max ?? row.estimated_tax_max,
      ),
      notes:
        typeof row.notes === "string"
          ? row.notes
          : row.skip_reason == null
            ? null
            : String(row.skip_reason),
      amount: num(row.amount),
      percent_of_nav: num(row.percent_of_nav ?? row.pct_of_nav),
      nav_on_distribution_day: num(row.nav_on_distribution_day),
      nav_on_distribution_day_as_of:
        row.nav_on_distribution_day_as_of == null
          ? null
          : String(row.nav_on_distribution_day_as_of),
      nav_on_distribution_day_source:
        row.nav_on_distribution_day_source == null
          ? null
          : String(row.nav_on_distribution_day_source),
    };
  });

  const totalsRaw = (raw.totals ?? {}) as Record<string, unknown>;
  const warnings = userFacingNotes(
    Array.isArray(raw.warnings)
      ? raw.warnings
      : Array.isArray(raw.notes)
        ? raw.notes
        : [],
  );

  return {
    tax_rates_applied: (raw.tax_rates_applied ??
      raw.tax_rates) as TaxRates,
    components,
    totals: {
      distribution_dollars: requiredNum(totalsRaw.distribution_dollars),
      distribution_dollars_min: num(totalsRaw.distribution_dollars_min),
      distribution_dollars_max: num(totalsRaw.distribution_dollars_max),
      estimated_tax_dollars: requiredNum(
        totalsRaw.estimated_tax_dollars ?? totalsRaw.estimated_tax,
      ),
      estimated_tax_dollars_min: num(
        totalsRaw.estimated_tax_dollars_min ?? totalsRaw.estimated_tax_min,
      ),
      estimated_tax_dollars_max: num(
        totalsRaw.estimated_tax_dollars_max ?? totalsRaw.estimated_tax_max,
      ),
    },
    warnings,
    nav_per_share: num(raw.nav_per_share),
  };
}

export async function postIllustrate(
  request: IllustrateRequest,
  init?: { signal?: AbortSignal },
): Promise<IllustrateResponse> {
  const endpoint = getIllustrateEndpoint();
  const remote = !isMockIllustrateEndpoint(endpoint);
  const payload = remote ? toDataApiIllustrateBody(request) : request;

  async function post(url: string, body: unknown) {
    return fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(body),
      signal: init?.signal,
    });
  }

  const response = await post(endpoint, payload);
  if (remote && response.status >= 500) {
    throw new IllustrateRequestError(
      `Illustrate failed (${response.status})`,
      response.status,
    );
  }

  if (!response.ok) {
    let mapped = userFacingIllustrateError(
      null,
      `Illustrate failed (${response.status})`,
    );
    try {
      const body = (await response.json()) as IllustrateErrorBody;
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

  const raw = (await response.json()) as Record<string, unknown>;
  return normalizeIllustrateResponse(raw);
}
