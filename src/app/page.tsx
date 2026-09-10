import { redirect } from "next/navigation";
import { AftertaxApp, type CheckoutReturn } from "@/components/AftertaxApp";
import {
  collectTaxYearsFromFunds,
  getDistributionRepository,
  mergeFundLists,
  mergeTaxYears,
} from "@/data";
import { loadCoverageSnapshot } from "@/lib/data-api/coverage";
import { loadFundPageFromDataApi } from "@/lib/data-api/funds-page";
import { firstSearchParam } from "@/lib/illustrate/fund-history";
import {
  compareTickersPath,
  parseCompareQueryTickers,
} from "@/lib/illustrate/compare-workspace";
import { listsTickersPath, parseListsQueryTickers } from "@/lib/lists/parse-tickers";

export const dynamic = "force-dynamic";

function firstParam(value: string | string[] | undefined): string | undefined {
  return Array.isArray(value) ? value[0] : value;
}

function checkoutFromSearchParams(
  value: string | string[] | undefined,
): CheckoutReturn {
  const raw = firstParam(value);
  if (raw === "success" || raw === "cancel") return raw;
  return null;
}

export default async function Home({
  searchParams,
}: {
  searchParams: Promise<{
    checkout?: string | string[];
    tab?: string | string[];
    ticker?: string | string[];
    tickers?: string | string[];
    left?: string | string[];
    right?: string | string[];
  }>;
}) {
  const params = await searchParams;
  if (firstParam(params.tab) === "portfolio") {
    redirect("/portfolio");
  }
  if (firstParam(params.tab) === "compare") {
    redirect(compareTickersPath(parseCompareQueryTickers(params)));
  }
  if (firstParam(params.tab) === "lists") {
    redirect(listsTickersPath(parseListsQueryTickers(params)));
  }
  const repository = await getDistributionRepository();
  const ticker = firstSearchParam(params.ticker);
  const [catalog, focused, highlights, facets, coverage] = await Promise.all([
    repository.search(),
    ticker
      ? loadFundPageFromDataApi({ query: ticker, limit: 10, offset: 0 })
      : Promise.resolve(null),
    repository.highlights(5),
    repository.facets(),
    loadCoverageSnapshot(),
  ]);
  const funds = mergeFundLists(catalog, focused?.items ?? []);
  const years = mergeTaxYears(
    facets.years,
    coverage.years,
    collectTaxYearsFromFunds(funds),
    focused?.years,
  );

  return (
    <main className="mx-auto w-full max-w-7xl px-4 pb-16 pt-6 sm:px-6 lg:px-8">
      <AftertaxApp
        funds={funds}
        highlights={highlights}
        facets={{ ...facets, years }}
        coverageFamilies={coverage.families}
        checkout={checkoutFromSearchParams(params.checkout)}
        ticker={ticker}
      />
    </main>
  );
}
