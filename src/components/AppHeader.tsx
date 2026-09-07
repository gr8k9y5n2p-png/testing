import { HOST } from "@/lib/copy";

export function AppHeader() {
  return (
    <header className="border-b border-line bg-surface">
      <div className="mx-auto flex w-full max-w-7xl items-center justify-between gap-4 px-4 py-3.5 sm:px-6 lg:px-8">
        <div className="flex items-center gap-3">
          <div
            aria-hidden="true"
            className="flex h-8 w-8 items-center justify-center rounded-sm border border-line bg-paper"
          >
            <span className="font-serif text-sm leading-none tracking-tight text-ink">
              A
            </span>
          </div>
          <div>
            <p className="font-serif text-[15px] leading-tight tracking-tight text-ink">
              Aftertax
            </p>
            <p className="text-[11px] uppercase tracking-[0.14em] text-muted">
              Wholesalers · advisors
            </p>
          </div>
        </div>
        <p className="hidden text-right text-xs text-muted sm:block">
          Taxable impact in dollars
          <span className="mt-0.5 block text-faint">{HOST}</span>
        </p>
      </div>
    </header>
  );
}
