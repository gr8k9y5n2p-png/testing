import type { ReactNode } from "react";
import type { FundEstimate } from "@/data/types";
import { distributionBucket, publicationStageLabel } from "@/data/distribution-bucket";
import type { IllustrationComponent, IllustrateResponse } from "@/lib/illustrate/types";
import { DistributionDateStrip } from "@/components/DistributionDateStrip";
import { Disclaimer } from "@/components/Disclaimer";
import {
  UPCOMING_UNAVAILABLE_DETAIL,
  UPCOMING_UNAVAILABLE_HEADLINE,
} from "@/lib/copy";
import { formatRatePct, formatUsd, formatUsdRange } from "@/lib/format";

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
}) {
  const { totals, components, warnings } = result;
  const upcomingComponents = components.filter(
    (component) => componentBucket(component) === "upcoming",
  );
  const paidComponents = components.filter(
    (component) => componentBucket(component) === "paid",
  );
  const hasUpcoming = upcomingComponents.length > 0;

  return (
    <div className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-2">
        <StatCard
          label="Estimated distribution"
          value={
            hasUpcoming
              ? formatUsdRange(
                  totals.distribution_dollars,
                  totals.distribution_dollars_min,
                  totals.distribution_dollars_max,
                )
              : UPCOMING_UNAVAILABLE_HEADLINE
          }
        />
        <StatCard
          label="Estimated tax"
          value={
            hasUpcoming
              ? formatUsdRange(
                  totals.estimated_tax_dollars,
                  totals.estimated_tax_dollars_min,
                  totals.estimated_tax_dollars_max,
                )
              : UPCOMING_UNAVAILABLE_HEADLINE
          }
          emphasize
        />
      </div>

      <ComponentTable
        heading="Upcoming / announced"
        kicker="unpaid announced · not paid history"
        wellClassName="bg-surface"
        components={upcomingComponents}
        empty={
          <div className="px-3 py-5">
            <p className="font-serif text-base tracking-tight text-ink">
              {UPCOMING_UNAVAILABLE_HEADLINE}
            </p>
            <p className="mt-1 text-sm text-muted">{UPCOMING_UNAVAILABLE_DETAIL}</p>
          </div>
        }
      />
      {paidComponents.length > 0 ? (
        <ComponentTable
          heading="Paid history"
          kicker="past · not upcoming"
          wellClassName="bg-paper"
          components={paidComponents}
        />
      ) : null}

      {fund && fund.paidHistory.length > 0 && paidComponents.length === 0 ? (
        <section className="rounded-xl border border-line bg-paper px-3 py-2">
          <div className="mb-2 flex flex-wrap items-baseline justify-between gap-2">
            <h3 className="text-[11px] font-semibold uppercase tracking-[0.12em] text-ink">
              Paid history
            </h3>
            <p className="text-[10px] text-muted">past · not upcoming</p>
          </div>
          <ul className="divide-y divide-line overflow-hidden rounded-md border border-line bg-surface">
            {fund.paidHistory.map((event) => (
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
                <p className="font-mono text-sm text-ink">
                  {formatUsd(event.estimatedDistributionAmount, 4)} / sh
                </p>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

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

function componentBucket(component: IllustrationComponent) {
  return distributionBucket({
    asOfDate: component.as_of,
    recordDate: component.record_date,
    exDate: component.ex_date,
    payableDate: component.payable_date,
    publicationStage: component.publication_stage,
  });
}

function ComponentTable({
  heading,
  kicker,
  wellClassName,
  components,
  empty,
}: {
  heading: string;
  kicker: string;
  wellClassName: string;
  components: IllustrationComponent[];
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
            <th className="px-3 py-2 text-right">Effective rate</th>
            <th className="px-3 py-2 text-right">Est. tax</th>
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
                      bucket: componentBucket(component),
                    }}
                    compact
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
