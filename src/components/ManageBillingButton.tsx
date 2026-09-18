"use client";

import { useState } from "react";
import { useAccountSession } from "@/components/AccountSession";
import { useBilling } from "@/components/BillingProvider";
import { ACCOUNT_SIGN_IN } from "@/lib/copy";
import {
  BILLING_NOT_CONFIGURED,
  MANAGE_BILLING_LABEL,
  UNLOCK_BILLING_LABEL,
} from "@/lib/stripe/billing-copy";
import {
  ACCOUNT_LOGIN_HREF,
  HOMEPAGE_LOGIN_HREF,
  unlockCtaStatus,
} from "@/lib/stripe/unlock-cta";
import Link from "next/link";

export function ManageBillingButton() {
  const { account } = useAccountSession();
  const billing = useBilling();
  const [busy, setBusy] = useState(false);
  const [detail, setDetail] = useState<string | null>(null);
  const [needsLogin, setNeedsLogin] = useState(false);
  const label = billing.subscribed ? MANAGE_BILLING_LABEL : UNLOCK_BILLING_LABEL;

  async function onClick() {
    setBusy(true);
    setDetail(null);
    setNeedsLogin(false);
    try {
      const result = await billing.manageBilling();
      const status = unlockCtaStatus(result, Boolean(account));
      if (status.kind === "redirect") return;
      setDetail(status.detail);
      setNeedsLogin(status.kind === "sign_in");
    } catch (caught) {
      setDetail(
        caught instanceof Error ? caught.message : BILLING_NOT_CONFIGURED,
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <button
        type="button"
        disabled={busy}
        onClick={() => {
          void onClick();
        }}
        className="mt-3 inline-flex h-9 items-center rounded-md border border-line bg-notice px-3 text-sm text-ink hover:border-line-strong disabled:opacity-50"
      >
        {label}
      </button>
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
    </div>
  );
}
