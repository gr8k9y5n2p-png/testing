/**
 * Confirmed ticker chips (Tab / Enter / autocomplete) use the LIVE / above
 * brand green. Search total=0 / Add to universe uses tax-more red.
 * Empty, placeholder, and mid-edit stay the neutral line token.
 */
export function tickerSlotBorderClass(input: {
  committed: boolean;
  midEdit: boolean;
  notInUniverse?: boolean;
}): string {
  if (input.midEdit) return "border-line";
  if (input.notInUniverse) return "border-tax-more";
  if (input.committed) return "border-above";
  return "border-line";
}
