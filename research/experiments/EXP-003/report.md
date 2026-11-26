<!-- SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0 -->
# EXP-003 report: quantization at fixed model (Q4_K_M versus Q8_0)

**Status: CONFIRMATORY, complete (optional experiment in the frozen plan, run with its frozen config).**

## 1. Identification

- Experiment: EXP-003. Run: RUN-EXP-003-0001. Date: 2026-11-25. Protocol v1.0, frozen 2026-11-24 (owner, G-FREEZE), SHA-256 8196740a07ce6b0d0e254a23729aa18e5866e0b72b7ac3dd97b779e23a024068; main protocol ea86d0bb2d1864f69ac545bde1c8dd263276c8dbd9d1b3fee5b7a49b8dd4d2c3.
- Config `experiments/EXP-003.json`, canonical SHA-256 3ebe5b2a60e4ddb6ae1c8e1e35f3d316f35f0fd56272f90299b992e702065560.
- Code revision 57f6187e7b450fea05eedbbee8c663943596a699. Authorship: Mohamed Bechir Kefi, independent researcher (C3; owner, 2026-11-26, decision sheet, B3); the AI was used as a research and development assistant.

## 2. Executive summary

The question was whether Llama 3.1 8B at Q8_0 differs in accuracy from Q4_K_M on a fixed 300-item ARC-Challenge test subset on this laptop, and at what cost. Both arms ran 5 greedy repetitions on every item (3,000 requests, 0 failures). Strict accuracy was 0.733 for Q8_0 and 0.717 for Q4_K_M. The difference is Delta = +1.67 percentage points, 95 % paired bootstrap CI [-1.00, +4.33], exact McNemar p = 0.332 (b = 11, c = 6). Under the frozen rule this is no detected difference, not equivalence. Q8_0 used 9,162.4 MiB of runtime-reported model memory against 5,872.0 MiB for Q4_K_M. It decoded more slowly (40.1 against 53.9 tokens/s) but had a lower median end-to-end latency (437.7 against 477.5 ms), because these short-answer requests are dominated by prefill. Principal caveat: the minimum detectable difference is about 9 pp.

## 3. Rationale

dettmers2022kbit (abstract opened at M0; full text checked at M6, p. 8) reports that 4-bit precision is generally near the best trade-off between model size and accuracy. llamacpp-quantize (opened) lists for Llama-3.1-8B Q4_K_M 4.58 GiB and 71.93 t/s against Q8_0 7.95 GiB and 50.93 t/s, on hardware that was not recorded. The gap this experiment fills is paired task accuracy measured alongside those costs on this laptop.

## 4. Hypotheses and definitions

- H0: Delta = 0. H1: Delta != 0.
- Delta = (1/n) sum_i (c_i,Q8 - c_i,Q4), where c is per-item correctness averaged over the 5 repetitions, n = 300.
- Contradiction criterion: the 95 % paired CI contains 0 and the exact McNemar test (majority correctness) does not reject at alpha 0.05. There is a single contrast, so no multiplicity correction applies.
- Secondary measures: latency and throughput ratios, the runtime-reported model memory (`/api/ps` size, F7) and peak RSS.

## 5. Methodology

- Data: ARC-Challenge test split (CC BY-SA 4.0), Hugging Face `allenai/ai2_arc` at revision 210d026f. JSONL SHA-256 86ccaace...1f63. The subset is 300 items drawn with seed 20261124; the IDs are in `data/arc_challenge_test_subset_ids.json`.
- Arms: Q4 = `llama3.1:8b` (Q4_K_M, installed). Q8 = `llama3.1:8b-instruct-q8_0`, pulled 2026-11-25 12:03Z to 12:29Z with manifest digest b158ded76fa05be6bce8a682099ce5df8c5571340a04cf63a2923464679db576, model blob 8,540,775,552 bytes (JRN-0005).
- Decoding and prompt: template T1, temperature 0, num_predict 8, num_ctx 2048.
- Repetitions and order: runtime seeds 0 to 4. Arm and item order come from seed 1000 + repetition. One discarded warm-up request precedes each arm block.
- Statistics: paired bootstrap over items (10,000 resamples, seed 7, percentile intervals) and exact McNemar.
- Hardware and software: Apple M1 Pro (10 cores), 16 GB, macOS 15.3.1, AC power, Ollama 0.9.6. The server was started by this session and no other client used it.
- Budget: 3,000 requests, 4-hour cap, zero cost.

