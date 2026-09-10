"use client";

import {
  useState,
  type KeyboardEvent,
  type MouseEvent,
  type ReactNode,
  type UIEvent,
} from "react";
import type { FundEstimateView } from "@/data/types";
import { hideUpcomingAmounts } from "@/data/hydrate-funds";
import { paidHistoryViews, splitFundsByBucket } from "@/data/queries";
import { publicationStageLabel } from "@/data/distribution-bucket";
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
  formatSoftPct,
  formatWeeklyNavLabel,
  pctOfNavForFund,
} from "@/lib/illustrate/nav-math";
import {
  PAID_HISTORY_EMPTY,
  SEARCH_PAID_HISTORY_DETAIL,
  SEARCH_PAID_HISTORY_HEADING,
  SEARCH_PAID_HISTORY_KICKER,
  SEARCH_UPCOMING_DETAIL,
  SEARCH_UPCOMING_HEADING,
  SEARCH_UPCOMING_KICKER,
  UPCOMING_UNAVAILABLE_DETAIL,
  UPCOMING_UNAVAILABLE_HEADLINE,
} from "@/lib/copy";
import { SearchTickerButton } from "@/components/SearchTickerButton";

const TABLE_VIEWPORT = 448;
const TABLE_ROW_HEIGHT = 76;
const TABLE_OVERSCAN = 4;

type SamplePage = {
  total: number;
  limit: number;
  offset: number;
  onOffset: (offset: number) => void;
};

function estimatePct(fund: FundEstimateView): string {
  if (hideUpcomingAmounts(fund)) return "—";
  return formatSoftPct(pctOfNavForFund(fund));
}

