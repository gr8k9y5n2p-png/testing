import type { Metadata } from "next";
import { ResetPasswordForm } from "@/components/ResetPasswordForm";
import { Disclaimer } from "@/components/Disclaimer";

export const metadata: Metadata = {
  title: "Reset password — Aftertax",
  description: "Choose a new Aftertax account password.",
  robots: { index: false, follow: false },
};

export const dynamic = "force-dynamic";

export default async function ResetPasswordPage({
  searchParams,
}: {
  searchParams: Promise<{ token?: string | string[] }>;
}) {
  const params = await searchParams;
  const token = Array.isArray(params.token) ? params.token[0] : params.token;

  return (
    <main className="mx-auto w-full max-w-xl px-4 pb-16 pt-8 sm:px-6 lg:px-8">
      <div className="rounded-lg border border-line bg-surface p-5">
        <ResetPasswordForm token={token ?? ""} />
      </div>
      <Disclaimer className="mt-8 text-xs leading-relaxed text-muted" />
    </main>
  );
}
