import { AMOUNT_UNITS, type AmountUnit } from "@/lib/illustrate/types";

export function distributionIdsForFund(
  fundId: string,
  unit: AmountUnit = AMOUNT_UNITS.percent_of_nav,
): string[] {
  return [`${fundId}:ordinary:${unit}`, `${fundId}:ltcg:${unit}`];
}

export function distributionId(
  fundId: string,
  kind: "ordinary" | "ltcg",
  unit: AmountUnit,
): string {
  return `${fundId}:${kind}:${unit}`;
}
