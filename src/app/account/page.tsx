import type { Metadata } from "next";
import { AccountPanel } from "@/components/AccountPanel";
import { Disclaimer } from "@/components/Disclaimer";

export const metadata: Metadata = {
  title: "Account — Aftertax",
  description: "Aftertax account, legal links, and billing placeholder.",
  robots: { index: false, follow: false },
};

export default function AccountPage() {
  return (
    <main className="mx-auto w-full max-w-xl px-4 pb-16 pt-8 sm:px-6 lg:px-8">
      <h1 className="font-serif text-3xl tracking-tight text-ink">Account</h1>
      <p className="mt-2 text-sm text-muted">
        Friends beta. Billing stays off until Checkout is enabled.
      </p>
      <div className="mt-8 rounded-lg border border-line bg-surface p-5">
        <AccountPanel />
      </div>
      <Disclaimer className="mt-8 text-xs leading-relaxed text-muted" />
    </main>
  );
}
