import { AftertaxApp } from "@/components/AftertaxApp";
import { getDistributionRepository } from "@/data";

export const dynamic = "force-dynamic";

export default async function Home() {
  const repository = getDistributionRepository();
  const [funds, highlights, facets] = await Promise.all([
    repository.search(),
    repository.highlights(5),
    repository.facets(),
  ]);

  return (
    <main className="mx-auto w-full max-w-7xl px-4 pb-16 pt-6 sm:px-6 lg:px-8">
      <AftertaxApp funds={funds} highlights={highlights} facets={facets} />
    </main>
  );
}
