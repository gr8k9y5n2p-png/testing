import { getDistributionRepository } from "@/data";
import { FUND_PAGE_SIZE, parseFundPageQuery } from "@/data/pagination";
import { DATA_SOURCE } from "@/data/types";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const query = parseFundPageQuery(searchParams);
  const repository = await getDistributionRepository();
  const page = repository.searchPage
    ? await repository.searchPage(query)
    : {
        items: [],
        total: 0,
        limit: query.limit ?? FUND_PAGE_SIZE,
        offset: query.offset ?? 0,
      };

  return Response.json({
    source: DATA_SOURCE,
    items: page.items,
    total: page.total,
    limit: page.limit,
    offset: page.offset,
    // Legacy aliases — prefer `items` / `total` for page controls.
    count: page.items.length,
    data: page.items,
  });
}
