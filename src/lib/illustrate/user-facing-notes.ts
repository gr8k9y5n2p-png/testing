/**
 * Developer / localhost demo chrome. Production UI must never show these.
 * Live Data API responses do not include them; mock fixtures still might.
 */

const MOCK_CHROME =
  /MOCK\s*\/illustrate|sample seed math|not the Data team service|sketch fixture so localhost|AFTERTAX\s*·\s*SAMPLE|demo data chrome/i;

export function isMockChromeNote(text: string): boolean {
  return MOCK_CHROME.test(text);
}

/** Warnings / notes that advisors may see. Drops MOCK / seed banners. */
export function userFacingNotes(notes: unknown): string[] {
  if (!Array.isArray(notes)) return [];
  return notes.map(String).filter((note) => note.trim() && !isMockChromeNote(note));
}

/**
 * MOCK banners for local demo only.
 * Production (`NODE_ENV=production`) and any host with `NEXT_PUBLIC_DATA_API_URL`
 * emit none — that env is what getaftertax.com sets.
 */
export function demoEngineNotes(...messages: string[]): string[] {
  if (process.env.NEXT_PUBLIC_DATA_API_URL?.trim()) return [];
  if (process.env.NEXT_PUBLIC_ILLUSTRATE_URL?.trim()) return [];
  if (process.env.NODE_ENV === "production") return [];
  return messages.filter((message) => message.trim());
}
