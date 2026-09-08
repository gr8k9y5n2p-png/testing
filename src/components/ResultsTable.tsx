"use client";

import { useState, type KeyboardEvent, type MouseEvent } from "react";
import type { FundEstimateView } from "@/data/types";
import { paidHistoryViews, splitFundsByBucket } from "@/data/queries";
import { publicationStageLabel } from "@/data/distribution-bucket";
import { DistributionDateStrip } from "@/components/DistributionDateStrip";
import { DeltaBadge } from "@/components/DeltaBadge";
import { useCoverage } from "@/components/coverage/CoverageProvider";
import {
  formatOptionalDate,
  formatPct,
  formatUsd,
  sortFunds,
  type SortDirection,
  type SortKey,
} from "@/lib/format";
import {
  PAID_HISTORY_EMPTY,
  UPCOMING_UNAVAILABLE_DETAIL,
  UPCOMING_UNAVAILABLE_HEADLINE,
} from "@/lib/copy";

function isNestedControl(target: EventTarget | null) {
  const element =
    target instanceof Element
      ? target
      : target instanceof Node
        ? target.parentElement
        : null;
  return Boolean(element?.closest("button, a, input, select, textarea, label"));
}

function toggleExpandedId(current: string | null, fundId: string) {
  return current === fundId ? null : fundId;
}

export function ResultsTable({
  funds,
  onIllustrate,
}: {
  funds: FundEstimateView[];
  onIllustrate?: (fund: FundEstimateView) => void;
}) {
  const [sortKey, setSortKey] = useState<SortKey>("fundName");
  const [sortDirection, setSortDirection] = useState<SortDirection>("asc");
  const coverage = useCoverage();
  const { upcoming } = splitFundsByBucket(funds);
  const paid = paidHistoryViews(funds);

  function toggleSort(key: SortKey) {
    if (key === sortKey) {
      setSortDirection((current) => (current === "asc" ? "desc" : "asc"));
      return;
    }
    setSortKey(key);
    setSortDirection(key === "fundName" || key === "family" || key === "category" ? "asc" : "desc");
  }

  const sourceByHistoryId = new Map<string, FundEstimateView>();
  for (const fund of funds) {
    sourceByHistoryId.set(fund.id, fund);
    if (fund.bucket === "paid") continue;
    for (const event of fund.paidHistory) {
      sourceByHistoryId.set(
        `${fund.id}:paid:${event.asOfDate}:${event.exDate ?? ""}`,
        fund,
      );
    }
  }

  function illustrate(row: FundEstimateView) {
    onIllustrate?.(sourceByHistoryId.get(row.id) ?? row);
  }

  return (
    <div className="space-y-6">
      <FundSection
        title="Upcoming / announced"
        description="Announced distributions that have not paid out yet. Past record/ex/payable dates stay in history below."
        kicker="unpaid announced · not paid history"
        wellClassName="bg-surface"
        funds={sortFunds(upcoming, sortKey, sortDirection)}
        sortKey={sortKey}
        sortDirection={sortDirection}
        onSort={toggleSort}
        onIllustrate={onIllustrate ? illustrate : undefined}
        coverage={coverage}
        emptyHeadline={UPCOMING_UNAVAILABLE_HEADLINE}
        empty={UPCOMING_UNAVAILABLE_DETAIL}
        showPayable
      />
      <FundSection
        title="Paid history"
        description="Paid, final-past, and estimates whose record/ex/payable date is already past. These never appear in Upcoming."
        kicker="past · not upcoming"
        wellClassName="bg-paper"
        funds={sortFunds(paid, sortKey, sortDirection)}
        sortKey={sortKey}
        sortDirection={sortDirection}
        onSort={toggleSort}
        onIllustrate={onIllustrate ? illustrate : undefined}
        coverage={coverage}
        empty={PAID_HISTORY_EMPTY}
        showPayable
      />
    </div>
  );
}

