<!-- SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0 -->
# Supplementary material

**Status: independent research manuscript / preprint draft, not peer-reviewed (M4, 2026-11-25; EXP-001 and EXP-002 entries updated 2026-11-26 after the owner-approved rerun on Ollama 0.40.6, DL-015, DL-016).** Companion to `research/paper/manuscript.md`. Every value maps to a committed file through `research/publication/artifact_manifest.json`.

## S1. Complete experimental matrix

| Experiment | Arms | Items | Repetitions or trials | Planned requests | Sent | Outcome | Report |
|-------------|-------------|-----------|----------|---------|--------|---------------|------------------|
| Smoke attempt, M2 (exploratory) | none | synthetic fixture | none | not applicable | 0 | runtime not running, exit 3, no output (JRN-0002) | `progress.md` (M2 session) |
| Smoke (exploratory) | A0, A1, A2 | 10 validation items | 2 | 60 | 60 (A2 all failed) | RUN-SMOKE-0005, JRN-0006 | `results/exploratory/RUN-SMOKE-0005/report.md` |
| Smoke cold/warm (exploratory) | A0 | 1 validation item (Mercury_7103180) | 5 cold, 5 warm | 10 | 10 | RUN-SMOKE-0006, JRN-0006 | `results/exploratory/RUN-SMOKE-0006/report.md` |
| EXP-001 attempt 1 (confirmatory, Ollama 0.9.6) | A0 phi4-mini:3.8b, A1 llama3.1:8b, A2 ministral-3:8b (Q4_K_M) | 300 test items | 5 | 4,500 | 0 | failed before any request (JRN-0007) | `research/experiments/EXP-001/report.md` |
| EXP-002 attempt 1 (confirmatory, Ollama 0.9.6) | A0, A1, A2 | 1 validation item (Mercury_192290) | 10 cold, 10 warm per arm | 60 | 0 | failed before any request (JRN-0007) | `research/experiments/EXP-002/report.md` |
| Smoke on 0.40.6 (exploratory) | A0, A1, A2 | 10 validation items | 2 | 60 | 60 | RUN-SMOKE-0007, JRN-0010 (0 failures) | `results/exploratory/RUN-SMOKE-0007/report.md` |
| EXP-001 attempt 2 (confirmatory, Ollama 0.40.6) | A0, A1, A2 (Q4_K_M) | 300 test items | 5 | 4,500 | 4,500 | matrix complete, RUN-EXP-001-0001 (JRN-0011); stopping criterion met at block 11, exclusion criterion at blocks 3 and 11, not enforced; status pending owner | `research/experiments/EXP-001/report.md` |
| EXP-002 attempt 2 (confirmatory, Ollama 0.40.6) | A0, A1, A2 | 1 validation item (Mercury_192290) | 10 cold, 10 warm per arm | 60 | 60 | complete, RUN-EXP-002-0001 (JRN-0012) | `research/experiments/EXP-002/report.md` |
| RERUN-EXPL-0001 (exploratory) | checks of RUN-EXP-001-0001 | 300 | none (no requests) | 0 | 0 | JRN-0013 | `results/exploratory/RERUN-EXPL-0001/` |
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
| RUN-EXP-001-0001 `result.json` | f95ee2055a9048559162cf8417a63f31682e5bf23dd724e0813b38e197cd003c |
| RUN-EXP-002-0001 `result.json` | d93a17aa3cf17dfcfebe335ab8ec0a23da89571f41e468963eb717cf831803da |
| RERUN-EXPL-0001 `exploratory_exp001.json` | a11b99d4d471dd757ea0b894779c538d403419e04017686be0c45d9a957443de |
| Ollama 0.40.6 `ollama-darwin.tgz` | b2b55434865a668decb494110d7fd970eed3ecc8837be2872f672ccbb95df974 |
| Ollama 0.40.6 `ollama` binary | 69fcb23ae7b95af30b5184998751f6158df84d0071f930670ee5c22db667c2ff |

