// SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0
// Published results: loaded from public/data/results.json, which
// scripts/export_demo_data.py writes from committed results only.
// Validation fails closed: any missing or malformed field means no numbers are shown.

export const SCHEMA = "lab-demo-results";
export const SCHEMA_MAJOR = 1;

export interface Estimate {
  label: string;
  kind: string;
  estimate: number;
  ci_low: number | null;
  ci_high: number | null;
  ci_level: number | null;
  /** What the interval is (confidence interval, interquartile range, none). */
  interval_kind: string | null;
  unit: string;
  /** Exact text the manuscript prints for the estimate and interval; shown verbatim when present. */
  display: string | null;
  interval_display: string | null;
}

export interface Experiment {
  id: string;
  title: string;
  status: string;
  outcome: "failed" | "null" | "positive" | "not run" | "exploratory";
  verdict: string;
  estimates: Estimate[];
  claim_ids: string[];
  report_path: string;
  notes: string[];
}

export interface Assumption {
  name: string;
  value: string;
  source: string;
}

export interface Source {
  path: string;
  sha256: string;
}

export interface FrontierArm {
  arm: string;
  model: string;
  quantization: string;
  accuracy_strict: number;
  accuracy_display: string;
  memory_mib: number;
  memory_display: string;
  latency_ms: number;
  latency_q1_ms: number;
  latency_q3_ms: number;
  latency_display: string;
  latency_iqr_display: string;
  decode_tps: number;
  decode_display: string;
}

export interface NotMeasured {
  arm: string;
  model: string;
  experiment: string;
  reason: string;
}

export interface Frontier {
  note: string;
  arms: FrontierArm[];
  not_measured: NotMeasured[];
}

export interface ItemRow {
  id: string;
  q4_strict: number;
  q8_strict: number;
  q4_lenient: number;
  q8_lenient: number;
  q4_latency_ms: number;
  q8_latency_ms: number;
  strict_miss_any: boolean;
}

export interface ReferenceContrast {
  delta_pp: number;
  ci_low_pp: number;
  ci_high_pp: number;
  b: number;
  c: number;
  mcnemar_p: number;
}

export interface SensitivityRow {
  check: string;
  status: string;
  result: string;
}

export interface PendingDecision {
  id: string;
  title: string;
  status: string;
  readings: string[];
  source: string;
}

export interface DisplayException {
  text: string;
  reason: string;
}

export interface Results {
  schema: string;
  schema_version: string;
  project: string;
  question: string;
  status_label: string;
  code_revision: string;
  run_code_revision: string;
  sources: Source[];
  experiments: Experiment[];
  assumptions: Assumption[];
  limitations: string[];
  frontier: Frontier;
  items: ItemRow[];
  sandbox_reference: { strict: ReferenceContrast; lenient: ReferenceContrast };
  sensitivity: SensitivityRow[];
  pending_owner_decisions: PendingDecision[];
  display_exceptions: DisplayException[];
}

export class ResultsError extends Error {}

type Obj = Record<string, unknown>;

function obj(v: unknown, where: string): Obj {
  if (typeof v !== "object" || v === null || Array.isArray(v)) {
    throw new ResultsError(`${where}: expected an object`);
  }
  return v as Obj;
}

function str(o: Obj, k: string, where: string): string {
  const v = o[k];
  if (typeof v !== "string" || v.length === 0) {
    throw new ResultsError(`${where}.${k}: expected a non-empty string`);
  }
  return v;
}

function optStr(o: Obj, k: string, where: string): string | null {
  const v = o[k];
  if (v === null || v === undefined) return null;
  if (typeof v !== "string" || v.length === 0) throw new ResultsError(`${where}.${k}: expected a string or null`);
  return v;
}

function num(o: Obj, k: string, where: string, nullable = false): number | null {
  const v = o[k];
  if (nullable && v === null) return null;
  if (typeof v !== "number" || !Number.isFinite(v)) {
    throw new ResultsError(`${where}.${k}: expected a finite number`);
  }
  return v;
}

function req(o: Obj, k: string, where: string): number {
  return num(o, k, where) as number;
}

function unit01(o: Obj, k: string, where: string): number {
  const v = req(o, k, where);
  if (v < 0 || v > 1) throw new ResultsError(`${where}.${k}: expected a value in [0, 1]`);
  return v;
}

function positive(o: Obj, k: string, where: string): number {
  const v = req(o, k, where);
  if (v <= 0) throw new ResultsError(`${where}.${k}: expected a positive number`);
  return v;
}

function bool(o: Obj, k: string, where: string): boolean {
  const v = o[k];
  if (typeof v !== "boolean") throw new ResultsError(`${where}.${k}: expected a boolean`);
  return v;
}

function arr(o: Obj, k: string, where: string): unknown[] {
  const v = o[k];
  if (!Array.isArray(v)) throw new ResultsError(`${where}.${k}: expected an array`);
  return v;
}

