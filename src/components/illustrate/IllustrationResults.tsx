import type { ReactNode } from "react";
import type { FundEstimate } from "@/data/types";
import { isUpcomingFund, publicationStageLabel } from "@/data/distribution-bucket";
import { hideUpcomingAmounts } from "@/data/hydrate-funds";
import type { IllustrationComponent, IllustrateResponse } from "@/lib/illustrate/types";
import {
  illustrationComponentBucket,
  splitIllustrationComponents,
  upcomingEstimateTypeRows,
  upcomingIllustrationTotals,
} from "@/lib/illustrate/illustration-upcoming";
import { DistributionDateStrip } from "@/components/DistributionDateStrip";
import { Disclaimer } from "@/components/Disclaimer";
import {
  UPCOMING_UNAVAILABLE_DETAIL,
  UPCOMING_UNAVAILABLE_HEADLINE,
} from "@/lib/copy";
import { formatRatePct, formatUsd, formatUsdRange } from "@/lib/format";
import {
  formatSoftPct,
  historicalPctOfNav,
  parseFiniteNumber,
  parsePositiveNav,
  pctOfNavForFund,
  upcomingPctOfNav,
  usesDistributionDayNav,
} from "@/lib/illustrate/nav-math";
import { userFacingNotes } from "@/lib/illustrate/user-facing-notes";

const ESTIMATE_LABELS: Record<string, string> = {
  ordinary_income: "Ordinary income",
  long_term_capital_gains: "Long-term capital gains",
  short_term_capital_gains: "Short-term capital gains",
  qualified_dividend: "Qualified dividends",
  total_capital_gains: "Total capital gains",
  special_dividend: "Special dividend",
  return_of_capital: "Return of capital",
  total: "Total (treated as ordinary)",
};

export function IllustrationResults({
  result,
  fund,
}: {
  result: IllustrateResponse;
  fund?: FundEstimate | null;
  /** Kept for callers; Upcoming % of NAV uses $/share ÷ weekly NAV. */
  holdingDollars?: number | null;
}) {
  const { components } = result;
  const warnings = userFacingNotes(result.warnings);
  const { upcoming: upcomingAll } = splitIllustrationComponents(
    components,
    fund,
  );
  const upcomingComponents = upcomingEstimateTypeRows(upcomingAll, fund);
  const upcomingTotals = upcomingIllustrationTotals(upcomingComponents);
  const catalogUpcoming =
    fund != null && isUpcomingFund(fund) && !hideUpcomingAmounts(fund);

  return (
    <div className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-2">
        <StatCard
          label="Estimated distribution"
          value={
            upcomingTotals != null
              ? formatUsdRange(
                  upcomingTotals.distribution_dollars,
                  upcomingTotals.distribution_dollars_min,
                  upcomingTotals.distribution_dollars_max,
                )
              : catalogUpcoming && fund
                ? `${formatUsd(fund.estimatedDistributionAmount, 4)} / sh`
                : UPCOMING_UNAVAILABLE_HEADLINE
          }
        />
        <StatCard
          label="Estimated tax"
          value={
            upcomingTotals != null
              ? formatUsdRange(
                  upcomingTotals.estimated_tax_dollars,
                  upcomingTotals.estimated_tax_dollars_min,
                  upcomingTotals.estimated_tax_dollars_max,
                )
              : UPCOMING_UNAVAILABLE_HEADLINE
          }
          emphasize
        />
      </div>

      <ComponentTable
        heading="Upcoming / Announced"
        kicker="unpaid announced · not paid history"
        wellClassName="bg-surface"
        components={upcomingComponents}
        fund={fund}
        empty={
          catalogUpcoming && fund ? (
            <div className="flex flex-wrap items-start justify-between gap-3 px-3 py-3">
              <div>
                <p className="font-mono text-sm font-medium text-ink">{fund.ticker}</p>
                <p className="mt-0.5 text-[11px] text-faint">{fund.fundName}</p>
                <DistributionDateStrip fund={fund} showPayable showStage className="mt-1.5" />
              </div>
              <p className="text-right font-mono text-sm text-ink">
                {formatUsd(fund.estimatedDistributionAmount, 4)} / sh
                <span className="mt-0.5 block text-[11px] text-faint">
                  {formatSoftPct(pctOfNavForFund(fund))} of NAV
                </span>
              </p>
            </div>
          ) : (
            <div className="px-3 py-5">
              <p className="font-serif text-base tracking-tight text-ink">
                {UPCOMING_UNAVAILABLE_HEADLINE}
              </p>
              <p className="mt-1 text-sm text-muted">{UPCOMING_UNAVAILABLE_DETAIL}</p>
            </div>
          )
        }
      />

      {warnings.length > 0 ? (
        <ul className="space-y-1 text-xs text-muted">
          {warnings.map((warning) => (
            <li key={warning}>{warning}</li>
          ))}
        </ul>
      ) : null}

      <Disclaimer />
    </div>
  );
}

