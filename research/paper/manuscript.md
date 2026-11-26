---
title: "Quantization cost and accuracy of a local 8B model on one laptop: a preregistered study with two failed experiments"
author: "[OWNER PLACEHOLDER: author line. Freeze decision C3 (2026-11-24) recorded \"Mohamed Bechir Kefi\", no affiliation; the owner confirms the final line before any release.]"
status: "Independent research manuscript / preprint draft, not peer-reviewed. M4 synthesis, 2026-11-25; EXP-001 and EXP-002 sections updated 2026-11-26 after the owner-approved rerun on Ollama 0.40.6 (DL-015, DL-016). Protocol v1.0 frozen 2026-11-24 (research/freeze.json)."
---

<!-- SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0 -->

**Status: independent research manuscript / preprint draft, not peer-reviewed.** Every number in this text comes from a committed result file; `research/publication/artifact_manifest.json` maps each one to its experiment, run, metric definition, result path, generator, hash and code revision. Values labelled *exploratory* come from re-analyses of committed records after the confirmatory analysis (JRN-0009, JRN-0013) and carry no confirmatory weight.

**Note on the title (for the owner).** The title was approved as written and is kept. It says "two failed experiments". After the rerun of 2026-11-26 this describes the first attempts of EXP-001 and EXP-002 (Ollama 0.9.6); on the second attempt EXP-002 is complete and EXP-001 ran its full matrix but met a frozen stopping criterion after the fact (Section 5.1). Whether the title changes is the owner's decision.

# Abstract

Running language models locally trades answer quality against latency and memory. The sources consulted for this study (a preliminary, non-systematic review) do not report task accuracy and resource use together, paired at the item level, on one consumer machine. This study asked how local model configurations trade off quality, latency and resource use on one Apple M1 Pro laptop (16 GB) running Ollama. Three experiments were preregistered and frozen by the owner before any model output was seen. On Ollama 0.9.6, two of them failed before sending any request: that runtime cannot render the chat template of one required model (ministral-3:8b), and the frozen protocol aborts a run when a model cannot be described. The owner then approved one change, the runtime version (0.9.6 to 0.40.6), and both frozen matrices were run again unchanged. The cold-start study (EXP-002) completed: the runtime-cold time-to-first-token penalty was 1,246.4 ms for phi4-mini:3.8b, 1,443.8 ms for llama3.1:8b and 6,039.8 ms for ministral-3:8b, an ordering by file size that the frozen rule counts as support, although ministral-3:8b also received a prompt about seven times longer. The primary comparison of model sizes (EXP-001) ran all 4,500 requests, but two blocks met frozen memory criteria that the runner does not enforce, one of them the stopping rule, so its confirmatory status is left to the owner. Its frozen strict analysis gives +16.00 percentage points [+9.67, +22.33] for llama3.1:8b and +33.33 [+27.67, +39.33] for ministral-3:8b over phi4-mini:3.8b; under lenient extraction the llama3.1:8b difference reverses (-9.33), because phi4-mini:3.8b often added text after the label. The third experiment (EXP-003, on 0.9.6) compared Llama 3.1 8B at Q8_0 and Q4_K_M on a fixed random subset of 300 ARC-Challenge test items, five greedy repetitions each (3,000 requests, no failures). Strict accuracy was 0.733 against 0.717: a difference of +1.67 percentage points, 95 % paired bootstrap interval [-1.00, +4.33], exact McNemar p = 0.332. No difference was detected; because no equivalence margin was frozen, this is not evidence of equivalence. Q8_0 used 56 % more runtime-reported model memory (9,162.4 against 5,872.0 MiB) and decoded more slowly (40.1 against 53.9 tokens/s), yet its median end-to-end latency was lower (437.7 against 477.5 ms), because these two-token answers are dominated by prefill. No latency comparison is made across runtime versions. The findings hold for this machine, these runtime versions, this benchmark and this prompt template only.

# Keywords

local inference; quantization; GGUF; latency; memory; preregistration; negative results

# 1. Introduction

Local inference on personal hardware moves the cost of a request from a provider's fee to the user's own memory, time and electricity, and quantized model files let 8-billion-parameter models run on a 16 GB laptop, as this study's runs show. The choice of a quantization level is usually made from file size and throughput tables (for example the llama.cpp quantization table, llamacpp-quantize) or from aggregate scaling results on datacentre hardware (dettmers2022kbit). What the sources consulted here do not give a user of one laptop is a paired measurement of task accuracy together with the latency and memory cost, at the item level and with uncertainty, on that laptop.

This study set out to provide such a measurement for the configurations installed on one machine. The research question (master prompt section 10) is: how do local model configurations trade off quality, latency and resource use? It was translated into three frozen experiments:

- **EXP-001 (primary):** do llama3.1:8b (A1) and ministral-3:8b (A2) differ in accuracy from the smallest installed instruction model, phi4-mini:3.8b (A0), all at Q4_K_M, and at what cost? H0_k: Delta_k = 0; H1_k: Delta_k != 0, Holm-corrected over two contrasts.
- **EXP-002:** is the runtime-cold time-to-first-token penalty larger for larger model files (A0 < A1 < A2)?
- **EXP-003:** for Llama 3.1 8B, does accuracy differ between Q8_0 and Q4_K_M, and what are the latency and memory costs of the higher precision? H0: Delta = 0; H1: Delta != 0.

The actual contributions are narrower than the plan, and are stated as such:

1. A preregistered, paired comparison of Q8_0 and Q4_K_M for one 8B model on one laptop, reporting accuracy with an item-level interval alongside runtime-reported memory, latency, time to first token and throughput (EXP-003).
2. A documented negative outcome and its resolution: two frozen experiments failed before any request because of a runtime and model-template incompatibility; after the owner approved a runtime upgrade as the only change, EXP-002 completed and EXP-001 ran its full matrix but met a frozen stopping criterion that the runner does not enforce (EXP-001, EXP-002).
3. An evidence pipeline in which every number in this manuscript maps to a committed result file, including an exploratory re-analysis that found and quantified a warm-up artefact in the runner.

