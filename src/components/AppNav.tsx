"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const TABS = [
  { href: "/", label: "Search", match: (path: string) => path === "/" },
  {
    href: "/compare",
    label: "Compare",
    match: (path: string) => path === "/compare",
  },
  {
    href: "/portfolio",
    label: "Portfolios",
    match: (path: string) => path === "/portfolio",
  },
] as const;

export function AppNav() {
  const pathname = usePathname();

  return (
    <nav aria-label="Primary" className="flex items-center gap-1">
      {TABS.map((tab) => {
        const active = tab.match(pathname);
        return (
          <Link
            key={tab.href}
            href={tab.href}
            aria-current={active ? "page" : undefined}
            className={`inline-flex h-9 items-center rounded-md px-3 text-sm ${
              active
                ? "bg-accent-soft font-medium text-ink"
                : "text-muted hover:bg-notice hover:text-ink"
            }`}
          >
            {tab.label}
          </Link>
        );
      })}
    </nav>
  );
}
