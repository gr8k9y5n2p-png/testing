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
  const deltaPanel =
    impact.polarity === "less"
      ? "bg-tax-less-soft"
      : impact.polarity === "more"
        ? "bg-tax-more-soft"
        : "bg-paper";

  return (
    <section
      aria-label="Portfolio tax summary"
      className="flex flex-col rounded-2xl border border-line bg-surface p-3 shadow-[0_8px_24px_rgba(26,29,26,0.06)] sm:p-4"
    >
      <header className="mb-3 flex flex-wrap items-end justify-between gap-2">
        <h2 className="font-serif text-lg tracking-tight text-ink">Total tax impact</h2>
        <p className="text-[10px] text-muted">Current vs Proposed · Δ</p>
      </header>

      <div className="grid gap-3 md:grid-cols-3">
        <div className="rounded-xl border border-line bg-surface px-3 py-2">
          <p className="text-[11px] font-semibold uppercase tracking-[0.12em] text-ink">
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
        <div className="rounded-xl border border-line bg-surface px-3 py-2">
          <p className="text-[11px] font-semibold uppercase tracking-[0.12em] text-ink">
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
        <div className={`rounded-xl border border-line px-3 py-2 ${deltaPanel}`}>
          <p className="text-[11px] font-semibold uppercase tracking-[0.12em] text-ink">
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
      </div>
    </section>
  );
}
