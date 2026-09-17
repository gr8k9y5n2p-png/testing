"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useAccountSession } from "@/components/AccountSession";
import {
  ACCOUNT_FORGOT_PASSWORD,
  ACCOUNT_PASSWORD_HINT,
  ACCOUNT_PASSWORD_LABEL,
  ACCOUNT_RESET_MISSING,
  ACCOUNT_RESET_SUBMIT,
  ACCOUNT_RESET_TITLE,
} from "@/lib/copy";
import { resetAccountPasswordClient } from "@/lib/account/client";

const inputClass =
  "mt-1.5 h-11 w-full rounded-md border border-line bg-surface px-3 text-sm text-ink placeholder:text-faint";
const primaryClass =
  "inline-flex h-11 w-full items-center justify-center rounded-md bg-accent px-4 text-sm font-medium text-white hover:bg-accent-hover disabled:opacity-50";

export function ResetPasswordForm({ token }: { token: string }) {
  const router = useRouter();
  const { setAccount } = useAccountSession();
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!token) {
    return (
      <div className="space-y-4">
        <h1 className="font-serif text-3xl tracking-tight text-ink">
          {ACCOUNT_RESET_TITLE}
        </h1>
        <p className="text-sm leading-relaxed text-muted">{ACCOUNT_RESET_MISSING}</p>
        <p className="text-sm">
          <Link
            href="/account/forgot"
            className="text-ink underline decoration-line underline-offset-2 hover:decoration-ink"
          >
            {ACCOUNT_FORGOT_PASSWORD}
          </Link>
        </p>
      </div>
    );
  }

  async function submit() {
    setBusy(true);
    setError(null);
    try {
      const account = await resetAccountPasswordClient(token, password);
      setAccount(account);
      router.replace("/account");
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
          {ACCOUNT_RESET_TITLE}
        </h1>
        <p className="mt-2 text-sm text-faint">{ACCOUNT_PASSWORD_HINT}</p>
      </div>
      <label className="block text-sm text-ink">
        {ACCOUNT_PASSWORD_LABEL}
        <input
          className={inputClass}
          type="password"
          name="account-new-password"
          autoComplete="new-password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          disabled={busy}
          required
          minLength={8}
        />
      </label>
      {error ? (
        <p className="text-sm text-muted" role="alert">
          {error}
        </p>
      ) : null}
      <button type="submit" className={primaryClass} disabled={busy}>
        {ACCOUNT_RESET_SUBMIT}
      </button>
    </form>
  );
}
