"use client";

import {
  useState,
  type KeyboardEvent,
  type MouseEvent,
  type ReactNode,
  type UIEvent,
} from "react";
import type { FundEstimateView } from "@/data/types";
import { paidHistoryViews, splitFundsByBucket } from "@/data/queries";
import { DistributionDateStrip } from "@/components/DistributionDateStrip";
import { DeltaBadge } from "@/components/DeltaBadge";
import { useCoverage } from "@/components/coverage/CoverageProvider";
import {
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

const TABLE_VIEWPORT = 448;
const TABLE_ROW_HEIGHT = 76;
const TABLE_OVERSCAN = 4;

function estimatePct(fund: FundEstimateView): string {
  if (fund.hasEstimate === false) return "—";
  return formatPct(fund.estimatedDistributionPctNav);
}

function estimateUsd(fund: FundEstimateView): string {
  if (fund.hasEstimate === false) return "—";
  return `${formatUsd(fund.estimatedDistributionAmount, 4)} / sh`;
}

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
  sortKey: sortKeyProp,
  sortDirection: sortDirectionProp,
  onSort,
  page,
}: {
  funds: FundEstimateView[];
  onIllustrate?: (fund: FundEstimateView) => void;
  sortKey?: SortKey;
  sortDirection?: SortDirection;
  onSort?: (key: SortKey) => void;
  page?: {
    total: number;
    limit: number;
    offset: number;
    onOffset: (offset: number) => void;
  };
}) {
  const [localSortKey, setLocalSortKey] = useState<SortKey>("fundName");
  const [localSortDirection, setLocalSortDirection] = useState<SortDirection>("asc");
  const sortKey = sortKeyProp ?? localSortKey;
  const sortDirection = sortDirectionProp ?? localSortDirection;
  const coverage = useCoverage();
  const { upcoming } = splitFundsByBucket(funds);
  const paid = paidHistoryViews(funds);
  const serverSorted = Boolean(onSort);

  function toggleSort(key: SortKey) {
    if (onSort) {
      onSort(key);
      return;
    }
    if (key === localSortKey) {
      setLocalSortDirection((current) => (current === "asc" ? "desc" : "asc"));
      return;
    }
    setLocalSortKey(key);
    setLocalSortDirection(
      key === "fundName" || key === "family" || key === "category" ? "asc" : "desc",
    );
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
      {page ? <PaginationBar {...page} /> : null}
      <FundSection
        title="Upcoming / announced"
        description="Announced distributions that have not paid out yet. Past record/ex/payable dates stay in history below."
        kicker="unpaid announced · not paid history"
        wellClassName="bg-surface"
        funds={serverSorted ? upcoming : sortFunds(upcoming, sortKey, sortDirection)}
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
        funds={serverSorted ? paid : sortFunds(paid, sortKey, sortDirection)}
        sortKey={sortKey}
        sortDirection={sortDirection}
        onSort={toggleSort}
        onIllustrate={onIllustrate ? illustrate : undefined}
        coverage={coverage}
        empty={PAID_HISTORY_EMPTY}
        showPayable
      />
      {page ? <PaginationBar {...page} /> : null}
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
            <VirtualizedTable
              funds={funds}
              expandedId={expandedId}
              columnCount={onIllustrate ? 7 : 6}
              header={
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
                    column="publishedAt"
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
              }
              renderRow={(fund) => (
                <EstimateRow
                  key={fund.id}
                  fund={fund}
                  open={expandedId === fund.id}
                  coverageGap={!coverage.isLive(fund.family)}
                  showPayable={showPayable}
                  onToggle={() =>
                    setExpandedId((current) =>
                      toggleExpandedId(current, fund.id),
                    )
                  }
                  onIllustrate={onIllustrate}
                />
              )}
            />
          </div>

          <div className="max-h-[28rem] space-y-3 overflow-y-auto md:hidden">
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
                    {!coverage.isLive(fund.family) ? (
                      <p className="mt-1 text-[10px] font-semibold uppercase tracking-[0.08em] text-muted">
                        Coverage gap
                      </p>
                    ) : null}
                  </div>
                  <DeltaBadge fund={fund} compact />
                </div>
                <DistributionDateStrip
                  fund={fund}
                  compact
                  showPayable={showPayable}
                  showStage
                  className="mt-2"
                />
                <dl className="mt-3 grid grid-cols-2 gap-x-3 gap-y-2 text-sm">
                  <Field label="Category" value={fund.category} />
                  <Field
                    label="% of NAV"
                    value={estimatePct(fund)}
                  />
                  <Field
                    label="$ / share"
                    value={fund.hasEstimate === false ? "—" : formatUsd(fund.estimatedDistributionAmount, 4)}
                  />
                  <Field
                    label="Category avg"
                    value={fund.hasEstimate === false ? "—" : formatPct(fund.categoryAveragePctNav)}
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
  showPayable,
  onToggle,
  onIllustrate,
}: {
  fund: FundEstimateView;
  open: boolean;
  coverageGap: boolean;
  showPayable: boolean;
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
          {estimatePct(fund)}
        </span>
        <span className="mt-0.5 block font-mono text-[11px] text-faint">
          {estimateUsd(fund)}
        </span>
      </td>
      <td className="px-3 py-3">
        <DistributionDateStrip
          fund={fund}
          compact
          showPayable={showPayable}
          showStage
        />
      </td>
      <td className="px-3 py-3 text-right">
        <div className="flex flex-col items-end gap-1">
          <DeltaBadge fund={fund} compact />
          <span className="font-mono text-[11px] text-faint">
            Cat. {fund.hasEstimate === false ? "—" : formatPct(fund.categoryAveragePctNav)}
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

function PaginationBar({
  total,
  limit,
  offset,
  onOffset,
}: {
  total: number;
  limit: number;
  offset: number;
  onOffset: (offset: number) => void;
}) {
  const page = Math.floor(offset / limit) + 1;
  const pages = Math.max(1, Math.ceil(total / limit));
  const from = total === 0 ? 0 : offset + 1;
  const to = Math.min(offset + limit, total);
  return (
    <nav
      aria-label="Sample estimates pages"
      className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-line bg-surface px-3 py-2.5"
    >
      <p className="font-mono text-xs text-faint">
        {from}–{to} of {total}
      </p>
      <div className="flex items-center gap-2">
        <button
          type="button"
          disabled={offset <= 0}
          onClick={() => onOffset(Math.max(0, offset - limit))}
          className="h-9 rounded-md border border-line px-3 text-sm text-ink disabled:cursor-not-allowed disabled:text-faint"
        >
          Previous
        </button>
        <p className="min-w-[7rem] text-center text-sm text-muted">
          Page {page} of {pages}
        </p>
        <button
          type="button"
          disabled={offset + limit >= total}
          onClick={() => onOffset(offset + limit)}
          className="h-9 rounded-md border border-line px-3 text-sm text-ink disabled:cursor-not-allowed disabled:text-faint"
        >
          Next
        </button>
      </div>
    </nav>
  );
}

function VirtualizedTable({
  funds,
  expandedId,
  columnCount,
  header,
  renderRow,
}: {
  funds: FundEstimateView[];
  expandedId: string | null;
  columnCount: number;
  header: ReactNode;
  renderRow: (fund: FundEstimateView) => ReactNode;
}) {
  const [scrollTop, setScrollTop] = useState(0);
  const expanded = Boolean(expandedId);
  const windowed = !expanded && funds.length > 12;
  const start = windowed
    ? Math.max(0, Math.floor(scrollTop / TABLE_ROW_HEIGHT) - TABLE_OVERSCAN)
    : 0;
  const visible = windowed
    ? Math.ceil(TABLE_VIEWPORT / TABLE_ROW_HEIGHT) + TABLE_OVERSCAN * 2
    : funds.length;
  const end = Math.min(funds.length, start + visible);
  const topPad = windowed ? start * TABLE_ROW_HEIGHT : 0;
  const bottomPad = windowed ? Math.max(0, (funds.length - end) * TABLE_ROW_HEIGHT) : 0;

  function onScroll(event: UIEvent<HTMLDivElement>) {
    setScrollTop(event.currentTarget.scrollTop);
  }

  return (
    <div
      className="max-h-[28rem] overflow-auto"
      onScroll={windowed ? onScroll : undefined}
    >
      <table className="min-w-full text-left text-sm">
        <thead className="sticky top-0 z-10 border-b border-line bg-paper text-[11px] font-semibold uppercase tracking-[0.1em] text-faint">
          {header}
        </thead>
        <tbody className="divide-y divide-line">
          {topPad > 0 ? (
            <tr aria-hidden="true">
              <td colSpan={columnCount} style={{ height: topPad, padding: 0 }} />
            </tr>
          ) : null}
          {(windowed ? funds.slice(start, end) : funds).map((fund) => renderRow(fund))}
          {bottomPad > 0 ? (
            <tr aria-hidden="true">
              <td colSpan={columnCount} style={{ height: bottomPad, padding: 0 }} />
            </tr>
          ) : null}
        </tbody>
      </table>
    </div>
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
