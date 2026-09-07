import { COPY } from "@/lib/copy";

export function PageIntro({ fundCount }: { fundCount: number }) {
  return (
    <section className="mt-8 mb-8 max-w-3xl">
      <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-muted">
        Aftertax
      </p>
      <h1 className="mt-2 font-serif text-3xl tracking-tight text-ink sm:text-[2.15rem]">
        {COPY.hero}
      </h1>
      <p className="mt-3 max-w-2xl text-[15px] leading-relaxed text-muted">
        {COPY.sub} {fundCount} sample funds are loaded for this template.
      </p>
    </section>
  );
}
