import type { ReactNode } from "react";
import type { FundEstimate } from "@/data/types";
import { publicationStageLabel } from "@/data/distribution-bucket";
import { paidEventsForFund } from "@/data/hydrate-funds";
import type { IllustrationComponent, IllustrateResponse } from "@/lib/illustrate/types";
import {
  illustrationComponentBucket,
  splitIllustrationComponents,
  upcomingIllustrationTotals,
} from "@/lib/illustrate/illustration-upcoming";
import { DistributionDateStrip } from "@/components/DistributionDateStrip";
import { Disclaimer } from "@/components/Disclaimer";
import {
  PAID_HISTORY_EMPTY,
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
  holdingDollars,
}: {
  result: IllustrateResponse;
  fund?: FundEstimate | null;
  /** Holding $ so Upcoming can show % of NAV without inventing a rate. */
  holdingDollars?: number | null;
}) {
  const { components } = result;
  const warnings = userFacingNotes(result.warnings);
  const { upcoming: upcomingComponents } = splitIllustrationComponents(
    components,
    fund,
  );
  const upcomingTotals = upcomingIllustrationTotals(upcomingComponents);
  const hasUpcoming = upcomingTotals != null;
  // Paid history is GET /distributions only — never illustration component $.
  const paidEvents = fund ? paidEventsForFund(fund) : [];

  return (
    <div className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-2">
        <StatCard
          label="Estimated distribution"
          value={
            hasUpcoming
              ? formatUsdRange(
                  upcomingTotals.distribution_dollars,
                  upcomingTotals.distribution_dollars_min,
                  upcomingTotals.distribution_dollars_max,
                )
              : UPCOMING_UNAVAILABLE_HEADLINE
          }
        />
        <StatCard
          label="Estimated tax"
          value={
            hasUpcoming
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
        holdingDollars={holdingDollars}
        empty={
          <div className="px-3 py-5">
            <p className="font-serif text-base tracking-tight text-ink">
              {UPCOMING_UNAVAILABLE_HEADLINE}
            </p>
            <p className="mt-1 text-sm text-muted">{UPCOMING_UNAVAILABLE_DETAIL}</p>
          </div>
        }
      />
      <section className="rounded-xl border border-line bg-paper px-3 py-2">
        <div className="mb-2 flex flex-wrap items-baseline justify-between gap-2">
          <h3 className="text-[11px] font-semibold uppercase tracking-[0.12em] text-ink">
            Paid history
          </h3>
          <p className="text-[10px] text-muted">past · not upcoming</p>
        </div>
        {paidEvents.length === 0 ? (
          <p className="rounded-lg border border-dashed border-line px-4 py-6 text-sm text-muted">
            {PAID_HISTORY_EMPTY}
          </p>
        ) : (
          <ul className="divide-y divide-line overflow-hidden rounded-md border border-line bg-surface">
            {paidEvents.map((event) => (
              <li
                key={`${event.asOfDate}-${event.exDate ?? ""}-${event.distributionYear}`}
                className="flex flex-wrap items-start justify-between gap-3 px-3 py-2.5"
              >
                <div>
                  <p className="text-sm text-ink">
                    {event.distributionYear} ·{" "}
                    {publicationStageLabel(event.publicationStage) || "Paid"}
                  </p>
                  <DistributionDateStrip
                    fund={{ ...event, bucket: "paid" }}
                    compact
                    showPayable
                    className="mt-1"
                  />
                </div>
                <p className="text-right font-mono text-sm text-ink">
                  {formatUsd(event.estimatedDistributionAmount, 4)} / sh
                  <span className="mt-0.5 block text-[11px] text-faint">
                    {formatSoftPct(pctOfNavForFund(event))} of NAV
                  </span>
                </p>
              </li>
            ))}
          </ul>
        )}
      </section>

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
  holdingDollars?: number | null,
): string {
  const published = parseFiniteNumber(component.percent_of_nav);
  if (published != null) return formatSoftPct(published);

  const perShare = parseFiniteNumber(component.amount);
  if (usesDistributionDayNav(component)) {
    return formatSoftPct(
      historicalPctOfNav(perShare, component.nav_on_distribution_day),
    );
  }

  const weekly = parsePositiveNav(fund?.nav);
  const fromWeekly = upcomingPctOfNav(perShare, weekly);
  if (fromWeekly != null) return formatSoftPct(fromWeekly);

  if (
    component.amount_unit === "percent_of_nav" &&
    component.distribution_dollars != null &&
    holdingDollars != null &&
    holdingDollars > 0
  ) {
    return formatSoftPct((component.distribution_dollars / holdingDollars) * 100);
  }
  return "—";
}

function ComponentTable({
  heading,
  kicker,
  wellClassName,
  components,
  fund,
  empty,
  holdingDollars,
}: {
  heading: string;
  kicker: string;
  wellClassName: string;
  components: IllustrationComponent[];
  fund?: FundEstimate | null;
  empty?: ReactNode;
  holdingDollars?: number | null;
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
                {componentPctOfNav(component, fund, holdingDollars)}
              </td>
              <td className="px-3 py-2 text-right font-mono text-muted">
                {formatRatePct(component.effective_rate)}
                <span className="block text-[11px] text-faint">
                  fed {formatRatePct(component.federal_rate)}
                  {component.state_rate
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
