/**
 * Confirmed ticker chips (Tab / Enter / autocomplete) use the LIVE / above
 * brand green. Search total=0 / Add to universe uses tax-more red.
 * Empty, placeholder, and mid-edit stay the neutral line token.
 *
 * Dedicated `ticker-lock-*` classes live in unlayered CSS so the global
 * `* { border-color: var(--line) }` reset cannot wash them back to gray.
 */
export function tickerSlotBorderClass(input: {
  committed: boolean;
  midEdit: boolean;
  notInUniverse?: boolean;
}): string {
  if (input.midEdit) return "border-line";
  if (input.notInUniverse) {
    return "border-2 border-tax-more ticker-lock-missing";
  }
  if (input.committed) {
    return "border-2 border-above ticker-lock-in-universe";
  }
  return "border-line";
}
