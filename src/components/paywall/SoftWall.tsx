"use client";

import Link from "next/link";
import { Disclaimer } from "@/components/Disclaimer";
import { useBilling } from "@/components/BillingProvider";
import { ACCOUNT_SIGN_IN, COPY } from "@/lib/copy";
import {
  BILLING_NOT_CONFIGURED,
  BILLING_SIGN_IN,
} from "@/lib/stripe/billing-copy";
import {
  ACCOUNT_LOGIN_HREF,
  HOMEPAGE_LOGIN_HREF,
  accountLoginHref,
  unlockCtaPreview,
  unlockCtaStatus,
} from "@/lib/stripe/unlock-cta";
import { useEffect, useState, type ReactNode } from "react";

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
  const preview = unlockCtaPreview(billing.signedIn);
  const [busy, setBusy] = useState(false);
  const [detail, setDetail] = useState<string | null>(preview?.detail ?? null);
  const [needsLogin, setNeedsLogin] = useState(preview?.kind === "sign_in");

  useEffect(() => {
    const next = unlockCtaPreview(billing.signedIn);
    if (next) {
      setDetail((current) => current ?? next.detail);
      setNeedsLogin(true);
    } else {
      setNeedsLogin(false);
      setDetail((current) => (current === BILLING_SIGN_IN ? null : current));
    }
  }, [billing.signedIn]);

  const limitCopy =
    surface === "search"
      ? "You’ve used 10 free fund searches."
      : surface === "compare"
        ? "You’ve used 3 free compare reports."
        : "You’ve used 3 free portfolio reviews.";

  async function unlock() {
    setBusy(true);
    try {
      if (!billing.signedIn) {
        const status = unlockCtaStatus(
          { detail: BILLING_SIGN_IN, needsAccount: true },
          false,
        );
        setDetail(status.detail);
        setNeedsLogin(true);
        const pathname =
          typeof window !== "undefined" ? window.location.pathname : "/";
        const href = accountLoginHref(pathname);
        if (href.startsWith("/#") && pathname === "/") {
          const id = href.slice(2);
          document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });
          window.location.hash = id;
        } else {
          window.location.assign(href);
        }
        return;
      }
      const result = await billing.unlock();
      const status = unlockCtaStatus(result, billing.signedIn);
      if (status.kind === "redirect") return;
      setDetail(status.detail);
      setNeedsLogin(status.kind === "sign_in");
    } catch (caught) {
      setDetail(
        caught instanceof Error ? caught.message : BILLING_NOT_CONFIGURED,
      );
      setNeedsLogin(!billing.signedIn);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="absolute inset-0 z-10 flex items-center justify-center bg-paper/45 px-4 py-8">
      <div
        className="w-full max-w-md rounded-lg border border-line bg-surface p-6 shadow-xl"
        role="region"
        aria-label="Unlock full access"
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
        {needsLogin ? (
          <p className="mt-2 text-xs">
            <Link
              href={HOMEPAGE_LOGIN_HREF}
              className="text-ink underline decoration-line underline-offset-2 hover:decoration-ink"
            >
              {ACCOUNT_SIGN_IN}
            </Link>
            {" · "}
            <Link
              href={ACCOUNT_LOGIN_HREF}
              className="text-ink underline decoration-line underline-offset-2 hover:decoration-ink"
            >
              Account
            </Link>
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
