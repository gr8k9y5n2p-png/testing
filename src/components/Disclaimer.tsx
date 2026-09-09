import { COPY } from "@/lib/copy";

/** Primary product disclaimer. Show near dollar results, the paywall, and the footer. */
export function Disclaimer({ className }: { className?: string }) {
  return (
    <p className={className ?? "text-xs leading-relaxed text-muted"}>
      {COPY.disclaimer}
    </p>
  );
}
