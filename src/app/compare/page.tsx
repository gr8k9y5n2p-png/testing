import type { Metadata } from "next";
import { Disclaimer } from "@/components/Disclaimer";
import { CoverageProvider } from "@/components/coverage/CoverageProvider";
import { HomepageFundCompare } from "@/components/illustrate/HomepageFundCompare";
import { getDistributionRepository } from "@/data";
import { loadCoverageSnapshot } from "@/lib/data-api/coverage";
import { COPY } from "@/lib/copy";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Aftertax — fund-to-fund comparison",
  description: `${COPY.sub} Year-over-year tax impact for two funds.`,
};

function firstParam(value: string | string[] | undefined): string | undefined {
  return Array.isArray(value) ? value[0] : value;
}

export default async function ComparePage({
  searchParams,
}: {
  searchParams: Promise<{ left?: string | string[]; right?: string | string[] }>;
}) {
  const params = await searchParams;
  const repository = await getDistributionRepository();
  const [funds, coverage] = await Promise.all([
    repository.search(),
    loadCoverageSnapshot(),
  ]);

  return (
    <main className="mx-auto w-full max-w-7xl px-4 pb-16 pt-6 sm:px-6 lg:px-8">
      <CoverageProvider families={coverage.families}>
        <HomepageFundCompare
          funds={funds}
          initialLeftTicker={firstParam(params.left)}
          initialRightTicker={firstParam(params.right)}
        />
      </CoverageProvider>
      <Disclaimer className="mt-8 text-xs leading-relaxed text-muted" />
    </main>
  );
}
