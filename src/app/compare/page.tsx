import type { Metadata } from "next";
import { FundTaxDeltaCompare } from "@/components/illustrate/FundTaxDeltaCompare";
import { TaxDragByYearDemo } from "@/components/illustrate/TaxDragByYearDemo";
import { COPY } from "@/lib/copy";

export const metadata: Metadata = {
  title: "Aftertax — fund-to-fund tax-delta compare",
  description:
    "Year-over-year tax impact delta for two funds, plus the reusable TaxDragByYearChart primitive.",
  robots: { index: false, follow: false },
};

const DEMO_LEFT = {
  label: "Vanguard Total Stock",
  selectors: {
    fund_family: "Vanguard",
    fund_identifier: "VTSAX",
    ticker: "VTSAX",
  },
};

const DEMO_RIGHT = {
  label: "Active Growth Fund",
  selectors: {
    fund_family: "American Funds",
    fund_identifier: "AGTHX",
    ticker: "AGTHX",
  },
};

const DEMO_UNANNOUNCED = {
  label: "Peer without estimate",
  selectors: {
    fund_family: "Demo",
    fund_identifier: "UNANN",
    ticker: "UNANN",
    publication_stage: "unannounced",
  },
};

export default function CompareDemoPage() {
  return (
    <main className="mx-auto w-full max-w-7xl px-4 pb-16 pt-8 sm:px-6 lg:px-8">
      <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-muted">
        Illustrate module
      </p>
      <h1 className="mt-1 font-serif text-3xl tracking-tight text-ink">
        Fund-to-fund tax-delta compare
      </h1>
      <p className="mt-2 max-w-2xl text-sm text-muted">
        Reusable cards for Website Engineering. Historical YoY bars stay the
        shared story when only one fund has announced. This page posts{" "}
        <code className="font-mono text-[13px] text-ink">
          POST /illustrate/compare
        </code>{" "}
        (`fund_vs_fund` and `yoy`) and falls back to the sketch fixture when
        the Data API is unreachable.
      </p>

      <div className="mt-8 flex flex-wrap justify-center gap-8 lg:justify-start">
        <FundTaxDeltaCompare
          left={DEMO_LEFT}
          right={DEMO_RIGHT}
          holdingDollars={10_000}
        />
      </div>

      <h2 className="mt-14 font-serif text-2xl tracking-tight text-ink">
        Mixed announce
      </h2>
      <p className="mt-2 max-w-2xl text-sm text-muted">
        Only Fund A has an upcoming estimate. The card stays up: chip + value on
        that side, “Not announced” / — on the peer. YoY bars are unchanged.
      </p>
      <div className="mt-6 flex flex-wrap justify-center gap-8 lg:justify-start">
        <FundTaxDeltaCompare
          left={DEMO_LEFT}
          right={DEMO_UNANNOUNCED}
          holdingDollars={10_000}
        />
      </div>

      <h2
        id="tax-drag-by-year"
        className="mt-14 font-serif text-2xl tracking-tight text-ink"
      >
        Tax drag by year
      </h2>
      <p className="mt-2 max-w-2xl text-sm text-muted">
        Calendar-year bars for Dollar Illustration. 2023 is a gap (empty tick,
        no invented data). Optional line is observed YoY tax. Upcoming chip
        renders when the compare summary has an announced vintage.
      </p>
      <div className="mt-6 flex flex-wrap justify-center gap-8 lg:justify-start">
        <TaxDragByYearDemo
          selectors={{
            fund_family: "American Funds",
            fund_identifier: "AMCPX",
            ticker: "AMCPX",
            fund_name: "AMCAP Fund",
          }}
          holdingDollars={10_000}
          metric="tax_dollars"
          showLine
        />
        <TaxDragByYearDemo
          title="Tax drag by year"
          selectors={{
            fund_family: "American Funds",
            fund_identifier: "AMCPX",
            ticker: "AMCPX",
            fund_name: "AMCAP Fund",
          }}
          holdingDollars={10_000}
          metric="effective_tax"
          showLine
        />
      </div>

      <pre className="mt-10 overflow-auto rounded-lg border border-line bg-surface p-4 text-[12px] leading-relaxed text-muted">
        {`import { TaxDragByYearChart } from "@/components/illustrate";

// Dollar Illustration — historical tax $ (or pass metric="effective_tax")
<TaxDragByYearChart
  periods={[
    { year: 2021, value: 120 },
    { year: 2022, value: 95 },
    { year: 2023, value: null }, // gap — empty tick, do not invent
    { year: 2024, value: 110 },
    { year: 2025, value: 85 },
  ]}
  metric="tax_dollars"
  showLine
  upcomingSummary={{ dollars: 85, announced: true, publicationStage: "preliminary_estimate" }}
/>

import { FundTaxDeltaCompare } from "@/components/illustrate";

<FundTaxDeltaCompare
  left={{
    label: "Vanguard Total Stock",
    selectors: { ticker: "VTSAX", fund_identifier: "VTSAX" },
  }}
  right={{
    label: "Active Growth Fund",
    selectors: { ticker: "AGTHX", fund_identifier: "AGTHX" },
  }}
  holdingDollars={10000}
  taxRates={{ state: 0.05 }}
/>`}
      </pre>

      <p className="mt-6 text-xs text-faint">{COPY.trust}</p>
    </main>
  );
}
