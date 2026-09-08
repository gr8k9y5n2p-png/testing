import { redirect } from "next/navigation";
import { AftertaxApp, type CheckoutReturn } from "@/components/AftertaxApp";
import { getDistributionRepository } from "@/data";
import { loadCoverageSnapshot } from "@/lib/data-api/coverage";

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
  searchParams: Promise<{ checkout?: string | string[]; tab?: string | string[] }>;
}) {
  const params = await searchParams;
  if (firstParam(params.tab) === "portfolio") {
    redirect("/portfolio");
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
      />
    </main>
  );
}
