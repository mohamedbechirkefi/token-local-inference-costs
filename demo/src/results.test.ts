// SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0
import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { ResultsError, validateResults } from "./results";

const good = () => JSON.parse(readFileSync("public/data/results.json", "utf8"));

describe("validateResults", () => {
  it("accepts the exported results file", () => {
    const r = validateResults(good());
    expect(r.experiments.map((e) => e.id)).toEqual(["EXP-001", "EXP-002", "EXP-003"]);
    expect(r.items.length).toBe(300);
  });
  it("rejects a wrong schema name", () => {
    expect(() => validateResults({ ...good(), schema: "other" })).toThrow(ResultsError);
  });
  it("rejects an unsupported major version", () => {
    expect(() => validateResults({ ...good(), schema_version: "2.0.0" })).toThrow(ResultsError);
  });
  it("rejects a missing estimate", () => {
    const r = good();
    delete r.experiments[2].estimates[0].estimate;
    expect(() => validateResults(r)).toThrow(ResultsError);
  });
  it("rejects a non-finite number", () => {
    const r = good();
    r.experiments[0].estimates = [{ label: "x", kind: "k", estimate: "NaN", ci_low: null, ci_high: null, ci_level: null, unit: "" }];
    expect(() => validateResults(r)).toThrow(ResultsError);
  });
  it("rejects a half-open interval", () => {
    const r = good();
    r.experiments[0].estimates = [{ label: "x", kind: "k", estimate: 1, ci_low: 0, ci_high: null, ci_level: 0.95, unit: "" }];
    expect(() => validateResults(r)).toThrow(ResultsError);
  });
  it("rejects a malformed source hash", () => {
    expect(() => validateResults({ ...good(), sources: [{ path: "a", sha256: "zz" }] })).toThrow(ResultsError);
  });
  it("rejects an unknown outcome", () => {
    const r = good();
    r.experiments[0].outcome = "success";
    expect(() => validateResults(r)).toThrow(ResultsError);
  });
  it("rejects a missing frontier or a malformed arm", () => {
    const r = good();
    delete r.frontier;
    expect(() => validateResults(r)).toThrow(ResultsError);
    const s = good();
    s.frontier.arms[0].latency_q1_ms = s.frontier.arms[0].latency_ms + 1;
    expect(() => validateResults(s)).toThrow(ResultsError);
  });
  it("rejects item rows out of range, duplicated or missing", () => {
    const r = good();
    r.items[0].q4_strict = 1.5;
    expect(() => validateResults(r)).toThrow(ResultsError);
    const d = good();
    d.items[1].id = d.items[0].id;
    expect(() => validateResults(d)).toThrow(ResultsError);
    const e = good();
    e.items = [];
    expect(() => validateResults(e)).toThrow(ResultsError);
  });
  it("rejects a pending decision that is not shown as pending or lists one reading", () => {
    const r = good();
    r.pending_owner_decisions[0].status = "decided";
    expect(() => validateResults(r)).toThrow(ResultsError);
    const s = good();
    s.pending_owner_decisions[1].readings = ["only one"];
    expect(() => validateResults(s)).toThrow(ResultsError);
  });
  it("rejects a missing sandbox reference or sensitivity table", () => {
    const r = good();
    delete r.sandbox_reference.lenient;
    expect(() => validateResults(r)).toThrow(ResultsError);
    const s = good();
    s.sensitivity = [];
    expect(() => validateResults(s)).toThrow(ResultsError);
  });
});