function estimateUsd(fund: FundEstimateView): string {
  if (hideUpcomingAmounts(fund)) return "—";
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
  year,
  highlightedTicker,
}: {
  funds: FundEstimateView[];
  onIllustrate?: (fund: FundEstimateView) => void;
  sortKey?: SortKey;
  sortDirection?: SortDirection;
  onSort?: (key: SortKey) => void;
  page?: SamplePage;
  /** Paid history year toggle. Upcoming stays unpaid announced only. */
  year?: number;
  /** Selected Search ticker — highlight only; does not filter Upcoming. */
  highlightedTicker?: string;
}) {
  const [localSortKey, setLocalSortKey] = useState<SortKey>("fundName");
  const [localSortDirection, setLocalSortDirection] = useState<SortDirection>("asc");
  const sortKey = sortKeyProp ?? localSortKey;
  const sortDirection = sortDirectionProp ?? localSortDirection;
  const coverage = useCoverage();
  const { upcoming } = splitFundsByBucket(funds);
  const paid = paidHistoryViews(funds, year);
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
      <FundSection
        title={SEARCH_UPCOMING_HEADING}
        description={SEARCH_UPCOMING_DETAIL}
        kicker={SEARCH_UPCOMING_KICKER}
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
        page={page}
        highlightedTicker={highlightedTicker}
      />
      <FundSection
        title={SEARCH_PAID_HISTORY_HEADING}
        description={SEARCH_PAID_HISTORY_DETAIL}
        kicker={SEARCH_PAID_HISTORY_KICKER}
        wellClassName="bg-paper"
        funds={serverSorted ? paid : sortFunds(paid, sortKey, sortDirection)}
        sortKey={sortKey}
        sortDirection={sortDirection}
        onSort={toggleSort}
        onIllustrate={onIllustrate ? illustrate : undefined}
        coverage={coverage}
        empty={PAID_HISTORY_EMPTY}
        showPayable
        showHeading
        highlightedTicker={highlightedTicker}
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
  page,
  showHeading = false,
  highlightedTicker,
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
  page?: SamplePage;
  showHeading?: boolean;
  highlightedTicker?: string;
}) {
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const highlightKey = highlightedTicker?.trim().toUpperCase();

  return (
    <section
      aria-label={title}
      className={`rounded-xl border border-line px-4 py-3 ${wellClassName}`}
    >
      <header
        className={`mb-3 flex flex-wrap gap-2 ${
          showHeading ? "items-end justify-between" : "items-end justify-end"
        }`}
      >
        {showHeading ? (
          <div>
            <h3 className="font-serif text-xl tracking-tight text-ink">{title}</h3>
            <p className="mt-1 max-w-2xl text-sm text-muted">{description}</p>
          </div>
        ) : (
          <p className="sr-only">{description}</p>
        )}
        <p className="text-[10px] text-muted">{kicker}</p>
      </header>

      {funds.length === 0 ? (
        <>
          {emptyHeadline ? (
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
          )}
          {page ? (
            <PaginationBar {...page} label={`${title} pages`} />
          ) : null}
        </>
      ) : (
        <>
          <div className="hidden overflow-hidden rounded-lg border border-line bg-surface shadow-[0_1px_2px_rgba(26,29,26,0.04)] md:block">
            <VirtualizedTable
              funds={funds}
              expandedId={expandedId}
              columnCount={(onIllustrate ? 8 : 7) + (showPayable ? 1 : 0)}
              header={
                <tr>
                  <SortHeader
                    label="Ticker"
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
                    label="Dist $/sh"
                    column="estimatedDistributionPctNav"
                    active={sortKey}
                    direction={sortDirection}
                    onSort={onSort}
                    align="right"
                  />
                  <th className="px-3 py-2.5 text-right">% NAV</th>
                  <SortHeader
                    label="Announced"
                    column="publishedAt"
                    active={sortKey}
                    direction={sortDirection}
                    onSort={onSort}
                  />
                  <th className="px-3 py-2.5">Record</th>
                  <th className="px-3 py-2.5">Ex-div</th>
                  {showPayable ? <th className="px-3 py-2.5">Payable</th> : null}
                  {onIllustrate ? <th className="px-3 py-2.5"> </th> : null}
                </tr>
              }
              renderRow={(fund) => (
                <EstimateRow
                  key={fund.id}
                  fund={fund}
                  open={expandedId === fund.id}
                  highlighted={
                    Boolean(
                      highlightKey &&
                        fund.ticker.trim().toUpperCase() === highlightKey,
                    )
                  }
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
            {page ? (
              <PaginationBar {...page} label={`${title} pages`} />
            ) : null}
          </div>

          <div className="max-h-[28rem] space-y-3 overflow-y-auto md:hidden">
            {funds.map((fund) => (
              <article
                key={fund.id}
                className={`rounded-lg border bg-surface p-4 ${
                  highlightKey &&
                  fund.ticker.trim().toUpperCase() === highlightKey
                    ? "border-accent"
                    : "border-line"
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h3 className="font-medium text-ink">
                      <SearchTickerButton fund={fund} onSelect={onIllustrate}>
                        {fund.fundName}
                      </SearchTickerButton>
                    </h3>
                    <p className="mt-0.5 font-mono text-[11px] text-faint">
                      <SearchTickerButton fund={fund} onSelect={onIllustrate} />
                      <span className="mx-1.5">·</span>
                      {fund.family}
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
                    value={estimatePct(fund)}
                  />
                  <Field
                    label="$ / share"
                    value={
                      hideUpcomingAmounts(fund)
                        ? "—"
                        : formatUsd(fund.estimatedDistributionAmount, 4)
                    }
                  />
                  <Field
                    label="Category avg"
                    value={
                      hideUpcomingAmounts(fund)
                        ? "—"
                        : formatPct(fund.categoryAveragePctNav)
                    }
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
          {page ? (
            <div className="mt-2 md:hidden">
              <PaginationBar {...page} label={`${title} pages`} />
            </div>
          ) : null}
        </>
      )}
    </section>
  );
}

function EstimateRow({
  fund,
  open,
  highlighted,
  coverageGap,
  showPayable,
  onToggle,
  onIllustrate,
}: {
  fund: FundEstimateView;
  open: boolean;
  highlighted?: boolean;
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
      className={`cursor-pointer align-top hover:bg-paper/80 ${
        highlighted ? "bg-paper ring-1 ring-inset ring-accent/40" : ""
      }`}
      tabIndex={0}
      aria-expanded={open}
      onClick={onRowClick}
      onKeyDown={onRowKeyDown}
    >
      <td className="px-3 py-3">
        <span className="block font-mono text-sm font-medium text-ink">
          <SearchTickerButton fund={fund} onSelect={onIllustrate} />
        </span>
        <span className="mt-0.5 block text-[11px] text-faint">
          <SearchTickerButton fund={fund} onSelect={onIllustrate}>
            {fund.fundName}
          </SearchTickerButton>
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
      <td className="px-3 py-3 text-right font-mono text-ink">
        {estimateUsd(fund)}
      </td>
      <td className="px-3 py-3 text-right font-mono text-ink">
        {estimatePct(fund)}
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
      {showPayable ? (
        <td className="whitespace-nowrap px-3 py-3 font-mono text-sm text-ink">
          {formatOptionalDate(fund.payableDate)}
        </td>
      ) : null}
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
      <Field label="NAV" value={formatWeeklyNavLabel(fund)} />
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
    </dl>
  );
}

function PaginationBar({
  total,
  limit,
  offset,
  onOffset,
  label = `${SEARCH_UPCOMING_HEADING} pages`,
}: SamplePage & { label?: string }) {
  const page = Math.floor(offset / limit) + 1;
  const pages = Math.max(1, Math.ceil(total / limit));
  const from = total === 0 ? 0 : offset + 1;
  const to = Math.min(offset + limit, total);
  return (
    <nav
      aria-label={label}
      className="flex flex-wrap items-center justify-between gap-x-2 gap-y-1 border-t border-line bg-paper/70 px-2.5 py-1"
    >
      <p className="font-mono text-[10px] tabular-nums text-faint">
        {from}–{to} of {total}
      </p>
      <div className="flex items-center gap-1">
        <button
          type="button"
          disabled={offset <= 0}
          onClick={() => onOffset(Math.max(0, offset - limit))}
          className="h-6 rounded border border-line px-1.5 text-[11px] leading-none text-ink disabled:cursor-not-allowed disabled:text-faint"
        >
          Previous
        </button>
        <p className="min-w-[4.75rem] text-center text-[10px] tabular-nums text-muted">
          {page}/{pages}
        </p>
        <button
          type="button"
          disabled={offset + limit >= total}
          onClick={() => onOffset(offset + limit)}
          className="h-6 rounded border border-line px-1.5 text-[11px] leading-none text-ink disabled:cursor-not-allowed disabled:text-faint"
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
