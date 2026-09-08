import type { Metadata } from "next";
import { FundTaxDeltaCompare } from "@/components/illustrate/FundTaxDeltaCompare";
import { TaxDeltaCompareCard } from "@/components/illustrate/TaxDeltaCompareCard";
import { YoYTaxChart } from "@/components/illustrate/YoYTaxChart";
import { mockCompareMixedUpcomingResponse } from "@/lib/illustrate/compare-fixture";
import { toTaxDeltaCardModel } from "@/lib/illustrate/compare-map";
import { COPY } from "@/lib/copy";

export const metadata: Metadata = {
  title: "Aftertax — fund-to-fund tax-delta compare",
  description:
    "Year-over-year tax impact delta for two funds. Mount FundTaxDeltaCompare in the illustrate flow.",
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
        Reusable card for Website Engineering. Drop{" "}
        <code className="font-mono text-[13px] text-ink">
          FundTaxDeltaCompare
        </code>{" "}
        into the illustrate flow with left/right selectors. This page posts{" "}
        <code className="font-mono text-[13px] text-ink">
          POST /illustrate/compare
        </code>{" "}
        and falls back to the sketch fixture when the Data API is unreachable.
      </p>

      <div className="mt-8 flex flex-wrap items-start gap-8">
        <FundTaxDeltaCompare
          left={DEMO_LEFT}
          right={DEMO_RIGHT}
          holdingDollars={10_000}
        />
        <div>
          <p className="mb-3 text-[11px] font-semibold uppercase tracking-[0.14em] text-faint">
            Mixed upcoming (B not announced)
          </p>
          <TaxDeltaCompareCard
            model={toTaxDeltaCardModel(
              mockCompareMixedUpcomingResponse({
                holding_dollars: 10_000,
                left: DEMO_LEFT,
                right: DEMO_RIGHT,
                periods: [
                  { year: 2021 },
                  { year: 2022 },
                  { year: 2023 },
                  { year: 2024 },
                  { year: 2025 },
                ],
              }),
            )}
          />
        </div>
      </div>

      <div className="mt-10 max-w-xl">
        <p className="mb-3 text-[11px] font-semibold uppercase tracking-[0.14em] text-faint">
          YoYTaxChart primitive
        </p>
        <YoYTaxChart
          headingId="yoy-tax-chart-demo"
          title="Tax by calendar year"
          line
          bars={[
            { year: 2021, value: 210 },
            { year: 2022, value: 164 },
            { year: 2023, value: 188 },
            { year: 2024, value: null },
            { year: 2025, value: 142 },
          ]}
        />
      </div>

      <pre className="mt-10 overflow-auto rounded-lg border border-line bg-surface p-4 text-[12px] leading-relaxed text-muted">
        {`import {
  FundTaxDeltaCompare,
  YoYTaxChart,
} from "@/components/illustrate";

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
/>

<YoYTaxChart
  bars={[{ year: 2023, value: 188 }, { year: 2024, value: null }, { year: 2025, value: 142 }]}
  line
/>`}
      </pre>

      <p className="mt-6 text-xs text-faint">{COPY.trust}</p>
    </main>
  );
}