## 6. Implementation verification

- Before the run, the full suite passed (144 tests).
- Every frozen hash matched, and the runner checked the item file and the subset IDs before the first request.
- On the exploratory smoke run (RUN-SMOKE-0005), 21 of 21 hand recomputations of the metrics agreed with the analysis code (JRN-0006). The checks covered accuracy, correctness flags, TTFT < latency, throughput formulas, per-item median latency, determinism and runtime memory.
- Chat template, system prompt and parameter hashes are identical between the two arms. The Modelfile hashes differ, as expected from the different weight blobs.

## 7. Execution record

- Command: `nice -n 5 .venv/bin/token-lab run --config experiments/EXP-003.json`, then `token-lab report --result results/confirmatory/RUN-EXP-003-0001/result.json`.
- Start 2026-11-25T12:30:58Z, end 12:56:08Z, 1,509.8 s, exit 0.
- Quiet-machine readings:
  - Start: load average 2.29 / 3.09 / 3.04. The run waited for the 1-minute load to fall below 2.5 after the pull. AC power, no model loaded, swap used 3,073.6 MiB.
  - End: load 1.36 / 1.19 / 1.41.
- Counts: 10 blocks, 3,000 records, 0 request errors.
- Exclusion criteria, checked from the block records: none was met. All blocks ran on AC power with runtime 0.9.6 and no foreign model, and the largest block swap delta was 61.1 MiB.
- Deviations: the manifest's `dirty` flag is true only because the tracked experiment journal was appended during the run. Code, configs and protocols were unchanged (DL-011).

## 8. Results

| Arm | Accuracy strict | Accuracy lenient | Format failures (strict, of 1,500) | Median latency [Q1, Q3] (ms) | TTFT median (ms) | Decode (tok/s) | Prefill (tok/s) | Runtime model memory (MiB) | Peak RSS (MiB) | Determinism |
|---|---|---|---|---|---|---|---|---|---|---|
| Q4 llama3.1:8b | 0.717 | 0.720 | 15 | 477.5 [472.9, 603.2] | 440.9 | 53.9 | 214.4 | 5,872.0 | 965.0 | 1.00 |
| Q8 llama3.1:8b-instruct-q8_0 | 0.733 | 0.737 | 20 | 437.7 [434.3, 547.2] | 388.7 | 40.1 | 245.3 | 9,162.4 | 932.3 | 1.00 |

| Contrast | Extraction | n | Delta (pp) | 95 % CI (pp) | b | c | McNemar p |
|---|---|---|---|---|---|---|---|
| Q8 vs Q4 | strict (primary) | 300 | +1.67 | [-1.00, +4.33] | 11 | 6 | 0.332 |
| Q8 vs Q4 | lenient (S2) | 300 | +1.67 | [-1.00, +4.33] | 11 | 6 | 0.332 |

- Accuracy was identical in every repetition (Q4 0.717 ×5, Q8 0.733 ×5).
- Per-repetition median latency had a CV of 0.002 in both arms. Median latency moved from 478.1 to 477.4 ms (Q4) and from 440.0 to 437.8 ms (Q8) between the first and last repetition. This is a descriptive S3 reading, with drift below 1 %.
- Relative effects, as point values only: latency ratio Q8/Q4 = 0.917, decode ratio 0.744, memory ratio 1.56. The frozen interval for the latency ratio is not implemented (DL-011 gap 1).
- Figure FIG-001 (`figures/FIG-001-exp003-latency.svg`): per-item median latency per arm. Each dot is one item (n = 300 per arm); the red bar is the median over items, in ms.

## 9. Interpretation

- **Accuracy.** The observed difference is small and its interval includes zero. Only 17 of 300 items were discordant. This agrees with dettmers2022kbit's observation that 4-bit precision loses little. It is not evidence of equivalence, because the design can only detect differences of about 9 pp.
- **Cost.**
  - Q8_0 needs about 56 % more runtime-reported memory and decodes about 26 % more slowly, consistent with bandwidth-bound decoding and with the direction of llamacpp-quantize.
  - Its faster prefill (245 against 214 tok/s) is a measured observation, not explained here; kernel efficiency of the Q8_0 path is one possible explanation, unverified. Because outputs are about two tokens, prefill decides end-to-end latency, so Q8_0 was faster here. That ordering is expected to reverse for long generations; this is an inference, not measured.
