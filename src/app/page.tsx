import { AftertaxApp, type CheckoutReturn } from "@/components/AftertaxApp";
import { getDistributionRepository } from "@/data";

export const dynamic = "force-dynamic";

function checkoutFromSearchParams(
  value: string | string[] | undefined,
): CheckoutReturn {
  const raw = Array.isArray(value) ? value[0] : value;
  if (raw === "success" || raw === "cancel") return raw;
  return null;
}

export default async function Home({
  searchParams,
}: {
  searchParams: Promise<{ checkout?: string | string[] }>;
}) {
  const params = await searchParams;
  const repository = getDistributionRepository();
  const [funds, highlights, facets] = await Promise.all([
    repository.search(),
    repository.highlights(5),
    repository.facets(),
  ]);

  return (
    <main className="mx-auto w-full max-w-7xl px-4 pb-16 pt-6 sm:px-6 lg:px-8">
      <AftertaxApp
        funds={funds}
        highlights={highlights}
        facets={facets}
        checkout={checkoutFromSearchParams(params.checkout)}
      />
    </main>
  );
}
