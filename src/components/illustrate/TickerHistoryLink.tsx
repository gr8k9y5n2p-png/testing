import type { ReactNode } from "react";
import Link from "next/link";
import { fundHistoryPath, normalizeTicker } from "@/lib/illustrate/fund-history";

export function TickerHistoryLink({
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
      href={fundHistoryPath(label)}
      className={`rounded-sm text-ink underline-offset-2 hover:underline ${className}`}
      aria-label={`Open ${label} historical distributions and upcoming estimates`}
    >
      {children ?? label}
    </Link>
  );
}
