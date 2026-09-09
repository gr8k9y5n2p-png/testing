import { COPY } from "@/lib/copy";

/** Compact line under charts and modules. */
export function CompactDisclaimer({ className }: { className?: string }) {
  return (
    <p className={className ?? "text-[10px] leading-relaxed text-faint"}>
      {COPY.compactDisclaimer}
    </p>
  );
}
