import { redirect } from "next/navigation";
import { AftertaxApp, type CheckoutReturn } from "@/components/AftertaxApp";
import { getDistributionRepository } from "@/data";
import { loadCoverageSnapshot } from "@/lib/data-api/coverage";
import { firstSearchParam } from "@/lib/illustrate/fund-history";

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
  }>;
}) {
  const params = await searchParams;
  if (firstParam(params.tab) === "portfolio") {
    redirect("/portfolio");
  }
  if (firstParam(params.tab) === "compare") {
    redirect("/compare");
  }
  const repository = await getDistributionRepository();
  const [funds, highlights, facets, coverage] = await Promise.all([
    repository.search(),
    repository.highlights(5),
    repository.facets(),
    loadCoverageSnapshot(),
  ]);

  return (
    <main className="mx-auto w-full max-w-7xl px-4 pb-16 pt-6 sm:px-6 lg:px-8">
      <AftertaxApp
        funds={funds}
        highlights={highlights}
        facets={facets}
        coverageFamilies={coverage.families}
        checkout={checkoutFromSearchParams(params.checkout)}
        ticker={firstSearchParam(params.ticker)}
      />
    </main>
  );
}
