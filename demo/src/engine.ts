// SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0
// Port of the project's paired statistics (src/token_lab/stats.py: paired_compare,
// paired_bootstrap_ci, mcnemar_exact) for the browser sandbox. It re-analyses the
// published per-item correctness; it runs no model and measures no time.
// The point difference, the discordant counts and the exact McNemar p are computed
// exactly as in Python. The bootstrap uses mulberry32 instead of numpy's PCG64, so
// its interval matches the Python engine within a stated tolerance, not bit for bit
// (see engine.test.ts): the sandbox is illustrative, not the research engine.

import type { ItemRow } from "./results";

export type Extraction = "strict" | "lenient";
export type Subset = "all" | "exclude_strict_miss";

export const MIN_BOOT = 1_000;
export const MAX_BOOT = 20_000;

export interface Pairs {
  cand: number[];
  base: number[];
}

export interface PairedResult {
  n: number;
  delta: number;
  ci_low: number;
  ci_high: number;
  b: number;
  c: number;
  mcnemar_p: number;
}

export function selectPairs(items: ItemRow[], extraction: Extraction, subset: Subset): Pairs {
  const keep = items.filter((r) => subset === "all" || !r.strict_miss_any);
  return {
    cand: keep.map((r) => (extraction === "strict" ? r.q8_strict : r.q8_lenient)),
    base: keep.map((r) => (extraction === "strict" ? r.q4_strict : r.q4_lenient)),
  };
}

export function mulberry32(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** Two-sided exact McNemar p-value from discordant counts (exact integer arithmetic). */
export function mcnemarExact(b: number, c: number): number {
  if (!Number.isInteger(b) || !Number.isInteger(c) || b < 0 || c < 0) {
    throw new RangeError("discordant counts must be non-negative integers");
  }
  const n = b + c;
  if (n === 0) return 1;
  const k = Math.min(b, c);
  let comb = 1n;
  let tail = 0n;
  for (let i = 0; i <= k; i++) {
    if (i > 0) comb = (comb * BigInt(n - i + 1)) / BigInt(i);
    tail += comb;
  }
  // tail / 2^n, correctly rounded like Python's int / int, for n below 1000.
  const p = 2 * ratio(tail, 1n << BigInt(n));
  return Math.min(1, p);
}

function ratio(num: bigint, den: bigint): number {
  // Scale so the quotient has 64 significant bits, then divide in floating point.
  const shift = BigInt(Math.max(0, den.toString(2).length - num.toString(2).length + 64));
  const q = (num << shift) / den;
  return Number(q) / 2 ** Number(shift);
}

/** numpy.quantile with the default linear method, on a sorted array. */
export function quantileSorted(s: Float64Array | number[], q: number): number {
  const h = (s.length - 1) * q;
  const lo = Math.floor(h);
  const hi = Math.min(lo + 1, s.length - 1);
  return s[lo] + (h - lo) * (s[hi] - s[lo]);
}

function check01(x: number[], name: string): void {
  if (x.length === 0) throw new RangeError(`${name} must be non-empty`);
  for (const v of x) if (!(v >= 0 && v <= 1)) throw new RangeError(`${name} must lie in [0, 1]`);
}

/**
 * Paired comparison of cand against base: mean difference, percentile bootstrap
 * interval over items, discordance on majority correctness, exact McNemar.
 * `yieldEvery` resamples, `onYield` is awaited; if it returns false the run stops
 * and the function returns null (cancellation).
 */
export async function pairedCompare(
  cand: number[],
  base: number[],
  nBoot: number,
  seed: number,
  level = 0.95,
  onYield?: (fraction: number) => Promise<boolean>,
  yieldEvery = 1_000,
): Promise<PairedResult | null> {
  check01(cand, "cand");
  check01(base, "base");
  if (cand.length !== base.length) throw new RangeError("paired vectors must have equal length");
  if (!Number.isInteger(nBoot) || nBoot < MIN_BOOT || nBoot > MAX_BOOT) {
    throw new RangeError(`resamples must be an integer from ${MIN_BOOT} to ${MAX_BOOT}`);
  }
  if (!(level > 0 && level < 1)) throw new RangeError("0 < level < 1 required");
  const n = cand.length;
  const d = cand.map((v, i) => v - base[i]);
  const delta = d.reduce((s, v) => s + v, 0) / n;
  const rng = mulberry32(seed);
  const means = new Float64Array(nBoot);
  for (let r = 0; r < nBoot; r++) {
    let s = 0;
    for (let j = 0; j < n; j++) s += d[Math.floor(rng() * n)];
    means[r] = s / n;
    if (onYield && (r + 1) % yieldEvery === 0 && r + 1 < nBoot) {
      if (!(await onYield((r + 1) / nBoot))) return null;
    }
  }
  means.sort();
  const alpha = (1 - level) / 2;
  let b = 0;
  let c = 0;
  for (let i = 0; i < n; i++) {
    const a1 = cand[i] >= 0.5;
    const b1 = base[i] >= 0.5;
    if (a1 && !b1) b++;
    if (!a1 && b1) c++;
  }
  return {
    n,
    delta,
    ci_low: quantileSorted(means, alpha),
    ci_high: quantileSorted(means, 1 - alpha),
    b,
    c,
    mcnemar_p: mcnemarExact(b, c),
  };
}

/** Signed percentage points with two decimals, as the manuscript prints them. */
export function ppText(x: number): string {
  const v = x * 100;
  const r = Math.round(v * 100) / 100;
  return `${r >= 0 ? "+" : "-"}${Math.abs(r).toFixed(2)}`;
}
