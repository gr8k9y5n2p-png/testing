"use client";

import { formatUsd } from "@/lib/format";
import type {
  AllocationUnit,
  PortfolioFundOption,
  PortfolioHoldingDraft,
} from "@/lib/illustrate/portfolio-compare-types";
import { TickerField } from "@/components/illustrate/portfolio-compare/TickerField";

function formatWeight(value: number): string {
  if (!Number.isFinite(value)) return "";
  const rounded = Math.round(value * 100) / 100;
  return Number.isInteger(rounded) ? String(rounded) : rounded.toFixed(2);
}

function parseNumeric(raw: string): number | null {
  const parsed = Number(raw.replace(/[$,%\s]/g, "").replace(/,/g, ""));
  return Number.isFinite(parsed) ? parsed : null;
}

export function AllocationColumn({
  title,
  holdings,
  bookDollars,
  unit,
  funds,
  inputIdPrefix,
  onUnitChange,
  onChange,
  className = "",
}: {
  title: string;
  holdings: PortfolioHoldingDraft[];
  bookDollars: number;
  unit: AllocationUnit;
  funds: PortfolioFundOption[];
  inputIdPrefix: string;
  onUnitChange: (unit: AllocationUnit) => void;
  onChange: (holdings: PortfolioHoldingDraft[]) => void;
  className?: string;
}) {
  const totalDollars = holdings.reduce((sum, holding) => sum + holding.holdingDollars, 0);
  const totalWeight = holdings.reduce((sum, holding) => sum + holding.weightPct, 0);

  function updateAt(index: number, patch: Partial<PortfolioHoldingDraft>) {
    onChange(holdings.map((holding, i) => (i === index ? { ...holding, ...patch } : holding)));
  }

  function commitWeight(index: number, raw: string) {
    const parsed = parseNumeric(raw);
    if (parsed == null || parsed < 0) return;
    updateAt(index, {
      weightPct: parsed,
      holdingDollars: (parsed / 100) * bookDollars,
    });
  }

  function commitDollars(index: number, raw: string) {
    const parsed = parseNumeric(raw);
    if (parsed == null || parsed < 0) return;
    updateAt(index, {
      holdingDollars: parsed,
      weightPct: bookDollars > 0 ? (parsed / bookDollars) * 100 : 0,
    });
  }

  return (
    <section className={`flex min-h-0 flex-col rounded-2xl border border-line bg-surface p-4 shadow-[0_8px_24px_rgba(26,29,26,0.06)] sm:p-5 ${className}`}>
      <header className="mb-4 flex items-center justify-between gap-3">
        <h2 className="text-[11px] font-semibold uppercase tracking-[0.14em] text-faint">
          {title}
        </h2>
        <div
          role="radiogroup"
          aria-label={`${title} display unit`}
          className="inline-flex rounded-md border border-line bg-paper p-0.5"
        >
          <UnitButton
            label="%"
            active={unit === "pct"}
            onClick={() => onUnitChange("pct")}
          />
          <UnitButton
            label="$"
            active={unit === "usd"}
            onClick={() => onUnitChange("usd")}
          />
        </div>
      </header>

      {holdings.length === 0 ? (
        <p className="rounded-xl border border-dashed border-line bg-paper/40 px-3 py-5 text-center text-sm text-muted">
          No holdings yet — use + Add holding to start.
        </p>
      ) : null}

      <ul className="flex flex-col gap-2.5">
        {holdings.map((holding, index) => (
          <li
            key={holding.id}
            className="rounded-xl border border-line bg-paper/80 px-3 py-3"
          >
            <div className="flex items-start gap-3">
              <TickerField
                ticker={holding.ticker}
                fundName={holding.fundName}
                funds={funds}
                inputId={`${inputIdPrefix}-ticker-${holding.id}`}
                onSelect={(fund) => {
                  updateAt(index, {
                    ticker: fund.ticker,
                    fundName: fund.fundName,
                    family: fund.family,
                    nav: fund.nav ?? null,
                  });
                }}
              />
              <div className="w-[7.5rem] shrink-0 text-right">
                {unit === "pct" ? (
                  <>
                    <label className="sr-only" htmlFor={`${inputIdPrefix}-weight-${holding.id}`}>
                      Weight percent for {holding.ticker || "holding"}
                    </label>
                    <div className="relative">
                      <input
                        id={`${inputIdPrefix}-weight-${holding.id}`}
                        inputMode="decimal"
                        defaultValue={formatWeight(holding.weightPct)}
                        key={`pct-${holding.id}-${formatWeight(holding.weightPct)}`}
                        onBlur={(event) => commitWeight(index, event.target.value)}
                        className="h-10 w-full rounded-md border border-line bg-surface pr-7 text-right font-mono text-sm text-ink"
                      />
                      <span className="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 text-xs text-faint">
                        %
                      </span>
                    </div>
                    <p className="mt-1 font-mono text-[11px] text-muted">
                      {formatUsd(holding.holdingDollars, 0)}
                    </p>
                  </>
                ) : (
                  <>
                    <label className="sr-only" htmlFor={`${inputIdPrefix}-dollars-${holding.id}`}>
                      Dollars for {holding.ticker || "holding"}
                    </label>
                    <div className="relative">
                      <span className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 text-xs text-faint">
                        $
                      </span>
                      <input
                        id={`${inputIdPrefix}-dollars-${holding.id}`}
                        inputMode="decimal"
                        defaultValue={Math.round(holding.holdingDollars).toLocaleString("en-US")}
                        key={`usd-${holding.id}-${Math.round(holding.holdingDollars)}`}
                        onBlur={(event) => commitDollars(index, event.target.value)}
                        className="h-10 w-full rounded-md border border-line bg-surface pl-5 pr-2 text-right font-mono text-sm text-ink"
                      />
                    </div>
                    <p className="mt-1 font-mono text-[11px] text-muted">
                      {formatWeight(holding.weightPct)}%
                    </p>
                  </>
                )}
              </div>
              <button
                type="button"
                aria-label={`Remove ${holding.ticker || "holding"}`}
                onClick={() => onChange(holdings.filter((_, i) => i !== index))}
                className="mt-1.5 shrink-0 rounded p-1 text-faint hover:bg-surface hover:text-ink"
              >
                ×
              </button>
            </div>
          </li>
        ))}
      </ul>

      <div className="mt-auto pt-3">
        <button
          type="button"
          onClick={() => {
            const option = funds[0];
            onChange([
              ...holdings,
              {
                id: `${inputIdPrefix}-${Date.now()}`,
                ticker: "",
                fundName: "",
                family: option?.family,
                nav: null,
                weightPct: 0,
                holdingDollars: 0,
              },
            ]);
          }}
          className="flex h-11 w-full items-center justify-center gap-1.5 rounded-xl border border-dashed border-line-strong text-sm font-medium text-muted hover:border-ink/30 hover:text-ink"
        >
          <span aria-hidden className="text-base leading-none">
            +
          </span>
          Add holding
        </button>

        <p className="mt-4 flex items-center justify-between border-t border-line pt-3 text-[11px] font-semibold uppercase tracking-[0.12em] text-faint">
          <span>Total</span>
          <span className="font-mono text-sm font-medium normal-case tracking-normal text-ink">
            {formatUsd(totalDollars, 0)}
            <span className="text-muted"> · {formatWeight(totalWeight)}%</span>
          </span>
        </p>
      </div>
    </section>
  );
}

function UnitButton({
  label,
  active,
  onClick,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      role="radio"
      aria-checked={active}
      onClick={onClick}
      className={`h-7 min-w-8 rounded-[5px] px-2.5 text-xs font-semibold ${
        active ? "bg-ink text-white" : "text-muted hover:text-ink"
      }`}
    >
      {label}
    </button>
  );
}
