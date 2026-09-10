import { getDistributionRepository } from "@/data";
import { loadListRowsFromDataApi } from "@/lib/data-api/lists-page";
import { parseTickerList } from "@/lib/lists/parse-tickers";

export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const tickers = parseTickerList(
    [searchParams.get("tickers"), ...searchParams.getAll("ticker")]
      .filter(Boolean)
      .join(","),
  );
  const repository = await getDistributionRepository();
  const catalog = await repository.search();
  const items = await loadListRowsFromDataApi({ tickers, catalog });
  return Response.json({
    items,
    tickers,
    count: items.length,
  });
}
