import { mapFundsApiItem, type FundsApiItem } from "@/data/funds-list";
import {
  collectTaxYearsFromFunds,
  mergeTaxYears,
  taxYearsFromPayload,
} from "@/data/tax-years";
import { loadCoverageSnapshot } from "@/lib/data-api/coverage";
import { fetchDataApi } from "@/lib/data-api/fetch";

type FundsYearPayload = {
  items?: unknown[];
  data?: unknown[];
  years?: unknown;
  tax_years?: unknown;
  facets?: unknown;
};

function isFundsApiItem(row: unknown): row is FundsApiItem {
  if (!row || typeof row !== "object") return false;
  const record = row as Record<string, unknown>;
  return (
    "fund_name" in record ||
    "fund_identifier" in record ||
    "fundName" in record ||
    "ticker" in record
  );
}

async function taxYearsFromFundsCatalog(): Promise<number[]> {
  try {
    const response = await fetchDataApi("/funds?limit=50&offset=0&page=1&page_size=50", {
      fallbackPath: "/funds?limit=50&offset=0",
    });
    if (!response.ok) return [];
    const payload = (await response.json()) as FundsYearPayload;
    const raw = Array.isArray(payload.items)
      ? payload.items
      : Array.isArray(payload.data)
        ? payload.data
        : [];
    const items = raw.filter(isFundsApiItem).map((row) => mapFundsApiItem(row));
    return mergeTaxYears(taxYearsFromPayload(payload), collectTaxYearsFromFunds(items));
  } catch {
    return [];
  }
}

async function taxYearsFromDistributionPage(): Promise<number[]> {
  try {
    const response = await fetchDataApi("/distributions?page=1&page_size=200");
    if (!response.ok) return [];
    const payload = (await response.json()) as {
      items?: Array<{
        as_of?: string | null;
        record_date?: string | null;
        ex_date?: string | null;
        payable_date?: string | null;
      }>;
    };
    const fromRows = (payload.items ?? []).flatMap((row) => [
      row.payable_date,
      row.ex_date,
      row.record_date,
      row.as_of,
    ]);
    return mergeTaxYears(taxYearsFromPayload(payload), fromRows);
  } catch {
    return [];
  }
}

/**
 * Concrete tax years Data has already published. Coverage first, then
 * /funds and /distributions dates. Never fills 2021–N when those years
 * are absent from the payload.
 */
export async function loadTaxYearsFromDataApi(): Promise<number[]> {
  const [coverage, fromFunds, fromDists] = await Promise.all([
    loadCoverageSnapshot().then((snapshot) => snapshot.years).catch(() => []),
    taxYearsFromFundsCatalog(),
    taxYearsFromDistributionPage(),
  ]);
  return mergeTaxYears(coverage, fromFunds, fromDists);
}
