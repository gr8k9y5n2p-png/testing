"use client";

import Link from "next/link";
import { useState } from "react";
import {
  ACCOUNT_EMAIL_LABEL,
  ACCOUNT_FORGOT_PASSWORD,
  ACCOUNT_HAVE_ACCOUNT,
  ACCOUNT_NEED_ACCOUNT,
  ACCOUNT_PASSWORD_HINT,
  ACCOUNT_PASSWORD_LABEL,
  ACCOUNT_SIGN_IN,
  ACCOUNT_SIGN_UP,
} from "@/lib/copy";
import {
  signInAccountClient,
  signUpAccountClient,
} from "@/lib/account/client";
import type { PublicAccount } from "@/lib/account/store";

const inputClass =
  "mt-1.5 h-11 w-full rounded-md border border-line bg-surface px-3 text-sm text-ink placeholder:text-faint";
const buttonClass =
  "inline-flex h-11 items-center justify-center rounded-md border border-line px-4 text-sm text-ink hover:border-line-strong disabled:opacity-50";
const primaryClass =
  "inline-flex h-11 items-center justify-center rounded-md bg-accent px-4 text-sm font-medium text-white hover:bg-accent-hover disabled:opacity-50";

export function AccountAuthForm({
  onSignedIn,
  layout = "stack",
  variant = "buttons",
  initialAction = "signin",
  onActionChange,
}: {
  onSignedIn: (account: PublicAccount) => void | Promise<void>;
  layout?: "stack" | "homepage";
  variant?: "buttons" | "unlock";
  initialAction?: "signin" | "signup";
  onActionChange?: (action: "signin" | "signup") => void;
}) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [action, setAction] = useState<"signin" | "signup">(initialAction);

  function switchAction(next: "signin" | "signup") {
    setAction(next);
    onActionChange?.(next);
  }

  async function submit(kind: "signin" | "signup") {
    setBusy(true);
    setError(null);
    try {
      const next =
        kind === "signup"
          ? await signUpAccountClient(email, password)
          : await signInAccountClient(email, password);
      setPassword("");
      await onSignedIn(next);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Couldn’t complete that.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form
      className="space-y-3"
      onSubmit={(event) => {
        event.preventDefault();
        void submit(variant === "unlock" ? action : "signin");
      }}
    >
      <label className="block text-sm text-ink">
        {ACCOUNT_EMAIL_LABEL}
        <input
          className={inputClass}
          type="email"
          name="account-email"
          autoComplete="username"
          autoFocus={variant === "unlock"}
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          disabled={busy}
          required
        />
      </label>
      <label className="block text-sm text-ink">
        {ACCOUNT_PASSWORD_LABEL}
        <input
          className={inputClass}
          type="password"
          name="account-password"
          autoComplete={
            variant === "unlock" && action === "signup"
              ? "new-password"
              : "current-password"
          }
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          disabled={busy}
          required
          minLength={8}
        />
      </label>
      <p className="text-xs text-faint">{ACCOUNT_PASSWORD_HINT}</p>
      {error ? (
        <p className="text-sm text-muted" role="alert">
          {error}
        </p>
      ) : null}
      {variant === "unlock" ? (
        <div className="flex flex-col gap-2">
          <button type="submit" className={`${primaryClass} w-full`} disabled={busy}>
            {action === "signup" ? ACCOUNT_SIGN_UP : ACCOUNT_SIGN_IN}
          </button>
          <button
            type="button"
            className="text-sm text-ink underline decoration-line underline-offset-2 hover:decoration-ink disabled:opacity-50"
            disabled={busy}
            onClick={() =>
              switchAction(action === "signup" ? "signin" : "signup")
            }
          >
            {action === "signup" ? ACCOUNT_HAVE_ACCOUNT : ACCOUNT_NEED_ACCOUNT}
          </button>
        </div>
      ) : (
        <div
          className={
            layout === "homepage"
              ? "flex flex-col gap-2"
              : "flex flex-col gap-2 sm:flex-row"
          }
        >
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
      )}
      <p className="text-sm">
        <Link
          href="/account/forgot"
          className="text-ink underline decoration-line underline-offset-2 hover:decoration-ink"
        >
          {ACCOUNT_FORGOT_PASSWORD}
        </Link>
      </p>
    </form>
  );
}
