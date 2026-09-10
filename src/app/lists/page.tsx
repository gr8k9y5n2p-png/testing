import type { Metadata } from "next";
import { Disclaimer } from "@/components/Disclaimer";
import { CoverageProvider } from "@/components/coverage/CoverageProvider";
import { ListsWorkspace } from "@/components/lists/ListsWorkspace";
import { COPY, LISTS_DETAIL, LISTS_HEADING } from "@/lib/copy";
import { loadCoverageSnapshot } from "@/lib/data-api/coverage";
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
  const coverage = await loadCoverageSnapshot();

  return (
    <main className="mx-auto w-full max-w-7xl px-4 pb-16 pt-6 sm:px-6 lg:px-8">
      <CoverageProvider families={coverage.families}>
        <ListsWorkspace funds={[]} initialTickers={initialTickers} />
      </CoverageProvider>
      <Disclaimer className="mt-8 text-xs leading-relaxed text-muted" />
    </main>
  );
}
