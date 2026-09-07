export function PageIntro({ fundCount }: { fundCount: number }) {
  return (
    <section className="mt-8 mb-8 max-w-3xl">
      <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-teal">
        Year-end tax planning workspace
      </p>
      <h1 className="mt-2 font-serif text-3xl tracking-tight text-navy sm:text-[2.15rem]">
        Estimated taxable distributions
      </h1>
      <p className="mt-3 max-w-2xl text-[15px] leading-relaxed text-muted">
        Search across fund families for published year-end estimates, compare
        payouts with category peers, and flag outliers before they reach client
        accounts. {fundCount} sample funds are loaded for this template.
      </p>
    </section>
  );
}
