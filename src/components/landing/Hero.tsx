import { COPY, freeSearchLabel } from "@/lib/copy";
import type { FundEstimateView } from "@/data/types";
import { FundPicker } from "@/components/illustrate/FundPicker";
import { RequestFundForm } from "@/components/RequestFundForm";

export function Hero({
  funds,
  selected,
  onSelect,
  remaining,
  unlimited,
  onNotice,
}: {
  funds: FundEstimateView[];
  selected: FundEstimateView | null;
  onSelect: (fund: FundEstimateView) => void;
  remaining: number;
  unlimited: boolean;
  onNotice?: (message: string) => void;
}) {
  return (
    <section className="mb-8 max-w-3xl pt-6 sm:pt-10">
      <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-muted">
        Aftertax
      </p>
      <div className="mt-6">
        <FundPicker
          funds={funds}
          selected={selected}
          onSelect={onSelect}
          autoFocus
          reportSearchMiss
          onNotice={onNotice}
        />
      </div>
      {onNotice ? (
        <RequestFundForm onNotice={onNotice} className="mt-3" />
      ) : null}
      <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
        <p className="font-mono text-xs text-faint" aria-live="polite">
          {unlimited ? "Unlimited searches" : freeSearchLabel(remaining)}
        </p>
      </div>
      <p className="mt-4 text-xs text-faint">{COPY.trust}</p>
    </section>
  );
}
