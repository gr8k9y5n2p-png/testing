"use client";

import { CONTACT_EMAIL } from "@/lib/copy";
import { ManageBillingButton } from "@/components/ManageBillingButton";
import { AccountAuthForm } from "@/components/AccountAuthForm";
import { useAccountSession } from "@/components/AccountSession";
import {
  ACCOUNT_SIGN_OUT,
  ACCOUNT_STRIPE_RESERVE,
} from "@/lib/copy";
import { signOutAccountClient } from "@/lib/account/client";
import {
  BILLING_CANCEL_NOTE,
  BILLING_NOT_CONFIGURED,
  BILLING_PLAN_LABEL,
} from "@/lib/stripe/billing-copy";
import { useBilling } from "@/components/BillingProvider";
import { useState } from "react";

const buttonClass =
  "inline-flex h-11 items-center justify-center rounded-md border border-line px-4 text-sm text-ink hover:border-line-strong disabled:opacity-50";

export function AccountPanel({ compact = false }: { compact?: boolean }) {
  const { account, setAccount } = useAccountSession();
  const billing = useBilling();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function signOut() {
    setBusy(true);
    setError(null);
    try {
      await signOutAccountClient();
      setAccount(null);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Couldn’t complete that.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className={compact ? "space-y-4" : "space-y-6"}>
      <div>
        <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-muted">
          Account
        </p>
        {account ? (
          <p className="mt-1 text-sm text-ink">{account.email}</p>
        ) : (
          <p className="mt-1 text-sm text-muted">Private beta</p>
        )}
        <p className="mt-2 text-xs leading-relaxed text-faint">
          {ACCOUNT_STRIPE_RESERVE}
        </p>
      </div>

      {account === undefined ? (
        <p className="text-sm text-muted">Loading…</p>
      ) : account ? (
        <div className="space-y-3">
          {error ? (
            <p className="text-sm text-muted" role="alert">
              {error}
            </p>
          ) : null}
          <button type="button" className={buttonClass} disabled={busy} onClick={() => void signOut()}>
            {ACCOUNT_SIGN_OUT}
          </button>
        </div>
      ) : (
        <AccountAuthForm onSignedIn={setAccount} />
      )}

      <div>
        <p className="text-sm text-ink">
          Plan · {BILLING_PLAN_LABEL}
          {billing.subscribed ? " · active" : ""}
          {billing.entitlement.cancelAtPeriodEnd ? " · cancels at period end" : ""}
        </p>
        <ManageBillingButton />
        <p className="mt-2 text-xs leading-relaxed text-faint">
          {billing.configured ? BILLING_CANCEL_NOTE : BILLING_NOT_CONFIGURED}
        </p>
      </div>

      <p className="border-t border-line pt-4 text-sm">
        <a
          href={`mailto:${CONTACT_EMAIL}`}
          className="text-ink underline decoration-line underline-offset-2 hover:decoration-ink"
        >
          Contact
        </a>
      </p>
    </div>
  );
}
