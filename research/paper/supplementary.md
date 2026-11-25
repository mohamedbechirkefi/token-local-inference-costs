<!-- SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0 -->
# Supplementary material

**Status: independent research manuscript / preprint draft, not peer-reviewed (M4, 2026-11-25).** Companion to `research/paper/manuscript.md`. Every value maps to a committed file through `research/publication/artifact_manifest.json`.

## S1. Complete experimental matrix

| Experiment | Arms | Items | Repetitions or trials | Planned requests | Sent | Outcome | Report |
|-------------|-------------|-----------|----------|---------|--------|---------------|------------------|
| Smoke attempt, M2 (exploratory) | none | synthetic fixture | none | not applicable | 0 | runtime not running, exit 3, no output (JRN-0002) | `progress.md` (M2 session) |
| Smoke (exploratory) | A0, A1, A2 | 10 validation items | 2 | 60 | 60 (A2 all failed) | RUN-SMOKE-0005, JRN-0006 | `results/exploratory/RUN-SMOKE-0005/report.md` |
| Smoke cold/warm (exploratory) | A0 | 1 validation item (Mercury_7103180) | 5 cold, 5 warm | 10 | 10 | RUN-SMOKE-0006, JRN-0006 | `results/exploratory/RUN-SMOKE-0006/report.md` |
| EXP-001 (confirmatory) | A0 phi4-mini:3.8b, A1 llama3.1:8b, A2 ministral-3:8b (Q4_K_M) | 300 test items | 5 | 4,500 | 0 | failed before any request (JRN-0007) | `research/experiments/EXP-001/report.md` |
| EXP-002 (confirmatory) | A0, A1, A2 | 1 validation item (Mercury_192290) | 10 cold, 10 warm per arm | 60 | 0 | failed before any request (JRN-0007) | `research/experiments/EXP-002/report.md` |
| EXP-003 (confirmatory) | llama3.1:8b Q4_K_M, llama3.1:8b-instruct-q8_0 | 300 test items | 5 | 3,000 | 3,000 | complete, RUN-EXP-003-0001 (JRN-0008) | `research/experiments/EXP-003/report.md` |
| M4-EXPL-0001 (exploratory) | re-analysis of RUN-EXP-003-0001 | 300 | none (no requests) | 0 | 0 | JRN-0009 | `results/exploratory/M4-EXPL-0001/` |

The simulated harness runs RUN-SMOKE-0001 to RUN-SMOKE-0004 (JRN-0003) used no model and carry no information about any model.

## S2. Configurations and hashes

| Item | SHA-256 |
|---------|-------------------|
| `research/protocol.md` v1.0 | ea86d0bb2d1864f69ac545bde1c8dd263276c8dbd9d1b3fee5b7a49b8dd4d2c3 |
| EXP-001 protocol | 1997317c931cf95d04c271ab2414aef82306f5976f1eea7262eb1e4d54fee8e4 |
| EXP-002 protocol | 54d46696e6b479c83235c789839ae3acaaaeeac1f38eccc6ef7c399d191c011e |
| EXP-003 protocol | 8196740a07ce6b0d0e254a23729aa18e5866e0b72b7ac3dd97b779e23a024068 |
| `experiments/EXP-001.json` (canonical) | 355d86f1cd3bc28373bef6e3e36c32828337583b0893d2b87d4c33fa48c7913e |
| `experiments/EXP-002.json` (canonical) | 6885e5f527df271897d6d2ba8f324fc73fd5135d250e92c8bd8dc94f4c3081cf |
| `experiments/EXP-003.json` (canonical) | 3ebe5b2a60e4ddb6ae1c8e1e35f3d316f35f0fd56272f90299b992e702065560 |
| ARC-Challenge test JSONL | 86ccaace4cd159b5c02b6b3339ebe8a7022a54f1b488e433c060b3bc38ac1f63 |
| Test subset IDs file | 8e694e8b842596dd642f4a022ddf438ff892994e7d0f69acdcae1e712f99d00f |
| RUN-EXP-003-0001 `result.json` | 3a5b2e60f24444cbdd282bb2dcb43bc61feff836ce9c4257ec241f6c92255064 |
| M4-EXPL-0001 `exploratory_exp003.json` | 65c421c4c26618020f01392da50e3a751611a164175ecd43ef6a8182cd111e6f |

Code revision of all M3 runs: 57f6187e7b450fea05eedbbee8c663943596a699. Fixed settings of the matrix design: template T1, temperature 0, num_predict 8, num_ctx 2048, runtime seeds 0 to 4, order seed 1000 + repetition, one discarded warm-up per block, at most 2 retries, 10 Hz memory sampling. Per-arm `/api/show` hashes for EXP-003 (run manifest): chat template 948af274... (both arms), parameters 2801e61a... (both arms), no default system prompt (both arms), Modelfile 05e50568... (Q4_K_M) and eb2088ee... (Q8_0).

## S3. Extended tables (EXP-003)

