import { redirect } from "next/navigation";
import { AftertaxApp, type CheckoutReturn } from "@/components/AftertaxApp";
import {
  collectTaxYearsFromFunds,
  getFacets,
  getHighlights,
  mergeFundLists,
  mergeTaxYears,
} from "@/data";
import { FUND_CATEGORIES } from "@/data/types";
import { loadCoverageSnapshot } from "@/lib/data-api/coverage";
import { loadUpcomingAnnouncedFromDataApi } from "@/lib/data-api/distributions";
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
  if (firstParam(params.tab) === "search") {
    const ticker = firstSearchParam(params.ticker);
    const checkout = checkoutFromSearchParams(params.checkout);
    const next = new URLSearchParams();
    if (ticker) next.set("ticker", ticker);
    if (checkout) next.set("checkout", checkout);
    const qs = next.toString();
    redirect(qs ? `/?${qs}` : "/");
  }
  if (firstParam(params.tab) === "portfolio") {
    redirect("/portfolio");
  }
  if (firstParam(params.tab) === "compare") {
    redirect(compareTickersPath(parseCompareQueryTickers(params)));
  }
  if (firstParam(params.tab) === "lists") {
    redirect(listsTickersPath(parseListsQueryTickers(params)));
  }
  const ticker = firstSearchParam(params.ticker);
  const [catalog, focused, coverage] = await Promise.all([
    loadUpcomingAnnouncedFromDataApi(),
    ticker
      ? loadFundPageFromDataApi({ query: ticker, limit: 10, offset: 0 })
      : Promise.resolve(null),
    loadCoverageSnapshot(),
  ]);
  const funds = mergeFundLists(catalog, focused?.items ?? []);
  const highlights = getHighlights(funds, 5);
  const facets = getFacets(funds);
  const years = mergeTaxYears(
    facets.years,
    coverage.years,
    collectTaxYearsFromFunds(funds),
    focused?.years,
  );
  const families = [
    ...new Set([
      ...facets.families,
      ...coverage.families.map((family) => family.display_name),
      "American Funds",
    ]),
  ]
    .filter((name) => name && name !== "—")
    .sort();
  const categories = [
    ...new Set([...facets.categories, ...FUND_CATEGORIES]),
  ]
    .filter((name) => name && name !== "—")
    .sort();

  return (
    <main className="mx-auto w-full max-w-7xl px-4 pb-16 pt-6 sm:px-6 lg:px-8">
      <AftertaxApp
        funds={funds}
        highlights={highlights}
        facets={{ families, categories, years }}
        coverageFamilies={coverage.families}
        checkout={checkoutFromSearchParams(params.checkout)}
        ticker={ticker}
      />
    </main>
  );
}
