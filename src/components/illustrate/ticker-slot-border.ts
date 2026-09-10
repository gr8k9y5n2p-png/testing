/**
 * Confirmed ticker chips (Tab / Enter / autocomplete) use the LIVE / above
 * brand green. Empty, placeholder, and mid-edit stay the neutral line token.
 * `ticker-slot-locked` is unlayered in globals.css so it beats `* { border-color }`.
 */
export function tickerSlotBorderClass(input: {
  committed: boolean;
  midEdit: boolean;
}): string {
  return input.committed && !input.midEdit ? "ticker-slot-locked" : "border-line";
}
