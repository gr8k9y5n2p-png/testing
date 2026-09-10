import { getDistributionRepository } from "@/data";
import { FUND_PAGE_SIZE, parseFundPageQuery } from "@/data/pagination";
import { collectTaxYearsFromFunds, mergeTaxYears } from "@/data/tax-years";
import { DATA_SOURCE } from "@/data/types";
import { isRemoteDataApi } from "@/lib/data-api/config";
import { loadFundPageFromDataApi } from "@/lib/data-api/funds-page";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const query = parseFundPageQuery(searchParams);
  const limit = query.limit ?? FUND_PAGE_SIZE;
  const offset = query.offset ?? 0;

  const live = await loadFundPageFromDataApi(query);
  if (live) {
    return Response.json({
      source: { kind: "live", label: "Data API /funds" },
      items: live.items,
      total: live.total,
      limit: live.limit,
      offset: live.offset,
      count: live.items.length,
      data: live.items,
      years: live.years ?? collectTaxYearsFromFunds(live.items),
    });
  }

  // Remote Data is set but /funds 5xx'd or failed — never a 200 empty catalog.
  if (isRemoteDataApi()) {
    return Response.json(
      {
        error: "upstream",
        source: { kind: "live", label: "Data API /funds unavailable" },
        items: [],
        total: 0,
        limit,
        offset,
        count: 0,
        data: [],
        years: [],
      },
      { status: 503, headers: { "Cache-Control": "no-store" } },
    );
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
