import type { Metadata } from "next";
import { ForgotPasswordForm } from "@/components/ForgotPasswordForm";
import { Disclaimer } from "@/components/Disclaimer";

export const metadata: Metadata = {
  title: "Forgot password — Aftertax",
  description: "Reset your Aftertax account password.",
  robots: { index: false, follow: false },
};

export default function ForgotPasswordPage() {
  return (
    <main className="mx-auto w-full max-w-xl px-4 pb-16 pt-8 sm:px-6 lg:px-8">
      <div className="rounded-lg border border-line bg-surface p-5">
        <ForgotPasswordForm />
      </div>
      <Disclaimer className="mt-8 text-xs leading-relaxed text-muted" />
    </main>
  );
}
