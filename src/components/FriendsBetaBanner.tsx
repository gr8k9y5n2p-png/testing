import { CONTACT_EMAIL, COPY } from "@/lib/copy";

export function FriendsBetaBanner() {
  const [before, after] = COPY.betaBanner.split(CONTACT_EMAIL);

  return (
    <div
      data-print-hide
      className="border-b border-line bg-notice"
    >
      <p className="mx-auto max-w-7xl px-4 py-2 text-[11px] leading-relaxed text-muted sm:px-6 lg:px-8">
        {before}
        <a
          href={`mailto:${CONTACT_EMAIL}`}
          className="underline decoration-line underline-offset-2 hover:text-ink"
        >
          {CONTACT_EMAIL}
        </a>
        {after}
      </p>
    </div>
  );
}