function componentPctOfNav(
  component: IllustrationComponent,
  fund?: FundEstimate | null,
): string {
  const unit = (component.amount_unit ?? "").trim().toLowerCase();
  const perShare =
    unit === "percent_of_nav" ? null : parseFiniteNumber(component.amount);
  const weekly = parsePositiveNav(fund?.nav);

  if (usesDistributionDayNav(component)) {
    return formatSoftPct(
      historicalPctOfNav(perShare, component.nav_on_distribution_day),
    );
  }

  return formatSoftPct(upcomingPctOfNav(perShare, weekly));
}

function ComponentTable({
  heading,
  kicker,
  wellClassName,
  components,
  fund,
  empty,
}: {
  heading: string;
  kicker: string;
  wellClassName: string;
  components: IllustrationComponent[];
  fund?: FundEstimate | null;
  empty?: ReactNode;
}) {
  return (
    <div className={`overflow-hidden rounded-xl border border-line ${wellClassName}`}>
      <div className="flex flex-wrap items-baseline justify-between gap-2 border-b border-line px-3 py-2">
        <p className="text-[11px] font-semibold uppercase tracking-[0.1em] text-ink">
          {heading}
        </p>
        <p className="text-[10px] text-muted">{kicker}</p>
      </div>
      {components.length === 0 && empty ? (
        empty
      ) : (
      <table className="min-w-full text-sm">
        <thead className="bg-paper text-[11px] font-semibold uppercase tracking-[0.1em] text-faint">
          <tr>
            <th className="px-3 py-2 text-left">Component</th>
            <th className="px-3 py-2 text-right">Distribution</th>
            <th className="px-3 py-2 text-right">% of NAV</th>
            <th className="px-3 py-2 text-right">Effective rate</th>
            <th className="px-3 py-2 text-right">$ impact</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-line">
          {components.map((component) => (
            <tr key={component.distribution_id}>
              <td className="px-3 py-2">
                <span className="block text-ink">
                  {ESTIMATE_LABELS[component.estimate_type] ?? component.estimate_type}
                </span>
                <span className="font-mono text-[11px] text-faint">
                  {component.amount_unit}
                  {component.publication_stage
                    ? ` · ${publicationStageLabel(component.publication_stage)}`
                    : ""}
                </span>
                {component.as_of || component.ex_date ? (
                  <DistributionDateStrip
                    fund={{
                      asOfDate: component.as_of ?? "",
                      recordDate: component.record_date,
                      exDate: component.ex_date,
                      payableDate: component.payable_date,
                      publicationStage: component.publication_stage,
                      bucket: illustrationComponentBucket(component, fund),
                    }}
                    showPayable={Boolean(component.payable_date)}
                    className="mt-1"
                  />
                ) : null}
              </td>
              <td className="px-3 py-2 text-right font-mono">
                {formatUsdRange(
                  component.distribution_dollars,
                  component.distribution_dollars_min,
                  component.distribution_dollars_max,
                )}
              </td>
              <td className="px-3 py-2 text-right font-mono">
                {componentPctOfNav(component, fund)}
              </td>
              <td className="px-3 py-2 text-right font-mono text-muted">
                {formatOptionalRate(component.effective_rate)}
                <span className="block text-[11px] text-faint">
                  {Number.isFinite(component.federal_rate)
                    ? `fed ${formatRatePct(component.federal_rate)}`
                    : "—"}
                  {Number.isFinite(component.state_rate) && component.state_rate
                    ? ` + st ${formatRatePct(component.state_rate)}`
                    : ""}
                </span>
              </td>
              <td className="px-3 py-2 text-right font-mono">
                {formatUsdRange(
                  component.estimated_tax_dollars,
                  component.estimated_tax_dollars_min,
                  component.estimated_tax_dollars_max,
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      )}
    </div>
  );
}

function formatOptionalRate(value: number): string {
  return Number.isFinite(value) ? formatRatePct(value) : "—";
}

function StatCard({
  label,
  value,
  emphasize = false,
}: {
  label: string;
  value: string;
  emphasize?: boolean;
}) {
  return (
    <div
      className={`rounded-md border px-4 py-3 ${
        emphasize ? "border-accent/25 bg-accent-soft" : "border-line bg-paper"
      }`}
    >
      <p
        className={`text-[11px] font-semibold uppercase tracking-[0.12em] ${
          emphasize ? "text-accent" : "text-faint"
        }`}
      >
        {label}
      </p>
      <p
        className={`mt-1 font-serif text-2xl tracking-tight ${
          emphasize ? "text-accent" : "text-ink"
        }`}
      >
        {value}
      </p>
    </div>
  );
}
