import { DATA_SOURCE, getDistributionRepository, OUTLIER_THRESHOLD_PP } from "@/data";

export async function GET() {
  const repository = getDistributionRepository();
  const highlights = await repository.highlights(5);

  return Response.json({
    source: DATA_SOURCE,
    outlierThresholdPp: OUTLIER_THRESHOLD_PP,
    data: highlights,
  });
}
