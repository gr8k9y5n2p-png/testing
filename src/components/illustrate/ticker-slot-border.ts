/**
 * Confirmed ticker chips (Tab / Enter / autocomplete) use the LIVE / above
 * brand green. Empty, placeholder, and mid-edit stay the neutral line token.
 */
export function tickerSlotBorderClass(input: {
  committed: boolean;
  midEdit: boolean;
}): string {
  return input.committed && !input.midEdit ? "border-above" : "border-line";
}
