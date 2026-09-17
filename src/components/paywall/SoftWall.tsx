"use client";

import { Disclaimer } from "@/components/Disclaimer";
import { useBilling } from "@/components/BillingProvider";
import { COPY } from "@/lib/copy";
import { BILLING_NOT_CONFIGURED, BILLING_SIGN_IN } from "@/lib/stripe/billing-copy";
import { useState, type ReactNode } from "react";

export function SoftWall({
  active,
  surface,
  children,
  className = "",
}: {
  active: boolean;
  surface: "search" | "compare" | "portfolio";
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={`relative ${className}`}>
      <div
        className={active ? "pointer-events-none select-none blur-sm" : undefined}
        aria-hidden={active || undefined}
      >
        {children}
      </div>
      {active ? <SoftWallCta surface={surface} /> : null}
    </div>
  );
}

export function SoftWallCta({
  surface,
}: {
  surface: "search" | "compare" | "portfolio";
}) {
  const billing = useBilling();
  const [busy, setBusy] = useState(false);
  const [detail, setDetail] = useState<string | null>(null);

  const limitCopy =
    surface === "search"
      ? "You’ve used 10 free fund searches."
      : surface === "compare"
        ? "You’ve used 3 free compare reports."
        : "You’ve used 3 free portfolio reviews.";

  async function unlock() {
    setBusy(true);
    setDetail(null);
    const result = await billing.unlock();
    if (result.url) return;
    if (result.needsAccount || !billing.signedIn) {
      setDetail(BILLING_SIGN_IN);
    } else {
      setDetail(result.detail || BILLING_NOT_CONFIGURED);
    }
    setBusy(false);
  }

  return (
    <div className="absolute inset-0 z-10 flex items-center justify-center bg-paper/45 px-4 py-8">
      <div
        className="w-full max-w-md rounded-lg border border-line bg-surface p-6 shadow-xl"
        role="region"
        aria-label="Unlock Aftertax"
      >
        <h2 className="font-serif text-2xl tracking-tight text-ink">
          {COPY.paywallHeadline}
        </h2>
        <p className="mt-3 text-sm leading-relaxed text-muted">
          {limitCopy} {COPY.paywallBody}
        </p>
        <p className="mt-2 text-sm font-medium text-ink">{COPY.paywallPrice}</p>
        {!billing.configured ? (
          <p className="mt-2 text-xs text-muted">{BILLING_NOT_CONFIGURED}</p>
        ) : null}
        {detail ? (
          <p className="mt-2 text-xs text-muted" role="status">
            {detail}
          </p>
        ) : null}
        <Disclaimer className="mt-4 text-xs leading-relaxed text-muted" />
        <button
          type="button"
          disabled={busy}
          onClick={() => {
            void unlock();
          }}
          className="mt-5 inline-flex h-11 w-full items-center justify-center rounded-md bg-accent px-4 text-sm font-medium text-white hover:bg-accent-hover disabled:opacity-50"
        >
          {COPY.paywallCta}
        </button>
      </div>
    </div>
  );
}
