import { LISTS_UNLOCK_PREVIEW_ALT } from "@/lib/copy";

/**
 * Lists Unlock Access underlay.
 * Ticker chips and the ticker column are strongly blurred so symbols are
 * not readable. Table headers stay sharp, L→R: NAV · Estimated $
 * Distribution/share · Distribution % of NAV · LTCG · STCG · Ordinary ·
 * QDI · Announced Date · Record Date · Ex-Date.
 * Swap `LISTS_UNLOCK_PREVIEW_SRC` (or pass `src`) if the asset path changes.
 */
export const LISTS_UNLOCK_PREVIEW_SRC = "/marketing/lists-unlock-preview.png";
export const LISTS_UNLOCK_PREVIEW_WEBP = "/marketing/lists-unlock-preview.webp";
export const LISTS_UNLOCK_PREVIEW_SRC_2X =
  "/marketing/lists-unlock-preview@2x.png";

export function ListsUnlockPreview({
  src = LISTS_UNLOCK_PREVIEW_SRC,
  className = "",
}: {
  src?: string;
  className?: string;
}) {
  const swapped = src !== LISTS_UNLOCK_PREVIEW_SRC;
  return (
    <div className={`overflow-hidden rounded-md border border-line bg-paper ${className}`}>
      {swapped ? (
        <img
          src={src}
          alt={LISTS_UNLOCK_PREVIEW_ALT}
          width={1600}
          height={700}
          className="h-auto w-full"
        />
      ) : (
        <picture>
          <source type="image/webp" srcSet={LISTS_UNLOCK_PREVIEW_WEBP} />
          <img
            src={LISTS_UNLOCK_PREVIEW_SRC}
            srcSet={`${LISTS_UNLOCK_PREVIEW_SRC} 1x, ${LISTS_UNLOCK_PREVIEW_SRC_2X} 2x`}
            alt={LISTS_UNLOCK_PREVIEW_ALT}
            width={1600}
            height={700}
            className="h-auto w-full"
          />
        </picture>
      )}
    </div>
  );
}
