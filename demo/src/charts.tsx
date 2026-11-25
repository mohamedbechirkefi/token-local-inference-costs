// SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0
// Hand-written SVG charts drawn from the exported results only.
import { useState } from "react";
import type { Estimate, FrontierArm, ItemRow, NotMeasured } from "./results";

const W = 480;

function ticks(lo: number, hi: number, step: number): number[] {
  const out: number[] = [];
  for (let v = Math.ceil(lo / step) * step; v <= hi + 1e-9; v += step) out.push(Number(v.toFixed(6)));
  return out;
}

type Metric = "memory" | "latency" | "decode";

const METRICS: Record<Metric, { name: string; unit: string; lo: number; hi: number; step: number; note: string }> = {
  memory: { name: "Runtime-reported model memory", unit: "MiB", lo: 0, hi: 10_000, step: 2_000,
    note: "Deterministic runtime report (/api/ps), no interval." },
  latency: { name: "Median of per-item median end-to-end latency", unit: "ms", lo: 0, hi: 700, step: 100,
    note: "Horizontal bars show the interquartile range over the 300 items, not a confidence interval." },
  decode: { name: "Median decode throughput over records", unit: "tokens/s", lo: 0, hi: 60, step: 10,
    note: "Descriptive median, no interval published." },
};

function xValue(a: FrontierArm, m: Metric): number {
  return m === "memory" ? a.memory_mib : m === "latency" ? a.latency_ms : a.decode_tps;
}

function xText(a: FrontierArm, m: Metric): string {
  return m === "memory" ? `${a.memory_display} MiB` : m === "latency" ? `${a.latency_display} ms` : `${a.decode_display} tokens/s`;
}