function nonEmpty(o: Obj, k: string, where: string): unknown[] {
  const a = arr(o, k, where);
  if (a.length === 0) throw new ResultsError(`${where}.${k}: empty`);
  return a;
}

function strArr(o: Obj, k: string, where: string): string[] {
  return arr(o, k, where).map((v, i) => {
    if (typeof v !== "string") throw new ResultsError(`${where}.${k}[${i}]: expected a string`);
    return v;
  });
}

function estimate(v: unknown, where: string): Estimate {
  const o = obj(v, where);
  const e: Estimate = {
    label: str(o, "label", where),
    kind: str(o, "kind", where),
    estimate: req(o, "estimate", where),
    ci_low: num(o, "ci_low", where, true),
    ci_high: num(o, "ci_high", where, true),
    ci_level: num(o, "ci_level", where, true),
    interval_kind: optStr(o, "interval_kind", where),
    unit: typeof o.unit === "string" ? o.unit : "",
    display: optStr(o, "display", where),
    interval_display: optStr(o, "interval_display", where),
  };
  if ((e.ci_low === null) !== (e.ci_high === null)) {
    throw new ResultsError(`${where}: interval must have both bounds or neither`);
  }
  if (e.ci_low !== null && e.ci_high !== null && e.ci_low > e.ci_high) {
    throw new ResultsError(`${where}: ci_low exceeds ci_high`);
  }
  if (e.interval_display !== null && e.ci_low === null) {
    throw new ResultsError(`${where}: interval text without interval bounds`);
  }
  return e;
}

const OUTCOMES = ["failed", "null", "positive", "not run", "exploratory"] as const;

function frontier(v: unknown): Frontier {
  const o = obj(v, "frontier");
  const arms = nonEmpty(o, "arms", "frontier").map((x, i) => {
    const w = `frontier.arms[${i}]`;
    const a = obj(x, w);
    const r: FrontierArm = {
      arm: str(a, "arm", w),
      model: str(a, "model", w),
      quantization: str(a, "quantization", w),
      accuracy_strict: unit01(a, "accuracy_strict", w),
      accuracy_display: str(a, "accuracy_display", w),
      memory_mib: positive(a, "memory_mib", w),
      memory_display: str(a, "memory_display", w),
      latency_ms: positive(a, "latency_ms", w),
      latency_q1_ms: positive(a, "latency_q1_ms", w),
      latency_q3_ms: positive(a, "latency_q3_ms", w),
      latency_display: str(a, "latency_display", w),
      latency_iqr_display: str(a, "latency_iqr_display", w),
      decode_tps: positive(a, "decode_tps", w),
      decode_display: str(a, "decode_display", w),
    };
    if (!(r.latency_q1_ms <= r.latency_ms && r.latency_ms <= r.latency_q3_ms)) {
      throw new ResultsError(`${w}: median outside its interquartile range`);
    }
    return r;
  });
  const notMeasured = arr(o, "not_measured", "frontier").map((x, i) => {
    const w = `frontier.not_measured[${i}]`;
    const a = obj(x, w);
    return { arm: str(a, "arm", w), model: str(a, "model", w), experiment: str(a, "experiment", w), reason: str(a, "reason", w) };
  });
  return { note: str(o, "note", "frontier"), arms, not_measured: notMeasured };
}

function items(v: unknown[]): ItemRow[] {
  if (v.length < 10) throw new ResultsError("results.items: too few items");
  const seen = new Set<string>();
  return v.map((x, i) => {
    const w = `items[${i}]`;
    const o = obj(x, w);
    const r: ItemRow = {
      id: str(o, "id", w),
      q4_strict: unit01(o, "q4_strict", w),
      q8_strict: unit01(o, "q8_strict", w),
      q4_lenient: unit01(o, "q4_lenient", w),
      q8_lenient: unit01(o, "q8_lenient", w),
      q4_latency_ms: positive(o, "q4_latency_ms", w),
      q8_latency_ms: positive(o, "q8_latency_ms", w),
      strict_miss_any: bool(o, "strict_miss_any", w),
    };
    if (seen.has(r.id)) throw new ResultsError(`${w}: duplicate item id`);
    seen.add(r.id);
    return r;
  });
}

function reference(v: unknown, where: string): ReferenceContrast {
  const o = obj(v, where);
  const r = {
    delta_pp: req(o, "delta_pp", where),
    ci_low_pp: req(o, "ci_low_pp", where),
    ci_high_pp: req(o, "ci_high_pp", where),
    b: req(o, "b", where),
    c: req(o, "c", where),
    mcnemar_p: unit01(o, "mcnemar_p", where),
  };
  if (r.ci_low_pp > r.ci_high_pp) throw new ResultsError(`${where}: ci_low exceeds ci_high`);
  return r;
}

