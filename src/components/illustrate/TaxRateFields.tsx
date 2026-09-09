"use client";

import type { TaxRates } from "@/lib/illustrate/types";

const fieldClass =
  "h-10 w-full rounded-md border border-line bg-paper px-2.5 font-mono text-sm text-ink";
const compactFieldClass =
  "h-9 w-full rounded-md border border-line bg-paper px-2 font-mono text-sm text-ink";

export function TaxRateFields({
  rates,
  combine,
  onRatesChange,
  onCombineChange,
  compact = false,
}: {
  rates: TaxRates;
  combine: boolean;
  onRatesChange: (next: TaxRates) => void;
  onCombineChange: (next: boolean) => void;
  /** Compare strip: same fields, tighter grid. Dollar Illustration stays full. */
  compact?: boolean;
}) {
  function setPct(key: keyof TaxRates, pct: string) {
    const parsed = Number(pct);
    if (Number.isNaN(parsed)) return;
    onRatesChange({ ...rates, [key]: Math.min(100, Math.max(0, parsed)) / 100 });
  }

  return (
    <fieldset>
      <legend className="text-[11px] font-semibold uppercase tracking-[0.12em] text-faint">
        Tax rates
      </legend>
      {compact ? (
        <p className="mt-1 mb-2 text-[11px] text-muted">
          Same fields as Dollar Illustration. Sent on every compare request —
          Tax $ and tax-drag recompute from these rates and dollars invested.
        </p>
      ) : (
        <p className="mt-1 mb-3 text-xs text-muted">
          Rates are sent to <code className="font-mono">POST /illustrate</code>. Math
          is not computed in the browser.
        </p>
      )}
      <div
        className={
          compact
            ? "grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-5"
            : "grid gap-3 sm:grid-cols-2"
        }
      >
        <RateInput
          compact={compact}
          label="Federal ordinary income"
          value={rates.ordinary_income}
          onChange={(pct) => setPct("ordinary_income", pct)}
        />
        <RateInput
          compact={compact}
          label="Federal LTCG"
          value={rates.long_term_capital_gains}
          onChange={(pct) => setPct("long_term_capital_gains", pct)}
        />
        <RateInput
          compact={compact}
          label="Federal STCG"
          hint={
            compact
              ? undefined
              : "Taxed as ordinary income; override independently if needed."
          }
          value={rates.short_term_capital_gains}
          onChange={(pct) => setPct("short_term_capital_gains", pct)}
        />
        <RateInput
          compact={compact}
          label="Qualified dividend (QDI)"
          value={rates.qualified_dividend}
          onChange={(pct) => setPct("qualified_dividend", pct)}
        />
        <RateInput
          compact={compact}
          label="State"
          hint={
            compact
              ? undefined
              : "Optional. Combined with federal when the box below is checked."
          }
          value={rates.state}
          onChange={(pct) => setPct("state", pct)}
        />
      </div>
      <label
        className={`flex items-start gap-2 text-sm text-ink ${compact ? "mt-2" : "mt-3"}`}
      >
        <input
          type="checkbox"
          className="mt-0.5"
          checked={combine}
          onChange={(event) => onCombineChange(event.target.checked)}
        />
        Combine state with federal (effective rate = federal + state)
      </label>
    </fieldset>
  );
}

function RateInput({
  label,
  hint,
  value,
  onChange,
  compact = false,
}: {
  label: string;
  hint?: string;
  value: number;
  onChange: (pct: string) => void;
  compact?: boolean;
}) {
  return (
    <label className="block">
      <span className={`mb-1 block text-muted ${compact ? "text-[11px]" : "text-xs"}`}>
        {label}
      </span>
      <div className="relative">
        <input
          type="number"
          min={0}
          max={100}
          step={0.1}
          className={compact ? compactFieldClass : fieldClass}
          value={Number((value * 100).toFixed(2))}
          onChange={(event) => onChange(event.target.value)}
        />
        <span className="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 text-xs text-faint">
          %
        </span>
      </div>
      {hint ? <span className="mt-1 block text-[11px] text-faint">{hint}</span> : null}
    </label>
  );
}
