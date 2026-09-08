import Link from "next/link";
import { COPY, freeSearchLabel } from "@/lib/copy";
import type { FundEstimateView } from "@/data/types";
import { FundPicker } from "@/components/illustrate/FundPicker";

export function Hero({
  funds,
  selected,
  onSelect,
  remaining,
  unlimited,
}: {
  funds: FundEstimateView[];
  selected: FundEstimateView | null;
  onSelect: (fund: FundEstimateView) => void;
  remaining: number;
  unlimited: boolean;
}) {
  return (
    <section className="mb-8 max-w-3xl pt-6 sm:pt-10">
      <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-muted">
        Aftertax
      </p>
      <h1 className="mt-2 font-serif text-3xl tracking-tight text-ink sm:text-[2.5rem] sm:leading-[1.15]">
        {COPY.hero}
      </h1>
      <p className="mt-3 text-[16px] leading-relaxed text-muted">{COPY.sub}</p>
      <div className="mt-6">
        <FundPicker
          funds={funds}
          selected={selected}
          onSelect={onSelect}
          autoFocus
        />
      </div>
      <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2">
          <Link
            href={
              selected
                ? `/compare?left=${encodeURIComponent(selected.ticker)}`
                : "/compare"
            }
            className="inline-flex h-10 items-center rounded-md border border-line px-4 text-sm text-ink hover:border-line-strong"
          >
            {COPY.compareCta}
          </Link>
          <Link
            href="/portfolio"
            className="inline-flex h-10 items-center rounded-md border border-line px-4 text-sm text-ink hover:border-line-strong"
          >
            {COPY.importCta}
          </Link>
        </div>
        <p className="font-mono text-xs text-faint" aria-live="polite">
          {unlimited ? "Unlimited searches" : freeSearchLabel(remaining)}
        </p>
      </div>
      <p className="mt-4 text-xs text-faint">{COPY.trust}</p>
    </section>
  );
}
