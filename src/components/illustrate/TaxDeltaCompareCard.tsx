import { TaxDragByYearChart } from "@/components/illustrate/TaxDragByYearChart";
import {
  chartScalePct,
  type TaxDeltaBar,
  type TaxDeltaCardModel,
  type TaxPolarity,
} from "@/lib/illustrate/compare-map";
import { TAX_DRAG_NA_LABEL } from "@/lib/illustrate/tax-drag-chart";

const POLARITY_TEXT: Record<TaxPolarity, string> = {
  more: "text-tax-more",
  less: "text-tax-less",
  even: "text-muted",
};

function formatBarPct(value: number): string {
  const abs = Math.abs(value).toFixed(1);
  if (value > 0.05) return `+${abs}%`;
  if (value < -0.05) return `−${abs}%`;
  return `${(0).toFixed(1)}%`;
}

function barAriaLabel(bar: TaxDeltaBar): string {
  if (bar.missing || bar.displayPct == null) {
    return `${bar.year}: ${TAX_DRAG_NA_LABEL}`;
  }
  if (bar.polarity === "even") return `${bar.year}: about even tax drag`;
  const side = bar.polarity === "more" ? "more tax" : "less tax";
  return `${bar.year}: ${formatBarPct(bar.displayPct)} ${side} for Fund A`;
}

export function TaxDeltaCompareCard({
  model,
  className = "",
}: {
  model: TaxDeltaCardModel;
  className?: string;
}) {
  const scale = chartScalePct(model.bars);
  const ticks = [-scale, -scale / 2, 0, scale / 2, scale];

  return (
    <article
      className={`flex min-h-[420px] w-full max-w-[420px] flex-col rounded-2xl border border-line bg-surface px-5 py-5 shadow-[0_8px_24px_rgba(26,29,26,0.08)] ${className}`}
    >
      <header>
        <p className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-faint">
          <span
            aria-hidden
            className="inline-block size-1.5 rounded-full bg-tax-less"
          />
          Aftertax · {model.sample ? "Sample" : "Live"}
        </p>

        <div className="mt-3 grid grid-cols-[1fr_auto_1fr] items-start gap-2">
          <FundHeading side="Fund A" name={model.leftLabel} align="left" />
          <p className="pt-5 text-[11px] uppercase tracking-[0.14em] text-faint">
            vs
          </p>
          <FundHeading side="Fund B" name={model.rightLabel} align="right" />
        </div>
      </header>

      <TaxDragByYearChart
        series={model.taxSeries}
        metric="effective_tax"
        title="Tax drag by year"
        showBarLabels={model.taxSeries.length <= 2}
        layout="flush"
        className="mt-4"
        sample={model.sample}
        emptyLabel="No overlapping tax-drag years"
      />

      <div className="mt-4 flex flex-wrap items-end justify-between gap-2">
          <p className="text-sm text-muted">Tax impact delta (YoY)</p>
          <ul className="flex items-center gap-3 text-[11px] text-muted">
            <li className="flex items-center gap-1.5">
              <span className="size-2.5 rounded-[2px] bg-tax-more-soft ring-1 ring-tax-more/20" />
              Higher tax drag
            </li>
            <li className="flex items-center gap-1.5">
              <span className="size-2.5 rounded-[2px] bg-tax-less-soft ring-1 ring-tax-less/25" />
              Lower tax drag
            </li>
          </ul>
        </div>

      <div
        className="mt-4 flex-1"
        role="img"
        aria-label={
          model.bars.length === 0
            ? `No overlapping years for ${model.leftLabel} versus ${model.rightLabel}. Upcoming coverage is still shown.`
            : `Year-over-year tax impact delta for ${model.leftLabel} versus ${model.rightLabel}. Left is more tax, right is less tax.`
        }
      >
        <div className="mb-1 grid grid-cols-[2.75rem_1fr] items-end text-[10px] font-medium text-faint">
          <span />
          <div className="relative h-4">
            <span className="absolute left-0 font-semibold text-ink">more tax</span>
            <span className="absolute left-1/2 -translate-x-1/2">0</span>
            <span className="absolute right-0 font-semibold text-ink">less tax</span>
          </div>
        </div>

        <div className="grid grid-cols-[2.75rem_1fr] items-center text-[10px] text-faint">
          <span />
          <div className="relative h-4">
            {ticks.map((tick) => (
              <span
                key={tick}
                className="absolute -translate-x-1/2 tabular-nums"
                style={{ left: `${((tick + scale) / (scale * 2)) * 100}%` }}
              >
                {tick === 0 ? "" : `${tick > 0 ? "+" : ""}${tick}%`}
              </span>
            ))}
          </div>
        </div>

        {model.bars.length === 0 ? (
          <p className="mt-6 px-1 text-sm text-muted">
            No overlapping years — historical bars stay empty. Upcoming below is
            per fund, so a missing announcement does not hide this card.
          </p>
        ) : (
          <ul className="mt-1 space-y-1.5">
            {model.bars.map((bar) => (
              <li key={bar.year} className="grid grid-cols-[2.75rem_1fr] items-center gap-1">
                <span className="font-mono text-[11px] text-muted">{bar.year}</span>
                <BarTrack bar={bar} scale={scale} ticks={ticks} />
              </li>
            ))}
          </ul>
        )}
        <span className="sr-only">
          {model.bars.map((bar) => barAriaLabel(bar)).join(". ")}
        </span>
      </div>

      <dl className="mt-5 grid grid-cols-2 overflow-hidden rounded-lg border border-line bg-tax-footer">
        {model.metrics.map((metric) => (
          <div
            key={metric.key}
            className="border-line px-3 py-3 [&:nth-child(-n+2)]:border-b [&:nth-child(odd)]:border-r"
          >
            <dt className="text-[10px] font-semibold uppercase tracking-[0.12em] text-faint">
              {metric.label}
            </dt>
            {metric.key === "upcoming_tax" ? (
              <>
                <dd
                  className={`mt-1 font-serif text-[17px] leading-tight tracking-tight ${POLARITY_TEXT[metric.polarity]}`}
                >
                  {metric.headline}
                </dd>
                <dd className="mt-1 font-mono text-[11px] leading-snug text-ink">
                  A {model.upcoming.left.display}
                  <span className="text-faint"> · </span>
                  B {model.upcoming.right.display}
                </dd>
                <dd className="mt-1 text-[10px] leading-snug text-faint">
                  {model.upcoming.left.announced
                    ? `A ${model.upcoming.left.statusLabel}`
                    : "A Not announced"}
                  <span> · </span>
                  {model.upcoming.right.announced
                    ? `B ${model.upcoming.right.statusLabel}`
                    : "B Not announced"}
                </dd>
              </>
            ) : (
              <>
                <dd className={`mt-1 font-serif text-[17px] leading-tight tracking-tight ${POLARITY_TEXT[metric.polarity]}`}>
                  {metric.headline}
                </dd>
                <dd className="mt-1 text-[10px] leading-snug text-faint">{metric.detail}</dd>
              </>
            )}
          </div>
        ))}
      </dl>

      <p className="mt-4 text-center text-[10px] leading-relaxed text-faint">
        Demo data · illustrative only · tax cost to holder · red = more tax ·
        green = less
      </p>
    </article>
  );
}

