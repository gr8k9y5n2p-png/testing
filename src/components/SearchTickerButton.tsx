"use client";

import type { MouseEvent, ReactNode } from "react";
import type { FundEstimateView } from "@/data/types";
import { normalizeTicker } from "@/lib/illustrate/fund-history";

/** Search-page ticker/name control: select into FundPicker, never /compare. */
export function SearchTickerButton({
  fund,
  onSelect,
  className = "",
  children,
}: {
  fund: FundEstimateView;
  onSelect?: (fund: FundEstimateView) => void;
  className?: string;
  children?: ReactNode;
}) {
  const label = normalizeTicker(fund.ticker);
  if (!label) return null;

  const content = children ?? label;
  if (!onSelect) {
    return <span className={className}>{content}</span>;
  }

  function onClick(event: MouseEvent<HTMLButtonElement>) {
    event.stopPropagation();
    onSelect?.(fund);
  }

  return (
    <button
      type="button"
      className={`rounded-sm text-left text-ink underline-offset-2 hover:underline ${className}`}
      aria-label={`Search ${label}`}
      onClick={onClick}
    >
      {content}
    </button>
  );
}
