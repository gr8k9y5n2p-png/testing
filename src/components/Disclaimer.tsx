import { COPY } from "@/lib/copy";

/** QA-final disclaimer. Show near every dollar result and the paywall. */
export function Disclaimer({ className }: { className?: string }) {
  return (
    <p className={className ?? "text-xs leading-relaxed text-muted"}>
      {COPY.disclaimer}
    </p>
  );
}
