/** Drop the selected fund, not just the typed query. */
export function shouldClearFundPickerSelection(input: {
  nextValue?: string;
  key?: string;
  hasSelection: boolean;
  suggestionsOpen: boolean;
}): boolean {
  if (!input.hasSelection) return false;
  if (input.nextValue === "") return true;
  return (
    !input.suggestionsOpen &&
    (input.key === "Backspace" || input.key === "Delete")
  );
}
