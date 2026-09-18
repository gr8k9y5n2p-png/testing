import { getDistributionRepository } from "@/data";
import { FUND_PAGE_SIZE, parseFundPageQuery, type FundPageResult } from "@/data/pagination";
import { collectTaxYearsFromFunds, mergeTaxYears } from "@/data/tax-years";
import { DATA_SOURCE } from "@/data/types";
import { isRemoteDataApi } from "@/lib/data-api/config";
import {
  loadFundPageFromDataApi,
  loadThinFundSearchFromDataApi,
} from "@/lib/data-api/funds-page";

export const maxDuration = 15;

function liveFundsJson(
  query: ReturnType<typeof parseFundPageQuery>,
  live: FundPageResult,
) {
  return {
    source: {
      kind: "live" as const,
      label: query.paidHistory
        ? (live.sourceLabel ?? "Data API /distributions")
        : "Data API /funds",
    },
    items: live.items,
    total: live.total,
    limit: live.limit,
    offset: live.offset,
    count: live.items.length,
    data: live.items,
    years: live.years ?? collectTaxYearsFromFunds(live.items),
    hasMore: live.hasMore === true,
  };
}

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const query = parseFundPageQuery(searchParams);
  const limit = query.limit ?? FUND_PAGE_SIZE;
  const offset = query.offset ?? 0;
  const thinPicker =
    query.navOnly === true &&
    Boolean(query.query?.trim()) &&
    !query.upcoming &&
    !query.paidHistory;

  // Compare / Search autocomplete: thin Data /funds?q=&limit= only.
  if (thinPicker) {
    const live = await loadThinFundSearchFromDataApi(query);
    if (live) return Response.json(liveFundsJson(query, live));
    return Response.json({
      source: {
        kind: "live",
        label: isRemoteDataApi()
          ? "Data API /funds unavailable"
          : "Data API /funds",
      },
      items: [],
      total: 0,
      limit,
      offset,
      count: 0,
      data: [],
      years: [],
    });
  }

  const live = await loadFundPageFromDataApi(query);
  if (live) {
    return Response.json(liveFundsJson(query, live));
  }

  // Remote Data is set but /funds 404'd or failed — do not dump /distributions.
  if (isRemoteDataApi()) {
    return Response.json({
      source: { kind: "live", label: "Data API /funds unavailable" },
      items: [],
      total: 0,
      limit,
      offset,
      count: 0,
      data: [],
      years: [],
    });
  }

  const repository = await getDistributionRepository();
  const page = repository.searchPage
    ? await repository.searchPage(query)
    : { items: [], total: 0, limit, offset };

  return Response.json({
    source: DATA_SOURCE,
    items: page.items,
    total: page.total,
    limit: page.limit,
    offset: page.offset,
    count: page.items.length,
    data: page.items,
    years: mergeTaxYears(page.years, collectTaxYearsFromFunds(page.items)),
  });
}
