"use client";

import type { TaxRates } from "@/lib/illustrate/types";

const fieldClass =
  "h-10 w-full rounded-md border border-line bg-paper px-2.5 font-mono text-sm text-ink";

export function TaxRateFields({
  rates,
  combine,
  onRatesChange,
  onCombineChange,
}: {
  rates: TaxRates;
  combine: boolean;
  onRatesChange: (next: TaxRates) => void;
  onCombineChange: (next: boolean) => void;
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
      <p className="mt-1 mb-3 text-xs text-muted">
        Rates are sent to <code className="font-mono">POST /illustrate</code>. Math
        is not computed in the browser.
      </p>
      <div className="grid gap-3 sm:grid-cols-2">
        <RateInput
          label="Federal ordinary income"
          value={rates.ordinary_income}
          onChange={(pct) => setPct("ordinary_income", pct)}
        />
        <RateInput
          label="Federal LTCG"
          value={rates.long_term_capital_gains}
          onChange={(pct) => setPct("long_term_capital_gains", pct)}
        />
        <RateInput
          label="Federal STCG"
          hint="Taxed as ordinary income; override independently if needed."
          value={rates.short_term_capital_gains}
          onChange={(pct) => setPct("short_term_capital_gains", pct)}
        />
        <RateInput
          label="Qualified dividend (QDI)"
          value={rates.qualified_dividend}
          onChange={(pct) => setPct("qualified_dividend", pct)}
        />
        <RateInput
          label="State"
          hint="Optional. Combined with federal when the box below is checked."
          value={rates.state}
          onChange={(pct) => setPct("state", pct)}
        />
      </div>
      <label className="mt-3 flex items-start gap-2 text-sm text-ink">
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
}: {
  label: string;
  hint?: string;
  value: number;
  onChange: (pct: string) => void;
}) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs text-muted">{label}</span>
      <div className="relative">
        <input
          type="number"
          min={0}
          max={100}
          step={0.1}
          className={fieldClass}
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