No novelty is claimed beyond this scope.

# 2. Related work

The literature review (`research/literature_review.md`) is preliminary and not systematic; every source below was opened on 2026-11-24, when for arXiv papers only the abstract page was read. On 2026-11-25 (M6) the free arXiv full text of each cited paper was opened and each statement made here was checked against the page given in brackets (page numbers of the arXiv PDF version named in the literature review); the papers were not read cover to cover.

**Quantization and accuracy.** Dettmers and Zettlemoyer (dettmers2022kbit; full text checked, pp. 2, 8) report, from more than 35,000 experiments on models from 19M to 176B parameters, that 4-bit precision is generally optimal for the trade-off between total model bits and zero-shot accuracy. Dettmers et al. (dettmers2022int8; full text checked, pp. 1, 2, 4) report that 8-bit inference roughly halves memory without performance degradation. Lin et al. (lin2023awq; full text checked, pp. 2, 3) describe activation-aware weight-only quantization. These results concern quantization methods and scaling across many models; they do not measure the GGUF k-quant files used here on a laptop.

**Throughput tables.** The llama.cpp quantization documentation (llamacpp-quantize; page opened) lists, for Llama-3.1-8B, Q4_K_M at 4.58 GiB and 71.93 tokens/s and Q8_0 at 7.95 GiB and 50.93 tokens/s. The hardware for that table was not recorded in our notes, and it reports no task accuracy. These values are external reference points and are never mixed with our measurements.

**Multi-metric and energy evaluation.** HELM (liang2022helm; full text checked, pp. 3, 4) includes efficiency among the measured dimensions of language-model evaluation. Samsi et al. (samsi2023watts; full text checked, pp. 2 to 4) benchmark energy and performance of LLaMA models on V100 and A100 GPUs. Both concern datacentre-scale settings.

**Prompt sensitivity.** Sclar et al. (sclar2023format; full text checked, pp. 1, 9) report accuracy differences of up to 76 points from formatting changes alone (for LLaMA-2-13B) and recommend reporting a range over formats. This motivated sensitivity analysis S1, which was not run (Section 5.4).

**Position of this study.** This is a small replication-style measurement in a new setting (one consumer laptop, one runtime), not an extension of any method. It adds paired item-level accuracy to the kind of cost figures that tool documentation reports.

# 3. Background and formal model

Let i = 1, ..., n index the benchmark items (n = 300) and r = 0, ..., 4 the repetitions. For arm k, let y_ikr in {0, 1} be the strict correctness of the answer extracted from the response. Accuracy uses the per-item mean over repetitions,

c_ik = (1/5) sum_r y_ikr,   Acc_k = (1/n) sum_i c_ik,

and the primary estimand for a candidate arm k against baseline 0 is the paired difference

Delta_k = (1/n) sum_i (c_ik - c_i0).

The exact McNemar test uses majority correctness m_ik = 1[c_ik >= 0.5]; with five repetitions no tie occurs. The discordant counts are b = #{i : m_ik = 1, m_i0 = 0} and c = #{i : m_ik = 0, m_i0 = 1}, and the two-sided exact p-value is min(1, 2 sum_{j <= min(b, c)} C(b + c, j) / 2^(b + c)).

For timing, each item's five end-to-end latencies are reduced to their median L_ik, and arms are summarised by the median and quartiles of L_ik over items. Decode throughput is eval_count / eval_duration x 1e9 tokens/s and prefill throughput is prompt_eval_count / prompt_eval_duration x 1e9 tokens/s, both from the runtime's own counters (field definitions in ollama-api) and both summarised as medians over records. The named memory metric (amendment F7) is the runtime-reported model size from `/api/ps` at the end of each block, maximised over blocks, in MiB (2^20 bytes).

The mechanism stated in the EXP-003 protocol (item 2) is that higher precision reduces quantization error but increases the bytes read per generated token, lowering decode throughput on bandwidth-bound hardware. This mechanism is a stated expectation, not a verified property of this machine.

# 4. Methods

## 4.1 Design and protocol registration

The main protocol (`research/protocol.md`) and the three experiment protocols were drafted at M0, amended with nine owner-approved amendments (F1 to F9), and frozen by the owner on 2026-11-24 (G-FREEZE; decision DL-008). Their SHA-256 values are recorded in `research/freeze.json`; the runner refuses a confirmatory config unless the protocol, config and item-file hashes match. No real model output and no ARC item had been seen before the freeze (freeze record, C4). The EXP-002 runner mode and config were added under the owner's second-round approval (DL-009), and the EXP-002 penalty analysis was committed before any EXP-002 output (DL-010). All three experiments are confirmatory; the smoke runs and the M4 and rerun re-analyses are exploratory. On 2026-11-26 the owner chose option (a) for the failed EXP-001 and EXP-002: "upgrade Ollama and run the frozen EXP-001 and EXP-002 matrices unchanged, runtime version recorded" (`labs/_shared/owner-approvals-2026-11-26.md`, R-TOKEN-1). The runtime version is the only change, recorded as a dated deviation (DL-015); protocols, configs, seeds, item order, template, decoding parameters and code are unchanged, and the first attempts stay recorded as failed.

## 4.2 Data

ARC-Challenge (clark2018arc; full text checked, pp. 1 to 3), test split, 1,172 items, licence CC BY-SA 4.0 (dataset card arc-hf), downloaded from the Hugging Face repository `allenai/ai2_arc` at revision 210d026f. A simple random sample of 300 items without replacement was drawn once with seed 20261124; the item IDs and the SHA-256 of the source file are committed (`data/arc_challenge_test_subset_ids.json`, `data/manifest.json`), the question texts are not, and `scripts/fetch_arc.py` regenerates them. No tuning was done on these items. A chance floor (the mean of 1 / number of options) is 0.251 for this subset.

