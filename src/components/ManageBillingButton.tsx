"use client";

import { useState } from "react";
import { useAccountSession } from "@/components/AccountSession";
import { useBilling } from "@/components/BillingProvider";
import { UnlockAccountModal, useUnlockAccountFlow } from "@/components/UnlockAccountModal";
import {
  BILLING_NOT_CONFIGURED,
  MANAGE_BILLING_LABEL,
  UNLOCK_BILLING_LABEL,
} from "@/lib/stripe/billing-copy";
import { unlockCtaStatus } from "@/lib/stripe/unlock-cta";

export function ManageBillingButton() {
  const { account } = useAccountSession();
  const billing = useBilling();
  const {
    modalOpen,
    setModalOpen,
    busy: unlockBusy,
    detail: unlockDetail,
    startOrCheckout,
    continueAfterAuth,
  } = useUnlockAccountFlow();
  const [portalBusy, setPortalBusy] = useState(false);
  const [portalDetail, setPortalDetail] = useState<string | null>(null);
  const label = billing.subscribed ? MANAGE_BILLING_LABEL : UNLOCK_BILLING_LABEL;
  const busy = unlockBusy || portalBusy;
  const detail = unlockDetail ?? portalDetail;

  async function onClick() {
    if (billing.subscribed) {
      setPortalBusy(true);
      setPortalDetail(null);
      try {
        const result = await billing.manageBilling();
        const status = unlockCtaStatus(result, Boolean(account));
        if (status.kind === "redirect") return;
        setPortalDetail(status.detail);
        if (status.kind === "sign_in") setModalOpen(true);
      } catch (caught) {
        setPortalDetail(
          caught instanceof Error ? caught.message : BILLING_NOT_CONFIGURED,
        );
      } finally {
        setPortalBusy(false);
      }
      return;
    }
    await startOrCheckout();
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
      <UnlockAccountModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onAuthenticated={continueAfterAuth}
      />
    </div>
  );
}
