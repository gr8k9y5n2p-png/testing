"use client";

import { Disclaimer } from "@/components/Disclaimer";
import { useBilling } from "@/components/BillingProvider";
import { UnlockAccountModal, useUnlockAccountFlow } from "@/components/UnlockAccountModal";
import { ListsUnlockPreview } from "@/components/lists/ListsUnlockPreview";
import { COPY, LISTS_PAYWALL_LEAD, LISTS_UNLOCK_KICKER } from "@/lib/copy";
import { BILLING_CREATE_ACCOUNT, BILLING_NOT_CONFIGURED } from "@/lib/stripe/billing-copy";
import { unlockCtaPreview } from "@/lib/stripe/unlock-cta";
import { useEffect, useState, type ReactNode } from "react";

export type SoftWallSurface = "search" | "compare" | "portfolio" | "lists";

export function SoftWall({
  active,
  surface,
  children,
  className = "",
}: {
  active: boolean;
  surface: SoftWallSurface;
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
  surface: SoftWallSurface;
}) {
  const billing = useBilling();
  const preview = unlockCtaPreview(billing.signedIn);
  const {
    modalOpen,
    setModalOpen,
    busy,
    detail: flowDetail,
    signedIn,
    startOrCheckout,
    continueAfterAuth,
  } = useUnlockAccountFlow();
  const [detail, setDetail] = useState<string | null>(
    preview?.detail ?? null,
  );

  useEffect(() => {
    const next = unlockCtaPreview(signedIn);
    if (next) {
      setDetail((current) => current ?? next.detail);
    } else {
      setDetail((current) => (current === BILLING_CREATE_ACCOUNT ? null : current));
    }
  }, [signedIn]);

  useEffect(() => {
    if (flowDetail) setDetail(flowDetail);
  }, [flowDetail]);

  const limitCopy =
    surface === "search"
      ? "You’ve used 10 free fund searches."
      : surface === "compare"
        ? "You’ve used 3 free compare reports."
        : surface === "lists"
          ? LISTS_PAYWALL_LEAD
          : "You’ve used 3 free portfolio reviews.";
  const lists = surface === "lists";

  return (
    <div className="absolute inset-0 z-10 flex items-center justify-center bg-paper/45 px-4 py-8">
      <div
        className={`w-full rounded-lg border border-line bg-surface p-6 shadow-xl ${
          lists ? "max-w-xl" : "max-w-md"
        }`}
        role="region"
        aria-label={lists ? LISTS_UNLOCK_KICKER : "Unlock full access"}
      >
        {lists ? (
          <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-faint">
            {LISTS_UNLOCK_KICKER}
          </p>
        ) : null}
        <h2 className={`font-serif text-2xl tracking-tight text-ink ${lists ? "mt-1" : ""}`}>
          {COPY.paywallHeadline}
        </h2>
        <p className="mt-3 text-sm leading-relaxed text-muted">
          {limitCopy} {COPY.paywallBody}
        </p>
        <p className="mt-2 text-sm font-medium text-ink">{COPY.paywallPrice}</p>
        {lists ? <ListsUnlockPreview className="mt-4" /> : null}
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
            void startOrCheckout();
          }}
          className="mt-5 inline-flex h-11 w-full items-center justify-center rounded-md bg-accent px-4 text-sm font-medium text-white hover:bg-accent-hover disabled:opacity-50"
        >
          {COPY.paywallCta}
        </button>
      </div>
      <UnlockAccountModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onAuthenticated={continueAfterAuth}
      />
    </div>
  );
}
