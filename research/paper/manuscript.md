---
title: "Quantization cost and accuracy of a local 8B model on one laptop: a preregistered study with two failed experiments"
author: "[OWNER PLACEHOLDER: author line. Freeze decision C3 (2026-11-24) recorded \"Mohamed Bechir Kefi\", no affiliation; the owner confirms the final line before any release.]"
status: "Independent research manuscript / preprint draft, not peer-reviewed. M4 synthesis, 2026-11-25. Protocol v1.0 frozen 2026-11-24 (research/freeze.json)."
---

<!-- SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0 -->

**Status: independent research manuscript / preprint draft, not peer-reviewed.** Every number in this text comes from a committed result file; `research/publication/artifact_manifest.json` maps each one to its experiment, run, metric definition, result path, generator, hash and code revision. Values labelled *exploratory* come from a re-analysis of committed records after the confirmatory analysis (JRN-0009) and carry no confirmatory weight.

# Abstract

Running language models locally trades answer quality against latency and memory. The sources consulted for this study (a preliminary, non-systematic review) do not report task accuracy and resource use together, paired at the item level, on one consumer machine. This study asked how local model configurations trade off quality, latency and resource use on one Apple M1 Pro laptop (16 GB) running Ollama 0.9.6. Three experiments were preregistered and frozen by the owner before any model output was seen. Two of them failed before sending any request: the installed runtime cannot render the chat template of one required model (ministral-3:8b), and the frozen protocol aborts a run when a model cannot be described. The primary comparison of model sizes (EXP-001) and the cold-start study (EXP-002) therefore produced no results. The third experiment (EXP-003) compared Llama 3.1 8B at Q8_0 and Q4_K_M on a fixed random subset of 300 ARC-Challenge test items, five greedy repetitions each (3,000 requests, no failures). Strict accuracy was 0.733 against 0.717: a difference of +1.67 percentage points, 95 % paired bootstrap interval [-1.00, +4.33], exact McNemar p = 0.332. No difference was detected; because no equivalence margin was frozen, this is not evidence of equivalence. Q8_0 used 56 % more runtime-reported model memory (9,162.4 against 5,872.0 MiB) and decoded more slowly (40.1 against 53.9 tokens/s), yet its median end-to-end latency was lower (437.7 against 477.5 ms), because these two-token answers are dominated by prefill. The findings hold for this machine, runtime, benchmark and prompt template only.

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
2. A documented negative outcome: two frozen experiments failed before any request because of a runtime and model-template incompatibility, with the failure mode, its detection point and the options left to the owner (EXP-001, EXP-002).
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

The main protocol (`research/protocol.md`) and the three experiment protocols were drafted at M0, amended with nine owner-approved amendments (F1 to F9), and frozen by the owner on 2026-11-24 (G-FREEZE; decision DL-008). Their SHA-256 values are recorded in `research/freeze.json`; the runner refuses a confirmatory config unless the protocol, config and item-file hashes match. No real model output and no ARC item had been seen before the freeze (freeze record, C4). The EXP-002 runner mode and config were added under the owner's second-round approval (DL-009), and the EXP-002 penalty analysis was committed before any EXP-002 output (DL-010). All three experiments are confirmatory; the smoke runs and the M4 re-analysis are exploratory.

## 4.2 Data

ARC-Challenge (clark2018arc; full text checked, pp. 1 to 3), test split, 1,172 items, licence CC BY-SA 4.0 (dataset card arc-hf), downloaded from the Hugging Face repository `allenai/ai2_arc` at revision 210d026f. A simple random sample of 300 items without replacement was drawn once with seed 20261124; the item IDs and the SHA-256 of the source file are committed (`data/arc_challenge_test_subset_ids.json`, `data/manifest.json`), the question texts are not, and `scripts/fetch_arc.py` regenerates them. No tuning was done on these items. A chance floor (the mean of 1 / number of options) is 0.251 for this subset.

## 4.3 Configurations and baseline

All arms ran in Ollama 0.9.6 on 127.0.0.1. EXP-001 and EXP-002 used A0 phi4-mini:3.8b (baseline, 2.49 GB), A1 llama3.1:8b (4.92 GB) and A2 ministral-3:8b (6.02 GB), all GGUF Q4_K_M. EXP-003 used `llama3.1:8b` (Q4_K_M, baseline) and `llama3.1:8b-instruct-q8_0` (Q8_0, pulled 2026-11-25, manifest digest b158ded7..., 8,540,789,934 bytes of layers; JRN-0005). qwen3.5:4b was excluded by the owner (F4). The owner accepted the Llama 3.1 Community License for this study (F6).