**Per-repetition values (`results/confirmatory/RUN-EXP-003-0001/report.md`).**

| Arm | Accuracy per repetition | Median latency per repetition (ms) | CV of repetition medians |
|---|---|---|---|
| Q4_K_M | 0.717 in all five | 478.09, 478.21, 476.15, 477.63, 477.40 | 0.002 |
| Q8_0 | 0.733 in all five | 439.98, 437.85, 437.69, 437.71, 437.78 | 0.002 |

**Block order (`result.json` blocks).** Repetition 0: Q4, Q8; 1: Q8, Q4; 2: Q4, Q8; 3: Q4, Q8; 4: Q8, Q4. Block wall times 140.4 to 160.8 s; largest block swap growth 61.1 MiB (Q8, repetition 0).

**Prefill duration by prompt length (exploratory, JRN-0009 E4; first-in-block records removed).**

| Prompt tokens | Records per arm | Q4_K_M median prefill (ms) | Q8_0 median prefill (ms) |
|---|---|---|---|
| 1 to 64 | 75 | 287.1 | 250.8 |
| 65 to 96 | 806 | 409.3 | 357.7 |
| 97 to 128 | 489 | 538.0 | 469.6 |
| 129 to 160 | 110 | 667.8 | 582.9 |
| 161 to 192 | 15 | 799.4 | 696.8 |

## S4. Robustness results (exploratory, JRN-0009)

- E1 latency ratio Q8/Q4: ratio of medians 0.917 [0.916, 0.918]; median of per-item ratios 0.916 [0.916, 0.917]; Q8_0 faster on 296 of 300 items. Bootstrap over items, 10,000 resamples, seed 7. Both readings are shown because the frozen definition is open (DL-011 gap 1).
- E2 decode ratio: 0.744 over records (as committed) and 0.744 [0.743, 0.744] over item medians; memory ratio 1.56, difference 3,290.4 MiB.
- E3 warm-up reuse: first-in-block records 102.1 to 106.9 ms (Q4) and 126.6 to 134.8 ms (Q8); minimum of all other records 347.2 ms (Q4) and 325.3 ms (Q8); medians of per-item medians unchanged.
- E5 strict format-failure items: Q4 Mercury_SC_407696, NYSEDREGENTS_2008_8_27, NYSEDREGENTS_2008_8_5; Q8 Mercury_7037555, Mercury_7223143, NYSEDREGENTS_2008_8_27, NYSEDREGENTS_2008_8_5. Only Mercury_SC_407696 is discordant. Delta without the 5 items with any strict failure: +1.36 pp (n = 295; post hoc, not a valid confirmatory analysis).
- E6 arm position: median record latency Q4 477.4 ms first, 478.0 ms second; Q8 437.8 ms first, 438.6 ms second.
- E7 precision: observed discordant proportion 0.057 against the assumed 0.25; observed CI half-width 2.67 pp against the planned 5.66 pp. No equivalence margin is frozen.
- E8 tokenizer: prompt token counts identical for all 1,500 item-repetition pairs.

## S5. Experiment report links

- EXP-001: `research/experiments/EXP-001/report.md` (failed)
- EXP-002: `research/experiments/EXP-002/report.md` (failed)
- EXP-003: `research/experiments/EXP-003/report.md` (complete), run report `results/confirmatory/RUN-EXP-003-0001/report.md`
- Evidence audit: `research/publication/evidence_audit.md`; second review pass: `research/publication/review_pass_2.md`

## S6. Deviations from the frozen protocol and owner decisions

| Item | Kind | Record |
|---|---|---|
| EXP-001 and EXP-002 aborted before any request (A2 template incompatible with Ollama 0.9.6) | failure | DL-011 deviation 1, JRN-0007 |
| Owner choice for EXP-001 and EXP-002 (a upgrade, b re-freeze, c keep failed) | **pending** (owner, 2026-11-25, "Next", does not decide it) | DL-011, DL-012 |
| EXP-003 manifest `dirty: true` (journal appended during the run) | record deviation | DL-011 deviation 2 |
| Latency-ratio interval not implemented; definition open | gap; **pending owner** | DL-011 gap 1; exploratory values in S4 |
| Block exclusion and repeat, 4-hour cap and memory abort not implemented in the runner | gap; nothing depended on it in RUN-EXP-003-0001 | DL-011 gap 2 |
| S1 to S4 without frozen configs; S2 and S3 reported from the committed analysis, S1 and S4 not run | gap | DL-011 gap 3, DL-012 |
| Warm-up request repeats the block's first item | implementation finding, not fixed | DL-012 decision 5, JRN-0009 E3 |
| Protocol section 13 and item 21 command texts differ from the implemented CLI | documentation mismatch, left unchanged (not an approved amendment) | DL-008, `research/freeze.json` |
| Owner decisions applied | F1 to F9 (DL-008), EXP-002 runner (DL-009), M3 start ("Start next"), report approval ("approve all recommendations, RIGGED A"), M4 start ("Next") | `research/decision_log.md`, `progress.md` |
