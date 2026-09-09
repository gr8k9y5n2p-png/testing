import type { ReactNode } from "react";
import Link from "next/link";
import { compareTickersPath } from "@/lib/illustrate/compare-workspace";
import { normalizeTicker } from "@/lib/illustrate/fund-history";

export function CompareTickerLink({
  ticker,
  className = "",
  children,
}: {
  ticker: string;
  className?: string;
  children?: ReactNode;
}) {
  const label = normalizeTicker(ticker);
  if (!label) return null;

  return (
    <Link
      href={compareTickersPath([label])}
      className={`rounded-sm text-ink underline-offset-2 hover:underline ${className}`}
      aria-label={`Compare ${label}`}
    >
      {children ?? label}
    </Link>
  );
}
