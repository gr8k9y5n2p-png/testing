import type { FundEstimateView } from "@/data/types";
import { DeltaBadge } from "@/components/DeltaBadge";
import { DistributionDateStrip } from "@/components/DistributionDateStrip";
import { CompareTickerLink } from "@/components/illustrate/CompareTickerLink";
import { UPCOMING_UNAVAILABLE_HEADLINE } from "@/lib/copy";
import { formatCompactDate, formatPct, formatUsd } from "@/lib/format";

type Variant = "recent" | "largest" | "outliers";

export function HighlightCard({
  title,
  metricLabel,
  description,
  funds = [],
  variant,
  above = [],
  below = [],
}: {
  title: string;
  metricLabel: string;
  description: string;
  funds?: FundEstimateView[];
  variant: Variant;
  above?: FundEstimateView[];
  below?: FundEstimateView[];
}) {
  return (
    <article className="flex min-h-[22rem] flex-col rounded-lg border border-line bg-surface shadow-[0_1px_2px_rgba(26,29,26,0.04)]">
      <header className="border-b border-line px-4 py-3.5">
        <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-faint">
          {metricLabel}
        </p>
        <h3 className="mt-1 font-serif text-lg text-ink">{title}</h3>
        <p className="mt-1 text-sm leading-snug text-muted">{description}</p>
      </header>
      {variant === "outliers" ? (
        <div className="flex flex-1 flex-col">
          <OutlierGroup
            label="Well above category"
            tone="above"
            funds={above}
          />
          <OutlierGroup
            label="Well below category"
            tone="below"
            funds={below}
          />
        </div>
      ) : funds.length === 0 ? (
        <p className="px-4 py-6 text-sm text-muted">
          {UPCOMING_UNAVAILABLE_HEADLINE}
        </p>
      ) : (
        <ul className="divide-y divide-line">
          {funds.map((fund) => (
            <li key={fund.id} className="px-4 py-3">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium text-ink">
                    <CompareTickerLink ticker={fund.ticker}>{fund.fundName}</CompareTickerLink>
                  </p>
                  <p className="mt-0.5 font-mono text-[11px] text-faint">
                    <CompareTickerLink ticker={fund.ticker} />
                    <span className="mx-1.5 text-line-strong">·</span>
                    {fund.family}
                  </p>
                </div>
                <p className="shrink-0 text-right font-mono text-sm text-ink">
                  {variant === "recent"
                    ? formatCompactDate(fund.asOfDate)
                    : formatPct(fund.estimatedDistributionPctNav)}
                </p>
              </div>
              <DistributionDateStrip
                fund={fund}
                compact
                showPayable={false}
                className="mt-1.5"
              />
              {variant === "largest" ? (
                <p className="mt-1 text-xs text-muted">
                  {formatUsd(fund.estimatedDistributionAmount, 4)} / share
                </p>
              ) : null}
            </li>
          ))}
        </ul>
      )}
    </article>
  );
}

function OutlierGroup({
  label,
  tone,
  funds,
}: {
  label: string;
  tone: "above" | "below";
  funds: FundEstimateView[];
}) {
  const bar =
    tone === "above"
      ? "border-l-[3px] border-l-above bg-above-soft/40"
      : "border-l-[3px] border-l-below bg-below-soft/50";

  return (
    <div className={`flex-1 ${tone === "below" ? "border-t border-line" : ""}`}>
      <p
        className={`px-4 py-2 text-[11px] font-semibold uppercase tracking-[0.12em] ${
          tone === "above" ? "text-above" : "text-below"
        }`}
      >
        {label}
      </p>
      {funds.length === 0 ? (
        <p className="px-4 pb-3 text-sm text-muted">None available.</p>
      ) : (
        <ul>
          {funds.slice(0, 3).map((fund) => (
            <li key={fund.id} className={`px-4 py-2.5 ${bar}`}>
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium text-ink">
                    <CompareTickerLink ticker={fund.ticker}>{fund.fundName}</CompareTickerLink>
                  </p>
                  <p className="mt-0.5 font-mono text-[11px] text-faint">
                    <CompareTickerLink ticker={fund.ticker} />
                    <span className="mx-1.5 text-line-strong">·</span>
                    {fund.category}
                  </p>
                </div>
                <DeltaBadge fund={fund} compact />
              </div>
              <DistributionDateStrip
                fund={fund}
                compact
                showPayable={false}
                className="mt-1.5"
              />
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
