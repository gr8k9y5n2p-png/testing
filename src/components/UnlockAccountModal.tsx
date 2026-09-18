"use client";

import { useCallback, useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { AccountAuthForm } from "@/components/AccountAuthForm";
import { useAccountSession } from "@/components/AccountSession";
import { useBilling } from "@/components/BillingProvider";
import type { PublicAccount } from "@/lib/account/store";
import {
  ACCOUNT_SIGN_IN,
  ACCOUNT_SIGN_UP,
  ACCOUNT_UNLOCK_DETAIL,
  COPY,
  SAVED_ASSET_CANCEL,
} from "@/lib/copy";
import { BILLING_NOT_CONFIGURED } from "@/lib/stripe/billing-copy";
import { unlockCtaStatus } from "@/lib/stripe/unlock-cta";

export function useUnlockAccountFlow() {
  const billing = useBilling();
  const { account, setAccount } = useAccountSession();
  const [modalOpen, setModalOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [detail, setDetail] = useState<string | null>(null);
  const signedIn = Boolean(account) || billing.signedIn;

  const startOrCheckout = useCallback(async () => {
    setBusy(true);
    setDetail(null);
    try {
      if (!signedIn) {
        setModalOpen(true);
        return;
      }
      const result = await billing.unlock();
      const status = unlockCtaStatus(result, true);
      if (status.kind === "redirect") return;
      setDetail(status.detail);
      if (status.kind === "sign_in") setModalOpen(true);
    } catch (caught) {
      setDetail(
        caught instanceof Error ? caught.message : BILLING_NOT_CONFIGURED,
      );
    } finally {
      setBusy(false);
    }
  }, [billing, signedIn]);

  const continueAfterAuth = useCallback(
    async (next: PublicAccount) => {
      setAccount(next);
      setBusy(true);
      try {
        const result = await billing.unlock();
        const status = unlockCtaStatus(result, true);
        if (status.kind === "redirect") return;
        setDetail(status.detail);
      } catch (caught) {
        setDetail(
          caught instanceof Error ? caught.message : BILLING_NOT_CONFIGURED,
        );
      } finally {
        setBusy(false);
        setModalOpen(false);
      }
    },
    [billing, setAccount],
  );

  return {
    modalOpen,
    setModalOpen,
    busy,
    detail,
    signedIn,
    startOrCheckout,
    continueAfterAuth,
  };
}

export function UnlockAccountModal({
  open,
  onClose,
  onAuthenticated,
}: {
  open: boolean;
  onClose: () => void;
  onAuthenticated: (account: PublicAccount) => void | Promise<void>;
}) {
  const [action, setAction] = useState<"signin" | "signup">("signup");

  useEffect(() => {
    if (!open) {
      setAction("signup");
      return;
    }
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [open, onClose]);

  if (!open) return null;

  const dialog = (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-ink/40 px-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="unlock-account-heading"
      onClick={onClose}
    >
      <div
        className="w-full max-w-md rounded-lg border border-line bg-surface p-6 shadow-xl"
        onClick={(event) => event.stopPropagation()}
      >
        <h2
          id="unlock-account-heading"
          className="font-serif text-2xl tracking-tight text-ink"
        >
          {action === "signup" ? ACCOUNT_SIGN_UP : ACCOUNT_SIGN_IN}
        </h2>
        <p className="mt-2 text-sm font-medium text-ink">{COPY.paywallPrice}</p>
        <p className="mt-2 text-sm leading-relaxed text-muted">
          {ACCOUNT_UNLOCK_DETAIL}
        </p>
        <div className="mt-4">
          <AccountAuthForm
            variant="unlock"
            initialAction="signup"
            onActionChange={setAction}
            onSignedIn={(next) => {
              void onAuthenticated(next);
            }}
          />
        </div>
        <button
          type="button"
          onClick={onClose}
          className="mt-4 text-xs text-faint underline decoration-line underline-offset-2 hover:decoration-ink"
        >
          {SAVED_ASSET_CANCEL}
        </button>
      </div>
    </div>
  );

  if (typeof document === "undefined") return dialog;
  return createPortal(dialog, document.body);
}