/** Resource frontier explorer: strict accuracy against a chosen measured cost. */
export function FrontierChart({ arms, notMeasured }: { arms: FrontierArm[]; notMeasured: NotMeasured[] }) {
  const [metric, setMetric] = useState<Metric>("memory");
  const M = METRICS[metric];
  const H = 330, L = 66, R = 36, T = 20, B = 64;
  const yLo = 0.65, yHi = 0.8;
  const x = (v: number) => L + ((v - M.lo) / (M.hi - M.lo)) * (W - L - R);
  const y = (v: number) => T + (1 - (v - yLo) / (yHi - yLo)) * (H - T - B);
  const desc =
    `Strict accuracy against ${M.name.toLowerCase()} for the two measured EXP-003 arms. ` +
    arms.map((a) => `${a.quantization}: accuracy ${a.accuracy_display}, ${xText(a, metric)}`).join("; ") +
    ". The EXP-001 arms have no result and are not plotted.";
  return (
    <figure className="chart">
      <div className="toggle" role="group" aria-label="Cost shown on the horizontal axis">
        {(Object.keys(METRICS) as Metric[]).map((k) => (
          <button key={k} type="button" aria-pressed={metric === k} onClick={() => setMetric(k)}>
            {k === "memory" ? "Memory" : k === "latency" ? "Latency" : "Decode throughput"}
          </button>
        ))}
      </div>
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={desc} className="svg">
        {ticks(yLo, yHi, 0.05).map((v) => (
          <g key={`y${v}`}>
            <line x1={L} x2={W - R} y1={y(v)} y2={y(v)} className="grid" />
            <text x={L - 8} y={y(v) + 5} textAnchor="end" className="tick">{v.toFixed(2)}</text>
          </g>
        ))}
        {ticks(M.lo, M.hi, M.step * (metric === "memory" ? 1.25 : 1)).map((v) => (
          <g key={`x${v}`}>
            <line x1={x(v)} x2={x(v)} y1={H - B} y2={H - B + 6} className="axis" />
            <text x={x(v)} y={H - B + 24} textAnchor="middle" className="tick">{v.toLocaleString("en-US")}</text>
          </g>
        ))}
        <line x1={L} x2={W - R} y1={H - B} y2={H - B} className="axis" />
        <line x1={L} x2={L} y1={T} y2={H - B} className="axis" />
        <text x={(L + W - R) / 2} y={H - 10} textAnchor="middle" className="axis-label">{M.name} ({M.unit})</text>
        <text x={18} y={(T + H - B) / 2} textAnchor="middle" className="axis-label" transform={`rotate(-90 18 ${(T + H - B) / 2})`}>
          Strict accuracy (cut axis)
        </text>
        {arms.map((a, i) => {
          const cx = x(xValue(a, metric));
          const cy = y(a.accuracy_strict);
          return (
            <g key={a.arm} className={`series s${i}`}>
              {metric === "latency" && (
                <>
                  <line x1={x(a.latency_q1_ms)} x2={x(a.latency_q3_ms)} y1={cy} y2={cy} className="whisker" />
                  <line x1={x(a.latency_q1_ms)} x2={x(a.latency_q1_ms)} y1={cy - 6} y2={cy + 6} className="whisker" />
                  <line x1={x(a.latency_q3_ms)} x2={x(a.latency_q3_ms)} y1={cy - 6} y2={cy + 6} className="whisker" />
                </>
              )}
              {i === 0 ? <circle cx={cx} cy={cy} r={8} className="mark" /> : <rect x={cx - 8} y={cy - 8} width={16} height={16} className="mark" />}
              <text x={cx} y={cy - 16} textAnchor={cx > W - 90 ? "end" : "middle"} className="point-label">{a.quantization}</text>
            </g>
          );
        })}
      </svg>
      <figcaption>
        <p>
          <span className="tag tag-measured">measured</span> {desc} {M.note} The vertical axis is cut at 0.65 to 0.80; the
          chance floor for this subset is 0.251. Neither arm's accuracy carries a published interval of its own; the paired
          difference does (next chart).
        </p>
        <div id="table-frontier" className="table-scroll" role="region" aria-label="Frontier values" tabIndex={0}>
          <table className="stack">
            <thead>
              <tr>
                <th scope="col">Arm (EXP-003)</th>
                <th scope="col">Strict accuracy</th>
                <th scope="col">Memory (MiB)</th>
                <th scope="col">Latency (ms) [Q1, Q3]</th>
                <th scope="col">Decode (tokens/s)</th>
              </tr>
            </thead>
            <tbody>
              {arms.map((a) => (
                <tr key={a.arm}>
                  <th scope="row">{a.quantization} <span className="meta">({a.model})</span></th>
                  <td data-label="Strict accuracy">{a.accuracy_display}</td>
                  <td data-label="Memory (MiB)">{a.memory_display}</td>
                  <td data-label="Latency (ms)">{a.latency_display} <span className="meta">{a.latency_iqr_display} IQR over items</span></td>
                  <td data-label="Decode (tokens/s)">{a.decode_display}</td>
                </tr>
              ))}
              {notMeasured.map((n) => (
                <tr key={n.arm} className="not-measured">
                  <th scope="row">{n.arm} {n.model} <span className="meta">({n.experiment})</span></th>
                  <td colSpan={4} data-label="Result">No result: {n.reason}.</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </figcaption>
    </figure>
  );
}

/** Paired difference with its 95 % interval against zero. */
export function ContrastChart({ rows }: { rows: { name: string; e: Estimate }[] }) {
  const H = 60 + rows.length * 56, L = 24, R = 24, T = 16, B = 44;
  const lo = -4, hi = 8;
  const x = (v: number) => L + ((v - lo) / (hi - lo)) * (W - L - R);
  const desc = rows
    .map((r) => `${r.name}: ${r.e.display} percentage points, 95 % interval ${r.e.interval_display}`)
    .join("; ");
  return (
    <figure className="chart">
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`Paired accuracy difference, Q8_0 minus Q4_K_M. ${desc}. The interval contains zero.`} className="svg">
        {ticks(lo, hi, 2).map((v) => (
          <g key={v}>
            <line x1={x(v)} x2={x(v)} y1={T} y2={H - B} className={v === 0 ? "zero" : "grid"} />
            <text x={x(v)} y={H - B + 22} textAnchor="middle" className="tick">{v > 0 ? `+${v}` : v}</text>
          </g>
        ))}
        <text x={(L + W - R) / 2} y={H - 6} textAnchor="middle" className="axis-label">Q8_0 minus Q4_K_M, percentage points</text>
        {rows.map((r, i) => {
          const cy = T + 30 + i * 56;
          return (
            <g key={r.name} className="series s1">
              <text x={W - R - 8} y={cy - 14} textAnchor="end" className="point-label">{r.name}</text>
              <line x1={x(r.e.ci_low!)} x2={x(r.e.ci_high!)} y1={cy} y2={cy} className="whisker thick" />
              <circle cx={x(r.e.estimate)} cy={cy} r={7} className="mark" />
            </g>
          );
        })}
      </svg>
      <figcaption>
        <span className="tag tag-measured">measured</span> Paired difference with its 95 % paired bootstrap interval: {desc}.
        The interval contains zero and the exact McNemar test does not reject, so no difference was detected. No
        equivalence margin was frozen, so this is not evidence of equivalence.
      </figcaption>
    </figure>
  );
}

function jitter(i: number): number {
  // Deterministic spread so dots do not overlap completely; carries no information.
  const s = Math.sin(i * 12.9898) * 43758.5453;
  return s - Math.floor(s) - 0.5;
}

/** Per-item median latency of both arms, one dot per item (as FIG-001). */
export function LatencyStrip({ items, arms }: { items: ItemRow[]; arms: FrontierArm[] }) {
  const H = 250, L = 84, R = 20, T = 16, B = 52;
  const all = items.flatMap((r) => [r.q4_latency_ms, r.q8_latency_ms]);
  const lo = Math.floor(Math.min(...all) / 100) * 100;
  const hi = Math.ceil(Math.max(...all) / 100) * 100;
  const x = (v: number) => L + ((v - lo) / (hi - lo)) * (W - L - R);
  const band = (H - T - B) / 2;
  const series = [
    { arm: arms[0], vals: items.map((r) => r.q4_latency_ms) },
    { arm: arms[1], vals: items.map((r) => r.q8_latency_ms) },
  ];
  return (
    <figure className="chart">
      <svg viewBox={`0 0 ${W} ${H}`} role="img" className="svg"
        aria-label={`Per-item median latency, ${items.length} items per arm. Median over items: ${arms.map((a) => `${a.quantization} ${a.latency_display} ms`).join(", ")}.`}>
        {ticks(lo, hi, 100).map((v) => (
          <g key={v}>
            <line x1={x(v)} x2={x(v)} y1={T} y2={H - B} className="grid" />
            <text x={x(v)} y={H - B + 22} textAnchor="middle" className="tick">{v}</text>
          </g>
        ))}
        <text x={(L + W - R) / 2} y={H - 8} textAnchor="middle" className="axis-label">Per-item median end-to-end latency (ms)</text>
        {series.map((s, k) => {
          const cy = T + band * (k + 0.5);
          return (
            <g key={s.arm.arm} className={`series s${k}`}>
              <text x={L - 10} y={cy + 5} textAnchor="end" className="point-label">{s.arm.quantization}</text>
              {s.vals.map((v, i) => (
                <circle key={i} cx={x(v)} cy={cy + jitter(i + k * 1000) * band * 0.7} r={3} className="dot" />
              ))}
              <line x1={x(s.arm.latency_ms)} x2={x(s.arm.latency_ms)} y1={cy - band * 0.45} y2={cy + band * 0.45} className="median" />
            </g>
          );
        })}
      </svg>
      <figcaption>
        <span className="tag tag-measured">measured</span> Each dot is one item's median latency over its five repetitions
        (RUN-EXP-003-0001); the vertical bar is the median over items ({arms.map((a) => `${a.quantization} ${a.latency_display} ms`).join(", ")}).
        Vertical spread inside each row is only for legibility. Answers were about two tokens long, so latency is mostly
        prefill; this does not transfer to long generations.
      </figcaption>
    </figure>
  );
}
