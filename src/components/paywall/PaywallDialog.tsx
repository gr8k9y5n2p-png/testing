"use client";

import { COPY } from "@/lib/copy";

export function PaywallDialog({
  open,
  remaining,
  reason = "limit",
  onClose,
  onUnlock,
}: {
  open: boolean;
  remaining: number;
  reason?: "import" | "limit";
  onClose: () => void;
  onUnlock: () => void;
}) {
  if (!open) return null;

  const body =
    reason === "import"
      ? "Portfolio import and aggregation unlock with Aftertax. See dollar taxable impact across the full book."
      : COPY.paywallBody;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-navy-deep/50 px-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="paywall-heading"
    >
      <div className="w-full max-w-md rounded-lg border border-line bg-surface p-6 shadow-xl">
        <h2
          id="paywall-heading"
          className="font-serif text-2xl tracking-tight text-navy"
        >
          {COPY.paywallHeadline}
        </h2>
        <p className="mt-3 text-sm leading-relaxed text-muted">{body}</p>
        <p className="mt-2 text-sm font-medium text-ink">{COPY.paywallPrice}</p>
        <p className="mt-4 text-xs leading-relaxed text-muted">{COPY.disclaimer}</p>
        <div className="mt-5 flex flex-col gap-2 sm:flex-row">
          <button
            type="button"
            onClick={onUnlock}
            className="inline-flex h-11 flex-1 items-center justify-center rounded-md bg-navy px-4 text-sm font-medium text-white hover:bg-navy-deep"
          >
            {COPY.paywallCta}
          </button>
          {remaining > 0 ? (
            <button
              type="button"
              onClick={onClose}
              className="inline-flex h-11 flex-1 items-center justify-center rounded-md border border-line px-4 text-sm text-ink"
            >
              {COPY.continueFree}
            </button>
          ) : null}
        </div>
        {remaining <= 0 ? (
          <button
            type="button"
            onClick={onClose}
            className="mt-3 text-xs text-faint underline"
          >
            Close
          </button>
        ) : null}
      </div>
    </div>
  );
}