## 4.3 Configurations and baseline

All arms ran in Ollama on 127.0.0.1. EXP-003 and the failed first attempts of EXP-001 and EXP-002 used Homebrew Ollama 0.9.6; the second attempts of EXP-001 and EXP-002 used the official Ollama 0.40.6 darwin build (tarball SHA-256 b2b55434...f974, binary SHA-256 69fcb23a...c2ff; JRN-0010), started by the rerun session with no other client. The three EXP-001 model files were verified without any download: each weights blob matched its content digest, and the A0 and A1 template, parameter and Modelfile hashes were the same on both runtimes. EXP-001 and EXP-002 used A0 phi4-mini:3.8b (baseline, 2.49 GB), A1 llama3.1:8b (4.92 GB) and A2 ministral-3:8b (6.02 GB), all GGUF Q4_K_M. EXP-003 used `llama3.1:8b` (Q4_K_M, baseline) and `llama3.1:8b-instruct-q8_0` (Q8_0, pulled 2026-11-25, manifest digest b158ded7..., 8,540,789,934 bytes of layers; JRN-0005). qwen3.5:4b was excluded by the owner (F4). The owner accepted the Llama 3.1 Community License for this study (F6).

## 4.4 Measurement

Each request used the zero-shot template T1 (answer with the label only), temperature 0, num_predict 8, num_ctx 2048 and runtime seeds 0 to 4 for the five repetitions. Item order within an arm and arm order within a repetition were shuffled with seed 1000 + repetition, identically for both arms. Each arm block began with one discarded warm-up request. The client measured end-to-end latency and time to first token with `time.perf_counter_ns` on the streamed response. Per arm, the run manifest records the SHA-256 of the chat template, default system prompt, default parameters and Modelfile reported by `/api/show` (F8). A 10 Hz sampler recorded the resident memory of Ollama processes, system memory and swap. On 0.40.6 the model runner is a separate process named `llama-server`, which the frozen process filter does not match, so peak RSS on the rerun covers the server process only (limitation 27). Energy was to be modelled from wall-clock time and an assumed power range (F5); no energy was measured.

The M4 re-analysis found that the discarded warm-up request uses the block's first item (`runner.run_matrix`), so the first measured request of every block repeats a prompt the runtime has just processed (Section 5.4). The frozen protocol does not specify the warm-up prompt.

## 4.5 Statistical analysis

Paired bootstrap over items (10,000 resamples, seed 7, percentile 95 % intervals) for Delta, and the exact McNemar test. EXP-003 has a single contrast and no multiplicity correction; EXP-001 would have used Holm over two. The frozen contradiction rule: H1 is not supported if the 95 % interval contains 0 and the test does not reject at alpha 0.05, and this outcome is reported as "no detected difference, never as equivalence" (main protocol section 2). **No equivalence margin is defined in any frozen protocol**, so no equivalence test is possible. Timing and memory are secondary and descriptive. The frozen protocol also asks for a bootstrap interval for "the median latency ratio of each arm to the baseline"; the analysis code does not compute it and the text does not say whether this is a ratio of medians or a median of per-item ratios (DL-011 gap 1). Section 5.4 reports both readings as exploratory values; the definition remains the owner's choice.

The planned sample size assumed a discordant-pair proportion of 0.25, giving a 95 % half-width of about 5.7 points and a minimum detectable difference of about 9 points at 80 % power (main protocol section 7).

## 4.6 Reproducibility

Environment: `uv sync --frozen` from `uv.lock` (Python 3.12, numpy 2.3.4, psutil 7.1.0, jsonschema 4.25.1). Data: `python3 -I scripts/fetch_arc.py --repo .`. Run: `.venv/bin/token-lab run --config experiments/EXP-003.json`. Report, tables and figure: `.venv/bin/token-lab report --result results/confirmatory/RUN-EXP-003-0001/result.json`. Exploratory re-analysis: `.venv/bin/python -I scripts/m4_exploratory_exp003.py --repo .`. The confirmatory run used code revision 57f6187e7b450fea05eedbbee8c663943596a699; its manifest's `dirty` flag is true only because the tracked experiment journal was appended during the run (DL-011 deviation 2). The reruns used `.venv/bin/token-lab run --config experiments/EXP-001.json` and `--config experiments/EXP-002.json` with Ollama 0.40.6 on 127.0.0.1:11434, at code revisions ca3a08fb536fbb80196354b5bdc0b3c26b38aa56 (EXP-001) and eadcedd7e959af12d40df967f842528a0cbde954 (EXP-002), both with a clean tree; tables and figures come from `token-lab report`, and the exploratory checks from `.venv/bin/python -I scripts/rerun_exploratory_exp001.py --repo .`.

# 5. Results

**Table 1. Planned and executed matrices.**

| Experiment | Arms | Planned requests | Requests sent | Status |
|---|---|---|---|---|
| EXP-001, attempt 1 (Ollama 0.9.6) | A0, A1, A2 (Q4_K_M) | 4,500 | 0 | failed before any request |
| EXP-001, attempt 2 (Ollama 0.40.6) | A0, A1, A2 (Q4_K_M) | 4,500 | 4,500 | matrix complete, 0 request errors; stopping criterion met at block 11 of 15 and exclusion criterion at blocks 3 and 11, not enforced; status pending owner decision |
| EXP-002, attempt 1 (Ollama 0.9.6) | A0, A1, A2, cold and warm | 60 | 0 | failed before any request |
| EXP-002, attempt 2 (Ollama 0.40.6) | A0, A1, A2, cold and warm | 60 | 60 | complete, 0 request errors, 0 invalid start states, 0 excluded blocks |
| EXP-003 (Ollama 0.9.6) | Llama 3.1 8B Q4_K_M, Q8_0 | 3,000 | 3,000 | complete, 0 request errors, 0 excluded blocks |

