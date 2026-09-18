"use client";

import { useState } from "react";
import { useAccountSession } from "@/components/AccountSession";
import { useBilling } from "@/components/BillingProvider";
import {
  BILLING_NOT_CONFIGURED,
  BILLING_SIGN_IN,
  MANAGE_BILLING_LABEL,
  UNLOCK_BILLING_LABEL,
} from "@/lib/stripe/billing-copy";

export function ManageBillingButton() {
  const { account } = useAccountSession();
  const billing = useBilling();
  const [busy, setBusy] = useState(false);
  const [detail, setDetail] = useState<string | null>(null);
  const label = billing.subscribed ? MANAGE_BILLING_LABEL : UNLOCK_BILLING_LABEL;

  async function onClick() {
    setBusy(true);
    setDetail(null);
    const result = await billing.manageBilling();
    if (result.url) return;
    if (!account) {
      setDetail(BILLING_SIGN_IN);
    } else if (!billing.configured) {
      setDetail(BILLING_NOT_CONFIGURED);
    } else {
      setDetail(result.detail || BILLING_NOT_CONFIGURED);
    }
    setBusy(false);
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
    </div>
  );
}