export function validateResults(raw: unknown): Results {
  const o = obj(raw, "results");
  if (o.schema !== SCHEMA) throw new ResultsError(`results.schema: expected "${SCHEMA}"`);
  const version = str(o, "schema_version", "results");
  if (Number(version.split(".")[0]) !== SCHEMA_MAJOR) {
    throw new ResultsError(`results.schema_version: unsupported major version ${version}`);
  }
  const experiments = arr(o, "experiments", "results").map((v, i) => {
    const w = `experiments[${i}]`;
    const e = obj(v, w);
    const outcome = str(e, "outcome", w);
    if (!(OUTCOMES as readonly string[]).includes(outcome)) throw new ResultsError(`${w}.outcome: unknown value`);
    return {
      id: str(e, "id", w),
      title: str(e, "title", w),
      status: str(e, "status", w),
      outcome: outcome as Experiment["outcome"],
      verdict: str(e, "verdict", w),
      estimates: arr(e, "estimates", w).map((x, j) => estimate(x, `${w}.estimates[${j}]`)),
      claim_ids: strArr(e, "claim_ids", w),
      report_path: str(e, "report_path", w),
      notes: strArr(e, "notes", w),
    };
  });
  if (experiments.length === 0) throw new ResultsError("results.experiments: empty");
  const rev = str(o, "code_revision", "results");
  const runRev = str(o, "run_code_revision", "results");
  if (!/^[0-9a-f]{7,40}$/.test(rev) || !/^[0-9a-f]{7,40}$/.test(runRev)) {
    throw new ResultsError("results: revisions must be git commit hashes");
  }
  const sr = obj(o.sandbox_reference, "sandbox_reference");
  return {
    schema: SCHEMA,
    schema_version: version,
    project: str(o, "project", "results"),
    question: str(o, "question", "results"),
    status_label: str(o, "status_label", "results"),
    code_revision: rev,
    run_code_revision: runRev,
    sources: nonEmpty(o, "sources", "results").map((v, i) => {
      const s = obj(v, `sources[${i}]`);
      const sha = str(s, "sha256", `sources[${i}]`);
      if (!/^[0-9a-f]{64}$/.test(sha)) throw new ResultsError(`sources[${i}].sha256: not a sha256`);
      return { path: str(s, "path", `sources[${i}]`), sha256: sha };
    }),
    experiments,
    assumptions: arr(o, "assumptions", "results").map((v, i) => {
      const a = obj(v, `assumptions[${i}]`);
      return {
        name: str(a, "name", `assumptions[${i}]`),
        value: str(a, "value", `assumptions[${i}]`),
        source: str(a, "source", `assumptions[${i}]`),
      };
    }),
    limitations: strArr(o, "limitations", "results"),
    frontier: frontier(o.frontier),
    items: items(nonEmpty(o, "items", "results")),
    sandbox_reference: {
      strict: reference(sr.strict, "sandbox_reference.strict"),
      lenient: reference(sr.lenient, "sandbox_reference.lenient"),
    },
    sensitivity: nonEmpty(o, "sensitivity", "results").map((v, i) => {
      const w = `sensitivity[${i}]`;
      const s = obj(v, w);
      return { check: str(s, "check", w), status: str(s, "status", w), result: str(s, "result", w) };
    }),
    pending_owner_decisions: nonEmpty(o, "pending_owner_decisions", "results").map((v, i) => {
      const w = `pending_owner_decisions[${i}]`;
      const p = obj(v, w);
      const status = str(p, "status", w);
      if (status !== "pending owner decision") throw new ResultsError(`${w}.status: must be "pending owner decision"`);
      const readings = strArr(p, "readings", w);
      if (readings.length < 2) throw new ResultsError(`${w}.readings: every reading must be listed`);
      return { id: str(p, "id", w), title: str(p, "title", w), status, readings, source: str(p, "source", w) };
    }),
    display_exceptions: arr(o, "display_exceptions", "results").map((v, i) => {
      const w = `display_exceptions[${i}]`;
      const x = obj(v, w);
      return { text: str(x, "text", w), reason: str(x, "reason", w) };
    }),
  };
}

export async function loadResults(url = "./data/results.json"): Promise<Results> {
  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) throw new ResultsError(`could not load ${url} (HTTP ${res.status})`);
  let raw: unknown;
  try {
    raw = await res.json();
  } catch {
    throw new ResultsError(`${url} is not valid JSON`);
  }
  return validateResults(raw);
}

/** Formats a number for display without inventing precision. */
export function fmt(x: number, digits = 3): string {
  if (Number.isInteger(x)) return x.toString();
  return Number(x.toPrecision(digits)).toString();
}

export function fmtEstimate(e: Estimate, digits = 3): string {
  return e.display ?? `${fmt(e.estimate, digits)}${e.unit ? " " + e.unit : ""}`;
}

export function fmtInterval(e: Estimate, digits = 3): string {
  if (e.interval_display !== null) return e.interval_display;
  if (e.ci_low === null || e.ci_high === null) return "no interval";
  const level = e.ci_level === null ? "" : `${Math.round(e.ci_level * 100)}% `;
  return `${level}[${fmt(e.ci_low, digits)}, ${fmt(e.ci_high, digits)}]`;
}