function FundSection({
  title,
  description,
  kicker,
  wellClassName,
  funds,
  sortKey,
  sortDirection,
  onSort,
  onIllustrate,
  coverage,
  emptyHeadline,
  empty,
  showPayable,
}: {
  title: string;
  description: string;
  kicker: string;
  wellClassName: string;
  funds: FundEstimateView[];
  sortKey: SortKey;
  sortDirection: SortDirection;
  onSort: (key: SortKey) => void;
  onIllustrate?: (fund: FundEstimateView) => void;
  coverage: ReturnType<typeof useCoverage>;
  emptyHeadline?: string;
  empty: string;
  showPayable: boolean;
}) {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  return (
    <section className={`rounded-xl border border-line px-4 py-3 ${wellClassName}`}>
      <header className="mb-3 flex flex-wrap items-end justify-between gap-2">
        <div>
          <h3 className="font-serif text-lg tracking-tight text-ink">{title}</h3>
          <p className="mt-0.5 text-sm text-muted">{description}</p>
        </div>
        <p className="text-[10px] text-muted">{kicker}</p>
      </header>

      {funds.length === 0 ? (
        emptyHeadline ? (
          <div className="px-1 py-5">
            <p className="font-serif text-base tracking-tight text-ink">
              {emptyHeadline}
            </p>
            <p className="mt-1 text-sm text-muted">{empty}</p>
          </div>
        ) : (
          <p className="rounded-lg border border-dashed border-line px-4 py-6 text-sm text-muted">
            {empty}
          </p>
        )
      ) : (
        <>
          <div className="hidden overflow-hidden rounded-lg border border-line bg-surface shadow-[0_1px_2px_rgba(26,29,26,0.04)] md:block">
            <div className="overflow-x-auto">
              <table className="min-w-full text-left text-sm">
                <thead className="border-b border-line bg-paper text-[11px] font-semibold uppercase tracking-[0.1em] text-faint">
                  <tr>
                    <SortHeader
                      label="Fund"
                      column="fundName"
                      active={sortKey}
                      direction={sortDirection}
                      onSort={onSort}
                    />
                    <SortHeader
                      label="Family"
                      column="family"
                      active={sortKey}
                      direction={sortDirection}
                      onSort={onSort}
                    />
                    <SortHeader
                      label="Category"
                      column="category"
                      active={sortKey}
                      direction={sortDirection}
                      onSort={onSort}
                    />
                    <SortHeader
                      label="Est. distribution"
                      column="estimatedDistributionPctNav"
                      active={sortKey}
                      direction={sortDirection}
                      onSort={onSort}
                      align="right"
                    />
                    <SortHeader
                      label="Announced"
                      column="asOfDate"
                      active={sortKey}
                      direction={sortDirection}
                      onSort={onSort}
                    />
                    <SortHeader
                      label="Record"
                      column="recordDate"
                      active={sortKey}
                      direction={sortDirection}
                      onSort={onSort}
                    />
                    <SortHeader
                      label="Ex-div"
                      column="exDate"
                      active={sortKey}
                      direction={sortDirection}
                      onSort={onSort}
                    />
                    <SortHeader
                      label="vs category avg"
                      column="vsCategoryPctNav"
                      active={sortKey}
                      direction={sortDirection}
                      onSort={onSort}
                      align="right"
                    />
                    {onIllustrate ? <th className="px-3 py-2.5"> </th> : null}
                  </tr>
                </thead>
                <tbody className="divide-y divide-line">
                  {funds.map((fund) => (
                    <EstimateRow
                      key={fund.id}
                      fund={fund}
                      open={expandedId === fund.id}
                      coverageGap={!coverage.isLive(fund.family)}
                      onToggle={() =>
                        setExpandedId((current) =>
                          toggleExpandedId(current, fund.id),
                        )
                      }
                      onIllustrate={onIllustrate}
                    />
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="space-y-3 md:hidden">
            {funds.map((fund) => (
              <article
                key={fund.id}
                className="rounded-lg border border-line bg-surface p-4"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h3 className="font-medium text-ink">{fund.fundName}</h3>
                    <p className="mt-0.5 font-mono text-[11px] text-faint">
                      {fund.ticker} · {fund.family}
                    </p>
                    <StageBadge fund={fund} />
                    {!coverage.isLive(fund.family) ? (
                      <p className="mt-1 text-[10px] font-semibold uppercase tracking-[0.08em] text-muted">
                        Coverage gap
                      </p>
                    ) : null}
                  </div>
                  <DeltaBadge fund={fund} compact />
                </div>
                <dl className="mt-3 grid grid-cols-2 gap-x-3 gap-y-2 text-sm">
                  <Field label="Announced" value={formatOptionalDate(fund.asOfDate)} />
                  <Field label="Record" value={formatOptionalDate(fund.recordDate)} />
                  <Field label="Ex-div" value={formatOptionalDate(fund.exDate)} />
                  {showPayable ? (
                    <Field
                      label="Payable"
                      value={formatOptionalDate(fund.payableDate)}
                    />
                  ) : null}
                  <Field label="Category" value={fund.category} />
                  <Field
                    label="% of NAV"
                    value={formatPct(fund.estimatedDistributionPctNav)}
                  />
                  <Field
                    label="$ / share"
                    value={formatUsd(fund.estimatedDistributionAmount, 4)}
                  />
                  <Field
                    label="Category avg"
                    value={formatPct(fund.categoryAveragePctNav)}
                  />
                </dl>
                {onIllustrate ? (
                  <button
                    type="button"
                    onClick={() => onIllustrate(fund)}
                    className="mt-3 h-9 w-full rounded-md border border-line text-sm text-ink"
                  >
                    Illustrate
                  </button>
                ) : null}
              </article>
            ))}
          </div>
        </>
      )}
    </section>
  );
}

function EstimateRow({
  fund,
  open,
  coverageGap,
  onToggle,
  onIllustrate,
}: {
  fund: FundEstimateView;
  open: boolean;
  coverageGap: boolean;
  onToggle: () => void;
  onIllustrate?: (fund: FundEstimateView) => void;
}) {
  function onRowClick(event: MouseEvent<HTMLTableRowElement>) {
    if (isNestedControl(event.target)) return;
    onToggle();
  }

  function onRowKeyDown(event: KeyboardEvent<HTMLTableRowElement>) {
    if (event.target !== event.currentTarget) return;
    if (event.key !== "Enter" && event.key !== " ") return;
    event.preventDefault();
    onToggle();
  }

  return (
    <tr
      className="cursor-pointer align-top hover:bg-paper/80"
      tabIndex={0}
      aria-expanded={open}
      onClick={onRowClick}
      onKeyDown={onRowKeyDown}
    >
      <td className="px-3 py-3">
        <span className="block font-medium text-ink">{fund.fundName}</span>
        <span className="mt-0.5 block font-mono text-[11px] text-faint">
          {fund.ticker}
          <span className="mx-1.5">·</span>
          {fund.shareClass}
        </span>
        <StageBadge fund={fund} />
        {open ? <ExpandedDetails fund={fund} /> : null}
      </td>
      <td className="px-3 py-3 text-muted">
        {fund.family}
        {coverageGap ? (
          <span className="mt-1 block text-[10px] font-semibold uppercase tracking-[0.08em] text-muted">
            Coverage gap
          </span>
        ) : null}
      </td>
      <td className="px-3 py-3 text-muted">{fund.category}</td>
      <td className="px-3 py-3 text-right">
        <span className="block font-mono text-ink">
          {formatPct(fund.estimatedDistributionPctNav)}
        </span>
        <span className="mt-0.5 block font-mono text-[11px] text-faint">
          {formatUsd(fund.estimatedDistributionAmount, 4)} / sh
        </span>
      </td>
      <td className="whitespace-nowrap px-3 py-3 font-mono text-sm text-ink">
        {formatOptionalDate(fund.asOfDate)}
      </td>
      <td className="whitespace-nowrap px-3 py-3 font-mono text-sm text-ink">
        {formatOptionalDate(fund.recordDate)}
      </td>
      <td className="whitespace-nowrap px-3 py-3 font-mono text-sm text-ink">
        {formatOptionalDate(fund.exDate)}
      </td>
      <td className="px-3 py-3 text-right">
        <div className="flex flex-col items-end gap-1">
          <DeltaBadge fund={fund} compact />
          <span className="font-mono text-[11px] text-faint">
            Cat. {formatPct(fund.categoryAveragePctNav)}
          </span>
        </div>
      </td>
      {onIllustrate ? (
        <td className="px-3 py-3 text-right">
          <button
            type="button"
            onClick={(event) => {
              event.stopPropagation();
              onIllustrate(fund);
            }}
            className="rounded-md border border-line px-2 py-1 text-xs text-ink hover:border-accent"
          >
            Illustrate
          </button>
        </td>
      ) : null}
    </tr>
  );
}

function StageBadge({ fund }: { fund: FundEstimateView }) {
  const stage = publicationStageLabel(fund.publicationStage);
  if (!stage) return null;
  return (
    <span className="mt-1 block text-[10px] font-semibold uppercase tracking-[0.08em] text-muted">
      {fund.bucket === "paid" ? "Paid history" : "Upcoming"} · {stage}
    </span>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-[11px] uppercase tracking-[0.1em] text-faint">
        {label}
      </dt>
      <dd className="mt-0.5 text-ink">{value}</dd>
    </div>
  );
}

function ExpandedDetails({ fund }: { fund: FundEstimateView }) {
  return (
    <dl className="mt-3 grid max-w-md grid-cols-2 gap-x-4 gap-y-2 rounded-md bg-paper px-3 py-2.5 text-xs text-muted">
      <Field label="CUSIP" value={fund.cusip} />
      <Field label="NAV" value={formatUsd(fund.nav)} />
      <Field
        label="Ordinary income"
        value={formatUsd(fund.estimatedOrdinaryIncome, 4)}
      />
      <Field
        label="Capital gains"
        value={formatUsd(fund.estimatedCapitalGains, 4)}
      />
      <Field label="Year" value={String(fund.distributionYear)} />
      <Field label="Share class" value={fund.shareClass} />
      {fund.paidHistory.length > 0 ? (
        <div className="col-span-2">
          <dt className="text-[11px] uppercase tracking-[0.1em] text-faint">
            Paid history
          </dt>
          <dd className="mt-1 space-y-1.5">
            {fund.paidHistory.map((event) => (
              <DistributionDateStrip
                key={`${event.asOfDate}-${event.exDate ?? ""}`}
                fund={{
                  ...event,
                  publicationStage: event.publicationStage,
                  bucket: "paid",
                }}
                compact
                showPayable
                showStage
              />
            ))}
          </dd>
        </div>
      ) : null}
    </dl>
  );
}

function SortHeader({
  label,
  column,
  active,
  direction,
  onSort,
  align = "left",
}: {
  label: string;
  column: SortKey;
  active: SortKey;
  direction: SortDirection;
  onSort: (column: SortKey) => void;
  align?: "left" | "right";
}) {
  const isActive = active === column;
  return (
    <th className={`px-3 py-2.5 ${align === "right" ? "text-right" : ""}`}>
      <button
        type="button"
        onClick={() => onSort(column)}
        className={`inline-flex items-center gap-1 hover:text-ink ${
          align === "right" ? "flex-row-reverse" : ""
        } ${isActive ? "text-ink" : ""}`}
      >
        {label}
        <span aria-hidden="true" className="font-mono text-[10px]">
          {isActive ? (direction === "asc" ? "↑" : "↓") : "↕"}
        </span>
      </button>
    </th>
  );
}
