import type { HighlightSets } from "@/data/types";
import { OUTLIER_THRESHOLD_PP } from "@/data/queries";
import { HighlightCard } from "@/components/HighlightCard";

export function HighlightsSection({ highlights }: { highlights: HighlightSets }) {
  return (
    <section aria-labelledby="highlights-heading" className="mb-10">
      <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2
            id="highlights-heading"
            className="font-serif text-xl tracking-tight text-navy"
          >
            Highlights
          </h2>
          <p className="mt-1 text-sm text-muted">
            Snapshot of the sample universe: newest filings, largest estimated
            payouts, and peers that sit well away from their category average.
          </p>
        </div>
        <p className="text-xs text-faint">
          Outlier threshold: ±{OUTLIER_THRESHOLD_PP.toFixed(2)} pp vs category
          average (% of NAV)
        </p>
      </div>
      <div className="grid gap-4 lg:grid-cols-3">
        <HighlightCard
          title="Most recent"
          metricLabel="Published date"
          description="Newest manager estimate publication dates."
          funds={highlights.mostRecent}
          variant="recent"
        />
        <HighlightCard
          title="Largest"
          metricLabel="% of NAV"
          description="Highest estimated taxable distribution as a percent of NAV."
          funds={highlights.largest}
          variant="largest"
        />
        <HighlightCard
          title="vs category average"
          metricLabel="Δ pp"
          description={`Well above or below the same-category mean by at least ${OUTLIER_THRESHOLD_PP} pp.`}
          funds={[...highlights.aboveCategory, ...highlights.belowCategory]}
          variant="outliers"
          above={highlights.aboveCategory}
          below={highlights.belowCategory}
        />
      </div>
    </section>
  );
}
