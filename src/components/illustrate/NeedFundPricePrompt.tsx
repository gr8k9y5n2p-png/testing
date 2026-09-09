import {
  ENTER_NAV_COPY,
  ENTER_NAV_DETAIL,
  NEED_FUND_PRICE_COPY,
} from "@/lib/illustrate/illustrate-error";

export type NavPromptHolding = {
  key: string;
  ticker: string;
  nav?: number | null;
};

export function NeedFundPricePrompt({
  holdings,
  onNavChange,
  className = "",
}: {
  holdings: NavPromptHolding[];
  onNavChange: (key: string, nav: number | null) => void;
  className?: string;
}) {
  return (
    <div
      role="status"
      className={`rounded-2xl border border-line bg-paper px-5 py-4 ${className}`}
    >
      <p className="font-serif text-lg tracking-tight text-ink">
        {NEED_FUND_PRICE_COPY}
      </p>
      <p className="mt-1 text-sm text-muted">{ENTER_NAV_DETAIL}</p>
      <p className="mt-3 text-[11px] font-semibold uppercase tracking-[0.12em] text-faint">
        {ENTER_NAV_COPY}
      </p>
      <ul className="mt-2 flex flex-col gap-2">
        {holdings.map((holding) => (
          <li key={holding.key} className="flex flex-wrap items-center gap-3">
            <label
              className="min-w-[5rem] font-mono text-sm text-ink"
              htmlFor={`nav-${holding.key}`}
            >
              {holding.ticker || "Holding"}
            </label>
            <div className="relative w-[10rem]">
              <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-faint">
                $
              </span>
              <input
                id={`nav-${holding.key}`}
                inputMode="decimal"
                min={0.01}
                step={0.01}
                placeholder="NAV / share"
                defaultValue={
                  holding.nav != null && holding.nav > 0
                    ? String(holding.nav)
                    : ""
                }
                onBlur={(event) => {
                  const parsed = Number(event.target.value.replace(/[$,\s]/g, ""));
                  onNavChange(holding.key, parsed > 0 ? parsed : null);
                }}
                className="h-10 w-full rounded-md border border-line bg-surface pl-7 pr-3 font-mono text-sm text-ink"
              />
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
