// SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0
// Hero: the question, the one-sentence answer built from the published results,
// and the thermal die illustration (a cold start). The illustration carries no
// data and shows no number.
import type { Results } from "./results";

type Cell = { x: number; y: number; w: number; h: number; heat: "core" | "hot" | "warm" | "low"; d: number };

const CX = 200, CY = 200;

function cells(): Cell[] {
  const out: Omit<Cell, "d">[] = [];
  // Core cluster, 2 x 2.
  for (let i = 0; i < 2; i++) for (let j = 0; j < 2; j++)
    out.push({ x: 152 + i * 50, y: 150 + j * 50, w: 44, h: 44, heat: i === j ? "core" : "hot" });
  // Cache strip above the cores.
  for (let i = 0; i < 4; i++) out.push({ x: 152 + i * 24.5, y: 106, w: 20, h: 30, heat: "hot" });
  // I/O strip below.
  for (let i = 0; i < 3; i++) out.push({ x: 152 + i * 33, y: 264, w: 28, h: 52, heat: "low" });
  // Two memory banks: the weights being loaded.
  for (const bx of [58, 294]) for (let k = 0; k < 8; k++)
    out.push({ x: bx, y: 86 + k * 30, w: 48, h: 24, heat: k > 1 && k < 6 ? "warm" : "low" });
  const withDist = out.map((c) => ({ ...c, dist: Math.hypot(c.x + c.w / 2 - CX, c.y + c.h / 2 - CY) }));
  const order = [...withDist].sort((a, b) => a.dist - b.dist);
  return withDist.map((c) => ({ ...c, d: 200 + order.indexOf(c) * 40 }));
}

const CELLS = cells();
const PADS = Array.from({ length: 11 }, (_, i) => 50 + i * 30);

export function DieIllustration() {
  return (
    <figure className="die" aria-labelledby="die-cap">
      <svg viewBox="0 0 400 400" className="die-svg" aria-hidden="true" focusable="false">
        <defs>
          <radialGradient id="bloom" cx="50%" cy="50%" r="50%">
            <stop offset="0" stopColor="#FFF3D6" stopOpacity="0.55" />
            <stop offset="0.35" stopColor="#F59A3C" stopOpacity="0.35" />
            <stop offset="0.7" stopColor="#E0559A" stopOpacity="0.16" />
            <stop offset="1" stopColor="#E0559A" stopOpacity="0" />
          </radialGradient>
        </defs>
        {PADS.map((p) => (
          <g key={p} className="pad">
            <rect x={p - 6} y={4} width={12} height={12} />
            <rect x={p - 6} y={384} width={12} height={12} />
            <rect x={4} y={p - 6} width={12} height={12} />
            <rect x={384} y={p - 6} width={12} height={12} />
          </g>
        ))}
        <path className="die-body" d="M76 24 H376 V376 H24 V76 Z" />
        <circle className="bloom" cx={CX} cy={CY} r={190} fill="url(#bloom)" />
        {CELLS.map((c, i) => (
          <g key={i}>
            <rect className="cell-cold" x={c.x} y={c.y} width={c.w} height={c.h} rx={2} />
            <rect className={`cell-heat heat-${c.heat}`} x={c.x} y={c.y} width={c.w} height={c.h} rx={2}
              style={{ animationDelay: `${c.d}ms` }} />
          </g>
        ))}
      </svg>
      <figcaption id="die-cap">
        <span className="illus-label">Illustration, not study data.</span> A chip warming from cold as a model loads; no
        value here is a measurement.
      </figcaption>
    </figure>
  );
}

export function Hero({ r }: { r: Results | null }) {
  const exp3 = r?.experiments.find((e) => e.id === "EXP-003");
  const diff = exp3?.estimates.find((x) => x.label.startsWith("Strict accuracy difference"));
  const q4 = r?.frontier.arms.find((a) => a.quantization === "Q4_K_M");
  const q8 = r?.frontier.arms.find((a) => a.quantization === "Q8_0");
  return (
    <section className="hero" aria-labelledby="h-question">
      <div className="hero-text">
        <h1 id="h-question">How do local model configurations trade off quality, latency and resource use?</h1>
        {diff && q4 && q8 ? (
          <p className="answer">
            On one laptop, Llama 3.1 8B at Q8_0 took <span className="num">{q8.memory_display} MiB</span> of
            runtime-reported memory against <span className="num">{q4.memory_display} MiB</span> at Q4_K_M, and no
            accuracy difference was detected: <span className="num">{diff.display}</span> percentage points, 95 %
            interval <span className="num">{diff.interval_display}</span>, which is not evidence of equivalence.{" "}
            <span className="tag tag-measured">measured</span>
          </p>
        ) : (
          <p className="answer muted">The answer appears here once the published results have loaded.</p>
        )}
        <p className="byline">Mohamed Bechir Kefi, independent researcher. A preregistered measurement study on one laptop.</p>
      </div>
      <DieIllustration />
    </section>
  );
}
