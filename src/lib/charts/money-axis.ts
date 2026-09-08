import { formatUsd } from "@/lib/format";

/** Keep growth / tax $ axes in the 4–6 tick band. Never emit a crowded stack. */
export const MIN_MONEY_TICKS = 4;
export const MAX_MONEY_TICKS = 6;

export type MoneyScale = {
  min: number;
  max: number;
  step: number;
  ticks: number[];
};

/**
 * Nice 1 / 2 / 2.5 / 5 / 10 step. Drop 2.5 once the step is $100k+
 * so $1M windows land on $1.0M / $1.2M instead of $1.25M.
 */
export function niceMoneyStep(span: number, targetTicks = 5): number {
  const safe = Math.max(Math.abs(span), 1);
  const raw = safe / Math.max(targetTicks - 1, 1);
  const pow = 10 ** Math.floor(Math.log10(raw));
  const err = raw / pow;
  const allowQuarter = pow < 100_000;
  const nice =
    err <= 1
      ? 1
      : err <= 2
        ? 2
        : allowQuarter && err <= 2.5
          ? 2.5
          : err <= 5
            ? 5
            : 10;
  return nice * pow;
}

function coarsenStep(step: number): number {
  const pow = 10 ** Math.floor(Math.log10(step));
  const n = step / pow;
  const next = n <= 1 ? 2 : n <= 2 ? 2.5 : n <= 2.5 ? 5 : n <= 5 ? 10 : 20;
  return next * pow;
}

function refineStep(step: number): number {
  const pow = 10 ** Math.floor(Math.log10(step));
  const n = step / pow;
  const next = n >= 10 ? 5 : n >= 5 ? 2.5 : n >= 2.5 ? 2 : n >= 2 ? 1 : 0.5;
  return next * pow;
}

function snapUp(value: number, step: number): number {
  if (!(step > 0)) return value;
  return Math.ceil(value / step - 1e-9) * step;
}

export function moneyTicks(min: number, max: number, step: number): number[] {
  if (!(step > 0) || max < min) return [min, max];
  const ticks: number[] = [];
  const last = max + step * 0.25;
  for (let value = min; value <= last && ticks.length <= MAX_MONEY_TICKS + 2; value += step) {
    ticks.push(Math.round(value * 1000) / 1000);
  }
  if (ticks.length && ticks[ticks.length - 1] < max - step * 0.01) {
    ticks.push(Math.round(max * 1000) / 1000);
  }
  return ticks.length >= 2 ? ticks : [min, max];
}

/**
 * Dollar scale that stays in ~4–6 ticks for $10k and $1M principals.
 * Anchors the floor at `startDollars` when data starts there.
 */
export function niceMoneyScale(
  min: number,
  max: number,
  startDollars: number,
): MoneyScale {
  const dataMin = Number.isFinite(min) ? min : 0;
  const dataMax = Number.isFinite(max) ? Math.max(max, dataMin) : dataMin;
  const floor =
    startDollars > 0 && dataMin >= startDollars * 0.95
      ? startDollars
      : Math.max(0, dataMin);
  const large = floor >= 100_000;
  const paddedMax = Math.max(dataMax * (large ? 1.06 : 1.08), floor * 1.12, floor + 1);

  let step = niceMoneyStep(paddedMax - floor, large ? 6 : 5);
  const scaleMin = floor;
  let scaleMax = Math.max(snapUp(paddedMax, step), scaleMin + step * (MIN_MONEY_TICKS - 1));
  let ticks = moneyTicks(scaleMin, scaleMax, step);

  let guard = 0;
  while (ticks.length > MAX_MONEY_TICKS && guard < 10) {
    step = coarsenStep(step);
    scaleMax = Math.max(snapUp(paddedMax, step), scaleMin + step * (MIN_MONEY_TICKS - 1));
    ticks = moneyTicks(scaleMin, scaleMax, step);
    guard += 1;
  }

  guard = 0;
  while (ticks.length < MIN_MONEY_TICKS && guard < 10) {
    const next = refineStep(step);
    if (next >= step) break;
    step = next;
    scaleMax = Math.max(snapUp(paddedMax, step), scaleMin + step * (MIN_MONEY_TICKS - 1));
    ticks = moneyTicks(scaleMin, scaleMax, step);
    guard += 1;
  }

  if (ticks.length > MAX_MONEY_TICKS) {
    const stride = Math.ceil((ticks.length - 1) / (MAX_MONEY_TICKS - 1));
    const thinned = ticks.filter((_, index) => index % stride === 0 || index === ticks.length - 1);
    ticks = thinned.slice(0, MAX_MONEY_TICKS);
    if (ticks[ticks.length - 1] !== scaleMax) ticks[ticks.length - 1] = scaleMax;
  }

  return { min: scaleMin, max: scaleMax, step, ticks };
}

/** $1.0M / $1.2M above $1M; $10k / $12.5k in the thousands. */
export function formatCompactUsd(value: number): string {
  const sign = value < 0 ? "-" : "";
  const abs = Math.abs(value);
  if (abs >= 1_000_000) {
    return `${sign}$${(abs / 1_000_000).toFixed(1)}M`;
  }
  if (abs >= 1000) {
    const k = abs / 1000;
    const digits = Math.abs(k - Math.round(k)) < 0.05 ? 0 : 1;
    return `${sign}$${k.toFixed(digits)}k`;
  }
  return formatUsd(value, 0);
}
