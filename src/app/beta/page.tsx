import type { Metadata } from "next";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { CONTACT_EMAIL } from "@/lib/copy";
import {
  FRIENDS_BETA_COOKIE,
  friendsBetaPassword,
  isFriendsBetaGateEnabled,
  isFriendsBetaSessionValid,
  safeNextPath,
} from "@/lib/friends-beta";

export const metadata: Metadata = {
  title: "Friends beta — Aftertax",
  description: "Shared password for the Aftertax friends beta.",
  robots: { index: false, follow: false },
};

export const dynamic = "force-dynamic";

export default async function FriendsBetaGatePage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string | string[]; next?: string | string[] }>;
}) {
  if (!isFriendsBetaGateEnabled()) {
    redirect("/");
  }

  const params = await searchParams;
  const next = safeNextPath(
    Array.isArray(params.next) ? params.next[0] : params.next,
  );
  const password = friendsBetaPassword();
  const cookieStore = await cookies();
  const session = cookieStore.get(FRIENDS_BETA_COOKIE)?.value;
  if (password && isFriendsBetaSessionValid(session, password)) {
    redirect(next);
  }

  const error = (Array.isArray(params.error) ? params.error[0] : params.error) === "1";

  return (
    <main className="mx-auto flex w-full max-w-md flex-col px-4 pb-16 pt-10 sm:px-6 lg:px-8">
      <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-muted">
        Friends beta
      </p>
      <h1 className="mt-2 font-serif text-3xl tracking-tight text-ink">
        Aftertax
      </h1>
      <p className="mt-3 text-sm leading-relaxed text-muted">
        Shared password for this private beta. Need access? Email{" "}
        <a
          href={`mailto:${CONTACT_EMAIL}`}
          className="text-accent underline decoration-accent/40 underline-offset-2 hover:decoration-accent"
        >
          {CONTACT_EMAIL}
        </a>
        .
      </p>

      <form
        method="POST"
        action="/api/beta/unlock"
        className="mt-8 rounded-lg border border-line bg-surface p-5 shadow-[0_1px_2px_rgba(26,29,26,0.04)]"
      >
        {next !== "/" ? <input type="hidden" name="next" value={next} /> : null}
        <label className="block">
          <span className="mb-1.5 block text-[11px] font-semibold uppercase tracking-[0.12em] text-faint">
            Password
          </span>
          <input
            name="password"
            type="password"
            autoComplete="current-password"
            required
            autoFocus
            className="h-10 w-full rounded-md border border-line bg-paper px-3 text-sm text-ink"
          />
        </label>
        {error ? (
          <p className="mt-3 text-sm text-tax-more" role="alert">
            Wrong password.
          </p>
        ) : null}
        <button
          type="submit"
          className="mt-4 h-10 w-full rounded-md bg-accent px-3 text-sm text-white hover:bg-accent-hover"
        >
          Enter
        </button>
      </form>
    </main>
  );
}
