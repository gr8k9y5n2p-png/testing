export function AppHeader() {
  return (
    <header className="border-b border-line bg-navy-deep text-white">
      <div className="mx-auto flex w-full max-w-7xl items-center justify-between gap-4 px-4 py-3.5 sm:px-6 lg:px-8">
        <div className="flex items-center gap-3">
          <div
            aria-hidden="true"
            className="flex h-8 w-8 items-center justify-center rounded-sm border border-white/20 bg-white/5"
          >
            <span className="font-serif text-sm leading-none tracking-tight">
              Dx
            </span>
          </div>
          <div>
            <p className="font-serif text-[15px] leading-tight tracking-tight">
              Distribution Estimates
            </p>
            <p className="text-[11px] uppercase tracking-[0.14em] text-white/55">
              Asset management · advisors
            </p>
          </div>
        </div>
        <p className="hidden text-right text-xs text-white/60 sm:block">
          Estimated taxable distributions
          <span className="mt-0.5 block text-white/40">2026 sample universe</span>
        </p>
      </div>
    </header>
  );
}