Code revision of all M3 runs: 57f6187e7b450fea05eedbbee8c663943596a699. Rerun revisions (clean tree): ca3a08fb536fbb80196354b5bdc0b3c26b38aa56 (RUN-EXP-001-0001) and eadcedd7e959af12d40df967f842528a0cbde954 (RUN-EXP-002-0001); against 57f6187, the runner, analysis code, protocols and frozen configs are unchanged; `src/token_lab/report.py` gained the M6 PDF-builder changes (DL-014, Markdown, CSV and SVG outputs byte-identical) and the exploratory config `experiments/smoke-cold-warm.json` was committed at M3; the rest are records, reports, the demo and release files. Fixed settings of the matrix design: template T1, temperature 0, num_predict 8, num_ctx 2048, runtime seeds 0 to 4, order seed 1000 + repetition, one discarded warm-up per block, at most 2 retries, 10 Hz memory sampling. Per-arm `/api/show` hashes for EXP-003 (run manifest): chat template 948af274... (both arms), parameters 2801e61a... (both arms), no default system prompt (both arms), Modelfile 05e50568... (Q4_K_M) and eb2088ee... (Q8_0). Per-arm hashes for EXP-001 and EXP-002 on 0.40.6: A0 template 813f53fd..., Modelfile c2413937...; A1 template 948af274..., parameters 2801e61a..., Modelfile 05e50568...; A2 template 5b74c26b..., parameters e96fd3ce..., Modelfile bfc40cd3...; no default system prompt field for any arm (A2's template contains its own default system text).

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

- EXP-001: `research/experiments/EXP-001/report.md` (attempt 1 failed; attempt 2 matrix complete, stopping criterion met, status pending owner), run report `results/confirmatory/RUN-EXP-001-0001/report.md`
- EXP-002: `research/experiments/EXP-002/report.md` (attempt 1 failed; attempt 2 complete), run report `results/confirmatory/RUN-EXP-002-0001/report.md`
- EXP-003: `research/experiments/EXP-003/report.md` (complete), run report `results/confirmatory/RUN-EXP-003-0001/report.md`
- Evidence audit: `research/publication/evidence_audit.md`; second review pass: `research/publication/review_pass_2.md`

## S6. Deviations from the frozen protocol and owner decisions

| Item | Kind | Record |
|---|---|---|
| EXP-001 and EXP-002 aborted before any request (A2 template incompatible with Ollama 0.9.6) | failure | DL-011 deviation 1, JRN-0007 |
| Owner choice for EXP-001 and EXP-002 (a upgrade, b re-freeze, c keep failed) | decided 2026-11-26: option (a) (R-TOKEN-1) | DL-015 |
| Runtime version 0.9.6 -> 0.40.6 for EXP-001 and EXP-002 | dated deviation, owner-approved | DL-015 |
| EXP-001 blocks 3 and 11 meet the exclusion criterion and block 11 the stopping rule; not enforced, run not stopped, blocks not repeated | deviation found after the run; **pending owner** | DL-016, JRN-0011, JRN-0013 |
| Peak RSS on 0.40.6 excludes the runner process (`llama-server`) | instrumentation finding, frozen config not changed | DL-016, JRN-0010 |
| EXP-003 manifest `dirty: true` (journal appended during the run) | record deviation | DL-011 deviation 2 |
| Latency-ratio interval not implemented; definition open | gap; owner chose none, both readings stay shown (R-TOKEN-2) | DL-011 gap 1, DL-015; exploratory values in S4 and S7 |
| Block exclusion and repeat, 4-hour cap and memory abort not implemented in the runner | gap; nothing depended on it in RUN-EXP-003-0001 or RUN-EXP-002-0001; RUN-EXP-001-0001 met two criteria | DL-011 gap 2, DL-016 |
| S1 to S4 without frozen configs; S2 and S3 reported from the committed analysis, S1 and S4 not run | gap | DL-011 gap 3, DL-012 |
| Warm-up request repeats the block's first item | implementation finding, not fixed | DL-012 decision 5, JRN-0009 E3 |
| Protocol section 13 and item 21 command texts differ from the implemented CLI | documentation mismatch, left unchanged (not an approved amendment) | DL-008, `research/freeze.json` |
| Owner decisions applied | F1 to F9 (DL-008), EXP-002 runner (DL-009), M3 start ("Start next"), report approval ("approve all recommendations, RIGGED A"), M4 start ("Next") | `research/decision_log.md`, `progress.md` |

## S7. EXP-001 and EXP-002 rerun details (Ollama 0.40.6)

**EXP-001 blocks (`RUN-EXP-001-0001/result.json` blocks; JRN-0013 B).** Block order and swap growth: 1 A0 rep 0 (0.0 MiB), 2 A2 rep 0 (0.0), 3 A1 rep 0 (734.1, exclusion criterion), 4 A2 rep 1 (0.0), 5 A1 rep 1 (0.0), 6 A0 rep 1 (0.0), 7 A0 rep 2 (0.0), 8 A2 rep 2 (0.0), 9 A1 rep 2 (-8.0), 10 A2 rep 3 (0.0), 11 A0 rep 3 (2,778.1, exclusion criterion and stopping rule), 12 A1 rep 3 (-374.2), 13 A0 rep 4 (-48.0), 14 A1 rep 4 (-120.1), 15 A2 rep 4 (-1,608.8). Block wall times 25.7 to 155.0 s.

**EXP-001 per-repetition accuracy (JRN-0013 R).** Strict: A0 0.560, A1 0.720, A2 0.893 in all five repetitions; lenient: 0.813, 0.720, 0.897 in all five.

**EXP-001 per-block median prefill (JRN-0013 P).** A0 about 191 ms in repetitions 0, 1, 3 and 4 and 22.0 ms in repetition 2 (the block after A0 repetition 1); A1 388.5 to 390.2 ms; A2 422.2 to 422.5 ms.

**EXP-001 latency ratios to A0, both readings (exploratory, JRN-0013 E1).** A1/A0: ratio of medians 1.962 [1.767, 1.968], median of per-item ratios 1.977 [1.973, 1.980]. A2/A0: 2.151 [1.937, 2.157] and 2.162 [2.156, 2.166]. Bootstrap over items, 10,000 resamples, seed 7.

**EXP-001 strict format failures (JRN-0013 F).** A0 520 records on 104 items; A1 10 on 2; A2 5 on 1.

**EXP-002 trials (`RUN-EXP-002-0001/result.json`).** Arm order A0, A1, A2 (seed 2002); all 30 cold trials had an empty `/api/ps` before the request. Cold prefill medians 202.5, 403.0 and 2,716.3 ms; warm 22.4, 40.9 and 44.1 ms; prompt lengths 81, 88 and 631 tokens. The first cold trial of A0 (2,258.4 ms) and of A1 (7,803.0 ms) was the slowest of its arm.

