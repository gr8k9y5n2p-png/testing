"use client";

import { AccountAuthForm } from "@/components/AccountAuthForm";
import { useAccountSession } from "@/components/AccountSession";
import {
  ACCOUNT_HOMEPAGE_LOGIN_DETAIL,
  ACCOUNT_HOMEPAGE_LOGIN_TITLE,
} from "@/lib/copy";

export function HomepageLoginPanel() {
  const { account, setAccount } = useAccountSession();

  if (account !== null) return null;

  return (
    <aside
      aria-label="Account sign in"
      className="rounded-lg border border-line bg-surface p-5 shadow-[0_1px_2px_rgba(26,29,26,0.04)]"
    >
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
    </aside>
  );
}
