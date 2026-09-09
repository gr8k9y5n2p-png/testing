import Link from "next/link";
import { CONTACT_EMAIL } from "@/lib/copy";
import {
  BILLING_PLAN_LABEL,
  BILLING_STUB_NOTE,
  MANAGE_BILLING_LABEL,
} from "@/lib/stripe/billing";

export function AccountPanel({ compact = false }: { compact?: boolean }) {
  return (
    <div className={compact ? "space-y-4" : "space-y-6"}>
      <div>
        <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-muted">
          Account
        </p>
        <p className="mt-1 text-sm text-muted">Private beta</p>
      </div>

      <nav aria-label="Account" className="flex flex-col gap-1 text-sm">
        <Link href="/terms" className="rounded-md px-2 py-1.5 text-ink hover:bg-notice">
          Terms
        </Link>
        <Link href="/privacy" className="rounded-md px-2 py-1.5 text-ink hover:bg-notice">
          Privacy
        </Link>
        <a
          href={`mailto:${CONTACT_EMAIL}`}
          className="rounded-md px-2 py-1.5 text-ink hover:bg-notice"
        >
          Contact
        </a>
      </nav>

      <div className="border-t border-line pt-4">
        <p className="text-sm text-ink">Plan · {BILLING_PLAN_LABEL}</p>
        <p className="mt-2 text-sm text-muted">{MANAGE_BILLING_LABEL}</p>
        <p className="mt-1 text-xs leading-relaxed text-faint">{BILLING_STUB_NOTE}</p>
      </div>
    </div>
  );
}