## 5.1 EXP-001 (primary): first attempt failed; second attempt complete, stopping criterion met after the fact

**First attempt (2026-11-25, Ollama 0.9.6): failed, no result.** The run passed the freeze guard and the item checks, then aborted at the per-arm `/api/show` fingerprint required by F8: for ministral-3:8b the runtime returned HTTP 500 "template: :10: function currentDate not defined" (JRN-0007). No generation request was sent and no result file was written. The same error had appeared for every A2 request in the exploratory smoke run RUN-SMOKE-0005 (JRN-0006); M0 could not detect it because the server was not running then. The failure reflects runtime compatibility, not model quality.

**Second attempt (2026-11-26, Ollama 0.40.6, owner option a).** RUN-EXP-001-0001 started at 12:31:06Z with a 1-minute load average of 1.68, on AC power, with no model loaded, and took 1,849.1 s (JRN-0011). All 4,500 requests completed without a request error; determinism was 1.00 in every arm and each arm's accuracy was identical in all five repetitions. An exploratory smoke run on the new runtime (RUN-SMOKE-0007, JRN-0010) ran all three arms beforehand.

**Status under the frozen rules.** The runner does not enforce the block exclusion rule or the stopping rules (DL-011 gap 2), so every block was checked after the run (JRN-0013). Block 3 (A1, repetition 0) and block 11 (A0, repetition 3) had swap growth of 734.1 and 2,778.1 MiB, above the 512 MiB exclusion threshold, and block 11 also exceeded the stopping rule's 2 GiB ("abort on any sign of memory exhaustion ...; report as a failure", main protocol section 9). Under that rule as written, EXP-001 is a failure; the run did not stop and neither block was repeated. Because accuracy was identical in every repetition, the two blocks change no accuracy value; their timing and memory readings were taken under memory pressure. The analysis below is the frozen analysis computed on the complete matrix, and **whether it counts as confirmatory is the owner's decision** (DL-016).

**Table 6. EXP-001 paired accuracy contrasts against A0 phi4-mini:3.8b (RUN-EXP-001-0001, `contrasts.csv`; Holm over the two contrasts within each extraction rule).**

| Contrast | Extraction | n | Delta (pp) | 95 % CI (pp) | b | c | Holm-adjusted exact McNemar p |
|---|---|---|---|---|---|---|---|
| A1 llama3.1:8b minus A0 | strict (primary) | 300 | +16.00 | [+9.67, +22.33] | 75 | 27 | 2.1e-06 |
| A2 ministral-3:8b minus A0 | strict (primary) | 300 | +33.33 | [+27.67, +39.33] | 108 | 8 | 3.3e-23 |
| A1 llama3.1:8b minus A0 | lenient (S2) | 300 | -9.33 | [-14.67, -4.33] | 19 | 47 | 7.6e-04 |
| A2 ministral-3:8b minus A0 | lenient (S2) | 300 | +8.33 | [+4.00, +12.67] | 35 | 10 | 4.9e-04 |

**Accuracy.** Strict accuracy was 0.560 (A0), 0.720 (A1) and 0.893 (A2); lenient accuracy 0.813, 0.720 and 0.897. Under the frozen decision rule applied to the strict contrasts, both intervals exclude zero and both Holm-adjusted tests reject, so H0 is rejected for A1 and for A2. The frozen sensitivity analysis S2 changes the reading for A1: A0 answered with the label followed by text (for example "B. liquid") in 520 of 1,500 records on 104 items, which strict extraction scores as incorrect, and under lenient extraction A1 is 9.33 points *below* A0. By the frozen S2 text, format compliance rather than knowledge drives the strict A1 versus A0 difference. A2 is ahead of A0 under both rules (+33.33 and +8.33 points).

**Table 7. EXP-001 per-arm costs (RUN-EXP-001-0001, `metrics.csv`; descriptive).** Latency is summarised over the 300 per-item medians; time to first token and throughputs are medians over the 1,500 records of each arm.

| Measure | A0 phi4-mini:3.8b | A1 llama3.1:8b | A2 ministral-3:8b |
|---|---|---|---|
| Median of per-item median latency [Q1, Q3] (ms) | 221.6 [218.2, 307.7] | 434.8 [430.9, 555.2] | 476.8 [470.9, 606.9] |
| Median time to first token (ms) | 195.2 | 393.6 | 430.4 |
| Median decode throughput (tokens/s) | 88.6 | 49.1 | 45.7 |
| Median prompt length (prompt_eval_count, tokens) | 84 | 91.5 | 636 |
| Runtime-reported model memory (MiB) | 2,698.6 | 4,777.5 | 5,113.6 |
| Strict format failures (records of 1,500) | 520 | 10 | 5 |

Both larger arms were slower than A0 on every item. The latency ratio to A0 is shown under both readings of protocol section 8, as the owner decided (R-TOKEN-2; exploratory, JRN-0013): A1/A0 1.962 [1.767, 1.968] as a ratio of medians and 1.977 [1.973, 1.980] as a median of per-item ratios; A2/A0 2.151 [1.937, 2.157] and 2.162 [2.156, 2.166]. On 0.40.6 the ministral-3:8b template adds a default system text, so A2's prompts are about seven times longer than A0's and A1's; A2's latency includes this text. Peak RSS on this runtime does not include the model runner (Section 4.4) and is not reported. Figure 2 shows the per-item latency distributions.

![FIG-002. Per-item median end-to-end latency per arm in EXP-001 (RUN-EXP-001-0001, Ollama 0.40.6). Each dot is one item (n = 300 per arm); the red bar is the median over items, in ms. Generated by `token-lab report` from `result.json`.](../experiments/EXP-001/figures/FIG-002-exp001-latency.svg)

