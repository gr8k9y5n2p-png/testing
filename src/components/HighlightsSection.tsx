import type { FundEstimateView, HighlightSets } from "@/data/types";
import { OUTLIER_THRESHOLD_PP } from "@/data/queries";
import { HighlightCard } from "@/components/HighlightCard";

export function HighlightsSection({
  highlights,
  onSelect,
}: {
  highlights: HighlightSets;
  onSelect?: (fund: FundEstimateView) => void;
}) {
  return (
    <section aria-labelledby="highlights-heading" className="mb-10">
      <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2
            id="highlights-heading"
            className="font-serif text-xl tracking-tight text-ink"
          >
            Highlights
          </h2>
          <p className="mt-1 text-sm text-muted">
            Snapshot of unpaid announced estimates: largest payouts, newest
            filings, and same-year peers that sit well away from their
            category average. Paid history is not mixed in.
          </p>
        </div>
        <p className="text-xs text-faint">
          Outlier threshold: ±{OUTLIER_THRESHOLD_PP.toFixed(2)} pp vs category
          average (% of NAV)
        </p>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <HighlightCard
          title="Largest"
          metricLabel="% of NAV"
          description="Highest estimated taxable distribution as a percent of NAV."
          funds={highlights.largest}
          variant="largest"
          onSelect={onSelect}
        />
        <HighlightCard
          title="Most recent"
          metricLabel="Announced"
          description="Newest announced (as_of) upcoming estimates — record and ex-div on each row."
          funds={highlights.mostRecent}
          variant="recent"
          onSelect={onSelect}
        />
      </div>
      <div className="mt-4">
        <HighlightCard
          title="Versus category"
          metricLabel="Δ pp"
          description={`Well above or below the same-category, same-year mean by at least ${OUTLIER_THRESHOLD_PP} pp.`}
          funds={[...highlights.aboveCategory, ...highlights.belowCategory]}
          variant="outliers"
          above={highlights.aboveCategory}
          below={highlights.belowCategory}
          wide
          onSelect={onSelect}
        />
      </div>
    </section>
  );
}
