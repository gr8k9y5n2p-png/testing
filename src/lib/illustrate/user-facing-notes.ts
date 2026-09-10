/**
 * Developer / localhost demo chrome. Production UI must never show these.
 * Live Data API responses do not include them; mock fixtures still might.
 */

import { allowDemoEngine } from "../data-api/runtime-env.ts";

const MOCK_CHROME =
  /MOCK\s*\/illustrate|sample seed math|not the Data team service|sketch fixture so localhost|AFTERTAX\s*·\s*SAMPLE|demo data chrome|Set NEXT_PUBLIC_(DATA_API_URL|ILLUSTRATE_URL)/i;

const NOTE_KEYS = new Set(["notes", "warnings"]);

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
 * Production (`NODE_ENV=production`) and any host with a live Data API URL
 * emit none — including when NEXT_PUBLIC_* was missing from the client bundle.
 */
export function demoEngineNotes(...messages: string[]): string[] {
  if (!allowDemoEngine()) return [];
  return messages.filter((message) => message.trim());
}

/** Drop MOCK chrome from API JSON so it cannot re-surface in the UI. */
export function stripMockChromeFromPayload<T>(value: T): T {
  if (Array.isArray(value)) {
    return value.map((item) => stripMockChromeFromPayload(item)) as T;
  }
  if (!value || typeof value !== "object") return value;

  const out: Record<string, unknown> = {};
  for (const [key, child] of Object.entries(value as Record<string, unknown>)) {
    if (NOTE_KEYS.has(key)) {
      if (Array.isArray(child)) {
        out[key] = userFacingNotes(child);
      } else if (typeof child === "string") {
        out[key] = isMockChromeNote(child) ? "" : child;
      } else {
        out[key] = stripMockChromeFromPayload(child);
      }
      continue;
    }
    if (typeof child === "string" && isMockChromeNote(child)) {
      out[key] = "";
      continue;
    }
    out[key] = stripMockChromeFromPayload(child);
  }
  return out as T;
}
