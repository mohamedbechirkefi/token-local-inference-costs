// SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0
// Bounded, cancellable sandbox: re-runs the paired bootstrap and the exact McNemar
// test (engine.ts) on the published per-item correctness. No model, no timing.

import { pairedCompare, type Extraction, type PairedResult, type Subset } from "./engine";

export type WorkerRequest =
  | { type: "run"; seed: number; nBoot: number; extraction: Extraction; subset: Subset; cand: number[]; base: number[] }
  | { type: "cancel" };
export type WorkerReply =
  | { type: "progress"; fraction: number }
  | { type: "done"; seed: number; nBoot: number; extraction: Extraction; subset: Subset; result: PairedResult }
  | { type: "cancelled" }
  | { type: "error"; message: string };

let cancelled = false;

onmessage = async (ev: MessageEvent<WorkerRequest>) => {
  const m = ev.data;
  if (m.type === "cancel") {
    cancelled = true;
    return;
  }
  cancelled = false;
  try {
    const result = await pairedCompare(m.cand, m.base, m.nBoot, m.seed, 0.95, async (fraction) => {
      await new Promise((r) => setTimeout(r, 0)); // let a cancel message in
      if (cancelled) return false;
      postMessage({ type: "progress", fraction } satisfies WorkerReply);
      return true;
    });
    postMessage(
      (result === null
        ? { type: "cancelled" }
        : { type: "done", seed: m.seed, nBoot: m.nBoot, extraction: m.extraction, subset: m.subset, result }) satisfies WorkerReply,
    );
  } catch (e) {
    postMessage({ type: "error", message: e instanceof Error ? e.message : String(e) } satisfies WorkerReply);
  }
};
