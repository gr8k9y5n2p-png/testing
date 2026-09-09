import { CONTACT_EMAIL } from "@/lib/copy";
import type { LegalDocument } from "@/lib/legal";

function LinkedCopy({ text }: { text: string }) {
  const parts = text.split(CONTACT_EMAIL);
  if (parts.length === 1) return text;
  return (
    <>
      {parts.map((part, index) => (
        <span key={`${part}-${index}`}>
          {index > 0 ? (
            <a
              href={`mailto:${CONTACT_EMAIL}`}
              className="text-accent underline decoration-accent/40 underline-offset-2 hover:decoration-accent"
            >
              {CONTACT_EMAIL}
            </a>
          ) : null}
          {part}
        </span>
      ))}
    </>
  );
}

export function LegalArticle({ document }: { document: LegalDocument }) {
  return (
    <main className="mx-auto w-full max-w-3xl px-4 pb-16 pt-8 sm:px-6 lg:px-8">
      <article>
        <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-muted">
          Aftertax
        </p>
        <h1 className="mt-2 font-serif text-3xl tracking-tight text-ink sm:text-[2.15rem]">
          {document.title}
        </h1>
        <p className="mt-3 text-sm text-muted">
          Last updated {document.lastUpdated}
        </p>
        <p className="mt-1 text-sm text-muted">
          Operator {document.operator} · {document.site}
        </p>

        <div className="mt-8 space-y-5 text-[15px] leading-relaxed text-ink">
          {document.intro.map((paragraph) => (
            <p key={paragraph}>
              <LinkedCopy text={paragraph} />
            </p>
          ))}
        </div>

        <ol className="mt-10 space-y-8">
          {document.sections.map((section) => (
            <li key={section.number} className="list-none">
              <h2 className="font-serif text-xl tracking-tight text-ink">
                <span className="mr-2 text-faint">{section.number}.</span>
                {section.title}
              </h2>
              <div className="mt-3 space-y-3 text-[15px] leading-relaxed text-ink">
                {section.paragraphs.map((paragraph) => (
                  <p key={paragraph}>
                    <LinkedCopy text={paragraph} />
                  </p>
                ))}
                {section.blocks?.map((block) => (
                  <div key={block.title} className="rounded-md border border-line bg-surface px-4 py-3">
                    <h3 className="text-[12px] font-semibold uppercase tracking-[0.12em] text-muted">
                      {block.title}
                    </h3>
                    {block.paragraphs.map((paragraph) => (
                      <p key={paragraph} className="mt-1.5">
                        <LinkedCopy text={paragraph} />
                      </p>
                    ))}
                  </div>
                ))}
              </div>
            </li>
          ))}
        </ol>
      </article>
    </main>
  );
}