## 4.4 Measurement

Each request used the zero-shot template T1 (answer with the label only), temperature 0, num_predict 8, num_ctx 2048 and runtime seeds 0 to 4 for the five repetitions. Item order within an arm and arm order within a repetition were shuffled with seed 1000 + repetition, identically for both arms. Each arm block began with one discarded warm-up request. The client measured end-to-end latency and time to first token with `time.perf_counter_ns` on the streamed response. Per arm, the run manifest records the SHA-256 of the chat template, default system prompt, default parameters and Modelfile reported by `/api/show` (F8). A 10 Hz sampler recorded the resident memory of Ollama processes, system memory and swap. Energy was to be modelled from wall-clock time and an assumed power range (F5); no energy was measured.

The M4 re-analysis found that the discarded warm-up request uses the block's first item (`runner.run_matrix`), so the first measured request of every block repeats a prompt the runtime has just processed (Section 5.4). The frozen protocol does not specify the warm-up prompt.

## 4.5 Statistical analysis

Paired bootstrap over items (10,000 resamples, seed 7, percentile 95 % intervals) for Delta, and the exact McNemar test. EXP-003 has a single contrast and no multiplicity correction; EXP-001 would have used Holm over two. The frozen contradiction rule: H1 is not supported if the 95 % interval contains 0 and the test does not reject at alpha 0.05, and this outcome is reported as "no detected difference, never as equivalence" (main protocol section 2). **No equivalence margin is defined in any frozen protocol**, so no equivalence test is possible. Timing and memory are secondary and descriptive. The frozen protocol also asks for a bootstrap interval for "the median latency ratio of each arm to the baseline"; the analysis code does not compute it and the text does not say whether this is a ratio of medians or a median of per-item ratios (DL-011 gap 1). Section 5.4 reports both readings as exploratory values; the definition remains the owner's choice.

The planned sample size assumed a discordant-pair proportion of 0.25, giving a 95 % half-width of about 5.7 points and a minimum detectable difference of about 9 points at 80 % power (main protocol section 7).

## 4.6 Reproducibility

Environment: `uv sync --frozen` from `uv.lock` (Python 3.12, numpy 2.3.4, psutil 7.1.0, jsonschema 4.25.1). Data: `python3 -I scripts/fetch_arc.py --repo .`. Run: `.venv/bin/token-lab run --config experiments/EXP-003.json`. Report, tables and figure: `.venv/bin/token-lab report --result results/confirmatory/RUN-EXP-003-0001/result.json`. Exploratory re-analysis: `.venv/bin/python -I scripts/m4_exploratory_exp003.py --repo .`. The confirmatory run used code revision 57f6187e7b450fea05eedbbee8c663943596a699; its manifest's `dirty` flag is true only because the tracked experiment journal was appended during the run (DL-011 deviation 2).

# 5. Results

**Table 1. Planned and executed matrices.**

| Experiment | Arms | Planned requests | Requests sent | Status |
|---|---|---|---|---|
| EXP-001 | A0, A1, A2 (Q4_K_M) | 4,500 | 0 | failed before any request |
| EXP-002 | A0, A1, A2, cold and warm | 60 | 0 | failed before any request |
| EXP-003 | Llama 3.1 8B Q4_K_M, Q8_0 | 3,000 | 3,000 | complete, 0 request errors, 0 excluded blocks |

## 5.1 EXP-001 (primary): failed, no result

The run passed the freeze guard and the item checks, then aborted at the per-arm `/api/show` fingerprint required by F8: for ministral-3:8b the runtime returned HTTP 500 "template: :10: function currentDate not defined" (JRN-0007). No generation request was sent and no result file was written. The same error had appeared for every A2 request in the exploratory smoke run RUN-SMOKE-0005 (JRN-0006), which ran the morning of the confirmatory window; M0 could not detect it because the server was not running then. The failure reflects runtime compatibility, not model quality. **The study therefore has no evidence on the primary question**: nothing is claimed about A0 versus A1 versus A2. The exploratory smoke run produced accuracy values for A0 and A1 on 10 validation items; they were never intended as evidence and are not reported as such.

## 5.2 EXP-002: failed, no result