- **Format compliance.** Q8_0 had more strict format failures (20 against 15 records, all recovered by lenient extraction). Lenient extraction did not change the contrast.

## 10. Threats to validity

- Internal: same session, same item order and same template, so the arms are well matched. The Q8_0 and Q4_K_M files come from different conversion pipelines; their template and parameters are identical, but the weights' provenance is not otherwise audited. About 3 GiB of swap was already in use before the run.
- External: one machine, one runtime version (0.9.6), one benchmark, short answers.
- Construct: ARC-Challenge multiple-choice accuracy is a narrow proxy for quality. Possible contamination is untested.
- Statistical: low power for small differences. Latency comparisons are descriptive, without intervals.

## 11. Conclusion and next experiment

On this laptop, the frozen design detected no accuracy difference between Llama 3.1 8B at Q8_0 and at Q4_K_M (+1.67 pp, CI -1.00 to +4.33). Q8_0 costs about 3.2 GiB more runtime memory and decodes more slowly, while its short-answer latency was lower. Possible next steps, all needing the owner:

- implement the frozen latency-ratio interval once the owner resolves its definition;
- run S1 (template sensitivity) under a frozen config;
- try a larger item set if smaller differences matter.

## 12. Reproduction appendix

- Environment: `../.tools/py/bin/uv sync --frozen --all-groups --all-extras` (Python 3.12, numpy 2.3.4, psutil 7.1.0, jsonschema 4.25.1).
- Data: `/usr/local/bin/python3 -I scripts/fetch_arc.py --repo .` (expected JSONL SHA-256 86ccaace4cd159b5c02b6b3339ebe8a7022a54f1b488e433c060b3bc38ac1f63).
- Models: `ollama pull llama3.1:8b-instruct-q8_0` (digest above). `llama3.1:8b` was installed before the study.
- Run: `.venv/bin/token-lab run --config experiments/EXP-003.json` (Ollama on 127.0.0.1:11434, AC power, no other client).
- Report and figures: `.venv/bin/token-lab report --result results/confirmatory/RUN-EXP-003-0001/result.json`.
- Raw outputs: `results/confirmatory/RUN-EXP-003-0001/` (result.json SHA-256 3a5b2e60f24444cbdd282bb2dcb43bc61feff836ce9c4257ec241f6c92255064; all hashes in `sha256_manifest.json`). Copies are in this folder: `config.json`, `run_manifest.json`, `metrics.csv`, `contrasts.csv`.
- Schema: result schema 1.0.0. The bootstrap is deterministic with seed 7, so a rerun should reproduce accuracy exactly and timing within run-to-run noise.

## Addendum (M4, 2026-11-25): exploratory re-analysis and evidence audit

This addendum adds no confirmatory result and changes no verdict. Source: `results/exploratory/M4-EXPL-0001/exploratory_exp003.json` (JRN-0009, DL-012), generated from the committed `result.json` without any new inference.

- **Latency ratio (DL-011 gap 1), exploratory.** Ratio of medians 0.917 [0.916, 0.918]; median of per-item ratios 0.916 [0.916, 0.917]; Q8_0 faster on 296 of 300 items. Both readings are shown because the frozen text does not choose; the choice is the owner's.
- **Warm-up prompt reuse.** The discarded warm-up request of each block uses the block's first item, so the first measured request repeats it. Those 10 records (one per block) took 102 to 135 ms against at least 325 ms for every other record. Removing them leaves both medians of per-item medians unchanged (477.5 and 437.7 ms). Recorded, not fixed (DL-012).
- **Prefill by prompt length.** Prefill time rises in steps across 32-token prompt-length bins in both arms and is lower for Q8_0 in every bin; the median prefill rate in section 8 summarises this mix of prompt lengths.
- **Format failures.** The strict failures are on 3 items for Q4 and 4 items for Q8; one of them is discordant. Excluding the 5 items with any failure gives +1.36 pp (post hoc, not a valid confirmatory analysis).
- **Equivalence.** The frozen protocols define no equivalence margin, so the interval in section 8 is not an equivalence result.
- **Summary levels.** In the results table, latency is summarised over the 300 per-item medians; TTFT and throughputs are medians over the 1,500 records of each arm.
