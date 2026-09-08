import {
  TAX_DRAG_CARD_DETAIL,
  TAX_IMPACT_DELTA_DETAIL,
} from "@/lib/illustrate/portfolio-compare-copy";
import {
  compactBookLabel,
  formatMoreLessTax,
  formatTaxDragPct,
  type TaxPolarity,
} from "@/lib/illustrate/portfolio-compare-map";
import type { PortfolioCompareResponse } from "@/lib/illustrate/portfolio-compare-types";

const POLARITY_TEXT: Record<TaxPolarity, string> = {
  more: "text-tax-more",
  less: "text-tax-less",
  even: "text-muted",
};

export function SummaryStrip({
  result,
  bookDollars,
}: {
  result: PortfolioCompareResponse;
  bookDollars: number;
}) {
  const currentDrag = result.current.totals.effective_tax_on_holding;
  const proposedDrag = result.proposed.totals.effective_tax_on_holding;
  const impact = formatMoreLessTax(result.deltas.estimated_tax);
  const sample =
    result.source === "mock" ||
    result.notes.some((note) => /mock|demo|illustrative/i.test(note));
  const demo = sample ? " · demo" : "";

  return (
    <section
      aria-label="Portfolio tax summary"
      className="grid overflow-hidden rounded-2xl border border-line bg-surface shadow-[0_8px_24px_rgba(26,29,26,0.06)] md:grid-cols-3"
    >
      <div className="border-line px-5 py-4 md:border-r">
        <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-faint">
          Current tax drag
        </p>
        <p className="mt-1 font-serif text-[28px] leading-tight tracking-tight text-ink">
          {formatTaxDragPct(currentDrag)}
        </p>
        <p className="mt-1 text-[11px] text-muted">
          {TAX_DRAG_CARD_DETAIL}
          {demo}
        </p>
      </div>
      <div className="border-line px-5 py-4 md:border-r">
        <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-faint">
          Proposed tax drag
        </p>
        <p className="mt-1 font-serif text-[28px] leading-tight tracking-tight text-ink">
          {formatTaxDragPct(proposedDrag)}
        </p>
        <p className="mt-1 text-[11px] text-muted">
          {TAX_DRAG_CARD_DETAIL}
          {demo}
        </p>
      </div>
      <div
        className={`px-5 py-4 ${
          impact.polarity === "less"
            ? "bg-tax-less-soft"
            : impact.polarity === "more"
              ? "bg-tax-more-soft"
              : "bg-paper"
        }`}
      >
        <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-faint">
          Tax impact Δ
        </p>
        <p
          className={`mt-1 font-serif text-[28px] leading-tight tracking-tight ${POLARITY_TEXT[impact.polarity]}`}
        >
          {impact.headline}
        </p>
        <p className="mt-1 text-[11px] text-muted">
          {TAX_IMPACT_DELTA_DETAIL} · on {compactBookLabel(bookDollars)}
          {demo}
        </p>
      </div>
    </section>
  );
}

