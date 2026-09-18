/**
 * Placeholder Lists preview for the Unlock Access module.
 * Modules’ final asset is a drop-in path swap — change
 * `LISTS_UNLOCK_PREVIEW_SRC` (or pass `src`) when it lands.
 */
export const LISTS_UNLOCK_PREVIEW_SRC = "/lists-unlock-preview.svg";

export function ListsUnlockPreview({
  src = LISTS_UNLOCK_PREVIEW_SRC,
  className = "",
}: {
  src?: string;
  className?: string;
}) {
  return (
    <div className={`overflow-hidden rounded-md border border-line bg-paper ${className}`}>
      {/* Plain img so a path swap (SVG or PNG) paints without next/image. */}
      <img
        src={src}
        alt="Lists preview — ticker paste, Upcoming-style rows, Save and Open"
        width={800}
        height={480}
        className="h-auto w-full"
      />
    </div>
  );
}
