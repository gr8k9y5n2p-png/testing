/**
 * Friends-beta source chrome for Portfolio + Compare.
 * Live Data API only — never SAMPLE / demo. Mock / localhost fixture /
 * unknown → blank so the eyebrow stays "Aftertax".
 */

export function isLiveDataSource(source?: string | null): boolean {
  return source === "live";
}

/** Suffix after "Aftertax". Live → " · Live"; mock / unknown → "". */
export function sourceEyebrowSuffix(source?: string | null): string {
  return isLiveDataSource(source) ? " · Live" : "";
}
