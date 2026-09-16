"use client";

import { useEffect, useState } from "react";
import { CONTACT_EMAIL } from "@/lib/copy";
import { ManageBillingButton } from "@/components/ManageBillingButton";
import {
  ACCOUNT_EMAIL_LABEL,
  ACCOUNT_PASSWORD_HINT,
  ACCOUNT_PASSWORD_LABEL,
  ACCOUNT_SIGN_IN,
  ACCOUNT_SIGN_OUT,
  ACCOUNT_SIGN_UP,
  ACCOUNT_STRIPE_RESERVE,
} from "@/lib/copy";
import {
  fetchAccountMe,
  signInAccountClient,
  signOutAccountClient,
  signUpAccountClient,
} from "@/lib/account/client";
import type { PublicAccount } from "@/lib/account/store";
import { BILLING_PLAN_LABEL, BILLING_STUB_NOTE } from "@/lib/stripe/billing-copy";

const inputClass =
  "mt-1.5 h-11 w-full rounded-md border border-line bg-surface px-3 text-sm text-ink placeholder:text-faint";
const buttonClass =
  "inline-flex h-11 items-center justify-center rounded-md border border-line px-4 text-sm text-ink hover:border-line-strong disabled:opacity-50";
const primaryClass =
  "inline-flex h-11 items-center justify-center rounded-md bg-accent px-4 text-sm font-medium text-white hover:bg-accent-hover disabled:opacity-50";

export function AccountPanel({ compact = false }: { compact?: boolean }) {
  const [account, setAccount] = useState<PublicAccount | null | undefined>(
    undefined,
  );
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    void fetchAccountMe()
      .then((next) => {
        if (!cancelled) setAccount(next);
      })
      .catch(() => {
        if (!cancelled) setAccount(null);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function submit(kind: "signin" | "signup") {
    setBusy(true);
    setError(null);
    try {
      const next =
        kind === "signup"
          ? await signUpAccountClient(email, password)
          : await signInAccountClient(email, password);
      setAccount(next);
      setPassword("");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Couldn’t complete that.");
    } finally {
      setBusy(false);
    }
  }

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
          <button type="button" className={buttonClass} disabled={busy} onClick={() => void signOut()}>
            {ACCOUNT_SIGN_OUT}
          </button>
        </div>
      ) : (
        <form
          className="space-y-3"
          onSubmit={(event) => {
            event.preventDefault();
            void submit("signin");
          }}
        >
          <label className="block text-sm text-ink">
            {ACCOUNT_EMAIL_LABEL}
            <input
              className={inputClass}
              type="email"
              autoComplete="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              disabled={busy}
            />
          </label>
          <label className="block text-sm text-ink">
            {ACCOUNT_PASSWORD_LABEL}
            <input
              className={inputClass}
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              disabled={busy}
            />
          </label>
          <p className="text-xs text-faint">{ACCOUNT_PASSWORD_HINT}</p>
          {error ? (
            <p className="text-sm text-muted" role="alert">
              {error}
            </p>
          ) : null}
          <div className="flex flex-col gap-2 sm:flex-row">
            <button type="submit" className={primaryClass} disabled={busy}>
              {ACCOUNT_SIGN_IN}
            </button>
            <button
              type="button"
              className={buttonClass}
              disabled={busy}
              onClick={() => void submit("signup")}
            >
              {ACCOUNT_SIGN_UP}
            </button>
          </div>
        </form>
      )}

      <div>
        <p className="text-sm text-ink">Plan · {BILLING_PLAN_LABEL}</p>
        <ManageBillingButton />
        <p className="mt-2 text-xs leading-relaxed text-faint">{BILLING_STUB_NOTE}</p>
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
