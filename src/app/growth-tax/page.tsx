import type { Metadata } from "next";
import { GrowthAndTaxDragModule } from "@/components/illustrate/GrowthAndTaxDragModule";
import { COPY } from "@/lib/copy";
import { firstSearchParam, growthFundFromTicker } from "@/lib/illustrate/fund-history";

export const metadata: Metadata = {
  title: "Aftertax — growth of $X and tax drag",
  description:
    "Stacked cumulative growth and annual tax-drag module. The homepage already mounts GrowthAndTaxDragModule as the illustrate hero.",
  robots: { index: false, follow: false },
};

const DEFAULT_FUNDS = [
  { ticker: "AGTHX", label: "AGTHX", fundFamily: "American Funds" },
  { ticker: "FCNTX", label: "FCNTX", fundFamily: "Fidelity" },
];

export default async function GrowthTaxDemoPage({
  searchParams,
}: {
  searchParams: Promise<{ ticker?: string | string[] }>;
}) {
  const ticker = firstSearchParam((await searchParams).ticker);
  const focused = ticker ? growthFundFromTicker(ticker) : undefined;

  return (
    <main className="mx-auto w-full max-w-5xl px-4 pb-16 pt-8 sm:px-6 lg:px-8">
      <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-muted">
        Homepage module
      </p>
      <h1 className="mt-1 font-serif text-3xl tracking-tight text-ink">
        Growth of $X + tax drag
      </h1>
      <p className="mt-2 max-w-2xl text-sm text-muted">
        Drop{" "}
        <code className="font-mono text-[13px] text-ink">
          GrowthAndTaxDragModule
        </code>{" "}
        into the homepage (already the illustrate hero). Top chart is{" "}
        <code className="font-mono text-[13px] text-ink">GET /performance</code>{" "}
        (or{" "}
        <code className="font-mono text-[13px] text-ink">
          POST /performance/growth
        </code>{" "}
        when the principal changes). Bottom bars are{" "}
        <code className="font-mono text-[13px] text-ink">
          POST /illustrate/compare
        </code>{" "}
        periods, drawn negative and side-by-side, with a % / $ toggle. Localhost
        uses mock fallbacks. Portfolio review links use{" "}
        <code className="font-mono text-[13px] text-ink">
          /?ticker=AMCAP#growth-and-tax
        </code>
        ; this demo also accepts{" "}
        <code className="font-mono text-[13px] text-ink">?ticker=</code>.
      </p>

      <div className="mt-8">
        <GrowthAndTaxDragModule
          funds={focused ? [focused] : DEFAULT_FUNDS}
        />
      </div>

      <pre className="mt-10 overflow-auto rounded-lg border border-line bg-surface p-4 text-[12px] leading-relaxed text-muted">
        {`import { GrowthAndTaxDragModule } from "@/components/illustrate";

<GrowthAndTaxDragModule
  funds={[
    { ticker: "AGTHX", label: "AGTHX" },
    { ticker: "FCNTX", label: "FCNTX" },
  ]}
  startDollars={10000}
/>`}
      </pre>

      <p className="mt-6 text-xs text-faint">{COPY.trust}</p>
    </main>
  );
}