## 5.2 EXP-002: first attempt failed; second attempt complete

**First attempt (2026-11-25, Ollama 0.9.6).** EXP-002 aborted at the same step for the same reason (JRN-0007). No penalty was measured on that attempt.

**Second attempt (2026-11-26, Ollama 0.40.6, owner option a).** RUN-EXP-002-0001 started at 13:07:16Z with a 1-minute load average of 1.15, on AC power, with no model loaded, and took 99.3 s (JRN-0012). All 60 trials completed; every cold trial had a confirmed empty `/api/ps` before its request, no trial was invalid, the 1-hour cap was not reached and no block met an exclusion criterion.

**Table 8. EXP-002 runtime-cold penalty (RUN-EXP-002-0001, `cold_warm.csv`; 10 cold and 10 warm trials per arm; 95 % bootstrap intervals over trials).**

| Arm (file size) | Cold TTFT median [95 % CI] (ms) | Warm TTFT median [95 % CI] (ms) | Penalty [95 % CI] (ms) | Cold load median (ms) | Prompt length (tokens) |
|---|---|---|---|---|---|
| A0 phi4-mini:3.8b (2.49 GB) | 1,273.9 [1,269.2, 1,281.6] | 27.5 [25.7, 27.8] | 1,246.4 [1,242.3, 1,254.8] | 1,063.0 | 81 |
| A1 llama3.1:8b (4.92 GB) | 1,488.5 [1,485.3, 1,495.0] | 44.7 [44.0, 44.9] | 1,443.8 [1,440.5, 1,450.3] | 1,081.7 | 88 |
| A2 ministral-3:8b (6.02 GB) | 6,091.7 [5,362.2, 6,582.7] | 51.9 [51.7, 52.2] | 6,039.8 [5,310.1, 6,530.9] | 3,359.6 | 631 |

The penalty increases with file size and adjacent intervals do not overlap, so under the frozen rule **H1 is supported**; with three configurations this is descriptive evidence only. The penalty is not loading alone: cold prefill medians were 202.5, 403.0 and 2,716.3 ms against 22.4, 40.9 and 44.1 ms warm, and A2's prompt is about seven times longer than the others, so the size ordering is confounded with prompt length. "Cold" is runtime-cold only; the OS page cache was not purged. Figure 3 shows every trial.

![FIG-003. Cold and warm time to first token per arm in EXP-002 (RUN-EXP-002-0001, Ollama 0.40.6). Dots are raw trials; the red bar is the median and the red line its 95 % bootstrap interval. Generated by `token-lab report` from `result.json`.](../experiments/EXP-002/figures/FIG-003-exp002-cold-warm.svg)

## 5.3 EXP-003: quantization at fixed model

The run took 1,509.8 s (2026-11-25, 12:30:58Z to 12:56:08Z) on AC power, with no foreign model loaded and a largest block swap growth of 61.1 MiB, so no exclusion criterion was met. Both arms gave identical responses in all five repetitions for every item (determinism 1.00).

**Table 2. EXP-003 per-arm results (RUN-EXP-003-0001, `metrics.csv`).** Latency is summarised over the 300 per-item medians; time to first token and throughputs are medians over the 1,500 records of each arm, as the report generator computes them.

| Measure | Q4_K_M (baseline) | Q8_0 |
|---|---|---|
| Accuracy, strict (n = 300) | 0.717 | 0.733 |
| Accuracy, lenient | 0.720 | 0.737 |
| Strict format failures (records of 1,500) | 15 | 20 |
| Median of per-item median latency [Q1, Q3] over items (ms) | 477.5 [472.9, 603.2] | 437.7 [434.3, 547.2] |
| Median time to first token over records (ms) | 440.9 | 388.7 |
| Median decode throughput over records (tokens/s) | 53.9 | 40.1 |
| Median prefill throughput over records (tokens/s) | 214.4 | 245.3 |
| Runtime-reported model memory (MiB) | 5,872.0 | 9,162.4 |
| Peak resident memory of Ollama processes (MiB, secondary) | 965.0 | 932.3 |
| Determinism (identical responses across repetitions) | 1.00 | 1.00 |

**Table 3. EXP-003 paired accuracy contrast, Q8_0 minus Q4_K_M (`contrasts.csv`).**

| Extraction | n | Delta (pp) | 95 % CI (pp) | b | c | Exact McNemar p |
|---|---|---|---|---|---|---|
| Strict (primary) | 300 | +1.67 | [-1.00, +4.33] | 11 | 6 | 0.332 |
| Lenient (S2) | 300 | +1.67 | [-1.00, +4.33] | 11 | 6 | 0.332 |

**Accuracy.** The interval contains zero and the test does not reject, so under the frozen rule H0 is not rejected: no difference was detected. Only 17 of 300 items were discordant. The data are compatible with Q8_0 being up to 1.00 points worse or up to 4.33 points better than Q4_K_M on this subset; they do not establish that the two are equivalent.

**Cost.** Q8_0 used 3,290.4 MiB (56 %) more runtime-reported model memory and decoded at 0.744 times the rate of Q4_K_M. Its median time to first token and median end-to-end latency were nevertheless lower, because almost every answer was two tokens long (eval_count 2 in 1,485 Q4 and 1,480 Q8 records), so latency is governed by prefill, and Q8_0's prefill was faster. Figure 1 shows the per-item latency distributions.

