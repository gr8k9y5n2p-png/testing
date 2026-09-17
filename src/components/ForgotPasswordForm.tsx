"use client";

import Link from "next/link";
import { useState } from "react";
import {
  ACCOUNT_EMAIL_LABEL,
  ACCOUNT_FORGOT_DETAIL,
  ACCOUNT_FORGOT_SUBMIT,
  ACCOUNT_FORGOT_TITLE,
  ACCOUNT_SIGN_IN,
} from "@/lib/copy";
import { requestPasswordResetClient } from "@/lib/account/client";

const inputClass =
  "mt-1.5 h-11 w-full rounded-md border border-line bg-surface px-3 text-sm text-ink placeholder:text-faint";
const primaryClass =
  "inline-flex h-11 w-full items-center justify-center rounded-md bg-accent px-4 text-sm font-medium text-white hover:bg-accent-hover disabled:opacity-50";

export function ForgotPasswordForm() {
  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [detail, setDetail] = useState<string | null>(null);

  async function submit() {
    setBusy(true);
    setError(null);
    try {
      const result = await requestPasswordResetClient(email);
      setDetail(result.detail);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Couldn’t complete that.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form
      className="space-y-4"
      onSubmit={(event) => {
        event.preventDefault();
        void submit();
      }}
    >
      <div>
        <h1 className="font-serif text-3xl tracking-tight text-ink">
          {ACCOUNT_FORGOT_TITLE}
        </h1>
        <p className="mt-2 text-sm leading-relaxed text-muted">
          {ACCOUNT_FORGOT_DETAIL}
        </p>
      </div>
      {detail ? (
        <p className="text-sm leading-relaxed text-ink" role="status">
          {detail}
        </p>
      ) : (
        <>
          <label className="block text-sm text-ink">
            {ACCOUNT_EMAIL_LABEL}
            <input
              className={inputClass}
              type="email"
              name="account-email"
              autoComplete="username"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              disabled={busy}
              required
            />
          </label>
          {error ? (
            <p className="text-sm text-muted" role="alert">
              {error}
            </p>
          ) : null}
          <button type="submit" className={primaryClass} disabled={busy}>
            {ACCOUNT_FORGOT_SUBMIT}
          </button>
        </>
      )}
      <p className="text-sm">
        <Link
          href="/account"
          className="text-ink underline decoration-line underline-offset-2 hover:decoration-ink"
        >
          {ACCOUNT_SIGN_IN}
        </Link>
      </p>
    </form>
  );
}
