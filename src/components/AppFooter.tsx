import Link from "next/link";
import { CONTACT_EMAIL, COPY, HOST } from "@/lib/copy";

const FOOTER_LINKS = [
  { href: "/terms", label: "Terms" },
  { href: "/privacy", label: "Privacy" },
  { href: `mailto:${CONTACT_EMAIL}`, label: "Contact", external: true },
] as const;

export function AppFooter() {
  return (
    <footer className="border-t border-line bg-surface">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-4 px-4 py-6 sm:px-6 lg:px-8">
        <p className="max-w-3xl text-xs leading-relaxed text-muted">
          {COPY.disclaimer}
        </p>
        <div className="flex flex-col gap-3 text-xs text-muted sm:flex-row sm:items-center sm:justify-between">
          <p>Aftertax · {HOST}</p>
          <nav aria-label="Legal" className="flex flex-wrap items-center gap-x-4 gap-y-2">
            {FOOTER_LINKS.map((link) =>
              "external" in link && link.external ? (
                <a
                  key={link.href}
                  href={link.href}
                  className="hover:text-ink"
                >
                  {link.label}
                </a>
              ) : (
                <Link key={link.href} href={link.href} className="hover:text-ink">
                  {link.label}
                </Link>
              ),
            )}
          </nav>
        </div>
      </div>
    </footer>
  );
}
