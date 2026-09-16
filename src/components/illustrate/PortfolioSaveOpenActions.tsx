"use client";

import type { MutableRefObject } from "react";
import { SavedAssetActions } from "@/components/saved-assets/SavedAssetActions";
import type { PortfolioCompareHandle } from "@/components/illustrate/PortfolioCompare";
import {
  portfolioBooksAreSavable,
  portfolioSavePayloadFromBooks,
} from "@/lib/illustrate/portfolio-save-open";
import { parsePortfolioBooksPayload } from "@/lib/saved-assets/payloads";

/** Modules Save/Open toolbar for PortfolioCompare via the shared #190 contract. */
export function PortfolioSaveOpenActions({
  booksApiRef,
  onNotice,
}: {
  booksApiRef: MutableRefObject<PortfolioCompareHandle | null>;
  onNotice?: (message: string) => void;
}) {
  return (
    <SavedAssetActions
      type="portfolio"
      canSave={() => portfolioBooksAreSavable(booksApiRef.current?.getBooks())}
      getPayload={() =>
        portfolioSavePayloadFromBooks(booksApiRef.current?.getBooks())
      }
      onOpen={(asset) => {
        const books = parsePortfolioBooksPayload(asset.payload);
        if (!books) return;
        booksApiRef.current?.setBooks(books);
      }}
      onNotice={onNotice}
    />
  );
}
