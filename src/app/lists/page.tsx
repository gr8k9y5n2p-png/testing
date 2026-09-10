import type { Metadata } from "next";
import { Disclaimer } from "@/components/Disclaimer";
import { CoverageProvider } from "@/components/coverage/CoverageProvider";
import { ListsWorkspace } from "@/components/lists/ListsWorkspace";
import { getDistributionRepository } from "@/data";
import { COPY, LISTS_DETAIL, LISTS_HEADING } from "@/lib/copy";
import { loadCoverageSnapshot } from "@/lib/data-api/coverage";
import { loadListRowsFromDataApi } from "@/lib/data-api/lists-page";
import { parseListsQueryTickers } from "@/lib/lists/parse-tickers";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: `Aftertax — ${LISTS_HEADING}`,
  description: `${COPY.sub} ${LISTS_DETAIL}`,
};

export default async function ListsPage({
  searchParams,
}: {
  searchParams: Promise<{
    tickers?: string | string[];
    ticker?: string | string[];
  }>;
}) {
  const params = await searchParams;
  const initialTickers = parseListsQueryTickers(params);
  const repository = await getDistributionRepository();
  const fundsPromise = repository.search();
  const [funds, coverage, initialRows] = await Promise.all([
    fundsPromise,
    loadCoverageSnapshot(),
    initialTickers.length
      ? fundsPromise.then((catalog) =>
          loadListRowsFromDataApi({ tickers: initialTickers, catalog }),
        )
      : Promise.resolve([]),
  ]);

  return (
    <main className="mx-auto w-full max-w-7xl px-4 pb-16 pt-6 sm:px-6 lg:px-8">
      <CoverageProvider families={coverage.families}>
        <ListsWorkspace
          key={initialTickers.join(",") || "empty"}
          funds={funds}
          initialTickers={initialTickers}
          initialRows={initialRows}
        />
      </CoverageProvider>
      <Disclaimer className="mt-8 text-xs leading-relaxed text-muted" />
    </main>
  );
}
