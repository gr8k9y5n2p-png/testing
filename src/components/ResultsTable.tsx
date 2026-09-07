"use client";

import { useState } from "react";
import type { FundEstimateView } from "@/data/types";
import { DeltaBadge } from "@/components/DeltaBadge";
import { useCoverage } from "@/components/coverage/CoverageProvider";
import {
  formatDate,
  formatPct,
  formatUsd,
  sortFunds,
  type SortDirection,
  type SortKey,
} from "@/lib/format";

export function ResultsTable({
  funds,
  onIllustrate,
}: {
  funds: FundEstimateView[];
  onIllustrate?: (fund: FundEstimateView) => void;
}) {
  const [sortKey, setSortKey] = useState<SortKey>("fundName");
  const [sortDirection, setSortDirection] = useState<SortDirection>("asc");
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const coverage = useCoverage();

  const rows = sortFunds(funds, sortKey, sortDirection);

  function toggleSort(key: SortKey) {
    if (key === sortKey) {
      setSortDirection((current) => (current === "asc" ? "desc" : "asc"));
      return;
    }
    setSortKey(key);
    setSortDirection(key === "fundName" || key === "family" || key === "category" ? "asc" : "desc");
  }

  return (
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
                  onSort={toggleSort}
                />
                <SortHeader
                  label="Family"
                  column="family"
                  active={sortKey}
                  direction={sortDirection}
                  onSort={toggleSort}
                />
                <SortHeader
                  label="Category"
                  column="category"
                  active={sortKey}
                  direction={sortDirection}
                  onSort={toggleSort}
                />
                <SortHeader
                  label="Est. distribution"
                  column="estimatedDistributionPctNav"
                  active={sortKey}
                  direction={sortDirection}
                  onSort={toggleSort}
                  align="right"
                />
                <SortHeader
                  label="As of / published"
                  column="publishedAt"
                  active={sortKey}
                  direction={sortDirection}
                  onSort={toggleSort}
                />
                <SortHeader
                  label="vs category avg"
                  column="vsCategoryPctNav"
                  active={sortKey}
                  direction={sortDirection}
                  onSort={toggleSort}
                  align="right"
                />
                {onIllustrate ? <th className="px-3 py-2.5"> </th> : null}
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {rows.map((fund) => {
                const open = expandedId === fund.id;
                return (
                  <tr
                    key={fund.id}
                    className="align-top hover:bg-paper/80"
                  >
                    <td className="px-3 py-3">
                      <button
                        type="button"
                        className="text-left"
                        onClick={() => setExpandedId(open ? null : fund.id)}
                        aria-expanded={open}
                      >
                        <span className="block font-medium text-ink">
                          {fund.fundName}
                        </span>
                        <span className="mt-0.5 block font-mono text-[11px] text-faint">
                          {fund.ticker}
                          <span className="mx-1.5">·</span>
                          {fund.shareClass}
                        </span>
                      </button>
                      {open ? <ExpandedDetails fund={fund} /> : null}
                    </td>
                    <td className="px-3 py-3 text-muted">
                      {fund.family}
                      {!coverage.isLive(fund.family) ? (
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
                    <td className="px-3 py-3 text-muted">
                      <span className="block">{formatDate(fund.asOfDate)}</span>
                      <span className="mt-0.5 block text-[11px] text-faint">
                        Pub. {formatDate(fund.publishedAt)}
                      </span>
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
                          onClick={() => onIllustrate(fund)}
                          className="rounded-md border border-line px-2 py-1 text-xs text-ink hover:border-accent"
                        >
                          Illustrate
                        </button>
                      </td>
                    ) : null}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      <div className="space-y-3 md:hidden">
        {rows.map((fund) => (
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
            <dl className="mt-3 grid grid-cols-2 gap-x-3 gap-y-2 text-sm">
              <Field label="Category" value={fund.category} />
              <Field
                label="% of NAV"
                value={formatPct(fund.estimatedDistributionPctNav)}
              />
              <Field
                label="$ / share"
                value={formatUsd(fund.estimatedDistributionAmount, 4)}
              />
              <Field label="As of" value={formatDate(fund.asOfDate)} />
              <Field label="Published" value={formatDate(fund.publishedAt)} />
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
