"use client";

import { Disclaimer } from "@/components/Disclaimer";
import { COPY } from "@/lib/copy";

export function PaywallDialog({
  open,
  remaining,
  onClose,
  onUnlock,
}: {
  open: boolean;
  remaining: number;
  onClose: () => void;
  onUnlock: () => void;
}) {
  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-ink/40 px-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="paywall-heading"
    >
      <div className="w-full max-w-md rounded-lg border border-line bg-surface p-6 shadow-xl">
        <h2
          id="paywall-heading"
          className="font-serif text-2xl tracking-tight text-ink"
        >
          {COPY.paywallHeadline}
        </h2>
        <p className="mt-3 text-sm leading-relaxed text-muted">
          {COPY.paywallBody}
        </p>
        <p className="mt-2 text-sm font-medium text-ink">{COPY.paywallPrice}</p>
        <Disclaimer className="mt-4 text-xs leading-relaxed text-muted" />
        <div className="mt-5 flex flex-col gap-2 sm:flex-row">
          <button
            type="button"
            onClick={onUnlock}
            className="inline-flex h-11 flex-1 items-center justify-center rounded-md bg-accent px-4 text-sm font-medium text-white hover:bg-accent-hover"
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
