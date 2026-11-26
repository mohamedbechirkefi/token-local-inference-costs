// SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0
// Visitor sandbox: re-runs the paired statistics on the published per-item
// correctness in a Web Worker. Its output is labelled as sandbox output and never
// mixed with the published results. It runs no model and reports no timing.
import { useEffect, useRef, useState } from "react";
import { MAX_BOOT, MIN_BOOT, ppText, selectPairs, type Extraction, type PairedResult, type Subset } from "./engine";
import type { ItemRow, Results } from "./results";
import type { WorkerReply, WorkerRequest } from "./sandbox.worker";

const DEFAULTS = { seed: 1, nBoot: 10_000, extraction: "strict" as Extraction, subset: "all" as Subset };

function describeRun(seed: number, nBoot: number, extraction: Extraction, subset: Subset, n: number): string {
  const set = subset === "all" ? `all ${n} items` : `${n} items, post hoc exclusion (exploratory)`;
  return `seed ${seed}, ${nBoot.toLocaleString("en-US")} resamples, ${extraction} extraction, ${set}`;
}

function summary(r: PairedResult): string {
  return (
    `Q8_0 minus Q4_K_M ${ppText(r.delta)} pp, 95 % percentile interval [${ppText(r.ci_low)}, ${ppText(r.ci_high)}] pp, ` +
    `b = ${r.b}, c = ${r.c}, exact McNemar p = ${r.mcnemar_p.toFixed(3)}.`
  );
}

export function Sandbox({ results }: { results: Results | null }) {
  const worker = useRef<Worker | null>(null);
  const [seed, setSeed] = useState(DEFAULTS.seed);
  const [nBoot, setNBoot] = useState(DEFAULTS.nBoot);
  const [extraction, setExtraction] = useState<Extraction>(DEFAULTS.extraction);
  const [subset, setSubset] = useState<Subset>(DEFAULTS.subset);
  const [running, setRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [out, setOut] = useState<string>("");
  const [ref, setRef] = useState<string>("");

  useEffect(() => {
    const w = new Worker(new URL("./sandbox.worker.ts", import.meta.url), { type: "module" });
    w.onmessage = (ev: MessageEvent<WorkerReply>) => {
      const m = ev.data;
      if (m.type === "progress") {
        setProgress(m.fraction);
        return;
      }
      if (m.type === "done") {
        setOut(
          `Sandbox output (illustrative, not a measurement; ${describeRun(m.seed, m.nBoot, m.extraction, m.subset, m.result.n)}): ${summary(m.result)}`,
        );
      }
      if (m.type === "error") setOut(`Sandbox run stopped with an error: ${m.message}`);
      if (m.type === "cancelled") setOut("Sandbox run cancelled.");
      setRunning(false);
      setProgress(0);
    };
    worker.current = w;
    return () => w.terminate();
  }, []);

  const items: ItemRow[] | null = results ? results.items : null;

  const run = () => {
    if (!items || !results) return;
    const { cand, base } = selectPairs(items, extraction, subset);
    setRunning(true);
    setOut("");
    const pub = subset === "all" ? results.sandbox_reference[extraction] : null;
    setRef(
      pub
        ? `Published result for this setting (measured, confirmatory, Python engine, seed 7, 10,000 resamples): ` +
            `${ppText(pub.delta_pp / 100)} pp, 95 % CI [${ppText(pub.ci_low_pp / 100)}, ${ppText(pub.ci_high_pp / 100)}] pp, p = ${pub.mcnemar_p.toFixed(3)}.`
        : "This setting has no published counterpart: the post hoc exclusion is exploratory, and the manuscript reports only its point difference (+1.36 pp on 295 items).",
    );
    worker.current?.postMessage({ type: "run", seed, nBoot, extraction, subset, cand, base } satisfies WorkerRequest);
  };
  const cancel = () => worker.current?.postMessage({ type: "cancel" } satisfies WorkerRequest);
  const reset = () => {
    if (running) cancel();
    setSeed(DEFAULTS.seed);
    setNBoot(DEFAULTS.nBoot);
    setExtraction(DEFAULTS.extraction);
    setSubset(DEFAULTS.subset);
    setOut("");
    setRef("");
  };

  return (
    <section id="sandbox" aria-labelledby="h-sandbox" className="sandbox">
      <h2 id="h-sandbox">
        Sandbox: re-run the accuracy statistics <span className="tag tag-sandbox">sandbox, illustrative</span>
      </h2>
      <p className="note">
        <strong>Illustrative, not the research engine, and not a measurement.</strong> Your browser resamples the 300
        published per-item correctness values of EXP-003 and recomputes the paired difference, its percentile bootstrap
        interval and the exact McNemar test. No model runs and nothing is timed. The point difference, the discordant
        counts and the p-value are computed as in the Python engine; the bootstrap uses a different random generator,
        so its interval agrees with the Python engine within one item step (1/n), not digit for digit.
      </p>
      <p className="note">
        The "295 items, post hoc" setting drops the 5 items on which strict extraction found no label in some repetition
        (exploratory check E5). Protocol section 9 forbids excluding items after outputs, so it is never a confirmatory
        analysis.
      </p>
      {!items && <p className="note">The sandbox needs the published results, which are not available.</p>}
      <div className="controls">
        <label>
          Seed{" "}
          <input id="sb-seed" type="number" min={1} max={1_000_000} value={seed} disabled={running}
            onChange={(e) => setSeed(Math.min(1_000_000, Math.max(1, Math.trunc(Number(e.target.value)) || 1)))} />
        </label>
        <label>
          Resamples{" "}
          <input id="sb-boot" type="number" min={MIN_BOOT} max={MAX_BOOT} step={1000} value={nBoot} disabled={running}
            onChange={(e) => setNBoot(Math.min(MAX_BOOT, Math.max(MIN_BOOT, Math.trunc(Number(e.target.value)) || MIN_BOOT)))} />
        </label>
        <label>
          Extraction{" "}
          <select id="sb-extraction" value={extraction} disabled={running} onChange={(e) => setExtraction(e.target.value as Extraction)}>
            <option value="strict">strict (primary)</option>
            <option value="lenient">lenient (S2)</option>
          </select>
        </label>
        <label>
          Items{" "}
          <select id="sb-subset" value={subset} disabled={running} onChange={(e) => setSubset(e.target.value as Subset)}>
            <option value="all">all 300 items</option>
            <option value="exclude_strict_miss">295 items, post hoc</option>
          </select>
        </label>
        <button type="button" onClick={run} disabled={running || !items}>Run re-analysis</button>
        <button type="button" onClick={cancel} disabled={!running}>Cancel</button>
        <button type="button" onClick={reset}>Reset</button>
      </div>
      {running && (
        <p className="meta">
          <label>
            Progress <progress max={1} value={progress} />
          </label>
        </p>
      )}
      <p aria-live="polite" className="sandbox-out">{out && <span key={out} className="fresh">{out}</span>}</p>
      {out && ref && <p className="meta">{ref}</p>}
      {!out && !running && items && <p className="meta">Choose the settings and run the re-analysis; the output is labelled as sandbox output.</p>}
    </section>
  );
}
