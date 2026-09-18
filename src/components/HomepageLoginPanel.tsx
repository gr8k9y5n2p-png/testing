"use client";

import { AccountAuthForm } from "@/components/AccountAuthForm";
import { useAccountSession } from "@/components/AccountSession";
import { useBilling } from "@/components/BillingProvider";
import { UnlockAccountModal, useUnlockAccountFlow } from "@/components/UnlockAccountModal";
import {
  ACCOUNT_HOMEPAGE_LOGIN_DETAIL,
  ACCOUNT_HOMEPAGE_LOGIN_TITLE,
  HOMEPAGE_UNLOCK_ACCESS,
} from "@/lib/copy";
import { UNLOCK_BILLING_LABEL } from "@/lib/stripe/billing-copy";

export function HomepageLoginPanel() {
  const { account, setAccount } = useAccountSession();
  const billing = useBilling();
  const {
    modalOpen,
    setModalOpen,
    busy,
    detail,
    startOrCheckout,
    continueAfterAuth,
  } = useUnlockAccountFlow();

  if (account === undefined) return null;

  const showLogin = account === null;
  const hideUnlock = billing.subscribed || billing.unlimited;
  const showUnlock = !hideUnlock;

  if (!showLogin && !showUnlock) return null;

  return (
    <aside
      id="account"
      aria-label={showLogin ? "Account sign in" : "Unlock full access"}
      className="rounded-lg border border-line bg-surface p-5 shadow-[0_1px_2px_rgba(26,29,26,0.04)]"
    >
      {showLogin ? (
        <>
          <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-muted">
            Account
          </p>
          <h2 className="mt-1 font-serif text-2xl tracking-tight text-ink">
            {ACCOUNT_HOMEPAGE_LOGIN_TITLE}
          </h2>
          <p className="mt-2 text-sm leading-relaxed text-muted">
            {ACCOUNT_HOMEPAGE_LOGIN_DETAIL}
          </p>
          <div className="mt-4">
            <AccountAuthForm layout="homepage" onSignedIn={setAccount} />
          </div>
        </>
      ) : null}
      {showUnlock ? (
        <div className={showLogin ? "mt-5 border-t border-line pt-4" : undefined}>
          <button
            type="button"
            disabled={busy}
            onClick={() => {
              void startOrCheckout();
            }}
            className="inline-flex h-11 w-full items-center justify-center rounded-md bg-accent px-4 text-sm font-medium text-white hover:bg-accent-hover disabled:opacity-50"
          >
            {showLogin ? HOMEPAGE_UNLOCK_ACCESS : UNLOCK_BILLING_LABEL}
          </button>
          {detail ? (
            <p className="mt-2 text-xs text-muted" role="status">
              {detail}
            </p>
          ) : null}
        </div>
      ) : null}
      <UnlockAccountModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onAuthenticated={continueAfterAuth}
      />
    </aside>
  );
}
