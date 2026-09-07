import { getDistributionRepository } from "@/data";
import { DATA_SOURCE } from "@/data/types";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const yearValue = searchParams.get("year");
  const repository = await getDistributionRepository();
  const funds = await repository.search({
    query: searchParams.get("q") ?? undefined,
    family: searchParams.get("family") ?? undefined,
    category: searchParams.get("category") ?? undefined,
    year: yearValue ? Number(yearValue) : undefined,
  });

  return Response.json({
    source: DATA_SOURCE,
    count: funds.length,
    data: funds,
  });
}
