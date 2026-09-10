import type { Metadata } from "next";
import { Disclaimer } from "@/components/Disclaimer";
import { CoverageProvider } from "@/components/coverage/CoverageProvider";
import { CompareWorkspace } from "@/components/illustrate/CompareWorkspace";
import { getDistributionRepository } from "@/data";
import { loadCoverageSnapshot } from "@/lib/data-api/coverage";
import { COPY } from "@/lib/copy";
import { parseCompareQueryTickers } from "@/lib/illustrate/compare-workspace";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Aftertax — compare funds",
  description: `${COPY.sub} Growth, tax drag, and upcoming for up to six tickers.`,
};

export default async function ComparePage({
  searchParams,
}: {
  searchParams: Promise<{
    tickers?: string | string[];
    ticker?: string | string[];
    left?: string | string[];
    right?: string | string[];
  }>;
}) {
  const params = await searchParams;
  const initialTickers = parseCompareQueryTickers(params);
  const repository = await getDistributionRepository();
  const [funds, coverage] = await Promise.all([
    repository.search(),
    loadCoverageSnapshot(),
  ]);

  return (
    <main className="mx-auto w-full max-w-7xl px-4 pb-16 pt-6 sm:px-6 lg:px-8">
      <CoverageProvider families={coverage.families}>
        <CompareWorkspace
          key={initialTickers.join(",") || "empty"}
          funds={funds}
          initialTickers={initialTickers}
        />
      </CoverageProvider>
      <Disclaimer className="mt-8 text-xs leading-relaxed text-muted" />
    </main>
  );
}