![FIG-001. Per-item median end-to-end latency per arm in EXP-003 (RUN-EXP-003-0001). Each dot is one item (n = 300 per arm); the red bar is the median over items, in ms. Upper row: arm Q4 (llama3.1:8b, Q4_K_M); lower row: arm Q8 (llama3.1:8b-instruct-q8_0). The generated figure clips the start of the lower row's label; the committed result figure is not edited (M6, DL-014). Generated by `token-lab report` from `result.json`.](../experiments/EXP-003/figures/FIG-001-exp003-latency.svg)

## 5.4 Sensitivity analyses and robustness checks

**Table 4. Sensitivity analyses (frozen S1 to S4) and exploratory checks (JRN-0009, `results/exploratory/M4-EXPL-0001/`).**

| Check | Status | Result |
|---|---|---|
| S1 prompt template (could invalidate the interpretation) | not run | no frozen config; would need new inference |
| S2 strict versus lenient extraction | run (confirmatory analysis) | identical contrast (Table 3); format failures on 3 Q4 items and 4 Q8 items, all recovered by lenient extraction |
| S3 first versus last repetition latency | run (descriptive) | 478.1 to 477.4 ms (Q4), 440.0 to 437.8 ms (Q8); drift below 1 %, under the 10 % trigger |
| S4 modelled energy over a power range | not run | the frozen protocol states no power range |
| E1 latency ratio Q8/Q4, both readings (exploratory) | computed | ratio of medians 0.917 [0.916, 0.918]; median of per-item ratios 0.916 [0.916, 0.917]; Q8 faster on 296 of 300 items |
| E2 decode ratio over item medians (exploratory) | computed | 0.744 [0.743, 0.744] |
| E3 warm-up prompt reuse (exploratory) | found | the 10 first-in-block records took 102 to 135 ms against at least 325 ms for all others; medians of per-item medians unchanged (477.5 and 437.7 ms) without them |
| E4 prefill by prompt length (exploratory) | computed | prefill time rises in steps across 32-token bins, Q4 287 to 799 ms, Q8 251 to 697 ms; Q8 lower in every bin |
| E5 format failures and discordance (exploratory, post hoc) | computed | one format-failure item is discordant; excluding the 5 items with any strict failure gives +1.36 pp on 295 items |
| E6 arm position within a repetition (exploratory) | computed | median record latency changes by less than 1 ms between first and second position |
| E8 tokenizer (exploratory) | computed | prompt token counts identical between arms for all 1,500 item-repetition pairs |

The two frozen sensitivity analyses that were run (S2, S3) did not change the EXP-003 reading. The one the protocol identifies as able to invalidate the main interpretation (S1) was not run, so the accuracy result holds for template T1 only. The exploratory latency intervals are narrow because they resample items within one session; they say nothing about variation between sessions, runtime versions or machines.

**Table 5. Expected versus observed, under the frozen rules.**

| Experiment and quantity | Prediction (frozen) | Observation | Verdict |
|---|---|---|---|
| EXP-001 Delta_A1, Delta_A2, attempt 1 | H1: Delta_k != 0 (nondirectional) | none: 0 of 4,500 requests | not testable; experiment failed |
| EXP-001 Delta_A1, Delta_A2, attempt 2 (strict) | H1: Delta_k != 0 (nondirectional) | +16.00 pp [+9.67, +22.33] and +33.33 pp [+27.67, +39.33], Holm p below 0.05 | H0 rejected for both arms by the decision rule; stopping criterion met at block 11, so the confirmatory status is the owner's decision |
| EXP-001 S2, attempt 2 | if conclusions differ, format compliance drives accuracy | A1: -9.33 pp [-14.67, -4.33]; A2: +8.33 pp [+4.00, +12.67] | the A1 conclusion differs: attributed to format compliance; A2 unchanged in sign |
| EXP-002 penalty ordering, attempt 1 | H1: A0 < A1 < A2 | none: 0 of 60 requests | not testable; experiment failed |
| EXP-002 penalty ordering, attempt 2 | H1: A0 < A1 < A2 | 1,246.4, 1,443.8, 6,039.8 ms; adjacent CIs do not overlap | H1 supported (descriptive; confounded with prompt length) |
| EXP-003 Delta (accuracy) | H1: Delta != 0; protocol notes a small or undetected difference is plausible | +1.67 pp [-1.00, +4.33], p = 0.332 | H0 not rejected: no detected difference, not equivalence |
| EXP-003 decode throughput | lower for Q8_0 (mechanism, item 2) | ratio 0.744 | consistent (descriptive) |
| EXP-003 model memory | higher for Q8_0 (implied by file size) | ratio 1.56 | consistent (descriptive) |
| EXP-003 end-to-end latency | no frozen prediction; the decode mechanism suggests slower for Q8_0 | ratio 0.917, Q8_0 faster | contrary to the naive expectation; explained by prefill dominance (descriptive) |
| S2 | if conclusions differ, format compliance drives accuracy | identical contrasts | S2 does not invalidate |
| S3 | drift above 10 % triggers a report | below 1 % | not triggered |

# 6. Discussion

**What the evidence supports.** On this laptop, moving Llama 3.1 8B from Q4_K_M to Q8_0 produced no detected accuracy difference on 300 ARC-Challenge items, at the price of about 3.2 GiB more runtime memory. This must not be read as "Q4_K_M is as accurate as Q8_0": the point estimate favours Q8_0 (11 against 6 discordant items), and the 95 % interval extends to a gain of 4.33 points. The interval's lower end (-1.00 points) is a property of this 300-item subset and this bootstrap; because no non-inferiority or equivalence margin was preregistered, it supports no non-inferiority claim. The result is compatible with the statement of dettmers2022kbit (full text checked, p. 8) that 4-bit precision is generally near the best size and accuracy trade-off, but one model and one benchmark do not test that statement.

**Cost.** The decode ratio of 0.744 has the same direction as the ratio implied by the llama.cpp table (50.93 / 71.93, about 0.708). That table comes from unrecorded hardware and settings, so the comparison is a sanity check on direction, not a replication. The memory ratio (1.56) is lower than the ratio of the model files (8.54 against 4.92 GB, about 1.74). One plausible reason is that the runtime-reported size also includes the KV cache and other allocations at num_ctx 2048, which would be similar for both arms; the allocation was not decomposed, so this is unverified.

**Why Q8_0 was faster end to end.** With answers of two tokens, latency is mostly prefill, and prefill was faster for Q8_0 in every prompt-length bin (E4). The protocol's mechanism predicts slower *decoding* for Q8_0, which was observed; it does not predict prefill. A kernel-efficiency difference between the Q8_0 and Q4_K_M code paths during the compute-bound prefill phase is one possible explanation; it is not verified here. The latency ordering is expected to reverse for longer generations, where decoding dominates, but that is an inference, not a measurement.

**Competing explanations for the EXP-003 conclusions.** The protocols name the following (main protocol section 12; EXP-003 item 4):

- *Different conversion pipelines or chat templates.* The template, system prompt and parameter hashes are identical between arms; the Modelfile hashes differ, as expected from different weight blobs. The provenance of the two weight files is otherwise not audited. Partly addressed.
- *Instruction-following and format compliance.* S2 gave the same contrast, and excluding the format-failure items (post hoc, exploratory) left a difference of the same sign and similar size. Addressed for T1.
- *Tokenizer effects.* Prompt token counts were identical for every item and repetition (E8): the arms share a tokenizer. Addressed.
- *Runtime scheduling and caching.* Arm order alternated between repetitions and position changed latency by less than 1 ms (E6). The warm-up artefact (E3) affects one record per block, the same item in both arms, and leaves the per-item medians unchanged. Prompt caching beyond that case was not tested. Partly addressed.
- *Background load on a shared laptop.* The run used an owner-scheduled quiet-machine window (start load average 2.29 after waiting for it to fall below 2.5, AC power, no other client of the session's own Ollama server), repetition medians varied with a coefficient of variation of 0.002, and drift was below 1 %; about 3 GiB of swap was already in use before the run. Partly addressed.
- *Training-data contamination.* Both arms are the same model at different precision, so contamination would not bias the paired contrast, but it limits what ARC accuracy says about quality. Not tested.

**The two failures and the rerun.** The F8 rule, added at the freeze so that each arm's chat template would be hashed, made the failure visible before any request instead of letting the run proceed with one arm returning errors. The experience suggests that a runtime compatibility check of every arm belongs in the feasibility audit, before the freeze; in this study it could not happen because the runtime was not running at M0. The owner's choice of a runtime upgrade as the only change allowed the frozen matrices to run, at the price of two runtime versions in one study, so no latency comparison is made between EXP-003 and the other two experiments.

**What EXP-001 supports.** If the owner counts the accuracy analysis as confirmatory, A2 ministral-3:8b answered more items correctly than A0 phi4-mini:3.8b under both extraction rules, while the strict A1 advantage over A0 is a format-compliance effect: with lenient extraction A1 was below A0. The configurations differ in parameter count, architecture, training data, tokenizer and, on 0.40.6, prompt length (A2 receives a long default system text), so these are differences between configurations, not effects of size. Cost followed size: both larger arms took about twice as long per item and used about 1.8 to 1.9 times A0's runtime-reported memory. The two blocks that met the memory criteria are a reminder that system-wide swap on a shared 16 GB laptop is not under the experiment's control; the runtime kept the previous arm's model loaded when the next arm's model was loaded in some blocks (for example block 11, where ministral-3:8b stayed listed beside phi4-mini:3.8b).

**What EXP-002 supports.** Runtime-cold requests cost between about 1.2 and 6.0 s more than warm ones on this laptop, and the penalty grew with file size. Most of A2's larger penalty is loading (3,359.6 ms median) and prefill of its much longer prompt (2,716.3 ms median cold prefill), which a warm request largely avoids. The study cannot separate file size from prompt length with three configurations.

# 7. Limitations and threats to validity

The full list is in `research/limitations.md`. The most important:

- **Primary result pending the owner.** On Ollama 0.9.6 EXP-001 and EXP-002 failed. On 0.40.6 EXP-002 completed, and EXP-001 ran its full matrix but met the frozen memory-exhaustion stopping criterion in one block and the exclusion criterion in two, neither of which the runner enforces; its confirmatory status is the owner's decision. No accuracy value depends on those blocks.
- **Two runtime versions.** EXP-003 ran on 0.9.6 and EXP-001 and EXP-002 on 0.40.6. No latency, throughput or memory comparison is made across them.
- **Format compliance.** Strict extraction penalises A0's habit of adding text after the label (520 of 1,500 records); under lenient extraction the A1 versus A0 difference reverses.
- **Prompt length differs by arm on 0.40.6.** ministral-3:8b receives a default system text that makes its prompt about seven times longer and depends on the run date; its latency and cold-start penalty include it.
- **Not equivalence.** No equivalence margin was frozen, so the EXP-003 interval is only an interval. Differences of a few points are compatible with the data.
- **Power and its assumption.** The design assumed a discordant proportion of 0.25 and a minimum detectable difference of about 9 points. The observed discordance was much lower (17 of 300) and the interval correspondingly narrower (half-width 2.67 against a planned 5.66 points), but that does not create an equivalence test after the fact.
- **One template.** S1 was not run; prompt format can change accuracy substantially (sclar2023format).
- **One machine, one runtime version per experiment, one benchmark, short answers.** Nothing generalises to other hardware, runtimes, tasks or generation lengths.
- **Latency is prefill-dominated and descriptive.** The frozen latency-ratio interval is not implemented; the exploratory intervals cover within-session item variation only. Prefill rates depend on prompt length (E4).
- **Memory metrics.** The named metric is the runtime's own accounting, not an independent measurement. Peak RSS was lower for Q8_0 than for Q4_K_M and does not capture the model's Metal allocations; on 0.40.6 it does not include the model runner at all. It is secondary only.
- **Warm-up artefact.** Ten of 3,000 records were measured right after an identical warm-up prompt (E3).
- **Energy.** No energy figure is reported; S4 lacks a frozen power range.
- **Construct.** ARC-Challenge multiple-choice accuracy is a narrow proxy for quality; contamination is untested.

# 8. Ethics and responsible research

The study uses a public benchmark under CC BY-SA 4.0; only item IDs and hashes are redistributed. Models are used under their own licences (MIT, Llama 3.1 Community License accepted by the owner, Apache-2.0), and no weights are redistributed. No human subjects, personal data or paid services were involved; all inference was local. No claim is made about any hosted provider, commercial product or model internals. No ethics approval was needed or is claimed.

# 9. Conclusion and future work

On one Apple M1 Pro laptop with Ollama 0.9.6, Llama 3.1 8B at Q8_0 showed no detected accuracy difference from Q4_K_M on 300 ARC-Challenge items (+1.67 pp, 95 % CI [-1.00, +4.33]), while using 56 % more runtime-reported memory and decoding about a quarter more slowly; for two-token answers its end-to-end latency was lower. The primary comparison of model sizes and the cold-start experiment first failed because of a runtime and template incompatibility; rerun unchanged on Ollama 0.40.6 with the owner's approval, the cold-start penalty grew with file size (1,246.4 to 6,039.8 ms, confounded with prompt length), and the size comparison gave strict differences of +16.00 and +33.33 points over phi4-mini:3.8b, the first of which reverses under lenient extraction, with a frozen stopping criterion met after the fact. Feasible next steps, each needing the owner: decide the EXP-001 status under the stopping rule and whether blocks 3 and 11 are repeated; implement the exclusion and stopping rules in the runner; fix the definition of the latency-ratio interval; freeze configs for S1 and an S4 power range; and, if smaller accuracy differences matter, preregister an equivalence margin and a larger item set.

# 10. Data and code availability

Code, configs, protocols, item IDs, result files and this manuscript are in the project repository at `[OWNER PLACEHOLDER: repository URL, not published]`. Paths in this manuscript are relative to the repository root. The ARC-Challenge texts are regenerated with `scripts/fetch_arc.py` from the pinned Hugging Face revision; models are pulled from the Ollama registry by tag and verified by manifest digest. Commands are in Section 4.6; `research/publication/artifact_manifest.json` maps every number to its source.

# 11. Funding, competing interests and AI assistance

**Funding:** `[OWNER PLACEHOLDER: funding statement]`.

**Competing interests:** `[OWNER PLACEHOLDER: competing interests statement]`.

**AI assistance:** An AI system (Claude, Anthropic) was used as a research and development assistant for drafting protocols, code, tests, analyses and text under the owner's direction; it is not an author. The owner took every decision on the protocol, its freeze, the model download and any publication. Human verification of this draft is pending the owner's review (`research/publication/author_review.md`). The AI's internal review passes (`research/publication/review_pass_2.md`) are quality control, not peer review.

# References

- [clark2018arc] P. Clark, I. Cowhey, O. Etzioni, T. Khot, A. Sabharwal, C. Schoenick, O. Tafjord. Think you have Solved Question Answering? Try ARC, the AI2 Reasoning Challenge. arXiv:1803.05457, 2018. <https://arxiv.org/abs/1803.05457> (abstract page read 2026-11-24; full text v1 opened 2026-11-25 and the cited statements checked).
- [arc-hf] AI2 ARC dataset card. <https://huggingface.co/datasets/allenai/ai2_arc> (read 2026-11-24).
- [dettmers2022kbit] T. Dettmers, L. Zettlemoyer. The case for 4-bit precision: k-bit Inference Scaling Laws. arXiv:2212.09720, 2022. <https://arxiv.org/abs/2212.09720> (abstract page read 2026-11-24; full text v2 opened 2026-11-25 and the cited statements checked).
- [dettmers2022int8] T. Dettmers, M. Lewis, Y. Belkada, L. Zettlemoyer. LLM.int8(): 8-bit Matrix Multiplication for Transformers at Scale. arXiv:2208.07339, 2022. <https://arxiv.org/abs/2208.07339> (abstract page read 2026-11-24; full text v2 opened 2026-11-25 and the cited statements checked).
- [lin2023awq] J. Lin et al. AWQ: Activation-aware Weight Quantization for LLM Compression and Acceleration. arXiv:2306.00978, 2023. <https://arxiv.org/abs/2306.00978> (abstract page read 2026-11-24; full text v5 opened 2026-11-25 and the cited statements checked).
- [liang2022helm] P. Liang et al. Holistic Evaluation of Language Models. arXiv:2211.09110, 2022. <https://arxiv.org/abs/2211.09110> (abstract page read 2026-11-24; full text v2 opened 2026-11-25 and the cited statements checked).
- [samsi2023watts] S. Samsi et al. From Words to Watts: Benchmarking the Energy Costs of Large Language Model Inference. arXiv:2310.03003, 2023. <https://arxiv.org/abs/2310.03003> (abstract page read 2026-11-24; full text v1 opened 2026-11-25 and the cited statements checked).
- [sclar2023format] M. Sclar, Y. Choi, Y. Tsvetkov, A. Suhr. Quantifying Language Models' Sensitivity to Spurious Features in Prompt Design or: How I learned to start worrying about prompt formatting. arXiv:2310.11324, 2023. <https://arxiv.org/abs/2310.11324> (abstract page read 2026-11-24; full text v2 opened 2026-11-25 and the cited statements checked).
- [llamacpp-quantize] llama.cpp quantize README. <https://github.com/ggml-org/llama.cpp/blob/master/tools/quantize/README.md> (read 2026-11-24).
- [ollama-api] Ollama API documentation (main branch). <https://raw.githubusercontent.com/ollama/ollama/main/docs/api.md> (read 2026-11-24; the runtimes used are 0.9.6 and 0.40.6).

# Supplementary appendix

`research/paper/supplementary.md` gives the complete matrix, configurations and hashes, extended tables, the exploratory results, report links and every deviation and owner decision.
