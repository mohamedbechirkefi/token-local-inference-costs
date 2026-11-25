// SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0
// Compares the browser port (engine.ts) with the Python research engine on the
// committed fixture (scripts/export_sandbox_fixture.py, token_lab.stats).
// Tolerance: the point difference and the exact McNemar p agree to 1e-12, the
// discordant counts exactly. The bootstrap uses a different random generator, so
// each interval bound must lie within one item step (1/n, 0.33 pp at n = 300) of
// the Python bound, for several sandbox seeds.
import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { mcnemarExact, pairedCompare, ppText, selectPairs, type Extraction, type Subset } from "./engine";
import { validateResults } from "./results";

const fixture = JSON.parse(readFileSync("src/engine.fixture.json", "utf8"));
const results = validateResults(JSON.parse(readFileSync("public/data/results.json", "utf8")));

describe("port against the Python engine fixture", () => {
  for (const s of fixture.scenarios) {
    it(`${s.extraction}, ${s.subset}: exact parts and bootstrap interval within one item step`, async () => {
      const { cand, base } = selectPairs(results.items, s.extraction as Extraction, s.subset as Subset);
      expect(cand.length).toBe(s.n);
      const tol = 1 / s.n + 1e-9;
      for (const seed of [7, 1, 2, 3]) {
        const r = await pairedCompare(cand, base, fixture.n_boot, seed);
        expect(r).not.toBeNull();
        expect(Math.abs(r!.delta - s.delta)).toBeLessThan(1e-12);
        expect(r!.b).toBe(s.b);
        expect(r!.c).toBe(s.c);
        expect(Math.abs(r!.mcnemar_p - s.mcnemar_p)).toBeLessThan(1e-12);
        expect(Math.abs(r!.ci_low - s.ci_low)).toBeLessThanOrEqual(tol);
        expect(Math.abs(r!.ci_high - s.ci_high)).toBeLessThanOrEqual(tol);
      }
    });
  }

  it("exact McNemar matches Python on the grid", () => {
    for (const g of fixture.mcnemar_grid) {
      expect(Math.abs(mcnemarExact(g.b, g.c) - g.p)).toBeLessThan(1e-15);
    }
  });

  it("the published contrast is reproduced in its printed form", async () => {
    const { cand, base } = selectPairs(results.items, "strict", "all");
    const r = await pairedCompare(cand, base, 10_000, 7);
    expect(ppText(r!.delta)).toBe("+1.67");
    expect(r!.mcnemar_p.toFixed(3)).toBe("0.332");
    expect(results.sandbox_reference.strict.b).toBe(r!.b);
  });
});

describe("engine bounds and determinism", () => {
  const { cand, base } = selectPairs(results.items, "strict", "all");
  it("the same seed gives the same interval", async () => {
    const a = await pairedCompare(cand, base, 2_000, 42);
    const b = await pairedCompare(cand, base, 2_000, 42);
    expect(a).toEqual(b);
  });
  it("rejects resample counts outside the bound", async () => {
    await expect(pairedCompare(cand, base, 999, 1)).rejects.toThrow(RangeError);
    await expect(pairedCompare(cand, base, 20_001, 1)).rejects.toThrow(RangeError);
  });
  it("rejects unpaired or out-of-range inputs", async () => {
    await expect(pairedCompare([1, 0], [1], 1_000, 1)).rejects.toThrow(RangeError);
    await expect(pairedCompare([2], [1], 1_000, 1)).rejects.toThrow(RangeError);
    expect(() => mcnemarExact(-1, 2)).toThrow(RangeError);
  });
  it("cancellation stops the run", async () => {
    const r = await pairedCompare(cand, base, 5_000, 1, 0.95, async () => false);
    expect(r).toBeNull();
  });
});