function FundHeading({
  side,
  name,
  align,
}: {
  side: string;
  name: string;
  align: "left" | "right";
}) {
  return (
    <div className={align === "right" ? "text-right" : "text-left"}>
      <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-faint">
        {side}
      </p>
      <p className="mt-0.5 font-serif text-lg leading-tight tracking-tight text-ink">
        {name}
      </p>
    </div>
  );
}

function BarTrack({
  bar,
  scale,
  ticks,
}: {
  bar: TaxDeltaBar;
  scale: number;
  ticks: number[];
}) {
  if (bar.missing || bar.displayPct == null) {
    return (
      <div className="relative h-7">
        {ticks.map((tick) => (
          <span
            key={tick}
            aria-hidden
            className={`absolute top-0 h-full w-px ${
              tick === 0 ? "bg-ink/35" : "bg-line"
            }`}
            style={{ left: `${((tick + scale) / (scale * 2)) * 100}%` }}
          />
        ))}
        <span className="absolute left-1/2 top-1.5 -translate-x-1/2 rounded-full bg-paper px-1.5 py-0.5 font-mono text-[10px] text-faint">
          {TAX_DRAG_NA_LABEL}
        </span>
      </div>
    );
  }

  const widthPct = Math.min(50, (Math.abs(bar.displayPct) / (scale * 2)) * 100);
  const more = bar.polarity === "more" || bar.displayPct < 0;
  const showBar = bar.polarity !== "even";

  return (
    <div className="relative h-7">
      {ticks.map((tick) => (
        <span
          key={tick}
          aria-hidden
          className={`absolute top-0 h-full w-px ${
            tick === 0 ? "bg-ink/35" : "bg-line"
          }`}
          style={{ left: `${((tick + scale) / (scale * 2)) * 100}%` }}
        />
      ))}
      {showBar ? (
        <div
          className={`absolute top-1.5 flex h-4 items-center ${
            more ? "flex-row-reverse" : "flex-row"
          }`}
          style={{
            width: `${widthPct}%`,
            left: more ? `${50 - widthPct}%` : "50%",
          }}
        >
          <span
            className={`h-full flex-1 rounded-sm ${
              more ? "bg-tax-more-soft" : "bg-tax-less-soft"
            }`}
          />
          <span
            className={`relative z-10 -mx-0.5 shrink-0 rounded-full px-1.5 py-0.5 font-mono text-[10px] font-medium ${
              more
                ? "bg-tax-more-soft text-tax-more"
                : "bg-tax-less-soft text-tax-less"
            }`}
          >
            {formatBarPct(bar.displayPct)}
          </span>
        </div>
      ) : (
        <span className="absolute left-1/2 top-1.5 -translate-x-1/2 rounded-full bg-paper px-1.5 py-0.5 font-mono text-[10px] text-muted">
          0.0%
        </span>
      )}
    </div>
  );
}
