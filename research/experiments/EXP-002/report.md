<!-- SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0 -->
# EXP-002 report: cold-start versus warm latency of installed local models

**Status: CONFIRMATORY, FAILED before any request. No results exist.**

## 1. Identification

- Experiment: EXP-002. Date: 2026-11-25. Protocol v1.0, frozen 2026-11-24, SHA-256 54d46696e6b479c83235c789839ae3acaaaeeac1f38eccc6ef7c399d191c011e.
- Config canonical SHA-256 6885e5f527df271897d6d2ba8f324fc73fd5135d250e92c8bd8dc94f4c3081cf. Code revision 57f6187e7b450fea05eedbbee8c663943596a699, which includes the penalty analysis committed before any EXP-002 output (DL-010).
- Authorship: Mohamed Bechir Kefi (C3); the AI was used as a research and development assistant.

## 2. Executive summary

- Question: is the runtime-cold TTFT penalty larger for larger model files (A0 < A1 < A2)?
- Outcome: the frozen run aborted before any request, for the same cause as EXP-001. Ollama 0.9.6 cannot describe or run ministral-3:8b (A2).
- No penalty was measured, and the hypothesis is untested.

## 3. Rationale

As in the frozen protocol, item 3.

## 4. Hypotheses

Unchanged and untested.
- Penalty_k = median cold TTFT minus median warm TTFT (ms).
- H1: penalty(A0) < penalty(A1) < penalty(A2).
- Not supported on a reversal of that order in the point estimates, or on overlapping adjacent 95 % CIs; the latter case is reported as unresolved.

## 5. Methodology (as frozen)

- Trials: per arm, 10 cold and 10 warm, alternating and starting cold. Arm order comes from seed 2002. Runtime seed 0.
- Prompt and decoding: one fixed validation prompt (Mercury_192290, template T1), temperature 0, num_predict 8, num_ctx 2048.
- Statistics: bootstrap over trials (10,000 resamples, seed 7, percentile intervals).
- Budget: 1-hour cap.

## 6. Implementation verification

- The penalty analysis was implemented and tested on the simulated backend before any EXP-002 output (`tests/test_cold_warm_analysis.py`).
- The cold/warm mechanism was exercised on the real runtime in the exploratory RUN-SMOKE-0006, on arm A0 with a different validation item (Mercury_7103180):
  - 5 cold and 5 warm trials, all with a valid confirmed start state.
  - Exploratory values only, with a concurrent model download: cold TTFT median 968.4 ms, warm 55.1 ms, penalty 913.3 ms [903.2, 916.9].
- These values are not confirmatory and are not used for any claim.

## 7. Execution record

- Command: `.venv/bin/token-lab run --config experiments/EXP-002.json`, at 2026-11-25T12:08:06Z.
- Machine state: load average 2.56 / 2.27 / 2.02, AC power.
- What happened: the run passed the freeze guard and the item checks, then aborted at the A2 `/api/show` fingerprint (F8).
- Output: exit 3, "backend error: HTTP 500 ... currentDate not defined". Generation requests: 0. No result file (JRN-0007, DL-011).

## 8. Results

None. Requests run: 0 of 60.

## 9. Interpretation

Runtime compatibility failure; this says nothing about cold-start behaviour.

## 10. Threats to validity

Not applicable to results.

## 11. Conclusion and next step

No conclusion. The owner options are the same as for EXP-001 (DL-011, a to c). The analysis code is ready and frozen in behaviour (DL-010).

## 12. Reproduction appendix

To reproduce the failure: start Ollama 0.9.6, then run `.venv/bin/token-lab run --config experiments/EXP-002.json`. Expected result: exit 3. Records: JRN-0006, JRN-0007, DL-010, DL-011. Exploratory cold/warm smoke: `results/exploratory/RUN-SMOKE-0006/` (`cold_warm.csv`, `cold_warm.svg`).

## Addendum (M4, 2026-11-25)

The status is unchanged: **failed before any request, no results.** M4 ran no inference and did not contact the runtime. This experiment is reported in the manuscript (Sections 5.1, 5.2, Tables 1 and 5) with the same prominence as EXP-003, and no statement about its hypotheses is made anywhere. The owner's choice remains pending and is not decided by the M4 instruction (owner, 2026-11-25, "Next"):

- (a) upgrade Ollama (a download, and a runtime change for the owner's other projects), then run the frozen matrix unchanged with the new runtime version recorded as a deviation;
- (b) a new freeze that drops or replaces A2 ministral-3:8b, which is a new protocol version;
- (c) keep the experiment recorded as failed.

Records: DL-011, DL-012, JRN-0007; claims CLM-004 and CLM-005.
