import { getDistributionRepository } from "@/data";
import { FUND_PAGE_SIZE, parseFundPageQuery } from "@/data/pagination";
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
    });
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
  });
}