EXP-002 aborted at the same step for the same reason (JRN-0007). No cold-start penalty was measured and its ordering hypothesis is untested. An exploratory smoke run of the cold/warm mechanism on A0 alone (RUN-SMOKE-0006, a different item, a concurrent model download) is evidence only that the unload-and-check mechanism works.

The owner's choice for EXP-001 and EXP-002 is pending (DL-011, DL-012): (a) upgrade Ollama and run the frozen matrices unchanged, recording the new runtime version; (b) a new freeze without A2 or with another arm; (c) keep both recorded as failed. This manuscript decides nothing among them.

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
| EXP-001 Delta_A1, Delta_A2 | H1: Delta_k != 0 (nondirectional) | none: 0 of 4,500 requests | not testable; experiment failed |
| EXP-002 penalty ordering | H1: A0 < A1 < A2 | none: 0 of 60 requests | not testable; experiment failed |
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

**The two failures.** The F8 rule, added at the freeze so that each arm's chat template would be hashed, made the failure visible before any request instead of letting the run proceed with one arm returning errors. The cost is that the primary question is unanswered. The experience suggests that a runtime compatibility check of every arm belongs in the feasibility audit, before the freeze; in this study it could not happen because the runtime was not running at M0.

# 7. Limitations and threats to validity

The full list is in `research/limitations.md`. The most important:

- **No result on the primary question.** EXP-001 and EXP-002 failed; the only confirmatory result concerns two quantizations of one model, an experiment the plan called optional.
- **Not equivalence.** No equivalence margin was frozen, so the EXP-003 interval is only an interval. Differences of a few points are compatible with the data.
- **Power and its assumption.** The design assumed a discordant proportion of 0.25 and a minimum detectable difference of about 9 points. The observed discordance was much lower (17 of 300) and the interval correspondingly narrower (half-width 2.67 against a planned 5.66 points), but that does not create an equivalence test after the fact.
- **One template.** S1 was not run; prompt format can change accuracy substantially (sclar2023format).
- **One machine, one runtime version, one benchmark, short answers.** Nothing generalises to other hardware, runtimes, tasks or generation lengths.
- **Latency is prefill-dominated and descriptive.** The frozen latency-ratio interval is not implemented; the exploratory intervals cover within-session item variation only. Prefill rates depend on prompt length (E4).
- **Memory metrics.** The named metric is the runtime's own accounting, not an independent measurement. Peak RSS was lower for Q8_0 than for Q4_K_M and does not capture the model's Metal allocations; it is secondary only.
- **Warm-up artefact.** Ten of 3,000 records were measured right after an identical warm-up prompt (E3).
- **Energy.** No energy figure is reported; S4 lacks a frozen power range.
- **Construct.** ARC-Challenge multiple-choice accuracy is a narrow proxy for quality; contamination is untested.

# 8. Ethics and responsible research

The study uses a public benchmark under CC BY-SA 4.0; only item IDs and hashes are redistributed. Models are used under their own licences (MIT, Llama 3.1 Community License accepted by the owner, Apache-2.0), and no weights are redistributed. No human subjects, personal data or paid services were involved; all inference was local. No claim is made about any hosted provider, commercial product or model internals. No ethics approval was needed or is claimed.

# 9. Conclusion and future work

On one Apple M1 Pro laptop with Ollama 0.9.6, Llama 3.1 8B at Q8_0 showed no detected accuracy difference from Q4_K_M on 300 ARC-Challenge items (+1.67 pp, 95 % CI [-1.00, +4.33]), while using 56 % more runtime-reported memory and decoding about a quarter more slowly; for two-token answers its end-to-end latency was lower. The study's primary comparison of model sizes and its cold-start experiment produced no results because of a runtime and template incompatibility. Feasible next steps, each needing the owner: resolve EXP-001 and EXP-002 (options a to c above); fix the definition of the latency-ratio interval; freeze configs for S1 and an S4 power range; and, if smaller accuracy differences matter, preregister an equivalence margin and a larger item set.

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
- [ollama-api] Ollama API documentation (main branch). <https://raw.githubusercontent.com/ollama/ollama/main/docs/api.md> (read 2026-11-24; the installed runtime is 0.9.6).

# Supplementary appendix

`research/paper/supplementary.md` gives the complete matrix, configurations and hashes, extended tables, the exploratory results, report links and every deviation and owner decision.
