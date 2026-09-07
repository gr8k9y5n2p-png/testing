/** Families with live ingest today (Data team). Everyone else is a coverage gap. */
export const LIVE_INGEST_FAMILIES = new Set(["American Funds", "Capital Group"]);

export const PLANNED_COVERAGE_FAMILIES = [
  "BlackRock / iShares",
  "Vanguard",
  "Fidelity",
  "State Street / SPDR",
  "J.P. Morgan AM",
  "Goldman Sachs AM",
  "Capital Group",
  "PIMCO",
  "Invesco",
  "T. Rowe Price",
] as const;

export function isLiveCoveredFamily(family: string): boolean {
  return LIVE_INGEST_FAMILIES.has(family);
}
