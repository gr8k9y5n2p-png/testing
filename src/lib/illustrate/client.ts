import {
  getIllustrateEndpoint,
  isMockIllustrateEndpoint,
} from "@/lib/data-api/config";
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
 * POSTs the locked request JSON as-is (`selector`, not `selectors`).
 * Inbound responses are coerced into the locked response shape if a host
 * still returns older aliases (`estimated_tax`, `notes`).
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
    };
  });

  const totalsRaw = (raw.totals ?? {}) as Record<string, unknown>;
  const warnings = Array.isArray(raw.warnings)
    ? raw.warnings.map(String)
    : Array.isArray(raw.notes)
      ? raw.notes.map(String)
      : [];

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
  };
}

export async function postIllustrate(
  request: IllustrateRequest,
  init?: { signal?: AbortSignal },
): Promise<IllustrateResponse> {
  const endpoint = getIllustrateEndpoint();
  const remote = !isMockIllustrateEndpoint(endpoint);

  let response: Response;
  try {
    response = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(request),
      signal: init?.signal,
    });
  } catch (error) {
    if (remote && !init?.signal?.aborted) {
      response = await fetch("/api/illustrate", {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify(request),
        signal: init?.signal,
      });
    } else {
      throw error;
    }
  }

  if (!response.ok) {
    let detail = `Illustrate failed (${response.status})`;
    let code: string | undefined;
    try {
      const body = (await response.json()) as IllustrateErrorBody;
      if (body.detail) detail = body.detail;
      code = body.code;
    } catch {
      /* ignore */
    }
    throw new IllustrateRequestError(detail, response.status, code);
  }

  const raw = (await response.json()) as Record<string, unknown>;
  return normalizeIllustrateResponse(raw);
}
