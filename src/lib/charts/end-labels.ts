/** Vertical collision-avoidance for growth-chart terminal labels. */

export const END_LABEL_MIN_GAP = 14;

export type EndLabelInput = {
  id: string;
  /** Preferred y (SVG, down is positive) of the series terminal. */
  y: number;
};

export type PlacedEndLabel = EndLabelInput & {
  /** Collision-resolved label baseline y. */
  labelY: number;
};

export type StaggerEndLabelOptions = {
  /** Minimum center-to-center gap between labels. */
  minGap?: number;
  /** Inclusive plot-area floor (top of the inner chart). */
  minY: number;
  /** Inclusive plot-area ceiling (bottom of the inner chart). */
  maxY: number;
};

/**
 * Vertically stagger end-of-series labels so none overlap.
 * Keeps each label as close as possible to its series y, then packs
 * clusters and clamps the stack into `[minY, maxY]`.
 *
 * Returns `null` when even a tightly packed stack cannot fit — caller
 * should drop labels and rely on the legend.
 */
export function staggerEndLabels(
  labels: readonly EndLabelInput[],
  options: StaggerEndLabelOptions,
): PlacedEndLabel[] | null {
  const minGap = options.minGap ?? END_LABEL_MIN_GAP;
  const { minY, maxY } = options;
  if (!(maxY > minY) || !(minGap > 0)) return null;
  if (labels.length === 0) return [];

  const span = maxY - minY;
  const needed = (labels.length - 1) * minGap;
  if (needed > span + 1e-6) return null;

  const sorted = [...labels].sort((a, b) => a.y - b.y || a.id.localeCompare(b.id));
  const placed = sorted.map((label) => ({ ...label, labelY: label.y }));

  packForward(placed, minGap);
  if (placed[placed.length - 1].labelY > maxY) {
    placed[placed.length - 1].labelY = maxY;
    packBackward(placed, minGap);
  }
  if (placed[0].labelY < minY) {
    placed[0].labelY = minY;
    packForward(placed, minGap);
  }
  if (placed[placed.length - 1].labelY > maxY + 1e-6) {
    packEvenly(placed, minY, minGap);
  }

  if (
    placed[0].labelY < minY - 1e-6 ||
    placed[placed.length - 1].labelY > maxY + 1e-6 ||
    hasOverlap(placed, minGap)
  ) {
    return null;
  }

  return placed;
}

/** True when any pair of placed label baselines is closer than `minGap`. */
export function hasOverlap(
  labels: readonly { labelY: number }[],
  minGap = END_LABEL_MIN_GAP,
): boolean {
  const ys = labels.map((label) => label.labelY).sort((a, b) => a - b);
  for (let i = 1; i < ys.length; i += 1) {
    if (ys[i] - ys[i - 1] < minGap - 1e-6) return true;
  }
  return false;
}

function packForward(labels: { labelY: number }[], minGap: number) {
  for (let i = 1; i < labels.length; i += 1) {
    if (labels[i].labelY < labels[i - 1].labelY + minGap) {
      labels[i].labelY = labels[i - 1].labelY + minGap;
    }
  }
}

function packBackward(labels: { labelY: number }[], minGap: number) {
  for (let i = labels.length - 2; i >= 0; i -= 1) {
    if (labels[i].labelY > labels[i + 1].labelY - minGap) {
      labels[i].labelY = labels[i + 1].labelY - minGap;
    }
  }
}

function packEvenly(
  labels: { labelY: number }[],
  minY: number,
  minGap: number,
) {
  for (let i = 0; i < labels.length; i += 1) {
    labels[i].labelY = minY + i * minGap;
  }
}
