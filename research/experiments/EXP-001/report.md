<!-- SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0 -->
# EXP-001 report: accuracy and cost of installed local models of different sizes

**Status: CONFIRMATORY, FAILED before any request. No results exist.**

## 1. Identification

- Experiment: EXP-001. Date: 2026-11-25. Protocol v1.0, frozen 2026-11-24 (owner, G-FREEZE), SHA-256 1997317c931cf95d04c271ab2414aef82306f5976f1eea7262eb1e4d54fee8e4.
- Config canonical SHA-256 355d86f1cd3bc28373bef6e3e36c32828337583b0893d2b87d4c33fa48c7913e. Code revision 57f6187e7b450fea05eedbbee8c663943596a699.
- Authorship: Mohamed Bechir Kefi (C3); the AI was used as a research and development assistant.

## 2. Executive summary

- Question: do llama3.1:8b (A1) or ministral-3:8b (A2) differ in accuracy from phi4-mini:3.8b (A0) on a fixed 300-item ARC-Challenge subset, and at what cost?
- Outcome: the frozen run aborted before any generation request. The installed Ollama 0.9.6 cannot render the chat template of ministral-3:8b, which calls the function `currentDate`; this runtime does not define that function.
- No accuracy or cost result exists, and nothing about the hypotheses can be concluded.

## 3. Rationale

As in the frozen protocol, items 2 and 3. No result bears on it.

## 4. Hypotheses

Unchanged and untested. H0_k: Delta_k = 0 against H1_k: Delta_k != 0, for k in {A1, A2}, with Holm correction over the two contrasts.

## 5. Methodology (as frozen)

300 ARC-Challenge test items, three Q4_K_M arms, 5 repetitions (seeds 0 to 4), template T1, temperature 0, num_predict 8, num_ctx 2048. The planned matrix is 4,500 requests with a 4-hour cap.

## 6. Implementation verification

- Before the attempt: 144 tests passed, the frozen hashes matched, and the item checks passed.
- The exploratory smoke run RUN-SMOKE-0005 (JRN-0006) showed A0 and A1 working. Every A2 request, and `/api/show` for A2, returned HTTP 500 "template: :10: function currentDate not defined".

## 7. Execution record

- Command: `.venv/bin/token-lab run --config experiments/EXP-001.json`, at 2026-11-25T12:08:06Z.
- Machine state: load average 2.56 / 2.27 / 2.02, AC power. Ollama 0.9.6 was started by this session, with phi4-mini still loaded from the smoke run.
- What happened: the run passed the freeze guard and the item verification, then aborted at the per-arm `/api/show` fingerprint. Under amendment F8, a confirmatory run aborts if a model cannot be described.
- Output: exit 3, "backend error: HTTP 500 ... currentDate not defined". Generation requests sent: 0. No result file.
- Not retried: the cause is the runtime version, not a transient fault (JRN-0007, DL-011).

## 8. Results

None. The matrix was not executed: 0 of 4,500 planned requests.

## 9. Interpretation

The failure reflects runtime compatibility, not the models' quality. M0 could not detect it because the server was not running at that time. The installed model files were apparently pulled with a newer Ollama than the binary present on the machine; this is an inference, not verified.

## 10. Threats to validity

Not applicable to results. A rerun on another runtime version would change a recorded condition of the study (runtime version, protocol section 9).

## 11. Conclusion and next step

No conclusion. The owner should choose one of:
- (a) upgrade Ollama (a download, and a change for the owner's other projects), then run the frozen matrix unchanged with the new runtime version recorded;
- (b) a new freeze that replaces or drops A2;
- (c) keep EXP-001 recorded as failed.

## 12. Reproduction appendix

To reproduce the failure: start Ollama 0.9.6, then run `.venv/bin/token-lab run --config experiments/EXP-001.json`. Expected result: exit 3 with the error above. Records: `research/experiment_journal.jsonl` (JRN-0006, JRN-0007), `research/decision_log.md` (DL-011), smoke evidence `results/exploratory/RUN-SMOKE-0005/`.
