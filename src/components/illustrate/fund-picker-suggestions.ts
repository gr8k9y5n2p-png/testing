/** Autocomplete only after the user types — never on empty focus/click. */
export function shouldOpenFundSuggestions(query: string): boolean {
  return query.trim().length > 0;
}
